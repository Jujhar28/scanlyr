from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.auth_context import AuthContext, get_auth_context, require_authenticated
from app.core.deps import get_current_user, get_db
from app.core.errors import ErrorResponse
from app.models.user import User
from app.schemas.scan import ScanRequest, ScanResponse
from app.schemas.scan_history import ScanAnalyticsResponse, ScanHistoryDetail, ScanHistoryListResponse
from app.services.http_errors import RouteHttpError
from app.services.scan_analytics_service import build_organization_scan_analytics
from app.services.scan_history_service import build_scan_history_list, get_scan_history_detail
from app.services.scan_text_service import run_rule_based_text_scan

router = APIRouter(
    prefix="/scan",
    tags=["scan"],
    dependencies=[Depends(require_authenticated)],
)
logger = logging.getLogger(__name__)


@router.get(
    "/history",
    response_model=ScanHistoryListResponse,
    summary="List scan history",
    description="Paginated scan history for the authenticated organization with optional filters.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def list_scan_history(
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    risk_level: Annotated[str | None, Query(description="low, medium, high, or critical")] = None,
    content_type: Annotated[str | None, Query(description="prompt, output, or auto")] = None,
    user_id: Annotated[uuid.UUID | None, Query()] = None,
    scanned_from: Annotated[datetime | None, Query()] = None,
    scanned_to: Annotated[datetime | None, Query()] = None,
    min_risk_score: Annotated[int | None, Query(ge=0, le=100)] = None,
    max_risk_score: Annotated[int | None, Query(ge=0, le=100)] = None,
) -> ScanHistoryListResponse:
    return build_scan_history_list(
        db,
        organization_id=auth.org_id,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        content_type=content_type,
        user_id=user_id,
        scanned_from=scanned_from,
        scanned_to=scanned_to,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
    )


@router.get(
    "/history/{scan_id}",
    response_model=ScanHistoryDetail,
    summary="Get scan by id",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_scan_history_item(
    scan_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> ScanHistoryDetail:
    try:
        return get_scan_history_detail(db, organization_id=auth.org_id, scan_id=scan_id)
    except RouteHttpError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get(
    "/analytics",
    response_model=ScanAnalyticsResponse,
    summary="Organization scan analytics",
    description=(
        "Aggregates total scans, average risk score, top threat categories, "
        "risk level distribution, and daily trends for the tenant."
    ),
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def get_scan_analytics(
    db: Annotated[Session, Depends(get_db)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
    scanned_from: Annotated[datetime | None, Query()] = None,
    scanned_to: Annotated[datetime | None, Query()] = None,
    trend_days: Annotated[int, Query(ge=7, le=90)] = 30,
) -> ScanAnalyticsResponse:
    return build_organization_scan_analytics(
        db,
        organization_id=auth.org_id,
        scanned_from=scanned_from,
        scanned_to=scanned_to,
        trend_days=trend_days,
    )


@router.post(
    "",
    response_model=ScanResponse,
    summary="AI security & LLM protection scan",
    description=(
        "Hybrid analysis: rule-engine detectors plus optional AI provider layer "
        "(40% rules / 60% AI when API keys are configured). Persists to `security_text_scans` "
        "and `ai_detection_events`. Set `content_type` to `prompt` or `output` for targeted scans."
    ),
    responses={
        401: {"model": ErrorResponse, "description": "`authentication_error`"},
        403: {"model": ErrorResponse, "description": "`authorization_error`"},
        422: {"model": ErrorResponse, "description": "`validation_error`"},
        500: {"model": ErrorResponse, "description": "`internal_error`"},
    },
)
def scan_text(
    body: ScanRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    auth: Annotated[AuthContext, Depends(get_auth_context)],
) -> ScanResponse:
    if auth.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token subject does not match authenticated user",
        )
    logger.info(
        "scan_api_request",
        extra={
            "organization_id": str(auth.org_id),
            "user_id": str(current_user.id),
            "role": auth.role,
            "content_type": body.content_type,
            "input_length": len(body.input_text),
        },
    )
    request_id = getattr(request.state, "request_id", None)
    return run_rule_based_text_scan(
        db,
        organization_id=auth.org_id,
        user_id=current_user.id,
        input_text=body.input_text,
        content_type=body.content_type,
        request_id=request_id,
    )
