"""EIP-712 Order type schema for USDm minting.

The Order type is fixed and matches the on-chain contract schema.
This must NOT be sourced from the API - it's a protocol constant.

Reference: https://github.com/ethena-labs/ethena-minting-client
"""

from typing import Final

# EIP-712 primary type name
PRIMARY_TYPE: Final[str] = "Order"

# EIP-712 Order type schema - matches on-chain contract exactly
# Note: Field names use snake_case to match the signing contract
ORDER_TYPES: Final[dict[str, list[dict[str, str]]]] = {
    "Order": [
        {"name": "order_id", "type": "string"},
        {"name": "order_type", "type": "uint8"},
        {"name": "expiry", "type": "uint120"},
        {"name": "nonce", "type": "uint128"},
        {"name": "benefactor", "type": "address"},
        {"name": "beneficiary", "type": "address"},
        {"name": "collateral_asset", "type": "address"},
        {"name": "collateral_amount", "type": "uint128"},
        {"name": "usdm_amount", "type": "uint128"},
    ],
}

# Order type enum values (for order_type field)
ORDER_TYPE_MINT: Final[int] = 0
ORDER_TYPE_REDEEM: Final[int] = 1
