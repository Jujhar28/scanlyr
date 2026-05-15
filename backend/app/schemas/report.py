from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ReportStatus


class ReportSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    report_type: str
    status: str
    period_start: datetime | None
    period_end: datetime | None
    created_at: datetime
    downloadable: bool = Field(
        description="True when a PDF file exists for this report.",
    )

    @classmethod
    def from_orm_row(cls, row: object) -> ReportSummary:
        from app.models.report import Report

        assert isinstance(row, Report)
        return cls(
            id=row.id,
            title=row.title,
            report_type=row.report_type,
            status=row.status,
            period_start=row.period_start,
            period_end=row.period_end,
            created_at=row.created_at,
            downloadable=bool(row.storage_uri and row.status == ReportStatus.ready.value),
        )


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    report_type: str
    status: str
    period_start: datetime | None
    period_end: datetime | None
    created_at: datetime
    updated_at: datetime
    created_by_user_id: uuid.UUID | None
    error_message: str | None
    downloadable: bool
    meta: dict | None = Field(default=None, description="Structured sections and generation metadata.")

    @classmethod
    def from_report(cls, row: object) -> ReportDetail:
        from app.models.report import Report

        assert isinstance(row, Report)
        return cls(
            id=row.id,
            title=row.title,
            report_type=row.report_type,
            status=row.status,
            period_start=row.period_start,
            period_end=row.period_end,
            created_at=row.created_at,
            updated_at=row.updated_at,
            created_by_user_id=row.created_by_user_id,
            error_message=row.error_message,
            downloadable=bool(row.storage_uri and row.status == ReportStatus.ready.value),
            meta=row.meta,
        )


class ReportListResponse(BaseModel):
    items: list[ReportSummary]
    total: int
    limit: int
    offset: int


class GenerateReportRequest(BaseModel):
    period_start: datetime | None = Field(default=None, description="Defaults to 30 days before period_end.")
    period_end: datetime | None = Field(default=None, description="Defaults to now (UTC).")


class GenerateReportResponse(BaseModel):
    id: uuid.UUID
    title: str
    status: str
