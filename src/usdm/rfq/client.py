import json
import logging

import httpx

from usdm.config import Settings
from usdm.rfq.order import Order
from usdm.rfq.types import RfqRequest, RfqResponse

logger = logging.getLogger(__name__)


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
            "benefactor": request.benefactor,
        }

        logger.debug("RFQ request params: %s", json.dumps(params, indent=2))

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/rfq",
                params=params,
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise RfqError(data["error"])

        logger.info("RFQ response: %s", json.dumps(data, indent=2))
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
        order_payload = dict(order)
        logger.info("Order submission - signature: %s", signature)
        logger.info("Order submission - payload: %s", json.dumps(order_payload, indent=2))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/order",
                params={"signature": signature},
                json=order_payload,
            )

            if response.is_error:
                try:
                    data = response.json()
                except ValueError:
                    raise RfqError(
                        f"HTTP {response.status_code} error from RFQ API"
                    )
                if "error" in data:
                    raise RfqError(data["error"])
                raise RfqError(
                    f"HTTP {response.status_code} error from RFQ API"
                )

            data = response.json()

        if "error" in data:
            raise RfqError(data["error"])

        return data["tx"]
