"""Shared pytest fixtures for USDm minting client tests."""

import os
from unittest.mock import MagicMock

import pytest
from eth_account import Account

from usdm.rfq.types import RfqResponse, Side


# Foundry/Hardhat default test account #0
# This is a publicly known test key - NEVER fund this address on mainnet!
# Source: https://book.getfoundry.sh/reference/anvil/
TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_ADDRESS = Account.from_key(TEST_PRIVATE_KEY).address  # 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266

# Test contract addresses
TEST_MINTING_CONTRACT = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"
TEST_COLLATERAL_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"  # USDC


@pytest.fixture
def env_settings(monkeypatch):
    """Set up environment variables for Settings."""
    monkeypatch.setenv("USDM_RPC_URL", "https://eth-mainnet.example.com")
    monkeypatch.setenv("USDM_PRIVATE_KEY", TEST_PRIVATE_KEY)
    monkeypatch.setenv("USDM_MINTING_CONTRACT", TEST_MINTING_CONTRACT)


@pytest.fixture
def settings(env_settings):
    """Create a Settings instance with test values."""
    from usdm.config import Settings
    return Settings()


@pytest.fixture
def mock_web3():
    """Create a mocked Web3 instance."""
    w3 = MagicMock()
    w3.eth.chain_id = 1
    w3.eth.gas_price = 20_000_000_000  # 20 gwei
    w3.eth.get_transaction_count.return_value = 0
    w3.eth.estimate_gas.return_value = 21000
    w3.to_checksum_address = MagicMock(side_effect=lambda addr: addr)
    w3.eth.account = Account
    return w3


@pytest.fixture
def sample_rfq_response():
    """Create a sample RFQ response for testing."""
    return RfqResponse(
        rfq_id="test-rfq-123",
        pair="USDC/USDm",
        side=Side.MINT,
        size=1000.0,
        collateral_asset_address=TEST_COLLATERAL_ADDRESS,
        collateral_amount="1000000000",  # 1000 USDC (6 decimals)
        usdm_amount="1000000000000000000000",  # 1000 USDm (18 decimals)
        gas="21000",
    )


@pytest.fixture
def sample_rfq_response_redeem():
    """Create a sample RFQ response for redeem testing."""
    return RfqResponse(
        rfq_id="test-rfq-456",
        pair="USDC/USDm",
        side=Side.REDEEM,
        size=1000.0,
        collateral_asset_address=TEST_COLLATERAL_ADDRESS,
        collateral_amount="1000000000",
        usdm_amount="1000000000000000000000",
        gas="21000",
    )


@pytest.fixture
def sample_order():
    """Create a sample order dict for testing."""
    return {
        "order_id": "test-rfq-123",
        "order_type": "MINT",
        "expiry": 1700000000,
        "nonce": 1700000000,
        "benefactor": TEST_ADDRESS,
        "beneficiary": TEST_ADDRESS,
        "collateral_asset": TEST_COLLATERAL_ADDRESS,
        "collateral_amount": 1000000000,
        "usdm_amount": 1000000000000000000000,
    }


@pytest.fixture
def sample_domain():
    """Create a sample EIP-712 domain for testing."""
    from usdm.signing import EIP712Domain
    return EIP712Domain(
        name="USDmMinting",
        version="1",
        chain_id=1,
        verifying_contract=TEST_MINTING_CONTRACT,
    )
