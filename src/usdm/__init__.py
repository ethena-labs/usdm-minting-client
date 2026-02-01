"""USDm Minting Client - Python SDK for mint/redeem operations."""

from usdm.allowances import get_allowance, send_approve_tx, wait_for_receipt
from usdm.config import Settings
from usdm.rfq import (
    AllowanceInsufficientError,
    DryRunResult,
    Order,
    RfqClient,
    RfqError,
    RfqRequest,
    RfqResponse,
    Side,
    SubmitResult,
    build_order,
    dry_run,
    submit_with_allowance,
)
from usdm.rpc import get_web3
from usdm.signing import (
    DomainResolutionError,
    EIP712Domain,
    ORDER_TYPE_MINT,
    ORDER_TYPE_REDEEM,
    SignedOrder,
    resolve_domain,
    sign_order,
)

__all__ = [
    # Config
    "Settings",
    "get_web3",
    # Allowances
    "get_allowance",
    "send_approve_tx",
    "wait_for_receipt",
    # Signing
    "EIP712Domain",
    "DomainResolutionError",
    "resolve_domain",
    "SignedOrder",
    "sign_order",
    "ORDER_TYPE_MINT",
    "ORDER_TYPE_REDEEM",
    # RFQ
    "RfqClient",
    "RfqError",
    "RfqRequest",
    "RfqResponse",
    "Side",
    "Order",
    "build_order",
    "submit_with_allowance",
    "SubmitResult",
    "AllowanceInsufficientError",
    "dry_run",
    "DryRunResult",
]
