from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import UTC, datetime
from typing import Any

from app.detections.contracts import NormalizedTelemetryEvent


def _parse_graph_datetime(value: object) -> datetime:
    if isinstance(value, str):
        try:
            raw = value.replace("Z", "+00:00")
            return datetime.fromisoformat(raw)
        except ValueError:
            pass
    return datetime.now(tz=UTC)


def _stable_id(prefix: str, payload: dict[str, Any]) -> str:
    gid = payload.get("id")
    if isinstance(gid, str) and gid.strip():
        return gid.strip()
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8"),
    ).hexdigest()[:48]
    return f"{prefix}:{digest}"


def _walk_strings(obj: Any, out: list[str], depth: int = 0) -> None:
    if depth > 14:
        return
    if isinstance(obj, str):
        if obj.strip():
            out.append(obj)
        return
    if isinstance(obj, dict):
        for v in obj.values():
            _walk_strings(v, out, depth + 1)
        return
    if isinstance(obj, list):
        for v in obj:
            _walk_strings(v, out, depth + 1)


def _build_corpus(parts: list[str]) -> str:
    blob = " \n ".join(parts)
    blob = re.sub(r"\s+", " ", blob)
    return blob.strip().lower()


def iter_sign_in_events(
    organization_id: uuid.UUID,
    payload: dict[str, Any],
) -> list[NormalizedTelemetryEvent]:
    rows = payload.get("value") or []
    events: list[NormalizedTelemetryEvent] = []
    if not isinstance(rows, list):
        return events
    for row in rows:
        if not isinstance(row, dict):
            continue
        strings: list[str] = []
        _walk_strings(row, strings)
        corpus = _build_corpus(strings)
        occurred = _parse_graph_datetime(row.get("createdDateTime") or row.get("activityDateTime"))
        gid = _stable_id("si", row)
        actor = None
        if isinstance(row.get("userPrincipalName"), str):
            actor = row["userPrincipalName"]
        elif isinstance(row.get("userDisplayName"), str):
            actor = row["userDisplayName"]
        events.append(
            NormalizedTelemetryEvent(
                organization_id=organization_id,
                source="m365_sign_in",
                graph_item_id=gid,
                occurred_at=occurred,
                corpus=corpus,
                raw_snapshot={
                    "id": row.get("id"),
                    "appDisplayName": row.get("appDisplayName"),
                    "resourceDisplayName": row.get("resourceDisplayName"),
                    "clientAppUsed": row.get("clientAppUsed"),
                    "ipAddress": row.get("ipAddress"),
                    "userPrincipalName": row.get("userPrincipalName"),
                    "status": row.get("status"),
                },
                actor_hint=actor,
            ),
        )
    return events


def iter_directory_audit_events(
    organization_id: uuid.UUID,
    payload: dict[str, Any],
) -> list[NormalizedTelemetryEvent]:
    rows = payload.get("value") or []
    events: list[NormalizedTelemetryEvent] = []
    if not isinstance(rows, list):
        return events
    for row in rows:
        if not isinstance(row, dict):
            continue
        strings: list[str] = []
        _walk_strings(row, strings)
        corpus = _build_corpus(strings)
        occurred = _parse_graph_datetime(row.get("activityDateTime"))
        gid = _stable_id("da", row)
        actor = None
        ib = row.get("initiatedBy")
        if isinstance(ib, dict):
            user = ib.get("user")
            if isinstance(user, dict) and isinstance(user.get("userPrincipalName"), str):
                actor = user["userPrincipalName"]
        events.append(
            NormalizedTelemetryEvent(
                organization_id=organization_id,
                source="m365_directory_audit",
                graph_item_id=gid,
                occurred_at=occurred,
                corpus=corpus,
                raw_snapshot={
                    "id": row.get("id"),
                    "activityDisplayName": row.get("activityDisplayName"),
                    "category": row.get("category"),
                    "result": row.get("result"),
                    "loggedByService": row.get("loggedByService"),
                },
                actor_hint=actor,
            ),
        )
    return events
