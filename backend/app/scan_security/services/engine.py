from __future__ import annotations

import logging
import time

from app.scan_security.context import ContentKind, ScanContext
from app.scan_security.detectors.base import SecurityDetector
from app.scan_security.detectors.registry import detectors_for_content_type
from app.scan_security.schemas.findings import SecurityFinding
from app.scan_security.schemas.results import ScanAnalysisResult
from app.scan_security.analysis.context import analyze_text_context
from app.scan_security.services.finding_refiner import ScanStrictness, refine_findings
from app.scan_security.services.scoring import aggregate_findings

logger = logging.getLogger(__name__)

ENGINE_VERSION = "scan_security_v5"


def run_security_scan(
    input_text: str,
    *,
    content_type: ContentKind = "auto",
    detectors: tuple[SecurityDetector, ...] | None = None,
    strictness: ScanStrictness = "balanced",
) -> ScanAnalysisResult:
    """Run content-aware detectors and aggregate into explainable risk scoring."""
    started = time.perf_counter()
    ctx = ScanContext(text=input_text, content_kind=content_type)
    active = detectors if detectors is not None else detectors_for_content_type(content_type)

    logger.info(
        "security_scan_started",
        extra={
            "engine": ENGINE_VERSION,
            "content_type": content_type,
            "input_length": len(input_text),
            "detector_count": len(active),
        },
    )

    raw_findings: list[SecurityFinding] = []
    triggered: list[str] = []

    for detector in active:
        if not detector.applies_to(ctx):
            continue
        try:
            hits = detector.detect_with_context(ctx)
        except Exception:
            logger.exception(
                "security_detector_failed",
                extra={"detector_id": detector.detector_id},
            )
            continue
        if hits:
            triggered.append(detector.detector_id)
        raw_findings.extend(hits)

    context_profile = analyze_text_context(input_text)
    findings = refine_findings(raw_findings, input_text, strictness=strictness)

    result = aggregate_findings(
        findings,
        content_kind=content_type,
        context_profile=context_profile,
    )
    duration_ms = round((time.perf_counter() - started) * 1000, 2)

    logger.info(
        "security_scan_completed",
        extra={
            "engine": ENGINE_VERSION,
            "content_type": content_type,
            "input_length": len(input_text),
            "duration_ms": duration_ms,
            "raw_finding_count": len(raw_findings),
            "finding_count": len(result.findings),
            "strictness": strictness,
            "benign_score": context_profile.benign_score,
            "detectors_triggered": triggered,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "confidence": result.confidence,
            "risk_categories": result.risk_categories,
            "top_drivers": list(result.score_breakdown.top_drivers),
        },
    )
    return result
