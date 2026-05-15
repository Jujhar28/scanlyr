"""Microsoft OAuth callback redirect wiring (browser redirect responses)."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.microsoft_graph.errors import MicrosoftGraphIntegrationError
from app.services import microsoft_graph_service as msft_service


def build_microsoft_oauth_callback_redirect(
    db: Session,
    *,
    code: str | None,
    state: str | None,
    error: str | None,
    error_description: str | None,
) -> RedirectResponse:
    frontend = settings.frontend_app_url.rstrip("/")
    target = f"{frontend}/dashboard/integrations"

    def redirect(q: dict[str, str]) -> RedirectResponse:
        return RedirectResponse(f"{target}?{urlencode(q)}", status_code=302)

    if error:
        return redirect(
            {
                "msft_error": error,
                "msft_error_description": (error_description or "")[:900],
            },
        )
    if not code or not state:
        return redirect({"msft_error": "missing_code_or_state"})
    try:
        msft_service.complete_oauth_callback(db, code=code, state=state)
        return redirect({"msft_connected": "1"})
    except MicrosoftGraphIntegrationError as exc:
        return redirect(
            {
                "msft_error": "oauth_failed",
                "msft_error_description": str(exc)[:900],
            },
        )
