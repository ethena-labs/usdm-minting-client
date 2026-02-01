"""Unit tests for usdm.rfq.client module."""

import pytest
import httpx
import respx

from usdm.config import Settings
from usdm.rfq.client import RfqClient, RfqError
from usdm.rfq.types import RfqRequest, Side


TEST_API_URL = "https://public.api.megausd.money"
TEST_BENEFACTOR = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"


@pytest.fixture
def rfq_client(settings):
    """Create an RfqClient instance."""
    return RfqClient(settings)


class TestRfqClientInit:
    """Tests for RfqClient initialization."""

    def test_client_stores_base_url(self, settings):
        """Client should store base URL from settings."""
        client = RfqClient(settings)

        assert TEST_API_URL in client.base_url

    def test_client_strips_trailing_slash(self, monkeypatch, env_settings):
        """Client should strip trailing slash from base URL."""
        monkeypatch.setenv("USDM_API_URL", "https://api.example.com/")
        settings = Settings()

        client = RfqClient(settings)

        assert not client.base_url.endswith("/")


class TestGetQuote:
    """Tests for RfqClient.get_quote method."""

    @respx.mock
    async def test_get_quote_returns_rfq_response(self, rfq_client):
        """get_quote should return parsed RfqResponse."""
        respx.get(f"{TEST_API_URL}/rfq").mock(
            return_value=httpx.Response(
                200,
                json={
                    "rfq_id": "quote-123",
                    "pair": "USDC/USDm",
                    "side": "MINT",
                    "size": 1000.0,
                    "collateral_asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "collateral_amount": "1000000000",
                    "usdm_amount": "1000000000000000000000",
                    "gas": "21000",
                },
            )
        )

        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )
        response = await rfq_client.get_quote(request)

        assert response.rfq_id == "quote-123"
        assert response.side == Side.MINT
        assert response.collateral_amount == "1000000000"

    @respx.mock
    async def test_get_quote_sends_correct_params(self, rfq_client):
        """get_quote should send correct query parameters."""
        route = respx.get(f"{TEST_API_URL}/rfq").mock(
            return_value=httpx.Response(
                200,
                json={
                    "rfq_id": "quote-123",
                    "pair": "USDC/USDm",
                    "side": "MINT",
                    "size": 1000.0,
                    "collateral_asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "collateral_amount": "1000000000",
                    "usdm_amount": "1000000000000000000000",
                    "gas": "21000",
                },
            )
        )

        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
            pair="USDC/USDm",
        )
        await rfq_client.get_quote(request)

        assert route.called
        call = route.calls[0]
        assert "side=MINT" in str(call.request.url)
        assert "size=1000" in str(call.request.url)

    @respx.mock
    async def test_get_quote_raises_on_api_error(self, rfq_client):
        """get_quote should raise RfqError on API error response."""
        respx.get(f"{TEST_API_URL}/rfq").mock(
            return_value=httpx.Response(
                200,
                json={"error": "Invalid request parameters"},
            )
        )

        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        with pytest.raises(RfqError) as exc_info:
            await rfq_client.get_quote(request)

        assert "Invalid request parameters" in str(exc_info.value)

    @respx.mock
    async def test_get_quote_raises_on_http_error(self, rfq_client):
        """get_quote should raise on HTTP error status."""
        respx.get(f"{TEST_API_URL}/rfq").mock(
            return_value=httpx.Response(500, json={"error": "Internal server error"})
        )

        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor=TEST_BENEFACTOR,
        )

        with pytest.raises(httpx.HTTPStatusError):
            await rfq_client.get_quote(request)


class TestSubmitOrder:
    """Tests for RfqClient.submit_order method."""

    @respx.mock
    async def test_submit_order_returns_tx_hash(self, rfq_client, sample_order):
        """submit_order should return transaction hash."""
        respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(
                200,
                json={"tx": "0x" + "ab" * 32},
            )
        )

        result = await rfq_client.submit_order(sample_order, "0xsignature")

        assert result == "0x" + "ab" * 32

    @respx.mock
    async def test_submit_order_sends_signature_param(self, rfq_client, sample_order):
        """submit_order should send signature as query param."""
        route = respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(200, json={"tx": "0x" + "ab" * 32})
        )

        await rfq_client.submit_order(sample_order, "0xtest_signature")

        assert route.called
        call = route.calls[0]
        assert "signature=0xtest_signature" in str(call.request.url)

    @respx.mock
    async def test_submit_order_sends_order_as_json_body(self, rfq_client, sample_order):
        """submit_order should send order as JSON body."""
        route = respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(200, json={"tx": "0x" + "ab" * 32})
        )

        await rfq_client.submit_order(sample_order, "0xsignature")

        assert route.called
        call = route.calls[0]
        assert b"order_id" in call.request.content

    @respx.mock
    async def test_submit_order_raises_on_error_field(self, rfq_client, sample_order):
        """submit_order should raise RfqError when response contains error."""
        respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(
                200,
                json={"error": "Order expired"},
            )
        )

        with pytest.raises(RfqError) as exc_info:
            await rfq_client.submit_order(sample_order, "0xsignature")

        assert "Order expired" in str(exc_info.value)

    @respx.mock
    async def test_submit_order_raises_on_error_name(self, rfq_client, sample_order):
        """submit_order should raise RfqError when response contains error_name."""
        respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(
                200,
                json={"error_name": "STALE_QUOTE", "error_code": 1001},
            )
        )

        with pytest.raises(RfqError) as exc_info:
            await rfq_client.submit_order(sample_order, "0xsignature")

        error_data = exc_info.value.args[0]
        assert error_data["error_name"] == "STALE_QUOTE"

    @respx.mock
    async def test_submit_order_raises_on_http_error(self, rfq_client, sample_order):
        """submit_order should raise RfqError on HTTP error status."""
        respx.post(f"{TEST_API_URL}/order").mock(
            return_value=httpx.Response(400, json={"message": "Bad request"})
        )

        with pytest.raises(RfqError) as exc_info:
            await rfq_client.submit_order(sample_order, "0xsignature")

        assert "400" in str(exc_info.value)


class TestRfqError:
    """Tests for RfqError exception."""

    def test_rfq_error_is_exception(self):
        """RfqError should be an Exception."""
        assert issubclass(RfqError, Exception)

    def test_rfq_error_with_string_message(self):
        """RfqError should accept string message."""
        error = RfqError("Quote expired")

        assert str(error) == "Quote expired"

    def test_rfq_error_with_dict_message(self):
        """RfqError should accept dict message."""
        error_data = {"error_name": "STALE_QUOTE", "error_code": 1001}
        error = RfqError(error_data)

        assert error.args[0] == error_data
