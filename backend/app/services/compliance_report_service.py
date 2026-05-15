from __future__ import annotations

import logging
import re
import uuid
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.integrations.microsoft_graph import graph_client
from app.models.ai_detection_event import AIDetectionEvent
from app.models.enums import DetectionSeverity, MicrosoftGraphConnectionStatus, ReportStatus, ReportType, RiskScoreKind
from app.models.microsoft_graph import MicrosoftGraphConnection
from app.models.organization import Organization
from app.models.report import Report
from app.repositories import report_repository
from app.reports.pdf_compliance import build_compliance_pdf
from app.services import microsoft_graph_service as msft_service
from app.services.audit_service import append_audit_event

logger = logging.getLogger(__name__)

ADM_ACTIVITY_RE = re.compile(
    r"mdm|intune|compliance policy|managed device|device enrollment|"
    r"app protection|mam\b|wip\b|conditional access|autopilot|endpoint security|"
    r"mobile application management|configuration policy|security baseline|"
    r"enrollment profile|defender for endpoint|windows update for business",
    re.IGNORECASE,
)

REPORT_META_VERSION = 1


class ComplianceReportError(Exception):
    """Raised when a report cannot be generated or stored."""


def _report_root() -> Path:
    root = Path(settings.report_storage_dir).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    return root


def pdf_absolute_path(storage_uri: str) -> Path:
    """Resolve stored relative key to an absolute path under ``report_storage_dir``."""
    parts = storage_uri.replace("\\", "/").split("/")
    if len(parts) != 2 or not parts[0] or not parts[1].endswith(".pdf"):
        raise ComplianceReportError("Invalid report storage key.")
    try:
        uuid.UUID(parts[0])
    except ValueError as exc:
        raise ComplianceReportError("Invalid report storage key.") from exc
    return _report_root() / parts[0] / parts[1]


def _detection_numeric_score(event: AIDetectionEvent) -> float | None:
    for rs in event.risk_scores:
        if rs.score_kind == RiskScoreKind.detection.value:
            return float(rs.score)
    return None


def _evidence_has_pii(evidence: dict[str, Any] | None) -> bool:
    if not evidence:
        return False
    for block in evidence.get("rules") or []:
        if not isinstance(block, dict):
            continue
        if block.get("rule_id") == "pii_keyword_v1" and (block.get("hits") or []):
            return True
    return False


def _pii_summary_line(evidence: dict[str, Any] | None) -> str:
    if not evidence:
        return "PII-related rules triggered"
    terms: list[str] = []
    for block in evidence.get("rules") or []:
        if not isinstance(block, dict) or block.get("rule_id") != "pii_keyword_v1":
            continue
        for h in block.get("hits") or []:
            if isinstance(h, dict):
                d = h.get("details") or {}
                if isinstance(d, dict) and d.get("term"):
                    terms.append(str(d["term"]))
                elif isinstance(d, dict) and d.get("pattern"):
                    terms.append(str(d["pattern"]))
    return ", ".join(terms[:6]) if terms else "PII keyword / pattern heuristics"


def _fetch_adm_audit_summary(db: Session, organization_id: uuid.UUID) -> dict[str, Any]:
    conn = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if conn is None or conn.status != MicrosoftGraphConnectionStatus.connected.value:
        return {
            "source": "unavailable",
            "match_count": 0,
            "sample_activities": [],
            "note": "Microsoft 365 is not connected; ADM summary skipped.",
        }
    try:
        access = msft_service.ensure_access_token(db, conn)
        payload = graph_client.fetch_directory_audits(access, top=100)
    except Exception as exc:
        logger.warning("ADM audit fetch failed", extra={"organization_id": str(organization_id)})
        return {
            "source": "microsoft_graph_directory_audits",
            "match_count": 0,
            "sample_activities": [],
            "note": f"Could not fetch directory audits: {exc}",
        }

    samples: list[str] = []
    count = 0
    for row in payload.get("value") or []:
        if not isinstance(row, dict):
            continue
        blob = " ".join(
            str(x)
            for x in (
                row.get("activityDisplayName"),
                row.get("category"),
                row.get("loggedByService"),
                row.get("operationType"),
            )
            if x
        )
        if ADM_ACTIVITY_RE.search(blob):
            count += 1
            if len(samples) < 12:
                when = str(row.get("activityDateTime") or "")[:19]
                samples.append(f"{when} — {blob.strip()[:160]}")

    return {
        "source": "microsoft_graph_directory_audits",
        "match_count": count,
        "sample_activities": samples,
    }


