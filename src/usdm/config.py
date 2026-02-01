import re

from pydantic import HttpUrl, field_validator
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

    eip712_name: str = "USDmMinting"
    eip712_version: str = "1"
    minting_contract: str = "0xE0406beE6D58bCd7C1cA78191b6fde9CA060F6f2"

    @field_validator("private_key")
    @classmethod
    def validate_private_key(cls, value: str) -> str:
        if not re.fullmatch(r"0x[0-9a-fA-F]{64}", value):
            raise ValueError(
                "private_key must be a 66-character hex string with 0x prefix"
            )
        return value

    @field_validator("minting_contract")
    @classmethod
    def validate_minting_contract(cls, value: str) -> str:
        if not re.fullmatch(r"0x[0-9a-fA-F]{40}", value):
            raise ValueError(
                "minting_contract must be a 0x-prefixed 40-byte hex address"
            )
        return value

def get_domain(settings: Settings, chain_id: int) -> dict[str, object]:
    return {
        "name": settings.eip712_name,
        "version": settings.eip712_version,
        "chainId": chain_id,
        "verifyingContract": settings.minting_contract,
    }
