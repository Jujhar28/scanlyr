"""HTTP-facing orchestration for detection routes."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.membership import Membership
from app.schemas.detection import (
    DetectionEventRead,
    DetectionListResponse,
    DetectionRunResponse,
    ScanPipelineRequest,
    ScanPipelineResponse,
)
from app.services.http_errors import RouteHttpError
from app.services.scan_pipeline_service import run_scan_pipeline
from app.services.shadow_ai_detection_service import (
    get_detection_event,
    list_detection_events,
    run_microsoft_graph_detection,
)


def clamp_microsoft_graph_top(top: int) -> int:
    return min(max(top, 20), 300)


def build_detection_list_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int,
    offset: int,
) -> DetectionListResponse:
    rows, total = list_detection_events(db, organization_id, limit=limit, offset=offset)
    return DetectionListResponse(
        items=[DetectionEventRead.from_model(r) for r in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_detection_event_read(
    db: Session,
    *,
    organization_id: uuid.UUID,
    event_id: uuid.UUID,
) -> DetectionEventRead:
    row = get_detection_event(db, organization_id, event_id)
    if row is None:
        raise RouteHttpError(404, "Detection not found")
    return DetectionEventRead.from_model(row)


def execute_graph_detection_run(
    db: Session,
    *,
    membership: Membership,
    top: int,
) -> DetectionRunResponse:
    top = clamp_microsoft_graph_top(top)
    result = run_microsoft_graph_detection(
        db,
        organization_id=membership.organization_id,
        started_by_user_id=membership.user_id,
        top=top,
    )
    return DetectionRunResponse.model_validate(result)


def execute_scan_pipeline(
    db: Session,
    *,
    membership: Membership,
    body: ScanPipelineRequest,
    request_id: str | None,
    ip_address: str | None,
    user_agent: str | None,
) -> ScanPipelineResponse:
    result = run_scan_pipeline(
        db,
        organization_id=membership.organization_id,
        started_by_user_id=membership.user_id,
        mode=body.mode,
        synthetic_event_count=body.synthetic_event_count,
        graph_top=body.graph_top,
        request_id=request_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return ScanPipelineResponse.model_validate(result)
