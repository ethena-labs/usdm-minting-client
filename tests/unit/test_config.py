"""Unit tests for usdm.config module."""

import pytest
from pydantic import ValidationError

from usdm.config import Settings, get_domain


class TestSettings:
    """Tests for Settings class."""

    def test_settings_loads_from_environment(self, env_settings):
        """Settings should load values from environment variables."""
        settings = Settings()

        assert str(settings.rpc_url) == "https://eth-mainnet.example.com/"
        assert settings.private_key.startswith("0x")
        assert len(settings.private_key) == 66

    def test_settings_has_default_api_url(self, env_settings):
        """Settings should have default API URL when not specified."""
        settings = Settings()

        assert "megausd.money" in str(settings.api_url)

    def test_settings_has_default_eip712_values(self, env_settings):
        """Settings should have default EIP-712 domain values."""
        settings = Settings()

        assert settings.eip712_name == "USDmMinting"
        assert settings.eip712_version == "1"

    def test_settings_requires_rpc_url(self, monkeypatch):
        """Settings should raise error when RPC URL is missing."""
        monkeypatch.delenv("USDM_RPC_URL", raising=False)
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 64)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "rpc_url" in str(exc_info.value)

    def test_settings_requires_private_key(self, monkeypatch):
        """Settings should raise error when private key is missing."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.delenv("USDM_PRIVATE_KEY", raising=False)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "private_key" in str(exc_info.value)


class TestPrivateKeyValidation:
    """Tests for private key validation."""

    def test_valid_private_key_accepted(self, monkeypatch):
        """Valid 0x-prefixed 64-char hex key should be accepted."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 64)

        settings = Settings()

        assert settings.private_key == "0x" + "a" * 64

    def test_private_key_without_prefix_rejected(self, monkeypatch):
        """Private key without 0x prefix should be rejected."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "a" * 64)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "0x prefix" in str(exc_info.value)

    def test_private_key_wrong_length_rejected(self, monkeypatch):
        """Private key with wrong length should be rejected."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 32)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "66-character" in str(exc_info.value)

    def test_private_key_invalid_hex_rejected(self, monkeypatch):
        """Private key with non-hex characters should be rejected."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "g" * 64)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "hex" in str(exc_info.value).lower()


class TestMintingContractValidation:
    """Tests for minting contract address validation."""

    def test_valid_contract_address_accepted(self, monkeypatch):
        """Valid 0x-prefixed 40-char hex address should be accepted."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 64)
        monkeypatch.setenv("USDM_MINTING_CONTRACT", "0x" + "b" * 40)

        settings = Settings()

        assert settings.minting_contract == "0x" + "b" * 40

    def test_contract_address_without_prefix_rejected(self, monkeypatch):
        """Contract address without 0x prefix should be rejected."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 64)
        monkeypatch.setenv("USDM_MINTING_CONTRACT", "b" * 40)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "0x-prefixed" in str(exc_info.value)

    def test_contract_address_wrong_length_rejected(self, monkeypatch):
        """Contract address with wrong length should be rejected."""
        monkeypatch.setenv("USDM_RPC_URL", "https://eth.example.com")
        monkeypatch.setenv("USDM_PRIVATE_KEY", "0x" + "a" * 64)
        monkeypatch.setenv("USDM_MINTING_CONTRACT", "0x" + "b" * 20)

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        assert "40-byte" in str(exc_info.value)


class TestGetDomain:
    """Tests for get_domain function."""

    def test_get_domain_returns_correct_structure(self, settings):
        """get_domain should return dict with EIP-712 domain fields."""
        domain = get_domain(settings, chain_id=1)

        assert domain["name"] == "USDmMinting"
        assert domain["version"] == "1"
        assert domain["chainId"] == 1
        assert domain["verifyingContract"] == settings.minting_contract

    def test_get_domain_uses_provided_chain_id(self, settings):
        """get_domain should use the provided chain_id."""
        domain = get_domain(settings, chain_id=137)

        assert domain["chainId"] == 137

    def test_get_domain_uses_settings_values(self, monkeypatch, env_settings):
        """get_domain should use custom EIP-712 values from settings."""
        monkeypatch.setenv("USDM_EIP712_NAME", "CustomName")
        monkeypatch.setenv("USDM_EIP712_VERSION", "2")
        settings = Settings()

        domain = get_domain(settings, chain_id=1)

        assert domain["name"] == "CustomName"
        assert domain["version"] == "2"
