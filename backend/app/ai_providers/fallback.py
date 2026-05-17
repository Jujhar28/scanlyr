"""Gemini primary with Groq fallback for AI text analysis."""

from __future__ import annotations

import logging

from app.ai_providers.base import AIProvider
from app.ai_providers.errors import AIProviderConfigError, AIProviderError, AIProviderResponseError
from app.ai_providers.gemini import GeminiProvider
from app.ai_providers.groq import GroqProvider
from app.ai_providers.schemas import HybridReverifyOutcome, HybridReverifyResult, ProviderAnalysisOutcome, TextAnalysisResult
from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class FallbackAIProvider(AIProvider):
    """
    Tries Gemini first; on failure falls back to Groq.

    Returns the same :class:`TextAnalysisResult` schema from either adapter.
    Use :meth:`analyze_with_outcome` or :attr:`last_outcome` to see which provider served the request.
    """

    provider_id = "auto"

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        gemini: GeminiProvider | None = None,
        groq: GroqProvider | None = None,
        timeout_seconds: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        cfg = settings or get_settings()
        self._settings = cfg
        self._gemini = gemini if gemini is not None else GeminiProvider(
            settings=cfg,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self._groq = groq if groq is not None else GroqProvider(
            settings=cfg,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
        )
        self._last_outcome: ProviderAnalysisOutcome | None = None

    @property
    def last_outcome(self) -> ProviderAnalysisOutcome | None:
        return self._last_outcome

    @property
    def last_provider_used(self) -> str | None:
        return self._last_outcome.provider_id if self._last_outcome else None

    def analyze_text(self, input_text: str) -> TextAnalysisResult:
        outcome = self.analyze_with_outcome(input_text)
        return outcome.result

    def analyze_with_outcome(self, input_text: str) -> ProviderAnalysisOutcome:
        attempted: list[str] = []
        errors: list[str] = []

        if self._gemini_configured():
            attempted.append("gemini")
            try:
                result = self._gemini.analyze_text(input_text)
                outcome = ProviderAnalysisOutcome(
                    result=result,
                    provider_id="gemini",
                    fallback_used=False,
                    attempted_providers=list(attempted),
                )
                self._last_outcome = outcome
                logger.info(
                    "ai_provider_analysis_succeeded",
                    extra={
                        "provider": "gemini",
                        "fallback_used": False,
                        "risk_level": result.risk_level,
                        "category": result.category,
                    },
                )
                return outcome
            except AIProviderError as exc:
                msg = f"gemini: {exc}"
                errors.append(msg)
                logger.warning(
                    "ai_provider_primary_failed",
                    extra={"provider": "gemini", "error": str(exc)},
                )
            except Exception as exc:
                msg = f"gemini: {exc}"
                errors.append(msg)
                logger.warning(
                    "ai_provider_primary_failed",
                    extra={"provider": "gemini", "error": str(exc)},
                    exc_info=True,
                )
        else:
            logger.info(
                "ai_provider_skipped",
                extra={"provider": "gemini", "reason": "GEMINI_API_KEY not configured"},
            )

        if not self._groq_configured():
            detail = "; ".join(errors) if errors else "no provider API keys configured"
            raise AIProviderConfigError(
                f"AI analysis unavailable. Gemini failed or skipped and GROQ_API_KEY is not set. ({detail})",
            )

        attempted.append("groq")
        try:
            result = self._groq.analyze_text(input_text)
            fallback = "gemini" in attempted
            outcome = ProviderAnalysisOutcome(
                result=result,
                provider_id="groq",
                fallback_used=fallback,
                attempted_providers=list(attempted),
            )
            self._last_outcome = outcome
            logger.info(
                "ai_provider_analysis_succeeded",
                extra={
                    "provider": "groq",
                    "fallback_used": fallback,
                    "risk_level": result.risk_level,
                    "category": result.category,
                },
            )
            if fallback:
                logger.info(
                    "ai_provider_fallback_used",
                    extra={"primary": "gemini", "fallback": "groq", "prior_errors": errors},
                )
            return outcome
        except AIProviderError as exc:
            errors.append(f"groq: {exc}")
            logger.error(
                "ai_provider_fallback_failed",
                extra={"provider": "groq", "error": str(exc), "attempted": attempted},
            )
        except Exception as exc:
            errors.append(f"groq: {exc}")
            logger.error(
                "ai_provider_fallback_failed",
                extra={"provider": "groq", "error": str(exc), "attempted": attempted},
                exc_info=True,
            )

        raise AIProviderResponseError(
            "All configured AI providers failed. " + "; ".join(errors),
        )

    def analyze_hybrid_reverify_with_outcome(
        self,
        input_text: str,
        findings: list[dict[str, object]],
    ) -> HybridReverifyOutcome:
        """Try Gemini re-verify, then Groq on failure."""
        attempted: list[str] = []
        errors: list[str] = []

        if self._gemini_configured():
            attempted.append("gemini")
            try:
                result = self._gemini.analyze_hybrid_reverify(input_text, findings)
                outcome = HybridReverifyOutcome(
                    result=result,
                    provider_id="gemini",
                    fallback_used=False,
                    attempted_providers=list(attempted),
                )
                return outcome
            except AIProviderError as exc:
                errors.append(f"gemini: {exc}")
                logger.warning("ai_reverify_primary_failed", extra={"provider": "gemini", "error": str(exc)})

        if not self._groq_configured():
            detail = "; ".join(errors) if errors else "no provider API keys configured"
            raise AIProviderConfigError(f"Hybrid re-verify unavailable. ({detail})")

        attempted.append("groq")
        result = self._groq.analyze_hybrid_reverify(input_text, findings)
        return HybridReverifyOutcome(
            result=result,
            provider_id="groq",
            fallback_used="gemini" in attempted,
            attempted_providers=list(attempted),
        )

    def _gemini_configured(self) -> bool:
        key = (self._settings.gemini_api_key or "").strip()
        return bool(key)

    def _groq_configured(self) -> bool:
        key = (self._settings.groq_api_key or "").strip()
        return bool(key)
