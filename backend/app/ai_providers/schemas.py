from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RiskLevel = Literal["low", "medium", "high", "critical"]
FindingVerdict = Literal["confirm", "downgrade", "dismiss"]


class TextAnalysisResult(BaseModel):
    """Structured output contract for ``AIProvider.analyze_text``."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    explanation: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=128)

    @field_validator("explanation", "category", mode="before")
    @classmethod
    def strip_strings(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    def as_dict(self) -> dict[str, object]:
        return self.model_dump(mode="json")


class FindingAdjudicationInput(BaseModel):
    """Rule finding passed to AI for re-verification."""

    index: int = Field(ge=0)
    title: str
    severity: RiskLevel
    description: str
    detector_id: str


class FindingAdjudicationVerdict(BaseModel):
    """AI judgment on a single rule-engine finding."""

    index: int = Field(ge=0)
    verdict: FindingVerdict
    reason: str = Field(min_length=1, max_length=500)
    adjusted_severity: RiskLevel | None = None


class HybridReverifyResult(BaseModel):
    """
    AI re-verification of rule findings plus overall contextual assessment.

    Used in hybrid mode: rules detect → AI adjudicates each finding → fused score.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    risk_score: int = Field(ge=0, le=100)
    risk_level: RiskLevel
    explanation: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=128)
    finding_verdicts: list[FindingAdjudicationVerdict] = Field(default_factory=list)

    def as_analysis_result(self) -> TextAnalysisResult:
        return TextAnalysisResult(
            risk_score=self.risk_score,
            risk_level=self.risk_level,
            explanation=self.explanation,
            category=self.category,
        )


class ProviderAnalysisOutcome(BaseModel):
    """Result of an analysis call including which adapter served the request."""

    result: TextAnalysisResult
    provider_id: str = Field(description="Adapter that produced the result: gemini | groq.")
    fallback_used: bool = Field(
        description="True when the primary provider failed and a secondary adapter was used.",
    )
    attempted_providers: list[str] = Field(default_factory=list)


class HybridReverifyOutcome(BaseModel):
    """Provider outcome for hybrid re-verify (includes per-finding verdicts)."""

    result: HybridReverifyResult
    provider_id: str
    fallback_used: bool = False
    attempted_providers: list[str] = Field(default_factory=list)

    def as_provider_analysis_outcome(self) -> ProviderAnalysisOutcome:
        return ProviderAnalysisOutcome(
            result=self.result.as_analysis_result(),
            provider_id=self.provider_id,
            fallback_used=self.fallback_used,
            attempted_providers=list(self.attempted_providers),
        )
