"""Unit tests for usdm.signing.signer module."""

from unittest.mock import patch

import pytest
from eth_account import Account

from usdm.signing.signer import (
    DomainResolutionError,
    EIP712Domain,
    SignedOrder,
    resolve_domain,
    sign_order,
)

# Foundry/Hardhat default test account #0
# This is a publicly known test key - NEVER fund this address on mainnet!
# Source: https://book.getfoundry.sh/reference/anvil/
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_ADDRESS = Account.from_key(TEST_PRIVATE_KEY).address
TEST_CONTRACT = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"


class TestEIP712Domain:
    """Tests for EIP712Domain dataclass."""

    def test_domain_stores_fields(self):
        """EIP712Domain should store all fields."""
        domain = EIP712Domain(
            name="USDmMinting",
            version="1",
            chain_id=1,
            verifying_contract=TEST_CONTRACT,
        )

        assert domain.name == "USDmMinting"
        assert domain.version == "1"
        assert domain.chain_id == 1
        assert domain.verifying_contract == TEST_CONTRACT

    def test_domain_is_frozen(self):
        """EIP712Domain should be immutable."""
        domain = EIP712Domain(
            name="USDmMinting",
            version="1",
            chain_id=1,
            verifying_contract=TEST_CONTRACT,
        )

        with pytest.raises(AttributeError):
            domain.name = "Modified"

    def test_domain_to_dict(self, sample_domain):
        """to_dict should return dict with camelCase keys."""
        result = sample_domain.to_dict()

        assert result["name"] == "USDmMinting"
        assert result["version"] == "1"
        assert result["chainId"] == 1
        assert result["verifyingContract"] == TEST_CONTRACT

    def test_domain_to_dict_key_format(self, sample_domain):
        """to_dict should use camelCase for chainId and verifyingContract."""
        result = sample_domain.to_dict()

        assert "chainId" in result
        assert "verifyingContract" in result
        assert "chain_id" not in result
        assert "verifying_contract" not in result


class TestResolveDomain:
    """Tests for resolve_domain function."""

    def test_resolve_domain_from_settings(self, settings):
        """resolve_domain should use settings when no other source provided."""
        domain = resolve_domain(settings, chain_id=1)

        assert domain.name == settings.eip712_name
        assert domain.version == settings.eip712_version
        assert domain.chain_id == 1
        assert domain.verifying_contract == settings.minting_contract

    def test_resolve_domain_uses_provided_chain_id(self, settings):
        """resolve_domain should use the provided chain_id."""
        domain = resolve_domain(settings, chain_id=137)

        assert domain.chain_id == 137

    def test_resolve_domain_api_overrides_settings(self, settings):
        """resolve_domain should let API domain override settings."""
        api_domain = {
            "name": "ApiName",
            "version": "2",
            "chainId": 1,
            "verifyingContract": "0x" + "a" * 40,
        }

        domain = resolve_domain(settings, chain_id=1, api_domain=api_domain)

        assert domain.name == "ApiName"
        assert domain.version == "2"
        assert domain.verifying_contract == "0x" + "a" * 40

    def test_resolve_domain_overrides_override_all(self, settings):
        """resolve_domain should let overrides override everything."""
        api_domain = {
            "name": "ApiName",
            "version": "2",
            "chainId": 1,
            "verifyingContract": "0x" + "a" * 40,
        }
        overrides = {
            "name": "OverrideName",
            "version": "3",
        }

        domain = resolve_domain(
            settings, chain_id=1, api_domain=api_domain, overrides=overrides
        )

        assert domain.name == "OverrideName"
        assert domain.version == "3"
        assert domain.verifying_contract == "0x" + "a" * 40

    def test_resolve_domain_partial_override(self, settings):
        """resolve_domain should allow partial overrides."""
        overrides = {"version": "99"}

        domain = resolve_domain(settings, chain_id=1, overrides=overrides)

        assert domain.name == settings.eip712_name
        assert domain.version == "99"

    def test_resolve_domain_raises_on_missing_fields(self, settings):
        """resolve_domain should raise DomainResolutionError on missing fields."""
        with patch("usdm.signing.signer.get_domain") as mock_get_domain:
            # Return an incomplete domain missing required fields
            mock_get_domain.return_value = {"chainId": 1}

            with pytest.raises(DomainResolutionError) as exc_info:
                resolve_domain(settings, chain_id=1)

            assert "missing fields" in str(exc_info.value).lower()

    def test_resolve_domain_error_message_lists_missing(self, settings):
        """DomainResolutionError should list missing fields."""
        # Create an incomplete override that will cause missing fields
        # by setting fields to non-dict values that won't merge properly
        with patch("usdm.signing.signer.get_domain") as mock_get_domain:
            # Return incomplete domain
            mock_get_domain.return_value = {"name": "Test"}

            with pytest.raises(DomainResolutionError) as exc_info:
                resolve_domain(settings, chain_id=1)

            error_msg = str(exc_info.value)
            assert "verifyingContract" in error_msg or "version" in error_msg


