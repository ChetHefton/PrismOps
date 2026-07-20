"""Public-release configuration and secret-safety tests."""

from pathlib import Path

import pytest
from pydantic import ValidationError

import prismops.agents.provider as provider_module
from prismops.agents.provider import (
    LLMConfigurationError,
    OpenAIStructuredOutputClient,
    classify_provider_error,
)
from prismops.config import Settings, get_llm_settings
from prismops.services import run_support_audit
from prismops.ui.session import (
    AUDIT_STATE_KEY,
    CHAT_HISTORY_STATE_KEY,
    clear_conversation,
)


def test_configuration_without_key_is_ai_disabled(monkeypatch) -> None:
    def fail_if_called(**kwargs):
        raise AssertionError("Provider constructor must not be called without a key")

    monkeypatch.setattr(provider_module, "ChatOpenAI", fail_if_called)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert get_llm_settings(settings).api_key_configured is False
    with pytest.raises(LLMConfigurationError):
        OpenAIStructuredOutputClient(settings)


def test_configuration_with_mock_key_calls_provider(monkeypatch) -> None:
    calls = []

    class FakeChatOpenAI:
        def __init__(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(provider_module, "ChatOpenAI", FakeChatOpenAI)
    settings = Settings(_env_file=None, OPENAI_API_KEY="placeholder-key")
    OpenAIStructuredOutputClient(settings)

    assert len(calls) == 1
    assert calls[0]["model"] == "gpt-4.1-mini"


def test_temperature_parsing_and_validation(monkeypatch) -> None:
    monkeypatch.setenv("PRISMOPS_LLM_TEMPERATURE", "0.25")
    assert Settings(_env_file=None).llm_temperature == pytest.approx(0.25)
    monkeypatch.setenv("PRISMOPS_LLM_TEMPERATURE", "not-a-number")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_public_settings_never_serialize_key() -> None:
    settings = Settings(_env_file=None, OPENAI_API_KEY="placeholder-secret")
    serialized = get_llm_settings(settings).model_dump_json()
    assert "placeholder-secret" not in serialized
    assert "openai_api_key" not in serialized


def test_deterministic_audit_needs_no_key(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert run_support_audit().summary.total_ticket_count == 3_000


def test_provider_error_message_is_sanitized() -> None:
    error = classify_provider_error(RuntimeError("provider leaked placeholder-secret"))
    assert "placeholder-secret" not in str(error)


def test_clear_conversation_preserves_audit() -> None:
    state = {AUDIT_STATE_KEY: "audit", CHAT_HISTORY_STATE_KEY: ["message"]}
    clear_conversation(state)
    assert state[AUDIT_STATE_KEY] == "audit"
    assert state[CHAT_HISTORY_STATE_KEY] == []


def test_public_security_files_exist_and_are_configured() -> None:
    env_example = Path(".env.example").read_text(encoding="utf-8")
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    streamlit_config = Path(".streamlit/config.toml").read_text(encoding="utf-8")

    assert "OPENAI_API_KEY=" in env_example
    assert "PRISMOPS_LLM_MODEL=gpt-4.1-mini" in env_example
    assert ".env" in gitignore and "!.env.example" in gitignore
    assert ".venv/" in gitignore and "venv/" in gitignore
    assert "__pycache__/" in gitignore and "*.pyc" in gitignore
    assert "gatherUsageStats = false" in streamlit_config
