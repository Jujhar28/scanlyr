from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class HardcodedCredentialsDetector(PatternListDetector):
    detector_id = "hardcoded_credentials"
    default_finding_type = "hardcoded_credential"
    default_category = "credential_exposure"
    default_risk_category = "credential_exposure"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)(password|passwd|pwd)\s*=\s*['\"][^'\"]{4,}['\"]",
                ),
                "critical",
                "Hardcoded password literal",
                "Quoted password literal in text: «{matched}».",
                "Remove hardcoded secrets; use environment variables or a secrets manager.",
            ),
            PatternSpec(
                re.compile(
                    r"(?i)(username|user)\s*[:=]\s*['\"]?\w+['\"]?\s*[,;\s]+\s*(password|pwd)\s*[:=]",
                ),
                "critical",
                "Username/password pair",
                "Inline username and password pair detected: «{matched}».",
                "Rotate credentials and purge from repositories and chat logs.",
            ),
            PatternSpec(
                re.compile(
                    r"(?i)mongodb(\+srv)?://[^@\s\"']+:[^@\s\"']+@[^\s\"']+",
                ),
                "high",
                "Database connection string with credentials",
                "MongoDB URI with embedded username and password: «{matched}».",
                "Rotate DB credentials and restrict connection string distribution.",
            ),
        )
