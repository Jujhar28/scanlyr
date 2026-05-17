from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["low", "medium", "high", "critical"]

FindingType = Literal[
    "api_key_leak",
    "secret_password",
    "jwt_token",
    "sql_injection",
    "command_injection",
    "prompt_injection",
    "phishing_url",
    "suspicious_link",
    "unsafe_code",
    "shell_command",
    "hardcoded_credential",
    "data_exfiltration",
    "jailbreak",
    "system_prompt_leak",
    "sensitive_data",
    "unsafe_agent",
    "output_moderation",
    "unsafe_instructions",
    "provider_risk",
]


class SecurityFinding(BaseModel):
    """Structured issue reported by a single detector."""

    model_config = ConfigDict(frozen=True)

    type: FindingType | str = Field(..., description="Canonical finding type for aggregation.")
    detector_id: str
    category: str
    risk_category: str
    severity: Severity
    title: str
    description: str
    remediation: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detector confidence for this match.")
    evidence: dict[str, Any] = Field(default_factory=dict)
