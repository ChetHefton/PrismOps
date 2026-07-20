"""Small provider abstraction for schema-constrained LLM calls."""

from __future__ import annotations

from typing import Protocol, TypeVar

from langchain_openai import ChatOpenAI
from langchain_core.exceptions import OutputParserException
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    RateLimitError,
)
from pydantic import BaseModel, ValidationError

from prismops.config import Settings, get_settings

StructuredModel = TypeVar("StructuredModel", bound=BaseModel)


class LLMConfigurationError(RuntimeError):
    """Raised when required provider configuration is missing or invalid."""


class LLMProviderError(RuntimeError):
    """Raised when the configured model provider cannot complete a request."""


class MalformedStructuredOutputError(LLMProviderError):
    """Raised when a provider response does not satisfy the requested schema."""


class LLMAuthenticationError(LLMProviderError):
    """Raised when the configured API key is rejected."""


class LLMQuotaError(LLMProviderError):
    """Raised when provider billing or quota prevents a request."""


class LLMRateLimitError(LLMProviderError):
    """Raised when the provider requests a temporary retry."""


class LLMNetworkError(LLMProviderError):
    """Raised when the provider cannot be reached."""


class LLMTimeoutError(LLMProviderError):
    """Raised when the provider request times out."""


class LLMUnsupportedModelError(LLMProviderError):
    """Raised when the configured model is unavailable."""


class StructuredOutputClient(Protocol):
    def generate(
        self, *, prompt: str, schema: type[StructuredModel]
    ) -> StructuredModel: ...


class OpenAIStructuredOutputClient:
    """OpenAI implementation isolated from graph and UI composition."""

    def __init__(self, settings: Settings | None = None) -> None:
        settings = settings or get_settings()
        if settings.openai_api_key is None or not settings.openai_api_key.get_secret_value():
            raise LLMConfigurationError(
                "OPENAI_API_KEY is required to generate AI recommendations."
            )
        if not 0 <= settings.llm_temperature <= 1:
            raise LLMConfigurationError(
                "PRISMOPS_LLM_TEMPERATURE must be between 0 and 1."
            )
        self._model = ChatOpenAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            api_key=settings.openai_api_key.get_secret_value(),
        )

    def generate(
        self, *, prompt: str, schema: type[StructuredModel]
    ) -> StructuredModel:
        try:
            structured_model = self._model.with_structured_output(
                schema, method="json_schema"
            )
            response = structured_model.invoke(prompt)
            if not isinstance(response, schema):
                return schema.model_validate(response)
            return response
        except (ValidationError, OutputParserException) as exc:
            raise MalformedStructuredOutputError(
                f"Model response did not match {schema.__name__}."
            ) from exc
        except MalformedStructuredOutputError:
            raise
        except Exception as exc:
            raise classify_provider_error(exc) from exc


def create_structured_output_client(
    settings: Settings | None = None,
) -> StructuredOutputClient:
    return OpenAIStructuredOutputClient(settings)


def classify_provider_error(exc: Exception) -> LLMProviderError:
    """Map provider exceptions to sanitized application errors."""

    if isinstance(exc, AuthenticationError):
        return LLMAuthenticationError("The configured OpenAI API key was rejected.")
    if isinstance(exc, APITimeoutError):
        return LLMTimeoutError("The OpenAI request timed out.")
    if isinstance(exc, APIConnectionError):
        return LLMNetworkError("PrismOps could not reach OpenAI.")
    if isinstance(exc, RateLimitError):
        code = _provider_error_code(exc)
        if code in {"insufficient_quota", "billing_hard_limit_reached"}:
            return LLMQuotaError("OpenAI quota or billing limits prevented the request.")
        return LLMRateLimitError("OpenAI is rate limiting requests temporarily.")
    if isinstance(exc, BadRequestError):
        if _provider_error_code(exc) in {"model_not_found", "unsupported_model"}:
            return LLMUnsupportedModelError(
                "The configured OpenAI model is unavailable or unsupported."
            )
    return LLMProviderError("The configured model provider request failed.")


def _provider_error_code(exc: Exception) -> str | None:
    code = getattr(exc, "code", None)
    if isinstance(code, str):
        return code
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        nested = body.get("error", body)
        if isinstance(nested, dict) and isinstance(nested.get("code"), str):
            return nested["code"]
    return None
