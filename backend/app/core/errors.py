"""Global FastAPI exception handlers — consistent JSON: ``code``, ``message``, ``details``, ``request_id``."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, ResponseValidationError, WebSocketRequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.exc import SQLAlchemyError
from starlette.authentication import AuthenticationError

from app.integrations.microsoft_graph.errors import (
    MicrosoftGraphApiError,
    MicrosoftGraphIntegrationError,
    MicrosoftGraphNotConfiguredError,
    MicrosoftGraphOAuthError,
)
from app.services.compliance_report_service import ComplianceReportError
from app.core.config import settings
from app.services.shadow_ai_detection_service import ShadowAIDetectionError

logger = logging.getLogger(__name__)


class ErrorResponse(BaseModel):
    """Standard API error envelope (also used by auth middleware)."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


def _request_id_from_request(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def error_payload(
    *,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    rid = _request_id_from_request(request) if request is not None else None
    return ErrorResponse(code=code, message=message, details=details, request_id=rid).model_dump()


def _code_for_http_status(status_code: int) -> str:
    if status_code == status.HTTP_401_UNAUTHORIZED:
        return "authentication_error"
    if status_code == status.HTTP_403_FORBIDDEN:
        return "authorization_error"
    if status_code == status.HTTP_404_NOT_FOUND:
        return "not_found"
    if status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        return "method_not_allowed"
    if status_code == status.HTTP_409_CONFLICT:
        return "conflict"
    if status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
        return "payload_too_large"
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        return "rate_limited"
    return "http_error"


def _validation_error_message(errors: list[Any]) -> str:
    """Surface the first human-readable validation message (e.g. password rules)."""
    for item in errors:
        if not isinstance(item, dict):
            continue
        msg = item.get("msg")
        if isinstance(msg, str) and msg.strip():
            loc = item.get("loc") or ()
            if isinstance(loc, (list, tuple)) and loc:
                field = str(loc[-1]).replace("_", " ")
                if field == "password" and "password" in msg.lower():
                    return msg
                return f"{field}: {msg}"
            return msg
    return "Request validation failed"


def _http_exception_message(detail: Any) -> tuple[str, dict[str, Any] | None]:
    if isinstance(detail, str):
        return detail, None
    if isinstance(detail, list):
        return "Request error", {"detail": detail}
    if isinstance(detail, dict):
        msg = detail.get("message") or detail.get("msg")
        if isinstance(msg, str):
            rest = {k: v for k, v in detail.items() if k not in ("message", "msg")}
            return msg, rest or None
        return "Request error", {"detail": detail}
    return "Request error", None


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        message, extra_details = _http_exception_message(exc.detail)
        code = _code_for_http_status(exc.status_code)
        details = extra_details
        headers: dict[str, str] = dict(exc.headers) if exc.headers else {}
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(code=code, message=message, details=details, request=request),
            headers=headers,
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_payload(
                code="authentication_error",
                message=str(exc) or "Authentication failed",
                request=request,
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = jsonable_encoder(exc.errors())
        message = _validation_error_message(errors)
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_payload(
                code="validation_error",
                message=message,
                details={"errors": errors},
                request=request,
            ),
        )

    @app.exception_handler(WebSocketRequestValidationError)
    async def websocket_validation_handler(
        request: Request,
        exc: WebSocketRequestValidationError,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_payload(
                code="validation_error",
                message="WebSocket validation failed",
                details={"errors": exc.errors()},
                request=request,
            ),
        )

    @app.exception_handler(ResponseValidationError)
    async def response_validation_handler(request: Request, exc: ResponseValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload(
                code="response_validation_error",
                message="Response serialization validation failed",
                details={"errors": exc.errors()} if exc.errors() else None,
                request=request,
            ),
        )

    @app.exception_handler(SQLAlchemyError)
    async def sqlalchemy_handler(request: Request, _exc: SQLAlchemyError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=error_payload(
                code="database_error",
                message="A database error occurred",
                request=request,
            ),
        )

    @app.exception_handler(MicrosoftGraphIntegrationError)
    async def microsoft_graph_integration_handler(
        request: Request,
        exc: MicrosoftGraphIntegrationError,
    ) -> JSONResponse:
        if isinstance(exc, MicrosoftGraphNotConfiguredError):
            code = "microsoft_graph_not_configured"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        elif isinstance(exc, MicrosoftGraphOAuthError):
            code = "microsoft_graph_oauth_error"
            status_code = status.HTTP_400_BAD_REQUEST
        elif isinstance(exc, MicrosoftGraphApiError):
            code = "microsoft_graph_upstream_error"
            status_code = status.HTTP_502_BAD_GATEWAY
        else:
            code = "microsoft_graph_error"
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return JSONResponse(
            status_code=status_code,
            content=error_payload(code=code, message=str(exc), request=request),
        )

    @app.exception_handler(ComplianceReportError)
    async def compliance_report_handler(request: Request, exc: ComplianceReportError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_payload(code="compliance_report_error", message=str(exc), request=request),
        )

    @app.exception_handler(ShadowAIDetectionError)
    async def shadow_ai_detection_handler(request: Request, exc: ShadowAIDetectionError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=error_payload(code="shadow_ai_detection_error", message=str(exc), request=request),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_exception",
            extra={
                "path": request.url.path,
                "method": request.method,
                "request_id": _request_id_from_request(request),
            },
        )
        message = "An internal error occurred"
        details: dict[str, Any] | None = None
        if settings.effective_expose_error_details:
            message = str(exc) or message
            details = {"type": type(exc).__name__}
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload(code="internal_error", message=message, details=details, request=request),
        )
