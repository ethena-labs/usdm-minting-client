"""Unit tests for usdm.signing.order_types module."""

import pytest

from usdm.signing.order_types import (
    ORDER_TYPE_MINT,
    ORDER_TYPE_REDEEM,
    ORDER_TYPES,
    PRIMARY_TYPE,
)


class TestOrderTypeConstants:
    """Tests for order type constants."""

    def test_order_type_mint_is_zero(self):
        """ORDER_TYPE_MINT should be 0."""
        assert ORDER_TYPE_MINT == 0

    def test_order_type_redeem_is_one(self):
        """ORDER_TYPE_REDEEM should be 1."""
        assert ORDER_TYPE_REDEEM == 1

    def test_primary_type_is_order(self):
        """PRIMARY_TYPE should be 'Order'."""
        assert PRIMARY_TYPE == "Order"


class TestOrderTypesSchema:
    """Tests for ORDER_TYPES EIP-712 schema."""

    def test_order_types_contains_order(self):
        """ORDER_TYPES should contain 'Order' key."""
        assert "Order" in ORDER_TYPES

    def test_order_schema_is_list(self):
        """Order schema should be a list of field definitions."""
        assert isinstance(ORDER_TYPES["Order"], list)

    def test_order_schema_has_required_fields(self):
        """Order schema should have all required fields."""
        expected_fields = [
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

        actual_fields = [field["name"] for field in ORDER_TYPES["Order"]]

        for field in expected_fields:
            assert field in actual_fields, f"Missing field: {field}"

    def test_order_schema_field_types(self):
        """Order schema fields should have correct EIP-712 types."""
        field_types = {field["name"]: field["type"] for field in ORDER_TYPES["Order"]}

        assert field_types["order_id"] == "string"
        assert field_types["order_type"] == "uint8"
        assert field_types["expiry"] == "uint120"
        assert field_types["nonce"] == "uint128"
        assert field_types["benefactor"] == "address"
        assert field_types["beneficiary"] == "address"
        assert field_types["collateral_asset"] == "address"
        assert field_types["collateral_amount"] == "uint128"
        assert field_types["usdm_amount"] == "uint128"

    def test_order_schema_field_count(self):
        """Order schema should have exactly 9 fields."""
        assert len(ORDER_TYPES["Order"]) == 9

    def test_order_schema_field_structure(self):
        """Each field in Order schema should have name and type."""
        for field in ORDER_TYPES["Order"]:
            assert "name" in field, f"Field missing 'name': {field}"
            assert "type" in field, f"Field missing 'type': {field}"
            assert isinstance(field["name"], str)
            assert isinstance(field["type"], str)