class TestSignOrder:
    """Tests for sign_order function."""

    def test_sign_order_returns_signed_order(self, sample_order, sample_domain):
        """sign_order should return SignedOrder."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert isinstance(result, SignedOrder)

    def test_sign_order_includes_signature(self, sample_order, sample_domain):
        """sign_order should include hex signature."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result.signature.startswith("0x")
        assert len(result.signature) == 132  # 0x + 130 hex chars

    def test_sign_order_includes_signer_address(self, sample_order, sample_domain):
        """sign_order should include signer address."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result.signer_address == TEST_ADDRESS

    def test_sign_order_includes_original_order(self, sample_order, sample_domain):
        """sign_order should include original order."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result.order == sample_order

    def test_sign_order_converts_order_type_mint(self, sample_order, sample_domain):
        """sign_order should convert MINT to 0 for signing."""
        sample_order["order_type"] = "MINT"

        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result.signature is not None

    def test_sign_order_converts_order_type_redeem(self, sample_order, sample_domain):
        """sign_order should convert REDEEM to 1 for signing."""
        sample_order["order_type"] = "REDEEM"

        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result.signature is not None

    def test_sign_order_deterministic(self, sample_order, sample_domain):
        """sign_order should produce same signature for same inputs."""
        result1 = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)
        result2 = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert result1.signature == result2.signature

    def test_sign_order_different_for_different_orders(self, sample_domain):
        """sign_order should produce different signatures for different orders."""
        order1 = {
            "order_id": "order-1",
            "order_type": "MINT",
            "expiry": 1700000000,
            "nonce": 1700000000,
            "benefactor": TEST_ADDRESS,
            "beneficiary": TEST_ADDRESS,
            "collateral_asset": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "collateral_amount": 1000000000,
            "usdm_amount": 1000000000000000000000,
        }
        order2 = {**order1, "order_id": "order-2"}

        result1 = sign_order(TEST_PRIVATE_KEY, order1, sample_domain)
        result2 = sign_order(TEST_PRIVATE_KEY, order2, sample_domain)

        assert result1.signature != result2.signature


class TestSignedOrder:
    """Tests for SignedOrder dataclass."""

    def test_signed_order_is_frozen(self, sample_order, sample_domain):
        """SignedOrder should be immutable."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        with pytest.raises(AttributeError):
            result.signature = "0xmodified"

    def test_signed_order_fields(self, sample_order, sample_domain):
        """SignedOrder should have order, signature, and signer_address."""
        result = sign_order(TEST_PRIVATE_KEY, sample_order, sample_domain)

        assert hasattr(result, "order")
        assert hasattr(result, "signature")
        assert hasattr(result, "signer_address")


class TestDomainResolutionError:
    """Tests for DomainResolutionError exception."""

    def test_error_is_exception(self):
        """DomainResolutionError should be an Exception."""
        assert issubclass(DomainResolutionError, Exception)

    def test_error_with_message(self):
        """DomainResolutionError should accept custom message."""
        error = DomainResolutionError("Missing chainId")

        assert str(error) == "Missing chainId"
