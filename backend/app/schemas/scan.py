from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

API_SCHEMA_VERSION = "2.1"


class ScanRequest(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=50_000)
    content_type: Literal["prompt", "output", "auto"] = Field(
        default="auto",
        description=(
            "Scan user prompts (`prompt`), model outputs (`output`), or both (`auto`). "
            "Prompt scans emphasize jailbreak/injection/exfiltration; output scans emphasize moderation."
        ),
    )


class ScanFinding(BaseModel):
    type: str = Field(..., description="Canonical finding type (e.g. api_key_leak, jwt_token).")
    detector: str = Field(..., description="Detector identifier that produced this finding.")
    category: str
    risk_category: str = Field(
        ...,
        description="Canonical risk bucket (e.g. jailbreak, data_exfiltration, output_moderation).",
    )
    severity: Literal["low", "medium", "high", "critical"]
    title: str
    description: str = Field(..., description="Human-readable explanation of the issue.")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence for this finding.")
    remediation: str
    evidence: dict[str, Any] | None = None


class CategoryScoreRead(BaseModel):
    risk_category: str
    score: int = Field(..., ge=0, le=100)
    finding_count: int = Field(..., ge=0)
    explanation: str


class ExplainableRiskScoreRead(BaseModel):
    overall: int = Field(..., ge=0, le=100)
    categories: list[CategoryScoreRead] = Field(default_factory=list)
    top_drivers: list[str] = Field(
        default_factory=list,
        description="Highest contributing risk categories, e.g. 'jailbreak (82)'.",
    )


class ScanFusionDetails(BaseModel):
    """Rules + AI score blend (optional; present when fusion ran or rules-only fallback)."""

    rules_score: int = Field(..., ge=0, le=100)
    ai_score: int | None = Field(default=None, ge=0, le=100)
    combined_score: int = Field(..., ge=0, le=100)
    rules_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    ai_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    ai_used: bool = False
    ai_provider: str | None = None
    ai_category: str | None = None


class ScanAssessmentSummary(BaseModel):
    """Top-level user-facing assessment (headline + short summary)."""

    headline: str = Field(..., description="e.g. High risk (81/100)")
    score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str = Field(..., description="2–4 sentences in plain language.")


class ScanRulesAssessment(BaseModel):
    """What the rule-based detector engine found."""

    score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    summary: str
    primary_concerns: list[str] = Field(
        default_factory=list,
        description="Short labels for top findings (finding titles).",
    )
    top_categories: list[str] = Field(
        default_factory=list,
        description="Human-readable risk category names.",
    )


