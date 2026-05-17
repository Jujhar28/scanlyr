"""Structured access logging with client IP and request correlation."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.services.request_context import client_ip_from_request

logger = logging.getLogger("scanlyr.access")


class AccessLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.url.path in ("/health", "/ready"):
            return await call_next(request)

        start = time.perf_counter()
        client_ip = client_ip_from_request(request)
        request.state.client_ip = client_ip

        response: Response
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.exception(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": client_ip,
                    "duration_ms": round(duration_ms, 2),
                    "request_id": getattr(request.state, "request_id", None),
                },
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        log_record = logger.makeRecord(
            logger.name,
            logging.INFO,
            __file__,
            0,
            f"{request.method} {request.url.path} {response.status_code}",
            (),
            None,
        )
        log_record.method = request.method
        log_record.path = request.url.path
        log_record.status_code = response.status_code
        log_record.client_ip = client_ip
        log_record.duration_ms = round(duration_ms, 2)
        log_record.request_id = getattr(request.state, "request_id", None)
        logger.handle(log_record)
        return response
