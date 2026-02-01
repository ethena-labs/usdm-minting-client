"""Order builder for RFQ quotes.

Builds an Order dict from an RfqResponse that can be signed and submitted.
"""

import time
from typing import TypedDict

from usdm.rfq.types import RfqResponse, Side


class Order(TypedDict):
    """Order dict shaped for the POST /order API."""

    order_id: str
    order_type: str  # "MINT" or "REDEEM"
    expiry: int
    nonce: int
    benefactor: str
    beneficiary: str
    collateral_asset: str
    collateral_amount: int  # base units from RFQ
    usdm_amount: int  # wei from RFQ


def build_order(
    rfq: RfqResponse,
    benefactor: str,
    beneficiary: str | None = None,
    expiry_seconds: int = 60,
) -> Order:
    """Build an order from RFQ response.

    Args:
        rfq: RFQ response with quote details
        benefactor: Address providing collateral (for mint) or USDm (for redeem)
        beneficiary: Address receiving output (defaults to benefactor)
        expiry_seconds: Order validity in seconds (default 60)

    Returns:
        Order dict ready for API submission and signing
    """
    expiry = int(time.time()) + expiry_seconds

    return Order(
        order_id=rfq.rfq_id,
        order_type=Side.MINT.value if rfq.side == Side.MINT else Side.REDEEM.value,
        expiry=expiry,
        nonce=expiry,  # simple: use expiry as nonce
        benefactor=benefactor,
        beneficiary=beneficiary or benefactor,
        collateral_asset=rfq.collateral_asset,
        collateral_amount=int(rfq.collateral_amount),
        usdm_amount=int(rfq.usdm_amount),
    )
