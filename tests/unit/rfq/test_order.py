"""Unit tests for usdm.rfq.order module."""

import time
from unittest.mock import patch

import pytest

from usdm.rfq.order import Order, build_order
from usdm.rfq.types import RfqResponse, Side


TEST_BENEFACTOR = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
TEST_BENEFICIARY = "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"
TEST_COLLATERAL = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


class TestBuildOrder:
    """Tests for build_order function."""

    def test_build_order_returns_order_dict(self, sample_rfq_response):
        """build_order should return Order TypedDict."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert isinstance(order, dict)
        assert "order_id" in order
        assert "order_type" in order
        assert "expiry" in order

    def test_build_order_copies_rfq_id_to_order_id(self, sample_rfq_response):
        """build_order should copy rfq_id to order_id."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["order_id"] == sample_rfq_response.rfq_id

    def test_build_order_sets_mint_order_type(self, sample_rfq_response):
        """build_order should set order_type to MINT for mint side."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["order_type"] == "MINT"

    def test_build_order_sets_redeem_order_type(self, sample_rfq_response_redeem):
        """build_order should set order_type to REDEEM for redeem side."""
        order = build_order(sample_rfq_response_redeem, benefactor=TEST_BENEFACTOR)

        assert order["order_type"] == "REDEEM"

    def test_build_order_sets_benefactor(self, sample_rfq_response):
        """build_order should set benefactor address."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["benefactor"] == TEST_BENEFACTOR

    def test_build_order_defaults_beneficiary_to_benefactor(self, sample_rfq_response):
        """build_order should default beneficiary to benefactor."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["beneficiary"] == TEST_BENEFACTOR

    def test_build_order_accepts_custom_beneficiary(self, sample_rfq_response):
        """build_order should accept custom beneficiary."""
        order = build_order(
            sample_rfq_response,
            benefactor=TEST_BENEFACTOR,
            beneficiary=TEST_BENEFICIARY,
        )

        assert order["beneficiary"] == TEST_BENEFICIARY

    def test_build_order_copies_collateral_asset(self, sample_rfq_response):
        """build_order should copy collateral_asset from RFQ response."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["collateral_asset"] == sample_rfq_response.collateral_asset

    def test_build_order_converts_collateral_amount_to_int(self, sample_rfq_response):
        """build_order should convert collateral_amount to int."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["collateral_amount"] == int(sample_rfq_response.collateral_amount)
        assert isinstance(order["collateral_amount"], int)

    def test_build_order_converts_usdm_amount_to_int(self, sample_rfq_response):
        """build_order should convert usdm_amount to int."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert order["usdm_amount"] == int(sample_rfq_response.usdm_amount)
        assert isinstance(order["usdm_amount"], int)

    @patch("usdm.rfq.order.time")
    def test_build_order_calculates_expiry(self, mock_time, sample_rfq_response):
        """build_order should calculate expiry from current time + expiry_seconds."""
        mock_time.time.return_value = 1700000000

        order = build_order(
            sample_rfq_response,
            benefactor=TEST_BENEFACTOR,
            expiry_seconds=60,
        )

        assert order["expiry"] == 1700000060

    @patch("usdm.rfq.order.time")
    def test_build_order_uses_expiry_as_nonce(self, mock_time, sample_rfq_response):
        """build_order should use expiry as nonce."""
        mock_time.time.return_value = 1700000000

        order = build_order(
            sample_rfq_response,
            benefactor=TEST_BENEFACTOR,
            expiry_seconds=120,
        )

        assert order["nonce"] == order["expiry"]
        assert order["nonce"] == 1700000120

    def test_build_order_default_expiry_seconds(self, sample_rfq_response):
        """build_order should default to 60 seconds expiry."""
        current_time = int(time.time())

        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        expected_expiry = current_time + 60
        assert abs(order["expiry"] - expected_expiry) <= 1

    def test_build_order_accepts_custom_expiry(self, sample_rfq_response):
        """build_order should accept custom expiry_seconds."""
        current_time = int(time.time())

        order = build_order(
            sample_rfq_response,
            benefactor=TEST_BENEFACTOR,
            expiry_seconds=300,
        )

        expected_expiry = current_time + 300
        assert abs(order["expiry"] - expected_expiry) <= 1


class TestOrderTypedDict:
    """Tests for Order TypedDict structure."""

    def test_order_has_all_required_fields(self, sample_rfq_response):
        """Order should have all required fields."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        required_fields = [
            "order_id",
            "order_type",
            "expiry",
            "nonce",
            "benefactor",
            "beneficiary",
            "collateral_asset",
            "collateral_amount",
            "usdm_amount",
        ]

        for field in required_fields:
            assert field in order, f"Missing field: {field}"

    def test_order_field_types(self, sample_rfq_response):
        """Order fields should have correct types."""
        order = build_order(sample_rfq_response, benefactor=TEST_BENEFACTOR)

        assert isinstance(order["order_id"], str)
        assert isinstance(order["order_type"], str)
        assert isinstance(order["expiry"], int)
        assert isinstance(order["nonce"], int)
        assert isinstance(order["benefactor"], str)
        assert isinstance(order["beneficiary"], str)
        assert isinstance(order["collateral_asset"], str)
        assert isinstance(order["collateral_amount"], int)
        assert isinstance(order["usdm_amount"], int)
