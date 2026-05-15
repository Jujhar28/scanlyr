from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integrations.microsoft_graph.errors import MicrosoftGraphApiError

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


def _headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }


def _raise_for_status(resp: httpx.Response, *, context: str) -> None:
    if resp.is_success:
        return
    body_preview = (resp.text or "")[:500]
    logger.warning(
        "Microsoft Graph request failed",
        extra={"context": context, "status_code": resp.status_code},
    )
    raise MicrosoftGraphApiError(
        f"{context}: HTTP {resp.status_code} — {body_preview}",
        status_code=resp.status_code,
    )


def exchange_authorization_code(
    *,
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    scopes: str,
) -> dict[str, Any]:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "scope": scopes,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            token_endpoint,
            content=urlencode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    _raise_for_status(resp, context="token exchange (authorization_code)")
    return resp.json()


def refresh_access_token(
    *,
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    refresh_token: str,
    scopes: str,
) -> dict[str, Any]:
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "scope": scopes,
    }
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(
            token_endpoint,
            content=urlencode(data),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    _raise_for_status(resp, context="token exchange (refresh_token)")
    return resp.json()


def fetch_directory_audits(access_token: str, *, top: int = 50) -> dict[str, Any]:
    params = urlencode({"$top": str(top)})
    url = f"{GRAPH_BASE}/auditLogs/directoryAudits?{params}"
    with httpx.Client(timeout=45.0) as client:
        resp = client.get(url, headers=_headers(access_token))
    _raise_for_status(resp, context="directoryAudits")
    return resp.json()


def fetch_sign_ins(access_token: str, *, top: int = 50) -> dict[str, Any]:
    params = urlencode({"$top": str(top)})
    url = f"{GRAPH_BASE}/auditLogs/signIns?{params}"
    with httpx.Client(timeout=45.0) as client:
        resp = client.get(url, headers=_headers(access_token))
    _raise_for_status(resp, context="signIns")
    return resp.json()


def fetch_service_principals(access_token: str, *, top: int = 50) -> dict[str, Any]:
    """Enterprise app inventory (useful for AI / SaaS app exposure reviews)."""
    select = "id,appId,displayName,servicePrincipalType,tags,createdDateTime"
    params = urlencode({"$top": str(top), "$select": select})
    url = f"{GRAPH_BASE}/servicePrincipals?{params}"
    with httpx.Client(timeout=45.0) as client:
        resp = client.get(url, headers=_headers(access_token))
    _raise_for_status(resp, context="servicePrincipals")
    return resp.json()
