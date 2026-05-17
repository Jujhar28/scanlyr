from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class JwtExposureDetector(PatternListDetector):
    detector_id = "jwt_exposure"
    default_finding_type = "jwt_token"
    default_category = "credential_exposure"
    default_risk_category = "credential_exposure"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b",
                ),
                "critical",
                "JWT token exposed",
                "JSON Web Token structure detected in text: «{matched}».",
                "Revoke the token, rotate signing keys, and never paste JWTs into prompts or logs.",
                finding_type="jwt_token",
                confidence=0.95,
            ),
            PatternSpec(
                re.compile(r"(?i)\b(jwt|id[_-]?token)\s*[:=]\s*['\"]?eyJ[a-zA-Z0-9_-]{8,}"),
                "critical",
                "JWT assignment",
                "JWT or ID token assignment in plaintext: «{matched}».",
                "Store tokens in secure cookies or headers; redact from application logs.",
                finding_type="jwt_token",
            ),
            PatternSpec(
                re.compile(r"(?i)\bauthorization:\s*eyJ[a-zA-Z0-9_-]{8,}"),
                "critical",
                "Authorization header JWT",
                "Raw JWT in Authorization header text: «{matched}».",
                "Use short-lived tokens and transport only over TLS; rotate if exposed.",
                finding_type="jwt_token",
            ),
        )
