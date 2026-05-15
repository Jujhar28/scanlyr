from __future__ import annotations

import base64
import json
import logging
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

from jose import JWTError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.integrations.microsoft_graph import graph_client
from app.integrations.microsoft_graph.errors import (
    MicrosoftGraphApiError,
    MicrosoftGraphNotConfiguredError,
    MicrosoftGraphOAuthError,
)
from app.integrations.microsoft_graph.oauth_state import create_oauth_state_token, decode_oauth_state_token
from app.integrations.microsoft_graph.token_crypto import decrypt_secret, encrypt_secret
from app.models.enums import MicrosoftGraphConnectionStatus
from app.models.microsoft_graph import MicrosoftGraphConnection, MicrosoftGraphSyncRun
from app.schemas.integrations_microsoft import (
    MicrosoftGraphConnectResponse,
    MicrosoftGraphRecentSyncSummary,
    MicrosoftGraphStatusResponse,
    MicrosoftGraphSyncResponse,
)

logger = logging.getLogger(__name__)


def _tid_from_access_token_jwt(access_token: str) -> str | None:
    """Extract `tid` from an access token JWT payload (no signature verification)."""
    try:
        parts = access_token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("ascii")))
        tid = payload.get("tid")
        return tid.strip() if isinstance(tid, str) and tid.strip() else None
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


_AI_APP_HINT_PATTERN = re.compile(
    r"(openai|anthropic|claude|chatgpt|copilot|azure\s*openai|vertex|gemini|grok|mistral|cohere)",
    re.IGNORECASE,
)


def _require_msft_config() -> tuple[str, str, str, str, str]:
    cid = settings.microsoft_graph_client_id
    csec = settings.microsoft_graph_client_secret
    redir = settings.microsoft_graph_redirect_uri
    if not cid or not csec or not redir:
        raise MicrosoftGraphNotConfiguredError(
            "Microsoft Graph is not configured (set MICROSOFT_GRAPH_CLIENT_ID, "
            "MICROSOFT_GRAPH_CLIENT_SECRET, MICROSOFT_GRAPH_REDIRECT_URI).",
        )
    tenant = settings.microsoft_graph_tenant.strip() or "organizations"
    authority = settings.microsoft_graph_authority_host.rstrip("/")
    scopes = " ".join(settings.microsoft_graph_scopes.split())
    return cid, csec, redir, f"{authority}/{tenant}", scopes


def _token_endpoints(authority_prefix: str) -> tuple[str, str]:
    return (
        f"{authority_prefix}/oauth2/v2.0/token",
        f"{authority_prefix}/oauth2/v2.0/authorize",
    )


def get_or_create_connection(db: Session, organization_id: uuid.UUID) -> MicrosoftGraphConnection:
    row = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if row is not None:
        return row
    row = MicrosoftGraphConnection(
        organization_id=organization_id,
        status=MicrosoftGraphConnectionStatus.disconnected.value,
    )
    db.add(row)
    db.flush()
    return row


def begin_connect_flow(
    db: Session,
    *,
    organization_id: uuid.UUID,
    admin_user_id: uuid.UUID,
) -> MicrosoftGraphConnectResponse:
    client_id, _client_secret, redirect_uri, authority_prefix, scopes = _require_msft_config()
    _token_url, authorize_url_base = _token_endpoints(authority_prefix)

    state = create_oauth_state_token(settings, organization_id=organization_id, user_id=admin_user_id)
    conn = get_or_create_connection(db, organization_id)
    conn.status = MicrosoftGraphConnectionStatus.pending.value
    conn.connected_by_user_id = admin_user_id
    conn.last_error_message = None
    conn.encrypted_refresh_token = None
    conn.encrypted_access_token = None
    conn.access_token_expires_at = None
    conn.azure_tenant_id = None
    conn.scopes = scopes
    db.commit()

    params = {
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "response_mode": "query",
        "scope": scopes,
        "state": state,
    }
    url = f"{authorize_url_base}?{urlencode(params)}"
    logger.info("Microsoft Graph OAuth started", extra={"organization_id": str(organization_id)})
    return MicrosoftGraphConnectResponse(authorization_url=url)


