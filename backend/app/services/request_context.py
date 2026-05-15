"""Extract common request metadata (keeps routers free of header parsing)."""

from __future__ import annotations

from starlette.requests import Request


def user_agent_from_request(request: Request) -> str | None:
    return request.headers.get("user-agent")


def client_ip_from_request(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None
