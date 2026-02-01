"""Step definitions for minting feature."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from behave import given, then, when

from usdm.rfq.flow import DryRunResult, dry_run
from usdm.rfq.types import RfqRequest, Side
from usdm.signing import EIP712Domain


@when("I perform a dry run of the mint operation")
def step_perform_dry_run(context):
    """Perform a dry run of the mint operation."""
    with (
        patch("usdm.rfq.flow.RfqClient") as mock_client_cls,
        patch("usdm.rfq.flow.get_web3") as mock_get_web3,
    ):
        mock_client = MagicMock()
        mock_client.get_quote = AsyncMock(return_value=context.rfq_response)
        mock_client_cls.return_value = mock_client

        mock_w3 = MagicMock()
        mock_w3.eth.chain_id = 1
        mock_get_web3.return_value = mock_w3

        request = RfqRequest(
            side=Side.MINT,
            size=float(context.rfq_response.size),
            benefactor=context.benefactor,
        )

        context.dry_run_result = asyncio.run(
            dry_run(
                context.settings,
                request,
                benefactor=context.benefactor,
            )
        )


@then("I should receive a complete dry run result")
def step_check_dry_run_result(context):
    """Verify dry run result is complete."""
    assert isinstance(context.dry_run_result, DryRunResult)


@then("the result should include the RFQ data")
def step_check_dry_run_has_rfq(context):
    """Verify dry run result includes RFQ data."""
    assert context.dry_run_result.rfq is not None
    assert "rfq_id" in context.dry_run_result.rfq


@then("the result should include the signed order")
def step_check_dry_run_has_order(context):
    """Verify dry run result includes signed order."""
    assert context.dry_run_result.order is not None
    assert context.dry_run_result.signature is not None
    assert context.dry_run_result.signature.startswith("0x")


@then("the result should include the EIP-712 domain")
def step_check_dry_run_has_domain(context):
    """Verify dry run result includes EIP-712 domain."""
    domain = context.dry_run_result.domain
    assert domain is not None
    assert "name" in domain
    assert "version" in domain
    assert "chainId" in domain
    assert "verifyingContract" in domain
