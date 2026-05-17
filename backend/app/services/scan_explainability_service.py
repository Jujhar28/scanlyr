"""Build layered, user-facing explainability for POST /scan responses."""

from __future__ import annotations

from typing import Literal

from app.ai_providers.schemas import ProviderAnalysisOutcome, TextAnalysisResult
from app.scan_security.schemas.results import ScanAnalysisResult
from app.schemas.scan import (
    ScanAIAssessment,
    ScanAssessmentSummary,
    ScanComposition,
    ScanExplainability,
    ScanFusionDetails,
    ScanRulesAssessment,
    ScanTechnicalDetails,
)
from app.scan_security.analysis.fixtures import scan_indicates_synthetic_fixture
from app.services.scan_safety_service import SAFE_ENGINE_VERSION

CompositionMethod = Literal["hybrid", "rules_only", "safe_default"]

_RISK_LABELS = {
    "low": "Low risk",
    "medium": "Medium risk",
    "high": "High risk",
    "critical": "Critical risk",
}


def humanize_category(slug: str) -> str:
    return slug.replace("_", " ").replace("-", " ").strip().title()


def build_scan_explainability(
    *,
    result: ScanAnalysisResult,
    rules_result: ScanAnalysisResult,
    fusion: ScanFusionDetails | None,
    ai_outcome: ProviderAnalysisOutcome | None,
    engine_version: str,
    input_text: str | None = None,
) -> ScanExplainability:
    """Assemble summary, rules, AI, composition, and optional technical layers."""
    method = _composition_method(fusion, engine_version)
    fusion = fusion or ScanFusionDetails(
        rules_score=rules_result.risk_score,
        ai_score=None,
        combined_score=result.risk_score,
        rules_weight=1.0,
        ai_weight=0.0,
        ai_used=False,
    )

    synthetic = bool(
        input_text
        and scan_indicates_synthetic_fixture(input_text, findings=list(rules_result.findings)),
    )
    rules_layer = _build_rules_layer(rules_result)
    ai_layer = _build_ai_layer(ai_outcome, fusion, synthetic_fixture=synthetic)
    composition = _build_composition(method, fusion, result.risk_score, synthetic_fixture=synthetic)
    summary = _build_summary(
        result=result,
        rules_layer=rules_layer,
        ai_layer=ai_layer,
        composition=composition,
        method=method,
    )
    technical = _build_technical(
        rules_result=rules_result,
        fusion=fusion,
        ai_outcome=ai_outcome,
        engine_version=engine_version,
    )

    return ScanExplainability(
        summary=summary,
        rules=rules_layer,
        ai=ai_layer,
        composition=composition,
        technical=technical,
    )


def summary_text(explainability: ScanExplainability) -> str:
    """Short legacy ``explanation`` field for backward compatibility."""
    return explainability.summary.summary


def _composition_method(fusion: ScanFusionDetails | None, engine_version: str) -> CompositionMethod:
    if engine_version == SAFE_ENGINE_VERSION:
        return "safe_default"
    if fusion and fusion.ai_used:
        return "hybrid"
    return "rules_only"


def _build_rules_layer(rules: ScanAnalysisResult) -> ScanRulesAssessment:
    concerns = [_finding_concern(f) for f in rules.findings[:4]]
    concerns = [c for c in concerns if c]

    if not rules.findings:
        summary = "Automated pattern checks did not flag any known security issues."
    elif len(concerns) == 1:
        summary = f"Pattern checks flagged: {concerns[0]}."
    else:
        lead = ", ".join(concerns[:2])
        extra = f" and {len(rules.findings) - 2} more" if len(rules.findings) > 2 else ""
        summary = f"Pattern checks flagged {len(rules.findings)} issue(s), including {lead}{extra}."

    top_categories = [
        humanize_category(c.risk_category)
        for c in sorted(rules.score_breakdown.categories, key=lambda x: x.score, reverse=True)
        if c.score > 0
    ][:3]

    return ScanRulesAssessment(
        score=rules.risk_score,
        risk_level=rules.risk_level,
        summary=summary,
        primary_concerns=concerns,
        top_categories=top_categories,
    )


def _finding_concern(finding: object) -> str:
    title = getattr(finding, "title", None)
    if isinstance(title, str) and title.strip():
        return title.strip()
    desc = getattr(finding, "description", None)
    if isinstance(desc, str) and desc.strip():
        return desc.strip()[:120]
    return ""


def _build_ai_layer(
    ai_outcome: ProviderAnalysisOutcome | None,
    fusion: ScanFusionDetails,
    *,
    synthetic_fixture: bool = False,
) -> ScanAIAssessment:
    if not fusion.ai_used or ai_outcome is None:
        return ScanAIAssessment(used=False)

    ai = ai_outcome.result
    category_label = humanize_category(ai.category)
    if synthetic_fixture:
        return ScanAIAssessment(
            used=True,
            score=min(ai.risk_score, fusion.rules_score + 12),
            risk_level="low" if fusion.rules_score <= 40 else ai.risk_level,
            category=category_label,
            summary=(
                "Contextual review noted credential-like wording, but it aligns with "
                "example or test data rather than a confirmed live secret."
            ),
        )

    summary = ai.explanation.strip()
    if summary and not summary.endswith("."):
        summary += "."

    return ScanAIAssessment(
        used=True,
        score=ai.risk_score,
        risk_level=ai.risk_level,
        category=category_label,
        summary=summary or f"Classified as {category_label}.",
    )


