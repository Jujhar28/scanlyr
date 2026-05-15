"""Mark handlers that are reachable under ``/api/v1`` without a Bearer token.

The auth middleware builds its allowlist from these markers so new public routes
cannot silently require auth (or stay open by mistake on a stale hardcoded list).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import ParamSpec, TypeVar

from fastapi import FastAPI
from fastapi.routing import APIRoute

P = ParamSpec("P")
R = TypeVar("R")

PUBLIC_API_ROUTE_ATTR = "__shadow_public_api_route__"


def public_api_route(fn: Callable[P, R]) -> Callable[P, R]:
    """Declare that this handler is exempt from Bearer auth (``/api/v1`` only)."""
    setattr(fn, PUBLIC_API_ROUTE_ATTR, True)
    return fn


def collect_public_api_route_keys(app: FastAPI) -> frozenset[tuple[str, str]]:
    """Return ``(HTTP method, path)`` pairs for handlers marked with ``@public_api_route``."""
    keys: set[tuple[str, str]] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not getattr(route.endpoint, PUBLIC_API_ROUTE_ATTR, False):
            continue
        for method in route.methods:
            if method == "OPTIONS":
                continue
            keys.add((method, route.path))
    return frozenset(keys)