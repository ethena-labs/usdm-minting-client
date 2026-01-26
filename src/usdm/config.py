import re

from pydantic import HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="USDM_",
        extra="ignore",
    )

    rpc_url: HttpUrl
    private_key: str
    api_url: HttpUrl = HttpUrl("https://public.api.megausd.money/")

    eip712_name: str | None = None
    eip712_version: str | None = None
    eip712_chain_id: int | None = None
    eip712_verifying_contract: str | None = None
    allowance_spender: str | None = None

    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, value: str) -> str:
        if not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
            raise ValueError(
                "private_key must be a 66-character hex string with 0x prefix"
            )
        return value

    @field_validator("eip712_verifying_contract")
    @classmethod
    def validate_verifying_contract(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
            raise ValueError(
                "eip712_verifying_contract must be a 0x-prefixed 40-byte hex address"
            )
        return value

    @field_validator("allowance_spender")
    @classmethod
    def validate_allowance_spender(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
            raise ValueError(
                "allowance_spender must be a 0x-prefixed 40-byte hex address"
            )
        return value

    @model_validator(mode="after")
    def validate_domain_fields(self) -> "Settings":
        fields = {
            "eip712_name": self.eip712_name,
            "eip712_version": self.eip712_version,
            "eip712_chain_id": self.eip712_chain_id,
            "eip712_verifying_contract": self.eip712_verifying_contract,
        }
        provided = [value is not None for value in fields.values()]
        if any(provided) and not all(provided):
            missing = [name for name, value in fields.items() if value is None]
            raise ValueError(
                "EIP-712 domain settings are incomplete; missing: "
                + ", ".join(missing)
            )
        return self


def settings_domain(settings: Settings) -> dict[str, object] | None:
    if (
        settings.eip712_name is None
        or settings.eip712_version is None
        or settings.eip712_chain_id is None
        or settings.eip712_verifying_contract is None
    ):
        return None
    return {
        "name": settings.eip712_name,
        "version": settings.eip712_version,
        "chainId": settings.eip712_chain_id,
        "verifyingContract": settings.eip712_verifying_contract,
    }
