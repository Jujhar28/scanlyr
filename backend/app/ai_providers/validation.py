"""Strict validation for AI provider JSON payloads."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import ValidationError

from app.ai_providers._http import parse_analysis_json, parse_json_object
from app.ai_providers.errors import AIProviderResponseError
from app.ai_providers.schemas import (
    HybridReverifyResult,
    ProviderAnalysisOutcome,
    TextAnalysisResult,
)

RiskLevel = Literal["low", "medium", "high", "critical"]

_MAX_EXPLANATION_LEN = 2_000
_MAX_CATEGORY_LEN = 128
_CATEGORY_SAFE_RE = re.compile(r"[^\w\s\-_/]", re.UNICODE)


_SEVERITY_ORDER: dict[str, int] = {
    "low": 0,
    "medium": 1,
    "high": 2,
    "critical": 3,
}


def risk_level_for_score(score: int) -> RiskLevel:
    """Map numeric score to canonical risk level (aligned with rules engine thresholds)."""
    if score >= 90:
        return "critical"
    if score >= 80:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def resolve_risk_level(score: int, declared: str) -> RiskLevel:
    """Use the higher of score-derived vs model-declared level (never under-state risk)."""
    if declared not in _SEVERITY_ORDER:
        raise AIProviderResponseError(f"invalid risk_level: {declared!r}")
    from_score = risk_level_for_score(score)
    if _SEVERITY_ORDER[declared] >= _SEVERITY_ORDER[from_score]:
        return declared  # type: ignore[return-value]
    return from_score


def parse_and_validate_analysis_json(raw: str) -> TextAnalysisResult:
    """Parse model JSON and apply strict schema + consistency checks."""
    try:
        parsed = parse_analysis_json(raw)
    except AIProviderResponseError:
        raise
    except Exception as exc:
        raise AIProviderResponseError(f"Failed to parse model JSON: {exc}") from exc
    return validate_text_analysis_result(parsed)


def validate_text_analysis_result(result: TextAnalysisResult) -> TextAnalysisResult:
    """
    Normalize and verify a parsed :class:`TextAnalysisResult`.

    Raises :class:`AIProviderResponseError` when the payload cannot be made safe.
    """
    try:
        score = int(result.risk_score)
    except (TypeError, ValueError) as exc:
        raise AIProviderResponseError("risk_score must be an integer.") from exc

    if not 0 <= score <= 100:
        raise AIProviderResponseError(f"risk_score out of range: {score}")

    explanation = (result.explanation or "").strip()
    if not explanation:
        raise AIProviderResponseError("explanation must not be empty.")
    if len(explanation) > _MAX_EXPLANATION_LEN:
        explanation = explanation[:_MAX_EXPLANATION_LEN].rstrip() + "…"

    category_raw = (result.category or "").strip()
    if not category_raw:
        raise AIProviderResponseError("category must not be empty.")
    category = _CATEGORY_SAFE_RE.sub("", category_raw).strip()[:_MAX_CATEGORY_LEN]
    if not category:
        raise AIProviderResponseError("category invalid after sanitization.")

    level = resolve_risk_level(score, result.risk_level)

    try:
        return TextAnalysisResult.model_validate(
            {
                "risk_score": score,
                "risk_level": level,
                "explanation": explanation,
                "category": category,
            },
        )
    except ValidationError as exc:
        raise AIProviderResponseError(f"analysis schema validation failed: {exc}") from exc


def parse_and_validate_hybrid_reverify_json(raw: str) -> HybridReverifyResult:
    """Parse model JSON for hybrid re-verify (rules findings adjudication)."""
    try:
        parsed = parse_json_object(raw)
    except AIProviderResponseError:
        raise
    except Exception as exc:
        raise AIProviderResponseError(f"Failed to parse hybrid reverify JSON: {exc}") from exc

    try:
        score = int(parsed.get("risk_score", -1))
    except (TypeError, ValueError) as exc:
        raise AIProviderResponseError("risk_score must be an integer.") from exc
    if not 0 <= score <= 100:
        raise AIProviderResponseError(f"risk_score out of range: {score}")

    explanation = str(parsed.get("explanation", "")).strip()
    if not explanation:
        raise AIProviderResponseError("explanation must not be empty.")

    category_raw = str(parsed.get("category", "")).strip()
    category = _CATEGORY_SAFE_RE.sub("", category_raw).strip()[:_MAX_CATEGORY_LEN]
    if not category:
        raise AIProviderResponseError("category invalid after sanitization.")

    declared = str(parsed.get("risk_level", "")).strip().lower()
    level = resolve_risk_level(score, declared)

    verdicts_raw = parsed.get("finding_verdicts")
    if not isinstance(verdicts_raw, list):
        raise AIProviderResponseError("finding_verdicts must be an array.")

    try:
        return HybridReverifyResult.model_validate(
            {
                "risk_score": score,
                "risk_level": level,
                "explanation": explanation[:_MAX_EXPLANATION_LEN],
                "category": category,
                "finding_verdicts": verdicts_raw,
            },
        )
    except ValidationError as exc:
        raise AIProviderResponseError(f"hybrid reverify validation failed: {exc}") from exc


def validate_provider_outcome(outcome: ProviderAnalysisOutcome) -> ProviderAnalysisOutcome:
    """Re-validate AI outcome before fusion; never trust raw provider output blindly."""
    validated = validate_text_analysis_result(outcome.result)
    if outcome.provider_id not in ("gemini", "groq", "auto"):
        raise AIProviderResponseError(f"unknown provider_id: {outcome.provider_id!r}")
    return outcome.model_copy(update={"result": validated})
