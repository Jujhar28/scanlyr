from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class PhishingIndicatorDetector(PatternListDetector):
    detector_id = "phishing"
    default_finding_type = "phishing_url"
    default_category = "social_engineering"
    default_risk_category = "social_engineering"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"(?i)\b(verify|confirm)\s+your\s+(account|identity|password)\b"),
                "medium",
                "Account verification lure",
                "Phishing-style account verification language: «{matched}».",
                "Train users on credential phishing; validate sender domains.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(urgent|immediate)\s+(action|response)\s+required\b"),
                "medium",
                "Urgency pressure",
                "Urgency pressure common in phishing: «{matched}».",
                "Treat urgent financial or login requests as suspicious.",
            ),
            PatternSpec(
                re.compile(r"(?i)\bclick\s+(here|this\s+link)\s+(now|immediately)\b"),
                "medium",
                "Clickbait call to action",
                "Aggressive link click prompt: «{matched}».",
                "Hover links and use email security gateways before clicking.",
            ),
            PatternSpec(
                re.compile(r"(?i)\b(wire\s+transfer|gift\s+card|bitcoin)\s+(payment|urgent)"),
                "high",
                "Financial fraud indicator",
                "Financial fraud phrasing detected: «{matched}».",
                "Verify payment requests via a second channel; report to security.",
            ),
        )
