from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class CommandInjectionDetector(PatternListDetector):
    detector_id = "command_injection"
    default_finding_type = "command_injection"
    default_category = "injection"
    default_risk_category = "injection"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i);\s*(rm\s+-rf|del\s+/|format\s+c:)"),
                "critical",
                "Chained destructive command",
                "Shell command chaining with destructive action: «{matched}».",
                "Never pass user text to a shell; use allow-listed subprocess arguments.",
            ),
            PatternSpec(
                re.compile(r"\$\([^)]+\)|`[^`]+`"),
                "high",
                "Command substitution",
                "Shell command substitution syntax detected: «{matched}».",
                "Disable shell interpolation; invoke programs with explicit argument arrays.",
            ),
            PatternSpec(
                re.compile(r"(?i)\|\s*(cat|type)\s+[/\\]etc[/\\]"),
                "high",
                "Pipe to sensitive file read",
                "Piped read of system paths: «{matched}».",
                "Sandbox file access and block path traversal in agents.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b&&\s*\w+"),
                "medium",
                "Shell command chaining",
                "Boolean command chaining (&&) detected: «{matched}».",
                "Reject metacharacters in inputs bound for system execution.",
            ),
        )
