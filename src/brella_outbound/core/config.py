"""Application settings with Pydantic Settings and lru_cache singleton."""

from enum import Enum
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers for message generation."""

    CLAUDE = "claude"
    OPENAI = "openai"
    TEMPLATE = "template"


class Settings(BaseSettings):
    """Application settings loaded from env vars and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Brella API
    BRELLA_API_BASE_URL: str = Field(default="https://api.brella.io/api")
    BRELLA_AUTH_TOKEN: str | None = Field(default=None)
    BRELLA_EMAIL: str | None = Field(default=None)
    BRELLA_PASSWORD: str | None = Field(default=None)
    BRELLA_RATE_LIMIT_DELAY: float = Field(default=0.5)

    # LLM Configuration
    LLM_PROVIDER: LLMProvider = Field(default=LLMProvider.TEMPLATE)
    ANTHROPIC_API_KEY: str | None = Field(default=None)
    CLAUDE_MODEL: str = Field(default="claude-haiku-4-5-20251001")
    OPENAI_API_KEY: str | None = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-5-mini")

    # Campaign defaults
    CAMPAIGN_MESSAGE_MAX_LENGTH: int = Field(default=500)
    CAMPAIGN_DRY_RUN: bool = Field(default=True)

    # Database
    DATABASE_URL: str = Field(default="sqlite:///brella_outbound.db")

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")

    # MCP Server
    MCP_SERVER_HOST: str = Field(default="127.0.0.1")
    MCP_SERVER_PORT: int = Field(default=8765)


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton Settings instance."""
    return Settings()
