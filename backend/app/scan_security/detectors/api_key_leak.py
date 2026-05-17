from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class ApiKeyLeakDetector(PatternListDetector):
    detector_id = "api_key_leak"
    default_finding_type = "api_key_leak"
    default_category = "credential_exposure"
    default_risk_category = "credential_exposure"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
                "critical",
                "AWS access key identifier",
                "Text contains a pattern matching an AWS access key id (AKIA…): «{matched}».",
                "Rotate the key immediately, revoke in IAM, and scan git history for leaks.",
            ),
            PatternSpec(
                re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"),
                "critical",
                "OpenAI-style API secret",
                "Text resembles an OpenAI API key prefix (sk-…): «{matched}».",
                "Revoke the key in the provider console and issue a new secret.",
            ),
            PatternSpec(
                re.compile(
                    r"(?i)(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{16,}",
                ),
                "high",
                "Embedded API key assignment",
                "Literal API key assignment detected: «{matched}».",
                "Remove secrets from source; load from a vault or environment at runtime.",
            ),
            PatternSpec(
                re.compile(r"\bghp_[a-zA-Z0-9]{36,}\b"),
                "critical",
                "GitHub personal access token",
                "GitHub PAT pattern (ghp_…) detected: «{matched}».",
                "Revoke the token on GitHub and audit repository access.",
            ),
        )
