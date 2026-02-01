"""Step definitions for allowances feature."""

from behave import given, then, when


@given("the current allowance is {amount:d}")
def step_set_allowance(context, amount):
    """Set the mocked current allowance."""
    context.current_allowance = amount


@when("I check if allowance is sufficient for the order")
def step_check_allowance_sufficient(context):
    """Check if allowance is sufficient."""
    required = int(context.rfq_response.collateral_amount)
    context.allowance_sufficient = context.current_allowance >= required


@then("the allowance should be insufficient")
def step_verify_allowance_insufficient(context):
    """Verify allowance is insufficient."""
    assert context.allowance_sufficient is False, "Expected allowance to be insufficient"


@then("the allowance should be sufficient")
def step_verify_allowance_sufficient(context):
    """Verify allowance is sufficient."""
    assert context.allowance_sufficient is True, "Expected allowance to be sufficient"
