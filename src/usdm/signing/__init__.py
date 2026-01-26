"""EIP-712 signing module for USDm orders."""

from usdm.signing.order_types import (
    ORDER_TYPE_MINT,
    ORDER_TYPE_REDEEM,
    ORDER_TYPES,
    PRIMARY_TYPE,
)
from usdm.signing.signer import (
    DomainResolutionError,
    EIP712Domain,
    SignedOrder,
    resolve_domain,
    sign_order,
)

__all__ = [
    # Order type constants
    "PRIMARY_TYPE",
    "ORDER_TYPES",
    "ORDER_TYPE_MINT",
    "ORDER_TYPE_REDEEM",
    # Domain resolution
    "EIP712Domain",
    "DomainResolutionError",
    "resolve_domain",
    # Signing
    "SignedOrder",
    "sign_order",
]