def _build_composition(
    method: CompositionMethod,
    fusion: ScanFusionDetails,
    combined_score: int,
    *,
    synthetic_fixture: bool = False,
) -> ScanComposition:
    rules_pct = int(round(fusion.rules_weight * 100))
    ai_pct = int(round(fusion.ai_weight * 100)) if fusion.ai_used else None
    label = {
        "hybrid": (
            "No urgent action — content looks like example or test credentials. "
            "Avoid pasting even sample passwords into production AI tools."
            if synthetic_fixture
            else "Pattern checks were re-verified by AI for context. Review remediations before sharing this content."
        ),
        "rules_only": "Based on automated pattern checks",
        "safe_default": "Limited assessment (services unavailable)",
    }[method]
    return ScanComposition(
        method=method,
        combined_score=combined_score,
        label=label,
        rules_weight_percent=rules_pct,
        ai_weight_percent=ai_pct,
        rules_score=fusion.rules_score,
        ai_score=fusion.ai_score,
    )


def _build_summary(
    *,
    result: ScanAnalysisResult,
    rules_layer: ScanRulesAssessment,
    ai_layer: ScanAIAssessment,
    composition: ScanComposition,
    method: CompositionMethod,
) -> ScanAssessmentSummary:
    headline = f"{_RISK_LABELS.get(result.risk_level, result.risk_level.title())} ({result.risk_score}/100)"

    if method == "safe_default":
        return ScanAssessmentSummary(
            headline="Assessment unavailable",
            score=result.risk_score,
            risk_level=result.risk_level,
            summary=(
                "We could not fully analyze this content. Treat it as unverified and "
                "re-run the scan when the service is available."
            ),
        )

    if not rules_layer.primary_concerns and not ai_layer.used:
        return ScanAssessmentSummary(
            headline=headline,
            score=result.risk_score,
            risk_level=result.risk_level,
            summary="No significant security issues were detected in this text.",
        )

    parts: list[str] = []
    if rules_layer.primary_concerns:
        parts.append(rules_layer.summary)
    if ai_layer.used and ai_layer.summary:
        parts.append(ai_layer.summary)

    body = " ".join(parts)
    if method == "hybrid":
        summary = (
            f"{_intent_aware_intro(result, rules_layer, ai_layer)} {body}".strip()
            if body
            else _intent_aware_intro(result, rules_layer, ai_layer)
        )
    else:
        summary = body or "Assessment based on automated security pattern checks."

    return ScanAssessmentSummary(
        headline=headline,
        score=result.risk_score,
        risk_level=result.risk_level,
        summary=summary,
    )


def _intent_aware_intro(
    result: ScanAnalysisResult,
    rules_layer: ScanRulesAssessment,
    ai_layer: ScanAIAssessment,
) -> str:
    """Product-facing one-liner without exposing fusion weights."""
    if result.risk_level == "low":
        if any("example" in c.lower() for c in rules_layer.primary_concerns):
            return (
                "Credential-like patterns were detected but appear to be test or example data, "
                "not a confirmed live leak."
            )
        return "This content looks low risk for active credential exposure."
    concerns = rules_layer.primary_concerns
    if concerns and any("example" in c.lower() for c in concerns):
        return (
            "We found credential-like patterns that appear to be examples or test data — "
            "review before sharing in production systems."
        )
    if ai_layer.used and ai_layer.risk_level == "low" and result.risk_level in ("medium", "high"):
        return (
            "Pattern checks raised concerns, but contextual review suggests limited real-world risk. "
            "Review the breakdown below."
        )
    return "Security signals were detected in this text."


def _build_technical(
    *,
    rules_result: ScanAnalysisResult,
    fusion: ScanFusionDetails,
    ai_outcome: ProviderAnalysisOutcome | None,
    engine_version: str,
) -> ScanTechnicalDetails | None:
    """Pipeline metadata for advanced / support views; omitted when empty."""
    provider = fusion.ai_provider
    fallback = bool(ai_outcome and ai_outcome.fallback_used)
    rules_detail = rules_result.explanation.strip() or None
    ai_detail = ai_outcome.result.explanation.strip() if ai_outcome else None

    if not any((provider, fallback, rules_detail, ai_detail, engine_version)):
        return None

    return ScanTechnicalDetails(
        engine_version=engine_version,
        rules_engine_detail=rules_detail,
        ai_provider=provider,
        ai_fallback_used=fallback,
        ai_detail=ai_detail,
        fusion_weights={
            "rules": fusion.rules_weight,
            "ai": fusion.ai_weight,
        }
        if fusion.ai_used
        else None,
    )
