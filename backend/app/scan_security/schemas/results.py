from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.scan_security.schemas.findings import SecurityFinding

RiskLevel = Literal["low", "medium", "high", "critical"]


class CategoryScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    risk_category: str
    score: int = Field(..., ge=0, le=100)
    finding_count: int = Field(..., ge=0)
    explanation: str


class ExplainableRiskScore(BaseModel):
    model_config = ConfigDict(frozen=True)

    overall: int = Field(..., ge=0, le=100)
    categories: tuple[CategoryScore, ...] = ()
    top_drivers: tuple[str, ...] = ()


class ScanAnalysisResult(BaseModel):
    """Aggregated output from all detectors and scoring."""

    model_config = ConfigDict(frozen=True)

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: RiskLevel
    confidence: float = Field(..., ge=0.0, le=1.0)
    explanation: str
    findings: tuple[SecurityFinding, ...] = ()
    remediation_steps: tuple[str, ...] = ()
    content_kind: Literal["prompt", "output", "auto"] = "auto"
    risk_categories: dict[str, int] = Field(default_factory=dict)
    score_breakdown: ExplainableRiskScore
