"""Unit tests for usdm.rfq.types module."""

import pytest
from pydantic import ValidationError

from usdm.rfq.types import RfqRequest, RfqResponse, Side


class TestSideEnum:
    """Tests for Side enum."""

    def test_side_has_mint_value(self):
        """Side enum should have MINT value."""
        assert Side.MINT.value == "MINT"

    def test_side_has_redeem_value(self):
        """Side enum should have REDEEM value."""
        assert Side.REDEEM.value == "REDEEM"

    def test_side_is_string_enum(self):
        """Side should be a string enum."""
        assert isinstance(Side.MINT, str)
        assert Side.MINT == "MINT"


class TestRfqRequest:
    """Tests for RfqRequest model."""

    def test_rfq_request_with_minimal_fields(self):
        """RfqRequest should work with required fields only."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        )

        assert request.side == Side.MINT
        assert request.size == 1000.0
        assert request.benefactor == "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"

    def test_rfq_request_has_default_pair(self):
        """RfqRequest should default to USDC/USDm pair."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        )

        assert request.pair == "USDC/USDm"

    def test_rfq_request_has_default_type(self):
        """RfqRequest should default to ALGO type."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        )

        assert request.type_ == "ALGO"

    def test_rfq_request_accepts_custom_pair(self):
        """RfqRequest should accept custom pair."""
        request = RfqRequest(
            side=Side.MINT,
            size=1000.0,
            benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            pair="USDT/USDm",
        )

        assert request.pair == "USDT/USDm"

    def test_rfq_request_redeem_side(self):
        """RfqRequest should accept REDEEM side."""
        request = RfqRequest(
            side=Side.REDEEM,
            size=500.0,
            benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
        )

        assert request.side == Side.REDEEM

    def test_rfq_request_requires_side(self):
        """RfqRequest should require side field."""
        with pytest.raises(ValidationError) as exc_info:
            RfqRequest(
                size=1000.0,
                benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            )

        assert "side" in str(exc_info.value)

    def test_rfq_request_requires_size(self):
        """RfqRequest should require size field."""
        with pytest.raises(ValidationError) as exc_info:
            RfqRequest(
                side=Side.MINT,
                benefactor="0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            )

        assert "size" in str(exc_info.value)

    def test_rfq_request_requires_benefactor(self):
        """RfqRequest should require benefactor field."""
        with pytest.raises(ValidationError) as exc_info:
            RfqRequest(
                side=Side.MINT,
                size=1000.0,
            )

        assert "benefactor" in str(exc_info.value)


class TestRfqResponse:
    """Tests for RfqResponse model."""

    def test_rfq_response_parses_valid_data(self):
        """RfqResponse should parse valid API response data."""
        data = {
            "rfq_id": "test-123",
            "pair": "USDC/USDm",
            "side": "MINT",
            "size": 1000.0,
            "collateral_asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "collateral_amount": "1000000000",
            "usdm_amount": "1000000000000000000000",
            "gas": "21000",
        }

        response = RfqResponse.model_validate(data)

        assert response.rfq_id == "test-123"
        assert response.pair == "USDC/USDm"
        assert response.side == Side.MINT
        assert response.collateral_asset == "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
        assert response.collateral_amount == "1000000000"
        assert response.usdm_amount == "1000000000000000000000"
        assert response.gas == "21000"

    def test_rfq_response_handles_string_size(self):
        """RfqResponse should handle size as string."""
        data = {
            "rfq_id": "test-123",
            "pair": "USDC/USDm",
            "side": "MINT",
            "size": "1000.0",
            "collateral_asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "collateral_amount": "1000000000",
            "usdm_amount": "1000000000000000000000",
            "gas": "21000",
        }

        response = RfqResponse.model_validate(data)

        assert response.size == "1000.0"

    def test_rfq_response_redeem_side(self):
        """RfqResponse should parse REDEEM side."""
        data = {
            "rfq_id": "test-456",
            "pair": "USDC/USDm",
            "side": "REDEEM",
            "size": 500.0,
            "collateral_asset_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "collateral_amount": "500000000",
            "usdm_amount": "500000000000000000000",
            "gas": "21000",
        }

        response = RfqResponse.model_validate(data)

        assert response.side == Side.REDEEM

    def test_rfq_response_uses_field_alias(self):
        """RfqResponse should use collateral_asset_address alias for collateral_asset."""
        data = {
            "rfq_id": "test-123",
            "pair": "USDC/USDm",
            "side": "MINT",
            "size": 1000.0,
            "collateral_asset_address": "0xTestAddress",
            "collateral_amount": "1000000000",
            "usdm_amount": "1000000000000000000000",
            "gas": "21000",
        }

        response = RfqResponse.model_validate(data)

        assert response.collateral_asset == "0xTestAddress"

    def test_rfq_response_requires_rfq_id(self):
        """RfqResponse should require rfq_id field."""
        data = {
            "pair": "USDC/USDm",
            "side": "MINT",
            "size": 1000.0,
            "collateral_asset_address": "0xTestAddress",
            "collateral_amount": "1000000000",
            "usdm_amount": "1000000000000000000000",
            "gas": "21000",
        }

        with pytest.raises(ValidationError) as exc_info:
            RfqResponse.model_validate(data)

        assert "rfq_id" in str(exc_info.value)

    def test_rfq_response_model_dump_uses_alias(self):
        """RfqResponse model_dump should use alias when by_alias=True."""
        data = {
            "rfq_id": "test-123",
            "pair": "USDC/USDm",
            "side": "MINT",
            "size": 1000.0,
            "collateral_asset_address": "0xTestAddress",
            "collateral_amount": "1000000000",
            "usdm_amount": "1000000000000000000000",
            "gas": "21000",
        }

        response = RfqResponse.model_validate(data)
        dumped = response.model_dump(by_alias=True)

        assert "collateral_asset_address" in dumped
        assert dumped["collateral_asset_address"] == "0xTestAddress"
