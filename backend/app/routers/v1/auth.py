from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, get_token_payload
from app.core.errors import ErrorResponse
from app.core.public_api import public_api_route
from app.models.user import User
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    LogoutRequest,
    MeResponse,
    RefreshRequest,
    RegisterRequest,
)
from app.services.auth_service import (
    build_me_response,
    login,
    logout,
    refresh_session,
    register,
)
from app.services.request_context import client_ip_from_request, user_agent_from_request

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthSessionResponse,
    summary="Register organization and admin user",
    description="Creates a tenant, admin membership, and returns access + refresh tokens.",
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
@public_api_route
def register_route(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    return register(
        db,
        payload,
        user_agent=user_agent_from_request(request),
        ip_address=client_ip_from_request(request),
    )


@router.post(
    "/login",
    response_model=AuthSessionResponse,
    summary="Login",
    description="Issues access + refresh tokens for an existing user.",
    responses={401: {"model": ErrorResponse}},
)
@public_api_route
def login_route(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    return login(
        db,
        payload,
        user_agent=user_agent_from_request(request),
        ip_address=client_ip_from_request(request),
    )


@router.post(
    "/refresh",
    response_model=AuthSessionResponse,
    summary="Refresh session",
    description="Rotates refresh token and returns a new access token.",
    responses={401: {"model": ErrorResponse}},
)
@public_api_route
def refresh_route(
    payload: RefreshRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> AuthSessionResponse:
    return refresh_session(
        db,
        payload,
        user_agent=user_agent_from_request(request),
        ip_address=client_ip_from_request(request),
    )


@router.post(
    "/logout",
    status_code=204,
    summary="Logout",
    description="Revokes the given refresh token, or all sessions when `revoke_all` is true.",
    responses={204: {"description": "No content — session revoked."}},
)
def logout_route(
    payload: LogoutRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    logout(db, user, payload.refresh_token, payload.revoke_all)
    return Response(status_code=204)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Current user context",
    description="Returns the authenticated user, organization, and token claims.",
    responses={401: {"model": ErrorResponse}},
)
def me_route(
    user: User = Depends(get_current_user),
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> MeResponse:
    return build_me_response(db, user, payload)
