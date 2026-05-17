"""Optional AI provider call for hybrid POST /scan."""

from __future__ import annotations

import logging

from app.ai_providers.errors import (
    AIProviderConfigError,
    AIProviderError,
    AIProviderResponseError,
    AIProviderTimeoutError,
)
from app.ai_providers.fallback import FallbackAIProvider
from app.ai_providers.factory import get_ai_provider
from app.ai_providers.schemas import ProviderAnalysisOutcome
from app.ai_providers.validation import validate_provider_outcome
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


def ai_keys_configured(settings: Settings | None = None) -> bool:
    cfg = settings or get_settings()
    provider_id = (cfg.ai_provider or "auto").strip().lower()
    if provider_id == "groq":
        return bool((cfg.groq_api_key or "").strip())
    if provider_id == "gemini":
        return bool((cfg.gemini_api_key or "").strip())
    return bool((cfg.gemini_api_key or "").strip()) or bool((cfg.groq_api_key or "").strip())


def _invoke_provider(
    provider: object,
    input_text: str,
) -> ProviderAnalysisOutcome:
    if isinstance(provider, FallbackAIProvider):
        return provider.analyze_with_outcome(input_text)
    from app.ai_providers.base import AIProvider

    if not isinstance(provider, AIProvider):
        raise AIProviderConfigError("Invalid AI provider instance.")
    result = provider.analyze_text(input_text)
    return ProviderAnalysisOutcome(
        result=result,
        provider_id=provider.provider_id,
        fallback_used=False,
        attempted_providers=[provider.provider_id],
    )


def try_ai_scan_analysis(
    input_text: str,
    *,
    settings: Settings | None = None,
) -> ProviderAnalysisOutcome | None:
    """
    Run the configured AI provider on ``input_text``.

    Returns ``None`` when fusion is disabled, keys are missing, the provider fails,
    or the response fails strict validation (rules-only fallback).
    """
    cfg = settings or get_settings()
    if not cfg.scan_ai_fusion_enabled:
        logger.debug("scan_ai_layer_skipped", extra={"reason": "fusion_disabled"})
        return None
    if not ai_keys_configured(cfg):
        logger.debug("scan_ai_layer_skipped", extra={"reason": "no_api_keys"})
        return None

    timeout = cfg.scan_ai_provider_timeout_seconds
    retries = cfg.scan_ai_max_retries

    try:
        provider = get_ai_provider(
            settings=cfg,
            timeout_seconds=timeout,
            max_retries=retries,
        )
        outcome = _invoke_provider(provider, input_text)
        outcome = validate_provider_outcome(outcome)
        logger.info(
            "scan_ai_layer_succeeded",
            extra={
                "ai_provider": outcome.provider_id,
                "ai_score": outcome.result.risk_score,
                "ai_risk_level": outcome.result.risk_level,
                "ai_category": outcome.result.category,
                "ai_fallback_used": outcome.fallback_used,
                "timeout_seconds": timeout,
            },
        )
        return outcome
    except AIProviderTimeoutError as exc:
        logger.warning(
            "scan_ai_layer_timeout",
            extra={
                "error": str(exc),
                "timeout_seconds": timeout,
            },
        )
        return None
    except (AIProviderError, AIProviderConfigError) as exc:
        logger.warning(
            "scan_ai_layer_failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return None
    except AIProviderResponseError as exc:
        logger.warning(
            "scan_ai_layer_invalid_response",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return None
    except Exception as exc:
        logger.exception(
            "scan_ai_layer_unexpected_error",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return None
