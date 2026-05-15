"""End-to-end scan pipeline: scan session → AI events → risk scores → compliance report."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy.orm import Session

from app.models.ai_detection_event import AIDetectionEvent
from app.models.enums import DetectionSeverity, ReportStatus, RiskScoreKind, ScanSessionStatus
from app.models.risk_score import RiskScore
from app.models.scan_session import ScanSession
from app.services.compliance_report_service import ComplianceReportError, generate_compliance_pdf_report
from app.services.shadow_ai_detection_service import ShadowAIDetectionError, run_microsoft_graph_detection

PipelineMode = Literal["synthetic", "microsoft_graph"]

SEVERITY_SCORE: dict[str, float] = {
    DetectionSeverity.critical.value: 96.0,
    DetectionSeverity.high.value: 78.0,
    DetectionSeverity.medium.value: 55.0,
    DetectionSeverity.low.value: 35.0,
    DetectionSeverity.info.value: 18.0,
}

SYNTHETIC_TOOLS: tuple[tuple[str, str, str], ...] = (
    ("ChatGPT", "OpenAI", DetectionSeverity.high.value),
    ("Microsoft Copilot", "Microsoft", DetectionSeverity.medium.value),
    ("Claude", "Anthropic", DetectionSeverity.medium.value),
    ("Gemini", "Google", DetectionSeverity.low.value),
)


@dataclass(frozen=True)
class ScanPipelineOutcome:
    mode: PipelineMode
    scan_session_id: uuid.UUID
    detection_events_inserted: int
    risk_scores_created: int
    report_id: uuid.UUID
    report_status: str
    report_title: str


def _severity_numeric(severity: str) -> Decimal:
    base = SEVERITY_SCORE.get(severity, SEVERITY_SCORE[DetectionSeverity.medium.value])
    return Decimal(str(round(base, 3)))


def run_synthetic_scan_pipeline(
    db: Session,
    *,
    organization_id: uuid.UUID,
    started_by_user_id: uuid.UUID,
    event_count: int = 3,
) -> ScanPipelineOutcome:
    """Create a scan session, seed detection events + risk scores (no Microsoft Graph)."""
    event_count = min(max(event_count, 1), 20)
    now = datetime.now(tz=UTC)

    session_row = ScanSession(
        organization_id=organization_id,
        started_by_user_id=started_by_user_id,
        status=ScanSessionStatus.running.value,
        scan_type="internal_shadow_ai",
        summary={"phase": "synthetic", "event_count": event_count},
    )
    db.add(session_row)
    db.flush()
    scan_id = session_row.id

    detection_scores: list[float] = []
    for i in range(event_count):
        tool_name, vendor, severity = SYNTHETIC_TOOLS[i % len(SYNTHETIC_TOOLS)]
        dedupe_key = f"internal:{scan_id}:{i}:{uuid.uuid4().hex[:8]}"
        ev = AIDetectionEvent(
            organization_id=organization_id,
            scan_session_id=scan_id,
            occurred_at=now,
            source="internal_shadow_ai",
            tool_name=tool_name,
            tool_vendor=vendor,
            channel="synthetic",
            severity=severity,
            confidence=0.82,
            dedupe_key=dedupe_key,
            evidence={
                "pipeline": "synthetic",
                "scan_session_id": str(scan_id),
                "index": i,
            },
        )
        db.add(ev)
        db.flush()

        score_val = _severity_numeric(severity)
        detection_scores.append(float(score_val))
        db.add(
            RiskScore(
                organization_id=organization_id,
                score_kind=RiskScoreKind.detection.value,
                ai_detection_event_id=ev.id,
                scan_session_id=None,
                score=score_val,
                factors={
                    "severity": severity,
                    "tool_name": tool_name,
                    "source": "internal_shadow_ai",
                },
                algorithm_version="pipeline-v1",
            ),
        )

    avg_score = round(sum(detection_scores) / len(detection_scores), 3) if detection_scores else 0.0
    max_score = max(detection_scores) if detection_scores else 0.0

    db.add(
        RiskScore(
            organization_id=organization_id,
            score_kind=RiskScoreKind.session.value,
            ai_detection_event_id=None,
            scan_session_id=scan_id,
            score=Decimal(str(round(avg_score, 3))),
            factors={
                "avg_detection_score": avg_score,
                "max_detection_score": max_score,
                "event_count": event_count,
                "scan_session_id": str(scan_id),
            },
            algorithm_version="pipeline-v1",
        ),
    )

    db.add(
        RiskScore(
            organization_id=organization_id,
            score_kind=RiskScoreKind.organization.value,
            ai_detection_event_id=None,
            scan_session_id=None,
            score=Decimal(str(round(max_score, 3))),
            factors={
                "rollup": "max_detection_in_scan",
                "scan_session_id": str(scan_id),
                "event_count": event_count,
            },
            algorithm_version="pipeline-v1",
        ),
    )

    session_row.status = ScanSessionStatus.completed.value
    session_row.ended_at = now
    session_row.summary = {
        "source": "internal_shadow_ai",
        "events": event_count,
        "avg_detection_score": avg_score,
        "max_detection_score": max_score,
        "algorithm": "pipeline-v1",
    }
    db.commit()
    db.refresh(session_row)

    risk_scores_created = event_count + 2

    period_start = session_row.started_at - timedelta(seconds=2)
    if period_start.tzinfo is None:
        period_start = period_start.replace(tzinfo=UTC)
    period_end = datetime.now(tz=UTC)

    report = generate_compliance_pdf_report(
        db,
        organization_id=organization_id,
        created_by_user_id=started_by_user_id,
        period_start=period_start,
        period_end=period_end,
    )

    return ScanPipelineOutcome(
        mode="synthetic",
        scan_session_id=scan_id,
        detection_events_inserted=event_count,
        risk_scores_created=risk_scores_created,
        report_id=report.id,
        report_status=report.status,
        report_title=report.title,
    )


def run_microsoft_graph_scan_pipeline(
    db: Session,
    *,
    organization_id: uuid.UUID,
    started_by_user_id: uuid.UUID,
    top: int = 120,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> ScanPipelineOutcome:
    """Graph-backed detection run, then compliance PDF for the scan window."""
    try:
        result = run_microsoft_graph_detection(
            db,
            organization_id=organization_id,
            started_by_user_id=started_by_user_id,
            top=top,
        )
    except ShadowAIDetectionError:
        raise

    scan_id = uuid.UUID(str(result["scan_session_id"]))
    session_row = db.get(ScanSession, scan_id)
    if session_row is None:
        raise ComplianceReportError("Scan session missing after detection run.")

    period_start = session_row.started_at - timedelta(seconds=2)
    if period_start.tzinfo is None:
        period_start = period_start.replace(tzinfo=UTC)
    period_end = datetime.now(tz=UTC)

    inserted = int(result.get("inserted") or 0)
    risk_scores_created = inserted + (1 if inserted > 0 else 0)

    report = generate_compliance_pdf_report(
        db,
        organization_id=organization_id,
        created_by_user_id=started_by_user_id,
        period_start=period_start,
        period_end=period_end,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    return ScanPipelineOutcome(
        mode="microsoft_graph",
        scan_session_id=scan_id,
        detection_events_inserted=inserted,
        risk_scores_created=risk_scores_created,
        report_id=report.id,
        report_status=report.status,
        report_title=report.title,
    )


def run_scan_pipeline(
    db: Session,
    *,
    organization_id: uuid.UUID,
    started_by_user_id: uuid.UUID,
    mode: PipelineMode,
    synthetic_event_count: int = 3,
    graph_top: int = 120,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> dict[str, Any]:
    if mode == "synthetic":
        out = run_synthetic_scan_pipeline(
            db,
            organization_id=organization_id,
            started_by_user_id=started_by_user_id,
            event_count=synthetic_event_count,
        )
    else:
        out = run_microsoft_graph_scan_pipeline(
            db,
            organization_id=organization_id,
            started_by_user_id=started_by_user_id,
            top=graph_top,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    return {
        "mode": out.mode,
        "scan_session_id": out.scan_session_id,
        "detection_events_inserted": out.detection_events_inserted,
        "risk_scores_created": out.risk_scores_created,
        "report": {
            "id": out.report_id,
            "status": out.report_status,
            "title": out.report_title,
            "downloadable": out.report_status == ReportStatus.ready.value,
        },
    }
