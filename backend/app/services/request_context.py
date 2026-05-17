"""Extract common request metadata (keeps routers free of header parsing)."""

from __future__ import annotations

from starlette.requests import Request

from app.core.config import get_settings


def user_agent_from_request(request: Request) -> str | None:
    ua = request.headers.get("user-agent")
    if ua and len(ua) > 512:
        return ua[:512]
    return ua


def client_ip_from_request(request: Request) -> str | None:
    if get_settings().trust_proxy_headers:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First hop is the original client when proxies append.
            client = forwarded.split(",")[0].strip()
            if client:
                return client[:45]
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()[:45]
    if request.client:
        return request.client.host
    return None
