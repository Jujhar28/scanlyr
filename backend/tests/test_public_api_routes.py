"""Public ``/api/v1`` surface must stay aligned with ``@public_api_route`` (auth middleware)."""

from __future__ import annotations

from app.core.public_api import collect_public_api_route_keys
from app.main import app

# Regression guard: every path here must remain reachable without a Bearer token.
_EXPECTED_PUBLIC: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/api/v1/health"),
        ("POST", "/api/v1/auth/register"),
        ("POST", "/api/v1/auth/login"),
        ("POST", "/api/v1/auth/refresh"),
        ("GET", "/api/v1/integrations/microsoft/callback"),
    },
)


def test_collected_public_routes_cover_expected_surface() -> None:
    keys = collect_public_api_route_keys(app)
    missing = _EXPECTED_PUBLIC - keys
    assert not missing, f"Missing public route keys (add @public_api_route?): {sorted(missing)}"
