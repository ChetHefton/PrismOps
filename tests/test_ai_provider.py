"""Tests for environment-driven model-provider configuration."""

import pytest

from prismops.agents.provider import LLMConfigurationError, OpenAIStructuredOutputClient
from prismops.config import Settings


def test_missing_api_key_has_clear_error() -> None:
    settings = Settings(_env_file=None, OPENAI_API_KEY="")

    with pytest.raises(LLMConfigurationError, match="OPENAI_API_KEY is required"):
        OpenAIStructuredOutputClient(settings)


def test_invalid_temperature_has_clear_error() -> None:
    settings = Settings(
        _env_file=None,
        OPENAI_API_KEY="test-key",
        llm_temperature=1.5,
    )

    with pytest.raises(LLMConfigurationError, match="between 0 and 1"):
        OpenAIStructuredOutputClient(settings)
