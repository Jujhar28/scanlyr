from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class MicrosoftGraphConnectResponse(BaseModel):
    authorization_url: str = Field(..., description="Redirect the browser here to start Entra ID consent.")


class MicrosoftGraphRecentSyncSummary(BaseModel):
    id: uuid.UUID
    started_at: datetime
    completed_at: datetime | None
    status: str
    stats: dict | None = None
    error_message: str | None = None


class MicrosoftGraphStatusResponse(BaseModel):
    status: str
    azure_tenant_id: str | None = None
    last_sync_at: datetime | None = None
    last_error_message: str | None = None
    connected_at: datetime | None = None
    scopes: str | None = None
    recent_sync: MicrosoftGraphRecentSyncSummary | None = None


class MicrosoftGraphSyncResponse(BaseModel):
    sync_run_id: uuid.UUID
    status: str
    stats: dict | None = None