def complete_oauth_callback(db: Session, *, code: str, state: str) -> None:
    client_id, client_secret, redirect_uri, authority_prefix, scopes = _require_msft_config()
    token_url, _authorize = _token_endpoints(authority_prefix)
    try:
        payload = decode_oauth_state_token(settings, state)
        org_id = uuid.UUID(str(payload["org_id"]))
        admin_user_id = uuid.UUID(str(payload["admin_user_id"]))
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise MicrosoftGraphOAuthError("Invalid or expired OAuth state") from exc

    token_body = graph_client.exchange_authorization_code(
        token_endpoint=token_url,
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        code=code,
        scopes=scopes,
    )
    refresh = token_body.get("refresh_token")
    access = token_body.get("access_token")
    if not refresh or not access:
        raise MicrosoftGraphOAuthError("Token response missing refresh_token or access_token")

    expires_in = int(token_body.get("expires_in", 3600))
    expires_at = datetime.now(tz=UTC) + timedelta(seconds=max(expires_in - 60, 60))

    tid = _tid_from_access_token_jwt(access)

    conn = get_or_create_connection(db, org_id)
    conn.encrypted_refresh_token = encrypt_secret(settings, refresh)
    conn.encrypted_access_token = encrypt_secret(settings, access)
    conn.access_token_expires_at = expires_at
    conn.status = MicrosoftGraphConnectionStatus.connected.value
    conn.connected_at = datetime.now(tz=UTC)
    conn.connected_by_user_id = admin_user_id
    conn.last_error_message = None
    conn.scopes = scopes
    if isinstance(tid, str) and tid.strip():
        conn.azure_tenant_id = tid.strip()
    db.commit()
    logger.info("Microsoft Graph OAuth completed", extra={"organization_id": str(org_id)})


def disconnect(db: Session, organization_id: uuid.UUID) -> None:
    conn = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if conn is None:
        return
    conn.encrypted_refresh_token = None
    conn.encrypted_access_token = None
    conn.access_token_expires_at = None
    conn.azure_tenant_id = None
    conn.status = MicrosoftGraphConnectionStatus.disconnected.value
    conn.last_error_message = None
    conn.sync_cursors = None
    db.commit()
    logger.info("Microsoft Graph disconnected", extra={"organization_id": str(organization_id)})


def _decrypt_refresh(conn: MicrosoftGraphConnection) -> str:
    if not conn.encrypted_refresh_token:
        raise MicrosoftGraphOAuthError("No refresh token stored; reconnect Microsoft 365.")
    return decrypt_secret(settings, conn.encrypted_refresh_token)


def _valid_access_token(conn: MicrosoftGraphConnection) -> str | None:
    if not conn.encrypted_access_token or conn.access_token_expires_at is None:
        return None
    if datetime.now(tz=UTC) >= conn.access_token_expires_at - timedelta(seconds=90):
        return None
    return decrypt_secret(settings, conn.encrypted_access_token)


def _persist_token_response(db: Session, conn: MicrosoftGraphConnection, body: dict[str, Any], scopes: str) -> str:
    access = body.get("access_token")
    if not access or not isinstance(access, str):
        raise MicrosoftGraphOAuthError("Refresh response missing access_token")
    new_refresh = body.get("refresh_token")
    if isinstance(new_refresh, str) and new_refresh.strip():
        conn.encrypted_refresh_token = encrypt_secret(settings, new_refresh)
    conn.encrypted_access_token = encrypt_secret(settings, access)
    expires_in = int(body.get("expires_in", 3600))
    conn.access_token_expires_at = datetime.now(tz=UTC) + timedelta(seconds=max(expires_in - 60, 60))
    conn.scopes = scopes
    db.flush()
    return access


def ensure_access_token(db: Session, conn: MicrosoftGraphConnection) -> str:
    cached = _valid_access_token(conn)
    if cached is not None:
        return cached
    client_id, client_secret, redirect_uri, authority_prefix, scopes = _require_msft_config()
    token_url, _ = _token_endpoints(authority_prefix)
    refresh_plain = _decrypt_refresh(conn)
    body = graph_client.refresh_access_token(
        token_endpoint=token_url,
        client_id=client_id,
        client_secret=client_secret,
        refresh_token=refresh_plain,
        scopes=scopes,
    )
    access = _persist_token_response(db, conn, body, scopes)
    db.commit()
    return access


