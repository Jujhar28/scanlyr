from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.types import ASGIApp

from app.core.errors import error_payload
from app.core.security import safe_decode_access_token


class APIAuthMiddleware(BaseHTTPMiddleware):
    """Require a Bearer access token for ``/api/v1/*`` except handlers marked ``@public_api_route``."""

    def __init__(self, app: ASGIApp, *, public_route_keys: frozenset[tuple[str, str]]) -> None:
        super().__init__(app)
        self.public_route_keys = public_route_keys

    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if not path.startswith("/api/v1"):
            return await call_next(request)

        key = (request.method, path)
        if key in self.public_route_keys:
            return await call_next(request)
        if request.method == "HEAD" and ("GET", path) in self.public_route_keys:
            return await call_next(request)

        authorization = request.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            return JSONResponse(
                status_code=401,
                content=error_payload(
                    code="authentication_error",
                    message="Authentication required",
                    request=request,
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split(" ", 1)[1].strip()
        payload = safe_decode_access_token(token)
        if payload is None:
            return JSONResponse(
                status_code=401,
                content=error_payload(
                    code="authentication_error",
                    message="Invalid or expired token",
                    request=request,
                ),
                headers={"WWW-Authenticate": "Bearer"},
            )

        request.state.jwt_payload = payload
        return await call_next(request)
