from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SuspiciousUrlDetector(PatternListDetector):
    detector_id = "suspicious_urls"
    default_finding_type = "suspicious_link"
    default_category = "network"
    default_risk_category = "network"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\bhttps?://[^\s\"'<>]+"),
                "medium",
                "HTTP(S) URL present",
                "Outbound URL reference detected: «{matched}».",
                "Allow-list domains for agents; scan links with safe browsing APIs.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bhttps?://\d{1,3}(?:\.\d{1,3}){3}"),
                "high",
                "IP-literal URL",
                "URL uses raw IP address (often evasive): «{matched}».",
                "Block direct IP URLs unless explicitly approved.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(javascript|data|vbscript):[^\s\"']+"),
                "high",
                "Dangerous URL scheme",
                "Non-HTTP executable URL scheme: «{matched}».",
                "Strip javascript: and data: URLs from rendered content.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(bit\.ly|t\.co|tinyurl\.com|goo\.gl)/\w+"),
                "medium",
                "URL shortener",
                "Shortened URL may hide destination: «{matched}».",
                "Expand short links server-side before policy evaluation.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bcall\s+api\b"),
                "medium",
                "External API call intent",
                "Text suggests calling an external API: «{matched}».",
                "Document approved integrations; monitor egress from AI tools.",
            ),
        )
