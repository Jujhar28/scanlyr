from __future__ import annotations

from app.ai_providers.base import AIProvider
from app.ai_providers.errors import AIProviderConfigError
from app.ai_providers.fallback import FallbackAIProvider
from app.ai_providers.gemini import GeminiProvider
from app.ai_providers.groq import GroqProvider
from app.core.config import Settings, get_settings


def registered_provider_ids() -> tuple[str, ...]:
    return ("auto", "gemini", "groq")


def get_ai_provider(
    name: str | None = None,
    *,
    settings: Settings | None = None,
    timeout_seconds: float | None = None,
    max_retries: int | None = None,
) -> AIProvider:
    """
    Resolve a provider adapter by id.

    - ``auto`` (default): Gemini with Groq fallback on failure.
    - ``gemini``: Gemini only.
    - ``groq``: Groq only.

    Optional ``timeout_seconds`` / ``max_retries`` override defaults (used by POST /scan).
    """
    cfg = settings or get_settings()
    provider_id = (name or cfg.ai_provider or "auto").strip().lower()
    timeout = (
        timeout_seconds if timeout_seconds is not None else cfg.ai_provider_timeout_seconds
    )
    retries = max_retries if max_retries is not None else cfg.gemini_max_retries

    if provider_id == "auto":
        return FallbackAIProvider(
            settings=cfg,
            timeout_seconds=timeout,
            max_retries=retries,
        )
    if provider_id == "gemini":
        return GeminiProvider(settings=cfg, timeout_seconds=timeout, max_retries=retries)
    if provider_id == "groq":
        groq_retries = max_retries if max_retries is not None else cfg.groq_max_retries
        return GroqProvider(
            settings=cfg,
            timeout_seconds=timeout,
            max_retries=groq_retries,
        )
    supported = ", ".join(registered_provider_ids())
    raise AIProviderConfigError(
        f"Unknown AI provider {provider_id!r}. Supported: {supported}.",
    )
