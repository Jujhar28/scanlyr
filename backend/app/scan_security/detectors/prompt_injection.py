from __future__ import annotations

import re
from typing import ClassVar

from app.scan_security.context import ContentKind
from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class PromptInjectionDetector(PatternListDetector):
    detector_id = "prompt_injection"
    default_finding_type = "prompt_injection"
    default_category = "llm_abuse"
    default_risk_category = "jailbreak"
    supported_content: ClassVar[frozenset[ContentKind]] = frozenset({"auto", "prompt"})

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+(instructions|prompts)",
                ),
                "high",
                "Instruction override attempt",
                "Prompt injection: attempt to override prior instructions: «{matched}».",
                "Use system prompts with delimiter guards and output filtering.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(disregard|forget)\s+(your|the)\s+(rules|guidelines|policy)"),
                "high",
                "Policy bypass phrasing",
                "Language suggesting policy or rule bypass: «{matched}».",
                "Enable jailbreak classifiers and human review for high-risk flows.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(jailbreak|dan\s+mode|developer\s+mode)\b"),
                "high",
                "Known jailbreak keyword",
                "Known jailbreak terminology detected: «{matched}».",
                "Log and block known jailbreak phrases at the gateway.",
            ),
            PatternSpec(
                re.compile(r"(?i)you\s+are\s+now\s+(in\s+)?(unrestricted|uncensored)\s+mode"),
                "medium",
                "Role-play jailbreak",
                "Role reassignment to unrestricted mode: «{matched}».",
                "Constrain model role in a fixed system message; ignore user role claims.",
            ),
        )
