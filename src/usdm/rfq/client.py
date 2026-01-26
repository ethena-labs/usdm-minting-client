import httpx

from usdm.config import Settings
from usdm.rfq.order import Order
from usdm.rfq.types import RfqRequest, RfqResponse


class RfqError(Exception):
    """Raised when RFQ request fails."""

    pass


class RfqClient:
    """Async client for RFQ API."""

    def __init__(self, settings: Settings):
        self.base_url = str(settings.api_url).rstrip("/")

    async def get_quote(self, request: RfqRequest) -> RfqResponse:
        """Request an RFQ quote.

        Args:
            request: RFQ parameters (pair, type, side, size)

        Returns:
            RfqResponse with quote details

        Raises:
            RfqError: If request fails or returns error
        """
        params = {
            "pair": request.pair,
            "type_": request.type_,
            "side": request.side.value,
            "size": request.size,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/rfq",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise RfqError(data["error"])

        return RfqResponse.model_validate(data)

    async def submit_order(self, order: Order, signature: str) -> str:
        """Submit a signed order.

        Args:
            order: Order dict from build_order
            signature: Hex signature from sign_order

        Returns:
            Transaction hash

        Raises:
            RfqError: If submission fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/order",
                params={"signature": signature},
                json=dict(order),  # TypedDict to dict for JSON
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise RfqError(data["error"])

        return data["tx"]
