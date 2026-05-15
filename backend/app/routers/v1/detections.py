from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_token_payload, require_roles
from app.core.errors import ErrorResponse
from app.models.membership import Membership
from app.schemas.detection import (
    DetectionEventRead,
    DetectionListResponse,
    DetectionRunResponse,
    ScanPipelineRequest,
    ScanPipelineResponse,
)
from app.services.detection_route_service import (
    build_detection_list_response,
    execute_graph_detection_run,
    execute_scan_pipeline,
    get_detection_event_read,
)
from app.services.http_errors import RouteHttpError

router = APIRouter(prefix="/detections", tags=["detections"])


@router.post(
    "/pipeline",
    response_model=ScanPipelineResponse,
    summary="Run full scan pipeline",
    description="Scan session → AI detection events → risk scores → stored compliance report.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def run_full_scan_pipeline(
    request: Request,
    body: ScanPipelineRequest,
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
) -> ScanPipelineResponse:
    return execute_scan_pipeline(
        db,
        membership=membership,
        body=body,
        request_id=getattr(request.state, "request_id", None),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post(
    "/run",
    response_model=DetectionRunResponse,
    summary="Run Graph-based detection",
    description="Pulls Microsoft Graph audit/sign-in feeds and runs detection rules for the tenant.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def run_detection(
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
    top: Annotated[int, Query(description="Max Graph rows per feed (audits + sign-ins).")] = 120,
) -> DetectionRunResponse:
    return execute_graph_detection_run(db, membership=membership, top=top)


@router.get(
    "",
    response_model=DetectionListResponse,
    summary="List detection events",
    responses={401: {"model": ErrorResponse}},
)
def list_detections(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> DetectionListResponse:
    org_id = uuid.UUID(str(payload["org_id"]))
    return build_detection_list_response(db, organization_id=org_id, limit=limit, offset=offset)


@router.get(
    "/{event_id}",
    response_model=DetectionEventRead,
    summary="Get detection event",
    responses={401: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_detection(
    event_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
) -> DetectionEventRead:
    org_id = uuid.UUID(str(payload["org_id"]))
    try:
        return get_detection_event_read(db, organization_id=org_id, event_id=event_id)
    except RouteHttpError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc
