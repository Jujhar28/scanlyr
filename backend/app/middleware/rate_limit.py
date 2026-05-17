"""In-memory sliding-window rate limiting per client IP."""

from __future__ import annotations

import time
from collections import defaultdict
from collections.abc import Callable
from threading import Lock

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.errors import error_payload
from app.services.request_context import client_ip_from_request

_WINDOW_SECONDS = 60.0


class _RateLimitStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str, *, limit: int) -> tuple[bool, int]:
        now = time.monotonic()
        cutoff = now - _WINDOW_SECONDS
        with self._lock:
            bucket = self._hits[key]
            self._hits[key] = [t for t in bucket if t > cutoff]
            if len(self._hits[key]) >= limit:
                retry_after = int(max(1, _WINDOW_SECONDS - (now - self._hits[key][0])))
                return False, retry_after
            self._hits[key].append(now)
            return True, 0


_store = _RateLimitStore()


def _limit_for_path(path: str, method: str) -> int | None:
    cfg = get_settings()
    if not cfg.rate_limit_enabled:
        return None
    if not path.startswith("/api/v1"):
        return None
    if path.startswith("/api/v1/auth/"):
        return cfg.rate_limit_auth_per_minute
    if path == "/api/v1/scan" and method == "POST":
        return cfg.rate_limit_scan_per_minute
    return cfg.rate_limit_default_per_minute


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        limit = _limit_for_path(request.url.path, request.method)
        if limit is None:
            return await call_next(request)

        client_ip = client_ip_from_request(request) or "unknown"
        bucket_key = f"{client_ip}:{request.url.path}"
        allowed, retry_after = _store.allow(bucket_key, limit=limit)
        if not allowed:
            return JSONResponse(
                status_code=429,
                content=error_payload(
                    code="rate_limited",
                    message="Too many requests; try again later",
                    details={"retry_after_seconds": retry_after},
                    request=request,
                ),
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