def _collect_ai_app_hints(service_principal_payload: dict[str, Any]) -> list[dict[str, str]]:
    hints: list[dict[str, str]] = []
    for item in service_principal_payload.get("value") or []:
        if not isinstance(item, dict):
            continue
        name = str(item.get("displayName") or "")
        if _AI_APP_HINT_PATTERN.search(name):
            hints.append(
                {
                    "displayName": name,
                    "appId": str(item.get("appId") or ""),
                    "id": str(item.get("id") or ""),
                },
            )
    return hints[:25]


def run_sync(db: Session, organization_id: uuid.UUID) -> MicrosoftGraphSyncResponse:
    conn = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if conn is None or conn.status != MicrosoftGraphConnectionStatus.connected.value:
        raise MicrosoftGraphOAuthError("Microsoft 365 is not connected for this organization.")

    sync_run = MicrosoftGraphSyncRun(organization_id=organization_id, status="running")
    db.add(sync_run)
    db.flush()

    stats: dict[str, Any] = {
        "directory_audits": {},
        "sign_ins": {},
        "service_principals": {},
        "ai_related_app_hints": [],
    }
    try:
        access = ensure_access_token(db, conn)
        sp_payload: dict[str, Any] | None = None

        for label, fetcher in (
            ("directory_audits", graph_client.fetch_directory_audits),
            ("sign_ins", graph_client.fetch_sign_ins),
            ("service_principals", graph_client.fetch_service_principals),
        ):
            try:
                payload = fetcher(access, top=50)
                n = len(payload.get("value") or [])
                stats[label] = {"fetched": n, "error": None}
                if label == "service_principals":
                    sp_payload = payload
            except MicrosoftGraphApiError as exc:
                stats[label] = {"fetched": 0, "error": str(exc)}
                logger.warning(
                    "Microsoft Graph sync step failed",
                    extra={"organization_id": str(organization_id), "step": label},
                )

        if sp_payload is not None:
            stats["ai_related_app_hints"] = _collect_ai_app_hints(sp_payload)

        sync_run.status = "completed"
        sync_run.stats = stats
        sync_run.completed_at = datetime.now(tz=UTC)
        conn.last_sync_at = sync_run.completed_at
        conn.last_error_message = None
        db.commit()
        logger.info(
            "Microsoft Graph sync completed",
            extra={"organization_id": str(organization_id), "sync_run_id": str(sync_run.id)},
        )
        return MicrosoftGraphSyncResponse(sync_run_id=sync_run.id, status=sync_run.status, stats=stats)
    except Exception as exc:
        sync_run.status = "failed"
        sync_run.completed_at = datetime.now(tz=UTC)
        sync_run.error_message = str(exc)
        conn.last_error_message = str(exc)
        conn.status = MicrosoftGraphConnectionStatus.error.value
        db.commit()
        logger.exception(
            "Microsoft Graph sync failed",
            extra={"organization_id": str(organization_id), "sync_run_id": str(sync_run.id)},
        )
        raise


def get_status(db: Session, organization_id: uuid.UUID) -> MicrosoftGraphStatusResponse:
    conn = db.execute(
        select(MicrosoftGraphConnection).where(MicrosoftGraphConnection.organization_id == organization_id),
    ).scalar_one_or_none()
    if conn is None:
        return MicrosoftGraphStatusResponse(status=MicrosoftGraphConnectionStatus.disconnected.value)

    recent = db.execute(
        select(MicrosoftGraphSyncRun)
        .where(MicrosoftGraphSyncRun.organization_id == organization_id)
        .order_by(MicrosoftGraphSyncRun.started_at.desc())
        .limit(1),
    ).scalar_one_or_none()

    recent_model: MicrosoftGraphRecentSyncSummary | None = None
    if recent is not None:
        recent_model = MicrosoftGraphRecentSyncSummary(
            id=recent.id,
            started_at=recent.started_at,
            completed_at=recent.completed_at,
            status=recent.status,
            stats=recent.stats,
            error_message=recent.error_message,
        )

    return MicrosoftGraphStatusResponse(
        status=conn.status,
        azure_tenant_id=conn.azure_tenant_id,
        last_sync_at=conn.last_sync_at,
        last_error_message=conn.last_error_message,
        connected_at=conn.connected_at,
        scopes=conn.scopes,
        recent_sync=recent_model,
    )