def _build_recommendations(payload: dict[str, Any]) -> list[str]:
    rec: list[str] = []
    high_n = len(payload.get("high_risk_events") or [])
    pii_n = len(payload.get("possible_pii_exposure") or [])
    tools = payload.get("ai_tool_usage_summary") or {}
    n_tools = len(tools.get("by_tool") or []) if isinstance(tools, dict) else 0
    adm = payload.get("adm_activity_summary") or {}

    if high_n:
        rec.append(
            "Prioritize review of high and critical severity AI detections with affected users and "
            "application owners.",
        )
    if pii_n:
        rec.append(
            "Investigate possible PII exposure near generative AI usage: tighten DLP, "
            "sensitivity labels, and user training on paste/upload behavior.",
        )
    if n_tools >= 4:
        rec.append(
            "Multiple AI tools detected: publish an approved-AI list, block high-risk domains at the "
            "proxy or SWG, and consider enterprise licenses for sanctioned tools.",
        )
    elif n_tools == 0:
        rec.append(
            "No AI tool hits in this window: extend the reporting period or verify Microsoft Graph "
            "ingestion and detection rules.",
        )

    adm_count = int(adm.get("match_count") or 0) if isinstance(adm, dict) else 0
    if adm_count == 0:
        rec.append(
            "Few or no ADM-patterned audit events in the sampled window: confirm Intune / Entra audit "
            "categories are retained and that directory audit permissions are granted.",
        )
    else:
        rec.append(
            "Review Intune, Conditional Access, and app protection policy changes alongside AI "
            "adoption to ensure managed-device requirements still align with risk appetite.",
        )

    rec.append(
        "Schedule recurring governance reviews and export this report for your compliance archive.",
    )
    return rec


def build_report_sections(
    db: Session,
    organization_id: uuid.UUID,
    *,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, Any]:
    org = db.get(Organization, organization_id)
    org_name = org.name if org else str(organization_id)

    q = (
        select(AIDetectionEvent)
        .where(
            AIDetectionEvent.organization_id == organization_id,
            AIDetectionEvent.occurred_at >= period_start,
            AIDetectionEvent.occurred_at <= period_end,
        )
        .options(selectinload(AIDetectionEvent.risk_scores))
        .order_by(AIDetectionEvent.occurred_at.desc())
        .limit(2500)
    )
    events = list(db.scalars(q).all())

    by_tool: Counter[str] = Counter()
    by_vendor: Counter[str] = Counter()
    by_severity: Counter[str] = Counter()
    user_hits: Counter[str] = Counter()
    scores: list[float] = []

    for ev in events:
        label = ev.tool_name or "Unknown"
        by_tool[label] += 1
        if ev.tool_vendor:
            by_vendor[ev.tool_vendor] += 1
        by_severity[ev.severity] += 1
        sc = _detection_numeric_score(ev)
        if sc is not None:
            scores.append(sc)
        ah = None
        if isinstance(ev.evidence, dict):
            ah = ev.evidence.get("actor_hint")
        if isinstance(ah, str) and ah.strip():
            user_hits[ah.strip()] += 1

    usage_rows = [
        {"tool": name, "vendor": "", "count": c}
        for name, c in by_tool.most_common(20)
    ]

    high_risk: list[dict[str, Any]] = []
    for ev in events:
        if ev.severity in (DetectionSeverity.high.value, DetectionSeverity.critical.value):
            high_risk.append(
                {
                    "id": str(ev.id),
                    "occurred_at": ev.occurred_at.isoformat(),
                    "tool_name": ev.tool_name,
                    "severity": ev.severity,
                    "risk_score": _detection_numeric_score(ev),
                },
            )
        if len(high_risk) >= 25:
            break

    pii_rows: list[dict[str, Any]] = []
    for ev in events:
        if _evidence_has_pii(ev.evidence if isinstance(ev.evidence, dict) else None):
            pii_rows.append(
                {
                    "id": str(ev.id),
                    "occurred_at": ev.occurred_at.isoformat(),
                    "tool_name": ev.tool_name,
                    "summary": _pii_summary_line(ev.evidence if isinstance(ev.evidence, dict) else None),
                },
            )
        if len(pii_rows) >= 25:
            break

    top_users = [{"user": u, "count": n} for u, n in user_hits.most_common(15)]

    avg_score = round(sum(scores) / len(scores), 3) if scores else None

    adm = _fetch_adm_audit_summary(db, organization_id)

    sections = {
        "organization_name": org_name,
        "period": {
            "start": period_start.isoformat(),
            "end": period_end.isoformat(),
        },
        "ai_tool_usage_summary": {
            "total_events": len(events),
            "by_tool": usage_rows,
            "by_vendor": [{"vendor": v, "count": c} for v, c in by_vendor.most_common(10)],
        },
        "high_risk_events": high_risk,
        "possible_pii_exposure": pii_rows,
        "top_users": top_users,
        "risk_score": {
            "avg_detection_score": avg_score,
            "event_count": len(events),
            "by_severity": dict(by_severity),
        },
        "adm_activity_summary": adm,
    }
    sections["recommendations"] = _build_recommendations(sections)
    return sections