class ScanAIAssessment(BaseModel):
    """Optional AI layer outcome (hidden when ``used`` is false)."""

    used: bool = False
    score: int | None = Field(default=None, ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"] | None = None
    category: str | None = Field(default=None, description="Human-readable category label.")
    summary: str | None = None


class ScanComposition(BaseModel):
    """How the final score was derived."""

    method: Literal["hybrid", "rules_only", "safe_default"]
    combined_score: int = Field(..., ge=0, le=100)
    label: str
    rules_weight_percent: int = Field(..., ge=0, le=100)
    ai_weight_percent: int | None = Field(default=None, ge=0, le=100)
    rules_score: int = Field(..., ge=0, le=100)
    ai_score: int | None = Field(default=None, ge=0, le=100)


class ScanTechnicalDetails(BaseModel):
    """Optional advanced / support metadata (not shown by default in UI)."""

    engine_version: str | None = None
    rules_engine_detail: str | None = None
    ai_provider: str | None = None
    ai_fallback_used: bool = False
    ai_detail: str | None = None
    fusion_weights: dict[str, float] | None = None


class ScanExplainability(BaseModel):
    """
    Layered explainability for SaaS UI.

    - ``summary``: primary card content
    - ``rules`` / ``ai``: per-layer narratives
    - ``composition``: score blending (user-friendly)
    - ``technical``: pipeline debug (collapsible in UI)
    """

    summary: ScanAssessmentSummary
    rules: ScanRulesAssessment
    ai: ScanAIAssessment
    composition: ScanComposition
    technical: ScanTechnicalDetails | None = None


class ScanAnalysisDetails(BaseModel):
    """Extended explainability fields (category scores and drivers)."""

    risk_categories: dict[str, int] = Field(default_factory=dict)
    score_breakdown: ExplainableRiskScoreRead
    fusion: ScanFusionDetails | None = Field(
        default=None,
        description="Rules/AI score contribution when hybrid scan is enabled.",
    )
    explainability: ScanExplainability | None = Field(
        default=None,
        description="Structured multi-layer assessment (preferred over raw ``explanation``).",
    )


class ScanMetadata(BaseModel):
    """Request tracing and persistence identifiers."""

    scan_id: uuid.UUID
    timestamp: datetime = Field(..., description="UTC time when the scan completed.")
    request_id: str | None = Field(
        default=None,
        description="Correlation id from `X-Request-ID` (also returned on the response header).",
    )
    content_type: Literal["prompt", "output", "auto"]
    engine_version: str
    schema_version: str = Field(default=API_SCHEMA_VERSION)


class ScanResponse(BaseModel):
    """
    Production scan result envelope.

    Core assessment fields are top-level; tracing lives under ``metadata``;
    explainability details live under ``analysis``.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "risk_score": 82,
                "risk_level": "high",
                "confidence": 0.91,
                "explanation": "Overall high risk (score 82). Top categories: credential_exposure (82). …",
                "findings": [],
                "remediation": ["Rotate compromised credentials and purge from chat logs."],
                "metadata": {
                    "scan_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2026-05-15T12:00:00Z",
                    "request_id": "a10b2c57-ff2f-4dbd-8721-e1c28cdee4e1",
                    "content_type": "auto",
                    "engine_version": "scan_security_v4",
                    "schema_version": API_SCHEMA_VERSION,
                },
                "analysis": {
                    "risk_categories": {"credential_exposure": 82},
                    "score_breakdown": {
                        "overall": 82,
                        "categories": [],
                        "top_drivers": ["credential_exposure (82)"],
                    },
                },
            },
        },
    )

    risk_score: int = Field(..., ge=0, le=100)
    risk_level: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Heuristic confidence in the assessment.")
    explanation: str = Field(
        ...,
        description="Short plain-language summary (duplicate of ``analysis.explainability.summary.summary``).",
    )
    findings: list[ScanFinding] = Field(default_factory=list)
    remediation: list[str] = Field(
        default_factory=list,
        description="Deduplicated remediation steps derived from findings.",
    )
    metadata: ScanMetadata
    analysis: ScanAnalysisDetails | None = None

    @model_validator(mode="before")
    @classmethod
    def _coerce_legacy_payload(cls, data: Any) -> Any:
        """Accept persisted v1 payloads when loading scan history."""
        if not isinstance(data, dict):
            return data
        raw = dict(data)
        if "metadata" not in raw:
            meta: dict[str, Any] = {
                "content_type": raw.get("content_type", "auto"),
                "engine_version": raw.get("engine_version", "scan_security_v3_llm"),
                "schema_version": raw.get("schema_version", "1.0"),
            }
            if scan_id := raw.pop("scan_id", None):
                meta["scan_id"] = scan_id
            if ts := raw.get("timestamp"):
                meta["timestamp"] = ts
            else:
                meta["timestamp"] = datetime.now(tz=UTC).isoformat()
            if rid := raw.get("request_id"):
                meta["request_id"] = rid
            raw["metadata"] = meta
        if "remediation" not in raw:
            raw["remediation"] = raw.get("remediation_steps") or raw.get("remediations") or []
        if "analysis" not in raw and ("score_breakdown" in raw or "risk_categories" in raw):
            raw["analysis"] = {
                "risk_categories": raw.pop("risk_categories", {}),
                "score_breakdown": raw.pop("score_breakdown", None),
            }
        return raw
