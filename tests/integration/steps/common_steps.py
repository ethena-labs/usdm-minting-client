"""Common step definitions shared across features."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

from behave import given, then, when
from eth_account import Account

from usdm.config import Settings
from usdm.rfq.order import build_order
from usdm.rfq.types import RfqResponse, Side
from usdm.signing import EIP712Domain, resolve_domain, sign_order


TEST_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
TEST_ADDRESS = Account.from_key(TEST_PRIVATE_KEY).address
TEST_CONTRACT = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"
TEST_COLLATERAL = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"


@given("valid configuration is loaded")
def step_load_configuration(context):
    """Load valid configuration from environment."""
    context.settings = Settings()
    context.benefactor = Account.from_key(context.settings.private_key).address


@given("an RFQ response for minting {amount:d} USDm")
def step_rfq_response_mint(context, amount):
    """Create an RFQ response for minting."""
    context.rfq_response = RfqResponse(
        rfq_id=f"mint-{amount}-{int(time.time())}",
        pair="USDC/USDm",
        side=Side.MINT,
        size=float(amount),
        collateral_asset_address=TEST_COLLATERAL,
        collateral_amount=str(amount * 1_000_000),  # 6 decimals for USDC
        usdm_amount=str(amount * 10**18),  # 18 decimals for USDm
        gas="21000",
    )


@given("an RFQ response for redeeming {amount:d} USDm")
def step_rfq_response_redeem(context, amount):
    """Create an RFQ response for redeeming."""
    context.rfq_response = RfqResponse(
        rfq_id=f"redeem-{amount}-{int(time.time())}",
        pair="USDC/USDm",
        side=Side.REDEEM,
        size=float(amount),
        collateral_asset_address=TEST_COLLATERAL,
        collateral_amount=str(amount * 1_000_000),
        usdm_amount=str(amount * 10**18),
        gas="21000",
    )


@when("I build an order from the RFQ response")
def step_build_order(context):
    """Build an order from the RFQ response."""
    context.order = build_order(
        context.rfq_response,
        benefactor=context.benefactor,
    )


@when("I build an order without specifying a beneficiary")
def step_build_order_no_beneficiary(context):
    """Build an order without explicit beneficiary."""
    context.order = build_order(
        context.rfq_response,
        benefactor=context.benefactor,
        beneficiary=None,
    )


@when('I build an order with a custom beneficiary "{address}"')
def step_build_order_custom_beneficiary(context, address):
    """Build an order with custom beneficiary."""
    context.order = build_order(
        context.rfq_response,
        benefactor=context.benefactor,
        beneficiary=address,
    )


@given("I build an order from the RFQ response")
def step_given_build_order(context):
    """Build an order (as Given step)."""
    step_build_order(context)


@when("I sign the order with my private key")
def step_sign_order(context):
    """Sign the order with EIP-712."""
    domain = EIP712Domain(
        name=context.settings.eip712_name,
        version=context.settings.eip712_version,
        chain_id=1,
        verifying_contract=context.settings.minting_contract,
    )
    context.signed_order = sign_order(
        context.settings.private_key,
        context.order,
        domain,
    )


@given('I build and sign the order as "{name}"')
def step_build_and_sign_named(context, name):
    """Build and sign order, storing with a name."""
    step_build_order(context)
    step_sign_order(context)
    if not hasattr(context, "named_signatures"):
        context.named_signatures = {}
    context.named_signatures[name] = context.signed_order.signature


@then('the order should have order_type "{order_type}"')
def step_check_order_type(context, order_type):
    """Verify order type."""
    assert context.order["order_type"] == order_type, (
        f"Expected order_type {order_type}, got {context.order['order_type']}"
    )


@then("the order should have the correct collateral amount")
def step_check_collateral_amount(context):
    """Verify collateral amount matches RFQ response."""
    expected = int(context.rfq_response.collateral_amount)
    actual = context.order["collateral_amount"]
    assert actual == expected, f"Expected {expected}, got {actual}"


@then("the order should have the correct USDm amount")
def step_check_usdm_amount(context):
    """Verify USDm amount matches RFQ response."""
    expected = int(context.rfq_response.usdm_amount)
    actual = context.order["usdm_amount"]
    assert actual == expected, f"Expected {expected}, got {actual}"


@then("the order should have a valid expiry timestamp")
def step_check_expiry(context):
    """Verify expiry is in the future."""
    current_time = int(time.time())
    assert context.order["expiry"] > current_time, "Expiry should be in the future"


@then("the signature should be valid")
def step_check_signature_valid(context):
    """Verify signature format."""
    sig = context.signed_order.signature
    assert sig.startswith("0x"), "Signature should start with 0x"
    assert len(sig) == 132, f"Signature should be 132 chars, got {len(sig)}"


@then("the signer address should match my wallet")
def step_check_signer_address(context):
    """Verify signer address matches benefactor."""
    expected = Account.from_key(context.settings.private_key).address
    actual = context.signed_order.signer_address
    assert actual == expected, f"Expected {expected}, got {actual}"


@then("the beneficiary should equal the benefactor")
def step_check_beneficiary_equals_benefactor(context):
    """Verify beneficiary defaults to benefactor."""
    assert context.order["beneficiary"] == context.order["benefactor"]


@then('the beneficiary should be "{address}"')
def step_check_beneficiary_address(context, address):
    """Verify beneficiary is specific address."""
    assert context.order["beneficiary"] == address


@then("the signatures should be different")
def step_check_signatures_different(context):
    """Verify named signatures are different."""
    sigs = list(context.named_signatures.values())
    assert len(set(sigs)) == len(sigs), "All signatures should be unique"
