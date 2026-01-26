from enum import Enum

from pydantic import BaseModel


class Side(str, Enum):
    MINT = "MINT"
    REDEEM = "REDEEM"


class RfqRequest(BaseModel):
    """Parameters for requesting an RFQ quote."""

    pair: str = "USDC/USDe"  # default pair
    type_: str = "STANDARD"  # quote type
    side: Side
    size: float  # human-readable amount


class RfqResponse(BaseModel):
    """RFQ quote response from API."""

    rfq_id: str
    pair: str
    side: Side
    size: float
    collateral_asset: str  # address
    collateral_amount: str  # wei string - DO NOT convert
    usde_amount: str  # wei string - DO NOT convert
    gas: int
