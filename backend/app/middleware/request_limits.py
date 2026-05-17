"""Reject oversized request bodies before handlers run."""

from __future__ import annotations

from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.errors import error_payload


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length is not None:
                try:
                    size = int(content_length)
                except ValueError:
                    return JSONResponse(
                        status_code=400,
                        content=error_payload(
                            code="invalid_request",
                            message="Invalid Content-Length header",
                            request=request,
                        ),
                    )
                if size > get_settings().max_request_body_bytes:
                    return JSONResponse(
                        status_code=413,
                        content=error_payload(
                            code="payload_too_large",
                            message=f"Request body exceeds {get_settings().max_request_body_bytes} bytes",
                            request=request,
                        ),
                    )
        return await call_next(request)
