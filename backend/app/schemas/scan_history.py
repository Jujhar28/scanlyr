from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.scan import ScanFinding, ScanResponse


class ScanHistorySummary(BaseModel):
    id: uuid.UUID
    scanned_at: datetime
    user_id: uuid.UUID | None
    content_type: Literal["prompt", "output", "auto"]
    risk_score: int
    risk_level: Literal["low", "medium", "high", "critical"]
    confidence: float
    finding_count: int
    input_text: str | None = None
    input_preview: str
    engine_version: str


class ScanHistoryDetail(ScanHistorySummary):
    findings: list[ScanFinding] = Field(default_factory=list)
    result: ScanResponse
    detection_event_id: uuid.UUID | None = None


class ScanHistoryListResponse(BaseModel):
    items: list[ScanHistorySummary]
    total: int
    limit: int
    offset: int


class ThreatCount(BaseModel):
    risk_category: str
    count: int


class RiskLevelCount(BaseModel):
    risk_level: str
    count: int


class ScanTrendPoint(BaseModel):
    date: datetime
    scan_count: int
    average_risk_score: float | None = None


class ScanAnalyticsResponse(BaseModel):
    organization_id: uuid.UUID
    total_scans: int
    average_risk_score: float | None
    risk_level_distribution: list[RiskLevelCount]
    top_threats: list[ThreatCount]
    trends: list[ScanTrendPoint]
