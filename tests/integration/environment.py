"""Behave environment configuration for integration tests."""

import os


def before_all(context):
    """Set up test environment before all tests."""
    # Set test environment variables
    os.environ.setdefault("USDM_RPC_URL", "https://eth-mainnet.example.com")
    os.environ.setdefault(
        "USDM_PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    )
    os.environ.setdefault(
        "USDM_MINTING_CONTRACT",
        "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"
    )

    # Store test constants in context
    context.test_private_key = os.environ["USDM_PRIVATE_KEY"]
    context.test_contract = os.environ["USDM_MINTING_CONTRACT"]
    context.test_collateral = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


def before_scenario(context, scenario):
    """Reset state before each scenario."""
    context.result = None
    context.error = None
    context.settings = None
    context.rfq_response = None
    context.order = None
    context.signed_order = None