def generate_compliance_pdf_report(
    db: Session,
    *,
    organization_id: uuid.UUID,
    created_by_user_id: uuid.UUID,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> Report:
    """Create a report row, build sections + PDF on disk, attach metadata."""
    end = period_end or datetime.now(tz=UTC)
    start = period_start or (end - timedelta(days=30))
    if start >= end:
        raise ComplianceReportError("period_start must be before period_end.")

    org = db.get(Organization, organization_id)
    org_name = org.name if org else "Organization"

    report = Report(
        organization_id=organization_id,
        created_by_user_id=created_by_user_id,
        title=f"AI governance compliance — {org_name}",
        report_type=ReportType.compliance.value,
        status=ReportStatus.rendering.value,
        period_start=start,
        period_end=end,
    )
    db.add(report)
    db.flush()

    try:
        sections = build_report_sections(db, organization_id, period_start=start, period_end=end)
        pdf_sections = {
            "organization_name": sections.get("organization_name"),
            "period": sections.get("period"),
            "ai_tool_usage_summary": sections.get("ai_tool_usage_summary"),
            "high_risk_events": sections.get("high_risk_events"),
            "possible_pii_exposure": sections.get("possible_pii_exposure"),
            "top_users": sections.get("top_users"),
            "risk_score": sections.get("risk_score"),
            "recommendations": sections.get("recommendations"),
            "adm_activity_summary": sections.get("adm_activity_summary"),
        }
        title = report.title
        pdf_bytes = build_compliance_pdf(title, pdf_sections)

        rel_key = f"{organization_id}/{report.id}.pdf"
        out_dir = _report_root() / str(organization_id)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{report.id}.pdf"
        out_path.write_bytes(pdf_bytes)

        report.status = ReportStatus.ready.value
        report.storage_uri = rel_key
        report.meta = {
            "version": REPORT_META_VERSION,
            "sections": sections,
            "pdf_bytes": len(pdf_bytes),
            "algorithm": "compliance-report-v1",
        }
        append_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=created_by_user_id,
            action="report.generated",
            resource_type="report",
            resource_id=str(report.id),
            payload={"title": report.title, "status": report.status},
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        db.refresh(report)
        return report
    except Exception as exc:
        logger.exception("Report generation failed", extra={"report_id": str(report.id)})
        report.status = ReportStatus.failed.value
        report.error_message = str(exc)[:2000]
        append_audit_event(
            db,
            organization_id=organization_id,
            actor_user_id=created_by_user_id,
            action="report.failed",
            resource_type="report",
            resource_id=str(report.id),
            payload={"error": str(exc)[:500]},
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.commit()
        db.refresh(report)
        raise ComplianceReportError("Report generation failed") from exc


def list_reports(
    db: Session,
    organization_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Report], int]:
    return report_repository.list_reports_for_organization(
        db,
        organization_id,
        limit=limit,
        offset=offset,
    )


def get_report(db: Session, organization_id: uuid.UUID, report_id: uuid.UUID) -> Report | None:
    return report_repository.fetch_report(db, organization_id, report_id)
