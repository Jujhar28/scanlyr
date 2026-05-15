from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RiskScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    score_kind: str
    score: Decimal
    factors: dict | None = None
    algorithm_version: str
    computed_at: datetime


class DetectionEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_session_id: uuid.UUID | None
    occurred_at: datetime
    source: str
    tool_name: str | None
    tool_vendor: str | None
    channel: str | None
    severity: str
    confidence: float | None
    external_ref: str | None
    evidence: dict | None = None
    risk_scores: list[RiskScoreRead] = Field(default_factory=list)

    @classmethod
    def from_model(cls, row: object) -> DetectionEventRead:
        from app.models.ai_detection_event import AIDetectionEvent

        assert isinstance(row, AIDetectionEvent)
        return cls.model_validate(row)


class DetectionListResponse(BaseModel):
    items: list[DetectionEventRead]
    total: int
    limit: int
    offset: int


class DetectionRunResponse(BaseModel):
    scan_session_id: uuid.UUID
    events_normalized: int
    candidates: int
    inserted: int
    skipped_duplicates: int


class ScanPipelineRequest(BaseModel):
    mode: Literal["synthetic", "microsoft_graph"] = "synthetic"
    synthetic_event_count: int = Field(default=3, ge=1, le=20)
    graph_top: int = Field(default=120, ge=20, le=300)


class ScanPipelineReportRef(BaseModel):
    id: uuid.UUID
    status: str
    title: str
    downloadable: bool


class ScanPipelineResponse(BaseModel):
    mode: str
    scan_session_id: uuid.UUID
    detection_events_inserted: int
    risk_scores_created: int
    report: ScanPipelineReportRef
