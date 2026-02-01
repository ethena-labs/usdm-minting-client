from enum import Enum

from pydantic import BaseModel, Field


class Side(str, Enum):
    MINT = "MINT"
    REDEEM = "REDEEM"


class RfqRequest(BaseModel):
    """Parameters for requesting an RFQ quote."""

    pair: str = "USDC/USDm"  # default pair
    type_: str = "ALGO"  # quote type
    side: Side
    size: float  # human-readable amount
    benefactor: str


class RfqResponse(BaseModel):
    """RFQ quote response from API."""

    rfq_id: str
    pair: str
    side: Side
    size: float | str
    collateral_asset: str = Field(alias="collateral_asset_address")  # address
    collateral_amount: str  # base units string - DO NOT convert
    usdm_amount: str
    gas: str  # quoted gas as string
