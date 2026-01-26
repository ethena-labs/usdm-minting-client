import time
from dataclasses import dataclass

from usdm.allowances import get_allowance, send_approve_tx, wait_for_receipt
from usdm.config import Settings
from usdm.rfq.client import RfqClient, RfqError
from usdm.rfq.order import build_order
from usdm.rfq.types import RfqRequest
from usdm.rpc import get_web3
from usdm.signing import resolve_domain, sign_order


class AllowanceInsufficientError(Exception):
    """Raised when allowance is below required amount."""


def is_stale_quote_error(error: Exception | str) -> bool:
    message = str(error).lower()
    keywords = ["stale", "expired", "rfq expired", "quote expired", "order expired"]
    return any(keyword in message for keyword in keywords)


@dataclass(frozen=True)
class SubmitResult:
    tx_hash: str
    rfq_id: str
    requoted: bool


async def submit_with_allowance(
    settings: Settings,
    request: RfqRequest,
    benefactor: str,
    beneficiary: str | None = None,
    *,
    expiry_seconds: int = 60,
    max_quote_age_seconds: int | None = None,
    auto_approve: bool = False,
    recheck_allowance_after_approve: bool = True,
    requote_on_stale: bool = True,
) -> SubmitResult:
    client = RfqClient(settings)
    w3 = get_web3(settings)

    async def fetch_quote() -> tuple[float, object]:
        received_at = time.time()
        rfq = await client.get_quote(request)
        return received_at, rfq

    received_at, rfq = await fetch_quote()
    if (
        max_quote_age_seconds is not None
        and time.time() - received_at > max_quote_age_seconds
    ):
        received_at, rfq = await fetch_quote()

    order = build_order(
        rfq,
        benefactor=benefactor,
        beneficiary=beneficiary,
        expiry_seconds=expiry_seconds,
    )
    domain = resolve_domain(settings)
    signed = sign_order(settings.private_key, order, domain)

    spender = settings.allowance_spender or domain.verifying_contract
    required = int(rfq.collateral_amount)
    current = get_allowance(w3, rfq.collateral_asset, benefactor, spender)
    if current < required:
        if not auto_approve:
            raise AllowanceInsufficientError(
                f"Allowance {current} below required {required} for spender {spender}"
            )
        tx_hash = send_approve_tx(
            w3,
            settings.private_key,
            rfq.collateral_asset,
            spender,
            required,
        )
        wait_for_receipt(w3, tx_hash)
        if recheck_allowance_after_approve:
            current = get_allowance(w3, rfq.collateral_asset, benefactor, spender)
            if current < required:
                raise AllowanceInsufficientError(
                    f"Allowance {current} still below required {required} after approve"
                )

    try:
        tx = await client.submit_order(order, signed.signature)
        return SubmitResult(tx_hash=tx, rfq_id=rfq.rfq_id, requoted=False)
    except RfqError as exc:
        if not requote_on_stale or not is_stale_quote_error(exc):
            raise

    _, rfq = await fetch_quote()
    order = build_order(
        rfq,
        benefactor=benefactor,
        beneficiary=beneficiary,
        expiry_seconds=expiry_seconds,
    )
    signed = sign_order(settings.private_key, order, domain)

    required = int(rfq.collateral_amount)
    current = get_allowance(w3, rfq.collateral_asset, benefactor, spender)
    if current < required:
        raise AllowanceInsufficientError(
            f"Allowance {current} below required {required} after requote"
        )

    tx = await client.submit_order(order, signed.signature)
    return SubmitResult(tx_hash=tx, rfq_id=rfq.rfq_id, requoted=True)
