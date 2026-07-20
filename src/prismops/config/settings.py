"""Typed settings loaded from environment variables and .env."""

from functools import lru_cache
from pathlib import Path
import re

from dotenv import load_dotenv
from pydantic import BaseModel, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for local development and deployment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PRISMOPS_",
        extra="ignore",
    )

    env: str = "development"
    demo_company_path: Path = Path("data/demo/company.json")
    support_tickets_path: Path = Path("data/demo/support_tickets.csv")
    support_process_path: Path = Path("data/demo/support_process.md")
    duckdb_path: Path = Path("data/local/prismops.duckdb")
    openai_api_key: SecretStr | None = Field(
        default=None, validation_alias="OPENAI_API_KEY"
    )
    llm_model: str = "gpt-4.1-mini"
    llm_temperature: float = 0.0
    max_chat_messages: int = Field(default=6, ge=1, le=20)

    @field_validator("llm_model")
    @classmethod
    def validate_model_name(cls, value: str) -> str:
        value = value.strip()
        if not value or not re.fullmatch(r"[A-Za-z0-9._:-]+", value):
            raise ValueError("PRISMOPS_LLM_MODEL contains invalid characters")
        return value


class LLMSettings(BaseModel):
    """Serializable, non-sensitive AI availability information."""

    provider: str = "OpenAI"
    model: str
    temperature: float
    api_key_configured: bool


def get_llm_settings(settings: Settings | None = None) -> LLMSettings:
    settings = settings or get_settings()
    configured = bool(
        settings.openai_api_key and settings.openai_api_key.get_secret_value().strip()
    )
    return LLMSettings(
        model=settings.llm_model,
        temperature=settings.llm_temperature,
        api_key_configured=configured,
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached settings instance."""

    load_dotenv(dotenv_path=".env", override=False)
    return Settings()
