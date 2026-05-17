"""Safe fallbacks when rules engine and/or AI layer fail during POST /scan."""

from __future__ import annotations

import logging

from app.scan_security.context import ContentKind
from app.scan_security.schemas.results import ExplainableRiskScore, ScanAnalysisResult
from app.services.scan_fusion_service import fuse_rules_and_ai
from app.services.security_scan_service import analyze_security_text
from app.ai_providers.schemas import ProviderAnalysisOutcome
from app.schemas.scan import ScanFusionDetails
from app.core.config import Settings

logger = logging.getLogger(__name__)

_RULES_NOT_RUN = object()

SAFE_ENGINE_VERSION = "scan_security_safe_default"
SAFE_DEFAULT_SCORE = 12


def build_safe_default_scan_result(content_type: ContentKind) -> ScanAnalysisResult:
    """Low-risk placeholder when neither rules nor AI could assess the input."""
    return ScanAnalysisResult(
        risk_score=SAFE_DEFAULT_SCORE,
        risk_level="low",
        confidence=0.45,
        explanation=(
            "Scan completed in safe mode. Automated rule and AI analysis were unavailable. "
            "Content was not fully assessed — treat as unverified and re-run when services recover."
        ),
        findings=(),
        remediation_steps=(
            "Re-run the scan after connectivity is restored.",
            "Review content manually if it may contain secrets or policy violations.",
        ),
        content_kind=content_type,
        risk_categories={},
        score_breakdown=ExplainableRiskScore(
            overall=SAFE_DEFAULT_SCORE,
            categories=(),
            top_drivers=(),
        ),
    )


def build_safe_fusion_details() -> ScanFusionDetails:
    return ScanFusionDetails(
        rules_score=SAFE_DEFAULT_SCORE,
        ai_score=None,
        combined_score=SAFE_DEFAULT_SCORE,
        ai_used=False,
        ai_provider=None,
        ai_category=None,
    )


def try_rules_scan(
    input_text: str,
    *,
    content_type: ContentKind = "auto",
) -> ScanAnalysisResult | None:
    """Run the rules engine; return ``None`` on any failure."""
    try:
        return analyze_security_text(input_text, content_type=content_type)
    except Exception as exc:
        logger.exception(
            "scan_rules_engine_failed",
            extra={"error": str(exc), "error_type": type(exc).__name__},
        )
        return None


def run_hybrid_scan_analysis(
    input_text: str,
    *,
    content_type: ContentKind = "auto",
    settings: Settings,
    ai_outcome: ProviderAnalysisOutcome | None,
    rules_result: ScanAnalysisResult | None | object = _RULES_NOT_RUN,
) -> tuple[ScanAnalysisResult, ScanFusionDetails, str]:
    """
    Combine rules + AI with full fallback chain.

    - Rules OK, AI fail → rules only
    - Rules fail → safe default (AI ignored)
    """
    from app.scan_security.services.engine import ENGINE_VERSION

    if rules_result is _RULES_NOT_RUN:
        rules = try_rules_scan(input_text, content_type=content_type)
    else:
        rules = rules_result  # type: ignore[assignment]

    if rules is None:
        safe = build_safe_default_scan_result(content_type)
        fusion = build_safe_fusion_details()
        logger.warning(
            "scan_using_safe_default",
            extra={"reason": "rules_engine_failed", "combined_score": SAFE_DEFAULT_SCORE},
        )
        return safe, fusion, SAFE_ENGINE_VERSION

    fused = fuse_rules_and_ai(
        rules,
        ai_outcome,
        rules_weight=settings.scan_rules_weight,
        ai_weight=settings.scan_ai_weight,
        input_text=input_text,
    )
    engine_version = f"{ENGINE_VERSION}+ai" if fused.fusion.ai_used else ENGINE_VERSION
    return fused.analysis, fused.fusion, engine_version
