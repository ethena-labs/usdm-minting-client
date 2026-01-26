"""Order builder for RFQ quotes.

Builds an Order dict from an RfqResponse that can be signed and submitted.
IMPORTANT: Amounts are copied directly from RFQ - no conversion or rounding.
"""

import time
from typing import TypedDict

from usdm.rfq.types import RfqResponse, Side
from usdm.signing.order_types import ORDER_TYPE_MINT, ORDER_TYPE_REDEEM


class Order(TypedDict):
    """Order dict matching EIP-712 Order schema."""

    order_id: str
    order_type: int
    expiry: int
    nonce: int
    benefactor: str
    beneficiary: str
    collateral_asset: str
    collateral_amount: str  # wei string from RFQ
    usde_amount: str  # wei string from RFQ


def build_order(
    rfq: RfqResponse,
    benefactor: str,
    beneficiary: str | None = None,
    expiry_seconds: int = 60,
) -> Order:
    """Build an order from RFQ response.

    IMPORTANT: This copies amounts directly from RFQ without any
    conversion or rounding. The API provides exact wei values.

    Args:
        rfq: RFQ response with quote details
        benefactor: Address providing collateral (for mint) or USDe (for redeem)
        beneficiary: Address receiving output (defaults to benefactor)
        expiry_seconds: Order validity in seconds (default 60)

    Returns:
        Order dict ready for signing
    """
    expiry = int(time.time()) + expiry_seconds

    return Order(
        order_id=rfq.rfq_id,
        order_type=ORDER_TYPE_MINT if rfq.side == Side.MINT else ORDER_TYPE_REDEEM,
        expiry=expiry,
        nonce=expiry,  # simple: use expiry as nonce
        benefactor=benefactor,
        beneficiary=beneficiary or benefactor,
        collateral_asset=rfq.collateral_asset,
        collateral_amount=rfq.collateral_amount,  # direct from RFQ
        usde_amount=rfq.usde_amount,  # direct from RFQ
    )
