"""Combine rule-engine and AI provider scores for POST /scan."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
from app.scan_security.analysis.fixtures import scan_indicates_synthetic_fixture
from app.scan_security.schemas.results import ScanAnalysisResult
from app.scan_security.services.scoring import risk_level_from_score
from app.schemas.scan import ScanFusionDetails

logger = logging.getLogger(__name__)

DEFAULT_RULES_WEIGHT = 0.4
DEFAULT_AI_WEIGHT = 0.6
_DEFAULT_AI_CONFIDENCE = 0.72


@dataclass(frozen=True)
class FusionResult:
    """Merged scan analysis plus explainability for the API envelope."""

    analysis: ScanAnalysisResult
    fusion: ScanFusionDetails


def fuse_rules_and_ai(
    rules: ScanAnalysisResult,
    ai_outcome: ProviderAnalysisOutcome | None,
    *,
    rules_weight: float = DEFAULT_RULES_WEIGHT,
    ai_weight: float = DEFAULT_AI_WEIGHT,
    input_text: str | None = None,
) -> FusionResult:
    """
    Blend rules engine output with optional AI provider output.

    When AI is unavailable, returns the rules result unchanged (100% rules).
    """
    rules_score = rules.risk_score

    if ai_outcome is None:
        fusion = ScanFusionDetails(
            rules_score=rules_score,
            ai_score=None,
            combined_score=rules_score,
            rules_weight=rules_weight,
            ai_weight=ai_weight,
            ai_used=False,
            ai_provider=None,
            ai_category=None,
        )
        logger.info(
            "scan_fusion_rules_only",
            extra={
                "rules_score": rules_score,
                "combined_score": rules_score,
                "ai_used": False,
            },
        )
        return FusionResult(analysis=rules, fusion=fusion)

    ai_score = ai_outcome.result.risk_score
    synthetic = bool(
        input_text
        and scan_indicates_synthetic_fixture(input_text, findings=list(rules.findings)),
    )
    if synthetic:
        # Example/test fixtures: rules-led score; do not let generic AI "secrets" panic dominate.
        capped_ai = min(ai_score, max(rules_score + 12, 28))
        effective_rules_w = 0.78
        effective_ai_w = 0.22
        combined = _weighted_score(rules_score, capped_ai, effective_rules_w, effective_ai_w)
        combined = min(combined, max(rules_score + 8, 35))
        logger.info(
            "scan_fusion_synthetic_fixture",
            extra={
                "rules_score": rules_score,
                "ai_score_raw": ai_score,
                "ai_score_capped": capped_ai,
                "combined_score": combined,
            },
        )
    else:
        combined = _weighted_score(rules_score, ai_score, rules_weight, ai_weight)
    combined_level = risk_level_from_score(combined, list(rules.findings))
    ai_confidence = _DEFAULT_AI_CONFIDENCE
    combined_confidence = round(
        min(0.99, rules_weight * rules.confidence + ai_weight * ai_confidence),
        3,
    )

    remediation = _merge_remediation(rules.remediation_steps, ai_outcome.result)

    risk_categories = dict(rules.risk_categories)
    if ai_outcome.result.category:
        cat_key = ai_outcome.result.category.replace(" ", "_").lower()[:64]
        existing = risk_categories.get(cat_key, 0)
        risk_categories[cat_key] = max(existing, ai_score)

    fused_breakdown = rules.score_breakdown
    if fused_breakdown.overall != combined:
        fused_breakdown = type(fused_breakdown)(
            overall=combined,
            categories=fused_breakdown.categories,
            top_drivers=tuple(
                list(fused_breakdown.top_drivers)
                + [f"ai:{ai_outcome.result.category} ({ai_score})"],
            )[:6],
        )

    fused = ScanAnalysisResult(
        risk_score=combined,
        risk_level=combined_level,
        confidence=combined_confidence,
        explanation=rules.explanation,
        findings=rules.findings,
        remediation_steps=remediation,
        content_kind=rules.content_kind,
        risk_categories=risk_categories,
        score_breakdown=fused_breakdown,
    )

    fusion = ScanFusionDetails(
        rules_score=rules_score,
        ai_score=ai_score,
        combined_score=combined,
        rules_weight=rules_weight,
        ai_weight=ai_weight,
        ai_used=True,
        ai_provider=ai_outcome.provider_id,
        ai_category=ai_outcome.result.category,
    )

    logger.info(
        "scan_fusion_combined",
        extra={
            "rules_score": rules_score,
            "ai_score": ai_score,
            "combined_score": combined,
            "rules_weight": rules_weight,
            "ai_weight": ai_weight,
            "rules_contribution": round(rules_weight * rules_score, 2),
            "ai_contribution": round(ai_weight * ai_score, 2),
            "ai_provider": ai_outcome.provider_id,
            "ai_fallback_used": ai_outcome.fallback_used,
            "risk_level": combined_level,
        },
    )

    return FusionResult(analysis=fused, fusion=fusion)


def _weighted_score(
    rules_score: int,
    ai_score: int,
    rules_weight: float,
    ai_weight: float,
) -> int:
    total_w = rules_weight + ai_weight
    if total_w <= 0:
        return rules_score
    blended = (rules_weight * rules_score + ai_weight * ai_score) / total_w
    return min(100, max(0, int(round(blended))))


def _merge_remediation(
    rules_steps: tuple[str, ...],
    ai_result: TextAnalysisResult,
) -> tuple[str, ...]:
    seen: set[str] = set()
    merged: list[str] = []
    for step in list(rules_steps) + [
        f"Review AI-flagged category «{ai_result.category}»: {ai_result.explanation}",
    ]:
        key = step.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(step.strip())
    return tuple(merged)
