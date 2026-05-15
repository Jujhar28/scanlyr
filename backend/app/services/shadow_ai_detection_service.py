from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.detections.engine import run_engine_on_events
from app.detections.microsoft_normalize import iter_directory_audit_events, iter_sign_in_events
from app.integrations.microsoft_graph import graph_client
from app.repositories import detection_repository
from app.models.ai_detection_event import AIDetectionEvent
from app.models.enums import MicrosoftGraphConnectionStatus, RiskScoreKind, ScanSessionStatus
from app.models.microsoft_graph import MicrosoftGraphConnection
from app.models.risk_score import RiskScore
from app.models.scan_session import ScanSession
from app.services import microsoft_graph_service as msft_service

logger = logging.getLogger(__name__)

RULE_ENGINE_VERSION = "rule-engine-v1"
DETECTION_SOURCE = "microsoft_graph"


class ShadowAIDetectionError(Exception):
    """Raised when a detection run cannot be executed."""


def _require_graph_connection(db: Session, organization_id: uuid.UUID) -> MicrosoftGraphConnection:
    conn = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if conn is None or conn.status != MicrosoftGraphConnectionStatus.connected.value:
        raise ShadowAIDetectionError("Microsoft 365 must be connected before running detections.")
    return conn


def run_microsoft_graph_detection(
    db: Session,
    *,
    organization_id: uuid.UUID,
    started_by_user_id: uuid.UUID,
    top: int = 120,
) -> dict[str, Any]:
    conn = _require_graph_connection(db, organization_id)
    access = msft_service.ensure_access_token(db, conn)

    try:
        audits = graph_client.fetch_directory_audits(access, top=top)
        sign_ins = graph_client.fetch_sign_ins(access, top=top)
    except Exception as exc:
        raise ShadowAIDetectionError(f"Microsoft Graph fetch failed: {exc}") from exc

    events = iter_directory_audit_events(organization_id, audits) + iter_sign_in_events(
        organization_id,
        sign_ins,
    )

    candidates = run_engine_on_events(events)

    session = ScanSession(
        organization_id=organization_id,
        started_by_user_id=started_by_user_id,
        status=ScanSessionStatus.running.value,
        scan_type="microsoft_graph_shadow_ai",
        summary={"phase": "rules", "events_normalized": len(events)},
    )
    db.add(session)
    db.flush()

    inserted = 0
    skipped = 0
    scores: list[float] = []
    scan_id = session.id

    db.commit()

    try:
        for cand in candidates:
            stmt = (
                pg_insert(AIDetectionEvent)
                .values(
                    organization_id=organization_id,
                    scan_session_id=scan_id,
                    occurred_at=cand.occurred_at,
                    source=DETECTION_SOURCE,
                    tool_name=cand.tool_name,
                    tool_vendor=cand.tool_vendor,
                    channel=cand.channel,
                    severity=cand.severity,
                    confidence=cand.confidence,
                    dedupe_key=cand.dedupe_key,
                    evidence=cand.evidence,
                    external_ref=cand.external_ref,
                )
                .on_conflict_do_nothing(constraint="uq_ai_detection_events_org_dedupe_key")
                .returning(AIDetectionEvent.id)
            )
            new_id = db.execute(stmt).scalar_one_or_none()
            if new_id is None:
                skipped += 1
                continue
            inserted += 1
            scores.append(cand.numeric_score)
            db.add(
                RiskScore(
                    organization_id=organization_id,
                    score_kind=RiskScoreKind.detection.value,
                    ai_detection_event_id=new_id,
                    score=Decimal(str(round(cand.numeric_score, 3))),
                    factors={
                        "numeric_score": cand.numeric_score,
                        "severity": cand.severity,
                        "tool_slug": cand.tool_slug,
                        "rules": [e.rule_id for e in cand.evaluations],
                    },
                    algorithm_version=RULE_ENGINE_VERSION,
                ),
            )

        avg_score = sum(scores) / len(scores) if scores else None
        if scores:
            db.add(
                RiskScore(
                    organization_id=organization_id,
                    score_kind=RiskScoreKind.session.value,
                    scan_session_id=scan_id,
                    score=Decimal(str(round(avg_score or 0.0, 3))),
                    factors={
                        "detection_new_count": inserted,
                        "detection_skipped_duplicates": skipped,
                        "avg_detection_score": avg_score,
                        "candidates_total": len(candidates),
                    },
                    algorithm_version=RULE_ENGINE_VERSION,
                ),
            )

        sess = db.get(ScanSession, scan_id)
        if sess is not None:
            sess.status = ScanSessionStatus.completed.value
            sess.ended_at = datetime.now(tz=UTC)
            sess.summary = {
                "source": DETECTION_SOURCE,
                "events_normalized": len(events),
                "candidates": len(candidates),
                "inserted": inserted,
                "skipped_duplicates": skipped,
                "algorithm": RULE_ENGINE_VERSION,
            }
        db.commit()
    except Exception as exc:
        db.rollback()
        sess = db.get(ScanSession, scan_id)
        if sess is not None:
            sess.status = ScanSessionStatus.failed.value
            sess.ended_at = datetime.now(tz=UTC)
            sess.error_message = str(exc)[:2000]
            db.commit()
        raise ShadowAIDetectionError("Detection pipeline failed") from exc

    logger.info(
        "Shadow AI detection run completed",
        extra={
            "organization_id": str(organization_id),
            "scan_session_id": str(scan_id),
            "inserted": inserted,
            "skipped": skipped,
        },
    )

    return {
        "scan_session_id": scan_id,
        "events_normalized": len(events),
        "candidates": len(candidates),
        "inserted": inserted,
        "skipped_duplicates": skipped,
    }


def list_detection_events(
    db: Session,
    organization_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AIDetectionEvent], int]:
    return detection_repository.list_detection_events_for_organization(
        db,
        organization_id,
        limit=limit,
        offset=offset,
    )


def get_detection_event(
    db: Session,
    organization_id: uuid.UUID,
    event_id: uuid.UUID,
) -> AIDetectionEvent | None:
    return detection_repository.fetch_detection_event(db, organization_id, event_id)
