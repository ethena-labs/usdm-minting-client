"""EIP-712 signing for USDm orders.

Domain resolution follows these rules:
1. Use API-provided domain values when available (passed via api_domain)
2. Fall back to config-provided domain values (from settings)
3. Per-request overrides can be passed to override specific fields
4. Fail fast if no complete domain is available (no silent defaults)
"""

from dataclasses import dataclass
from typing import Any, cast

from eth_account import Account

from usdm.config import Settings, settings_domain
from usdm.signing.order_types import ORDER_TYPES, PRIMARY_TYPE


@dataclass(frozen=True)
class EIP712Domain:
    """EIP-712 domain separator fields."""

    name: str
    version: str
    chain_id: int
    verifying_contract: str

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict format expected by eth_account."""
        return {
            "name": self.name,
            "version": self.version,
            "chainId": self.chain_id,
            "verifyingContract": self.verifying_contract,
        }


class DomainResolutionError(Exception):
    """Raised when EIP-712 domain cannot be resolved."""

    pass


def resolve_domain(
    settings: Settings,
    api_domain: dict[str, Any] | None = None,
    overrides: dict[str, Any] | None = None,
) -> EIP712Domain:
    """Resolve EIP-712 domain from available sources.

    Resolution order (later sources override earlier):
    1. Settings (config/env) - base domain if configured
    2. API response - domain provided by the RFQ API
    3. Overrides - per-request field overrides

    Args:
        settings: Application settings (may have EIP-712 domain fields)
        api_domain: Domain dict from API response (optional)
        overrides: Per-request field overrides (optional)

    Returns:
        EIP712Domain with all required fields

    Raises:
        DomainResolutionError: If no complete domain can be assembled
    """
    # Start with settings domain (may be None if not configured)
    base = settings_domain(settings) or {}

    # Layer API domain on top (if provided)
    if api_domain:
        base = {**base, **api_domain}

    # Apply per-request overrides last
    if overrides:
        base = {**base, **overrides}

    # Validate completeness
    required = {"name", "version", "chainId", "verifyingContract"}
    missing = required - set(base.keys())
    if missing:
        raise DomainResolutionError(
            f"Cannot resolve EIP-712 domain; missing fields: {', '.join(sorted(missing))}. "
            "Provide domain via API response, settings (USDM_EIP712_*), or overrides."
        )

    # Cast validated values to expected types
    name = cast(str, base["name"])
    version = cast(str, base["version"])
    chain_id = cast(int, base["chainId"])
    verifying_contract = cast(str, base["verifyingContract"])

    return EIP712Domain(
        name=name,
        version=version,
        chain_id=chain_id,
        verifying_contract=verifying_contract,
    )


@dataclass(frozen=True)
class SignedOrder:
    """A signed EIP-712 order ready for submission."""

    order: dict[str, Any]
    signature: str
    signer_address: str


def sign_order(
    private_key: str,
    order: dict[str, Any],
    domain: EIP712Domain,
) -> SignedOrder:
    """Sign an order using EIP-712 typed data signing.

    Args:
        private_key: Hex-encoded private key (0x-prefixed, 64 hex chars)
        order: Order fields matching ORDER_TYPES schema
        domain: Resolved EIP-712 domain

    Returns:
        SignedOrder with the order, signature, and signer address
    """
    # Sign using eth_account's 3-argument style
    # (domain_data, message_types, message_data)
    signed = Account.sign_typed_data(
        private_key,
        domain_data=domain.to_dict(),
        message_types=ORDER_TYPES,
        message_data=order,
    )

    return SignedOrder(
        order=order,
        signature=signed.signature.hex(),
        signer_address=Account.from_key(private_key).address,
    )
