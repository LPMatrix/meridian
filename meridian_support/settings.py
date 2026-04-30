from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-driven configuration; no secrets in code."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mcp_server_url: HttpUrl = Field(
        default="https://order-mcp-74afyau24q-uc.a.run.app/mcp",
        description="Streamable HTTP MCP endpoint",
    )

    openai_api_key: str = Field(default="", description="Required for chat unless mocking tests")

    openai_base_url: str | None = Field(
        default=None,
        description="Optional alternate API base (Azure OpenAI, proxies)",
    )

    llm_model: str = Field(default="gpt-4o-mini", description="Cost-efficient tier recommended")

    max_tool_rounds: int = Field(default=12, ge=1, le=64)

    request_timeout_seconds: float = Field(default=120.0, gt=0)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
