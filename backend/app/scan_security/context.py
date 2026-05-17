from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ContentKind = Literal["prompt", "output", "auto"]

# Canonical LLM risk taxonomy for explainable scoring.
RiskCategory = Literal[
    "data_exfiltration",
    "jailbreak",
    "system_prompt_leakage",
    "unsafe_instructions",
    "sensitive_data_exposure",
    "unsafe_agent_action",
    "output_moderation",
    "credential_exposure",
    "injection",
    "network",
    "social_engineering",
    "code_execution",
    "llm_abuse",
    "provider_risk",
]


@dataclass(frozen=True)
class ScanContext:
    """Input context passed to every detector for content-aware analysis."""

    text: str
    content_kind: ContentKind = "auto"

    def targets_prompt(self) -> bool:
        return self.content_kind in ("prompt", "auto")

    def targets_output(self) -> bool:
        return self.content_kind in ("output", "auto")
