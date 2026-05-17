"""Security text scan for POST /scan — modular detectors + persistence + audit."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Literal

from sqlalchemy.orm import Session

from app.models.ai_detection_event import AIDetectionEvent
from app.models.enums import DetectionSeverity
from app.repositories.scan_history_repository import create_security_text_scan
from app.scan_security.context import ContentKind
from app.scan_security.schemas.findings import SecurityFinding
from app.scan_security.schemas.results import ScanAnalysisResult
from app.core.config import get_settings
from app.scan_security.services.engine import ENGINE_VERSION
from app.scan_security.analysis.fixtures import scan_indicates_synthetic_fixture
from app.services.scan_ai_adjudication_service import try_ai_hybrid_reverify_rules
from app.services.scan_ai_layer_service import try_ai_scan_analysis
from app.services.scan_explainability_service import (
    build_scan_explainability,
    summary_text,
)
from app.services.scan_safety_service import (
    build_safe_default_scan_result,
    run_hybrid_scan_analysis,
    try_rules_scan,
)
from app.services.security_audit_service import record_security_audit
from app.schemas.scan import (
    API_SCHEMA_VERSION,
    CategoryScoreRead,
    ExplainableRiskScoreRead,
    ScanAnalysisDetails,
    ScanExplainability,
    ScanFinding,
    ScanFusionDetails,
    ScanMetadata,
    ScanResponse,
)

logger = logging.getLogger(__name__)

_INPUT_PREVIEW_MAX = 500


def _severity_for_level(level: Literal["low", "medium", "high", "critical"]) -> str:
    if level in ("high", "critical"):
        return DetectionSeverity.high.value
    if level == "medium":
        return DetectionSeverity.medium.value
    return DetectionSeverity.low.value


def _finding_to_schema(f: SecurityFinding) -> ScanFinding:
    return ScanFinding(
        type=f.type,
        detector=f.detector_id,
        category=f.category,
        risk_category=f.risk_category,
        severity=f.severity,
        title=f.title,
        description=f.description,
        confidence=f.confidence,
        remediation=f.remediation,
        evidence=f.evidence or None,
    )


def _to_response(
    result: ScanAnalysisResult,
    *,
    scan_id: uuid.UUID,
    scanned_at: datetime,
    content_type: ContentKind,
    request_id: str | None = None,
    fusion: ScanFusionDetails | None = None,
    engine_version: str | None = None,
    explainability: ScanExplainability | None = None,
) -> ScanResponse:
    breakdown = ExplainableRiskScoreRead(
        overall=result.score_breakdown.overall,
        categories=[
            CategoryScoreRead(
                risk_category=c.risk_category,
                score=c.score,
                finding_count=c.finding_count,
                explanation=c.explanation,
            )
            for c in result.score_breakdown.categories
        ],
        top_drivers=list(result.score_breakdown.top_drivers),
    )
    short_explanation = (
        summary_text(explainability) if explainability else result.explanation
    )
    return ScanResponse(
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        confidence=result.confidence,
        explanation=short_explanation,
        findings=[_finding_to_schema(f) for f in result.findings],
        remediation=list(result.remediation_steps),
        metadata=ScanMetadata(
            scan_id=scan_id,
            timestamp=scanned_at,
            request_id=request_id,
            content_type=content_type,
            engine_version=engine_version or ENGINE_VERSION,
            schema_version=API_SCHEMA_VERSION,
        ),
        analysis=ScanAnalysisDetails(
            risk_categories=result.risk_categories,
            score_breakdown=breakdown,
            fusion=fusion,
            explainability=explainability,
        ),
    )


def _build_result_payload(response: ScanResponse) -> dict[str, object]:
    return response.model_dump(mode="json")


def run_rule_based_text_scan(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    input_text: str,
    content_type: ContentKind = "auto",
    request_id: str | None = None,
) -> ScanResponse:
    settings = get_settings()
    rules_result = try_rules_scan(input_text, content_type=content_type)
    ai_outcome = None
    if rules_result is not None and rules_result.findings:
        rules_result, ai_outcome = try_ai_hybrid_reverify_rules(
            input_text,
            rules_result,
            content_type=content_type,
            settings=settings,
        )
    if ai_outcome is None and rules_result is not None:
        synthetic_fixture = scan_indicates_synthetic_fixture(
            input_text,
            findings=list(rules_result.findings),
        )
        if synthetic_fixture and rules_result.risk_score <= 40:
            logger.info(
                "scan_ai_layer_skipped",
                extra={"reason": "synthetic_fixture_rules_sufficient"},
            )
        else:
            ai_outcome = try_ai_scan_analysis(input_text, settings=settings)
    elif ai_outcome is None:
        ai_outcome = try_ai_scan_analysis(input_text, settings=settings)
    result, fusion_meta, engine_version = run_hybrid_scan_analysis(
        input_text,
        content_type=content_type,
        settings=settings,
        ai_outcome=ai_outcome,
        rules_result=rules_result,
    )
    rules_for_explain = (
        rules_result
        if rules_result is not None
        else build_safe_default_scan_result(content_type)
    )
    explainability = build_scan_explainability(
        result=result,
        rules_result=rules_for_explain,
        fusion=fusion_meta,
        ai_outcome=ai_outcome,
        engine_version=engine_version,
        input_text=input_text,
    )

    occurred_at = datetime.now(UTC)
    scan_uuid = uuid.uuid4()

    response = _to_response(
        result,
        scan_id=scan_uuid,
        scanned_at=occurred_at,
        content_type=content_type,
        request_id=request_id,
        fusion=fusion_meta,
        engine_version=engine_version,
        explainability=explainability,
    )
    payload = _build_result_payload(response)

    evidence: dict[str, object] = {
        **payload,
        "input_text": input_text,
        "content_type": content_type,
        "request_id": request_id,
        "schema_version": API_SCHEMA_VERSION,
    }

    detection_row = AIDetectionEvent(
        organization_id=organization_id,
        user_id=user_id,
        scan_session_id=None,
        occurred_at=occurred_at,
        source="text_rule_scan",
        tool_name="security_scan_engine",
        tool_vendor=None,
        channel="api",
        severity=_severity_for_level(result.risk_level),
        confidence=result.confidence,
        dedupe_key=f"text-scan:{scan_uuid}",
        evidence=evidence,
        external_ref=None,
        notes=None,
    )
    db.add(detection_row)
    db.flush()

    preview = input_text[:_INPUT_PREVIEW_MAX]
    if len(input_text) > _INPUT_PREVIEW_MAX:
        preview += "…"

    history_row = create_security_text_scan(
        db,
        scan_id=scan_uuid,
        organization_id=organization_id,
        user_id=user_id,
        detection_event_id=detection_row.id,
        scanned_at=occurred_at,
        content_type=content_type,
        risk_score=result.risk_score,
        risk_level=result.risk_level,
        confidence=result.confidence,
        finding_count=len(result.findings),
        input_text=input_text,
        input_preview=preview,
        result_payload=payload,
        engine_version=engine_version,
    )
    record_security_audit(
        db,
        action="scan.text_completed",
        organization_id=organization_id,
        actor_user_id=user_id,
        resource_type="security_text_scan",
        resource_id=str(history_row.id),
        payload={
            "risk_level": result.risk_level,
            "risk_score": result.risk_score,
            "finding_count": len(result.findings),
            "content_type": content_type,
            "engine": engine_version,
            "request_id": request_id,
            "rules_score": fusion_meta.rules_score,
            "ai_score": fusion_meta.ai_score,
            "ai_used": fusion_meta.ai_used,
            "ai_provider": fusion_meta.ai_provider,
        },
    )
    db.commit()

    final = _to_response(
        result,
        scan_id=scan_uuid,
        scanned_at=occurred_at,
        content_type=content_type,
        request_id=request_id,
        fusion=fusion_meta,
        engine_version=engine_version,
        explainability=explainability,
    )

    logger.info(
        "security_scan_persisted",
        extra={
            "organization_id": str(organization_id),
            "user_id": str(user_id),
            "scan_id": str(history_row.id),
            "request_id": request_id,
            "event_id": str(detection_row.id),
            "content_type": content_type,
            "engine": engine_version,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "finding_count": len(result.findings),
            "risk_categories": result.risk_categories,
            "rules_score": fusion_meta.rules_score,
            "ai_score": fusion_meta.ai_score,
            "combined_score": fusion_meta.combined_score,
            "rules_contribution": round(
                fusion_meta.rules_weight * fusion_meta.rules_score,
                2,
            ),
            "ai_contribution": round(
                fusion_meta.ai_weight * (fusion_meta.ai_score or 0),
                2,
            )
            if fusion_meta.ai_used
            else 0.0,
            "ai_used": fusion_meta.ai_used,
            "ai_provider": fusion_meta.ai_provider,
        },
    )

    return final
