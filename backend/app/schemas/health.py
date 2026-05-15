from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(..., examples=["ok"])


ReadinessState = Literal["pass", "fail", "warn", "skipped", "unknown"]


class ReadinessCheck(BaseModel):
    """Single dependency check (database, migrations, etc.)."""

    status: ReadinessState
    message: str | None = None
    details: dict[str, Any] | None = None


OverallReadiness = Literal["ready", "degraded", "not_ready"]


class ReadinessResponse(BaseModel):
    """Structured readiness for orchestrators (e.g. Kubernetes) and dashboards."""

    status: OverallReadiness = Field(
        description="ready = all critical checks pass and no warnings; degraded = critical OK but warnings present; not_ready = a critical check failed.",
    )
    critical_ok: bool = Field(
        description="True when database, migrations, and report storage are all ``pass`` (not fail/skipped/unknown).",
    )
    checks: dict[str, ReadinessCheck] = Field(
        description="Named checks: database, migrations, report_storage, security.",
    )
