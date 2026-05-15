from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_token_payload, require_roles
from app.core.errors import ErrorResponse
from app.core.public_api import public_api_route
from app.models.membership import Membership
from app.schemas.integrations_microsoft import (
    MicrosoftGraphConnectResponse,
    MicrosoftGraphStatusResponse,
    MicrosoftGraphSyncResponse,
)
from app.services import microsoft_graph_service as msft_service
from app.services.microsoft_oauth_callback_service import build_microsoft_oauth_callback_redirect

router = APIRouter(prefix="/integrations/microsoft", tags=["integrations-microsoft"])


@router.post(
    "/connect",
    response_model=MicrosoftGraphConnectResponse,
    summary="Start Microsoft OAuth",
    description="Returns the authorization URL for an admin to connect Microsoft 365.",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def start_microsoft_connect(
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
) -> MicrosoftGraphConnectResponse:
    return msft_service.begin_connect_flow(
        db,
        organization_id=membership.organization_id,
        admin_user_id=membership.user_id,
    )


@router.get(
    "/callback",
    summary="Microsoft OAuth callback",
    description="Public browser callback; always responds with HTTP 302 to the frontend integrations page (query params carry success or error).",
    responses={302: {"description": "Redirect to frontend with `msft_connected` or `msft_error` query parameters."}},
)
@public_api_route
def microsoft_oauth_callback(
    db: Annotated[Session, Depends(get_db)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
    error_description: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    return build_microsoft_oauth_callback_redirect(
        db,
        code=code,
        state=state,
        error=error,
        error_description=error_description,
    )


@router.get(
    "/status",
    response_model=MicrosoftGraphStatusResponse,
    summary="Microsoft integration status",
    responses={401: {"model": ErrorResponse}},
)
def microsoft_integration_status(
    db: Annotated[Session, Depends(get_db)],
    payload: Annotated[dict, Depends(get_token_payload)],
) -> MicrosoftGraphStatusResponse:
    org_id = uuid.UUID(str(payload["org_id"]))
    return msft_service.get_status(db, org_id)


@router.delete(
    "/disconnect",
    status_code=204,
    summary="Disconnect Microsoft",
    responses={204: {"description": "Integration disconnected."}, 401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def microsoft_disconnect(
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
) -> None:
    msft_service.disconnect(db, membership.organization_id)


@router.post(
    "/sync",
    response_model=MicrosoftGraphSyncResponse,
    summary="Run Microsoft sync",
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
def microsoft_sync_now(
    db: Annotated[Session, Depends(get_db)],
    membership: Annotated[Membership, Depends(require_roles("admin"))],
) -> MicrosoftGraphSyncResponse:
    return msft_service.run_sync(db, membership.organization_id)
