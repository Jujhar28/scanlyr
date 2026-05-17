"""Shared HTTP helpers for provider adapters."""

from __future__ import annotations

import json
import re
from typing import Any

from app.ai_providers.errors import AIProviderResponseError
from app.ai_providers.schemas import TextAnalysisResult


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def parse_analysis_json(raw: str) -> TextAnalysisResult:
    """Extract and validate model JSON from a raw string (may include markdown fences)."""
    text = raw.strip()
    if not text:
        raise AIProviderResponseError("Empty model response.")

    fence = _JSON_FENCE_RE.search(text)
    if fence:
        text = fence.group(1).strip()

    try:
        payload: Any = json.loads(text)
    except json.JSONDecodeError as exc:
        raise AIProviderResponseError(f"Model did not return valid JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise AIProviderResponseError("Model JSON must be an object.")

    allowed = frozenset({"risk_score", "risk_level", "explanation", "category"})
    extra = set(payload.keys()) - allowed
    if extra:
        raise AIProviderResponseError(f"Unexpected JSON fields: {', '.join(sorted(extra))}")

    try:
        return TextAnalysisResult.model_validate(payload)
    except Exception as exc:
        raise AIProviderResponseError(f"JSON does not match analysis schema: {exc}") from exc
