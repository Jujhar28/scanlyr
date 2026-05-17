from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind, ScanContext
from app.scan_security.contracts import SecurityFinding
from app.scan_security.detectors.base import PatternListDetector, PatternSpec, SecurityDetector


class ProviderPromptRiskDetector(PatternListDetector):
    """
    Heuristic prompt risk analysis aligned with OpenAI/Anthropic moderation categories.
    Uses pattern rules (no external API call) for deterministic, offline scanning.
    """

    detector_id = "llm_provider_risk"
    default_finding_type = "provider_risk"
    default_category = "provider_moderation"
    default_risk_category = "provider_risk"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\b(hate|harassment)\s+(speech|content)\b"),
                "high",
                "Hate/harassment category (provider-style)",
                "Content matches hate/harassment moderation category: «{matched}».",
                "Align with provider moderation API before production LLM calls.",
                risk_category="provider_risk",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(violence|violent)\s+(threat|act|content)\b"),
                "high",
                "Violence category (provider-style)",
                "Violence-related moderation signal: «{matched}».",
                "Route to provider moderation endpoint when API keys are configured.",
                risk_category="provider_risk",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(sexual|adult)\s+(content|material|services)\b"),
                "high",
                "Sexual content category (provider-style)",
                "Sexual content moderation signal: «{matched}».",
                "Enable provider content filters for adult content categories.",
                risk_category="provider_risk",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(self[- ]?harm|suicide)\b"),
                "critical",
                "Self-harm category (provider-style)",
                "Self-harm moderation signal (OpenAI/Anthropic class): «{matched}».",
                "Apply crisis resources and block generation per provider policy.",
                risk_category="provider_risk",
            ),
        )


class CompositeProviderRiskDetector(SecurityDetector):
    """
    Wraps provider-style heuristics and annotates findings with vendor analysis metadata.
    Extend with live OpenAI/Anthropic API calls when keys are present.
    """

    detector_id = "llm_provider_composite"
    default_finding_type = "provider_risk"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    def __init__(self) -> None:
        self._heuristic = ProviderPromptRiskDetector()

    def detect_with_context(self, context: ScanContext) -> list[SecurityFinding]:
        if not self.applies_to(context):
            return []
        findings = self._heuristic.detect_with_context(context)
        enriched: list[SecurityFinding] = []
        for f in findings:
            enriched.append(
                SecurityFinding(
                    type=f.type,
                    detector_id=f.detector_id,
                    category=f.category,
                    risk_category=f.risk_category,
                    severity=f.severity,
                    title=f.title,
                    description=f.description,
                    remediation=f.remediation,
                    confidence=f.confidence,
                    evidence={
                        **f.evidence,
                        "provider_analysis": {
                            "mode": "heuristic",
                            "vendors": ["openai", "anthropic"],
                            "note": "Rule-based proxy for moderation categories; "
                            "configure OPENAI_API_KEY or ANTHROPIC_API_KEY for live checks.",
                        },
                    },
                ),
            )
        return enriched
