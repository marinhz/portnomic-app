import json
import logging
import uuid
from dataclasses import dataclass

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.resilience import CircuitBreaker
from app.schemas.ai import ParsedEmailResult
from app.services.tenant_llm_config_svc import get_decrypted_llm_credentials, get_tenant_llm_config
from app.telemetry import get_tracer

logger = logging.getLogger("shipflow.llm")
tracer = get_tracer()

TRANSIENT_EXCEPTIONS = (APIConnectionError, APITimeoutError, RateLimitError)

# Circuit breaker: global for v1; tenant-specific in future if needed.
_llm_circuit = CircuitBreaker(
    name="llm",
    failure_threshold=settings.cb_failure_threshold,
    recovery_timeout=settings.cb_recovery_timeout,
    half_open_max_calls=settings.cb_half_open_max_calls,
)


class LlmConfigError(Exception):
    """Raised when LLM config cannot be resolved (no key, invalid key, etc.)."""

    pass


@dataclass
class LlmConfig:
    """Resolved LLM configuration (tenant or platform)."""

    api_key: str
    base_url: str
    model: str


def _build_client(config: LlmConfig) -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=settings.llm_timeout_seconds,
    )


async def _get_llm_config(
    db: AsyncSession | None,
    tenant_id: uuid.UUID | None,
) -> LlmConfig:
    """Resolve LLM config: tenant if enabled, else platform defaults.

    Raises LlmConfigError if no valid key available.
    """
    if db and tenant_id:
        config = await get_tenant_llm_config(db, tenant_id)
        creds = get_decrypted_llm_credentials(config)
        if creds is not None:
            api_key, base_url, model = creds
            return LlmConfig(api_key=api_key, base_url=base_url, model=model)
        if config is not None and config.enabled and config.api_key_encrypted:
            raise LlmConfigError("API key invalid or expired. Please update in Settings.")

    # Platform fallback
    if not settings.llm_api_key or not settings.llm_api_key.strip():
        raise LlmConfigError("AI parsing not configured. Contact your administrator.")
    return LlmConfig(
        api_key=settings.llm_api_key,
        base_url=settings.llm_api_url,
        model=settings.llm_model,
    )


async def call_llm(
    system_prompt: str,
    user_content: str,
    *,
    model: str | None = None,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> dict:
    """Call the LLM and return parsed JSON response.

    The call is wrapped by a circuit breaker that trips after repeated
    failures, and by an OpenTelemetry span for distributed tracing.

    When tenant_id and db are provided, uses tenant LLM config if enabled;
    otherwise falls back to platform config.

    Raises LlmConfigError if no valid API key. Raises TRANSIENT_EXCEPTIONS
    for retryable errors, ValueError for malformed output, CircuitBreakerOpen
    when the breaker is open.
    """
    llm_config = await _get_llm_config(db, tenant_id)
    target_model = model or llm_config.model

    async def _do_call() -> dict:
        with tracer.start_as_current_span(
            "llm.chat_completion",
            attributes={"llm.model": target_model},
        ) as span:
            client = _build_client(llm_config)

            response = await client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content
            if not raw_text:
                raise ValueError("LLM returned empty response")

            span.set_attribute("llm.response_length", len(raw_text))

            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError as exc:
                raise ValueError(f"LLM returned invalid JSON: {exc}") from exc

            return parsed

    return await _llm_circuit.call(_do_call)


async def parse_email_content(
    system_prompt: str,
    email_body: str,
    email_subject: str | None = None,
    *,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
) -> ParsedEmailResult:
    """Parse an email using the LLM and return a validated result."""
    user_content = ""
    if email_subject:
        user_content += f"Subject: {email_subject}\n\n"
    user_content += email_body

    max_chars = settings.llm_max_input_chars
    if len(user_content) > max_chars:
        original_len = len(user_content)
        user_content = user_content[:max_chars] + "\n\n[... truncated for token limit ...]"
        logger.info("Email truncated from %d to %d chars for LLM", original_len, max_chars)

    raw_result = await call_llm(system_prompt, user_content, tenant_id=tenant_id, db=db)
    return ParsedEmailResult.model_validate(raw_result)


def is_transient_error(exc: Exception) -> bool:
    return isinstance(exc, TRANSIENT_EXCEPTIONS)


async def test_llm_connection(
    *,
    tenant_id: uuid.UUID | None = None,
    db: AsyncSession | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    model: str | None = None,
) -> tuple[str, str]:
    """Test LLM connection with minimal prompt.

    When api_key, base_url, or model are provided, use those for the test
    (test-before-save). Otherwise resolve from tenant/platform config.

    Returns (model_used, response_message) on success.
    Raises LlmConfigError, APIConnectionError, APITimeoutError, RateLimitError,
    AuthenticationError, or ValueError (invalid URL).
    """
    if api_key is not None or base_url is not None or model is not None:
        # Test with override config (unsaved form values)
        resolved_key = api_key
        resolved_base = base_url
        resolved_model = model

        if resolved_key is None or not resolved_key.strip():
            # Fall back to saved config for api_key when testing base_url/model only
            creds = None
            if db and tenant_id:
                config = await get_tenant_llm_config(db, tenant_id)
                creds = get_decrypted_llm_credentials(config)
            if creds is None:
                if not settings.llm_api_key or not settings.llm_api_key.strip():
                    raise LlmConfigError("API key is required. Enter your key or save config first.")
                resolved_key = settings.llm_api_key
                resolved_base = resolved_base or settings.llm_api_url
                resolved_model = resolved_model or settings.llm_model
            else:
                saved_key, saved_base, saved_model = creds
                resolved_key = resolved_key or saved_key
                resolved_base = resolved_base or saved_base
                resolved_model = resolved_model or saved_model
        else:
            resolved_base = resolved_base or settings.llm_api_url
            resolved_model = resolved_model or settings.llm_model

        llm_config = LlmConfig(
            api_key=resolved_key.strip(),
            base_url=resolved_base.strip(),
            model=resolved_model.strip(),
        )
    else:
        llm_config = await _get_llm_config(db, tenant_id)

    client = _build_client(llm_config)

    await client.chat.completions.create(
        model=llm_config.model,
        messages=[
            {"role": "user", "content": "Reply with exactly: OK"},
        ],
        max_tokens=10,
    )

    return (llm_config.model, "OK")
