"""High-signal secret and token patterns (no bare keyword-only password hits)."""

from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class SecretsTokensDetector(PatternListDetector):
    detector_id = "secrets_tokens"
    default_finding_type = "secret_password"
    default_category = "secrets"
    default_risk_category = "credential_exposure"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(
                    r"(?i)\bbearer\s+([a-zA-Z0-9_\-\.]{20,})",
                ),
                "critical",
                "Bearer token value",
                "Non-redacted bearer token material present: «{matched}».",
                "Revoke the token immediately and avoid pasting into AI tools.",
                confidence=0.94,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)authorization:\s*bearer\s+([a-zA-Z0-9_\-\.]{20,})",
                ),
                "critical",
                "Authorization bearer header",
                "HTTP Authorization bearer value detected: «{matched}».",
                "Strip tokens from requests and rotate credentials.",
                confidence=0.95,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)(client[_-]?secret|access[_-]?token|refresh[_-]?token)\s*[:=]\s*"
                    r"['\"]?[a-zA-Z0-9_\-\.]{12,}",
                ),
                "high",
                "OAuth secret assignment",
                "OAuth client secret or token assigned inline: «{matched}».",
                "Use vault storage; never embed OAuth secrets in prompts or code snippets.",
                confidence=0.9,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)(api[_-]?secret|private[_-]?key|signing[_-]?key)\s*[:=]\s*"
                    r"['\"]?[a-zA-Z0-9_/+\-]{16,}",
                ),
                "high",
                "Signing secret assignment",
                "Inline signing or API secret assignment: «{matched}».",
                "Store signing keys in HSM or vault; never paste into chat interfaces.",
                confidence=0.9,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)password\s*[:=]\s*['\"]([^'\"]{6,})['\"]",
                ),
                "high",
                "Password literal assignment",
                "Quoted password literal in text: «{matched}».",
                "Remove hardcoded secrets; use environment variables or a secrets manager.",
                confidence=0.88,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)\b(?:password|passwd|pwd)\s+is\s+['\"]?([^\s'\",;]{4,})",
                ),
                "high",
                "Password disclosed in plain language",
                "Password value stated in plain text: «{matched}».",
                "Never share passwords in chat or tickets; rotate if this is a real credential.",
                confidence=0.87,
            ),
            PatternSpec(
                re.compile(
                    r"(?i)\b(?:password|passwd|pwd)\s*[:=]\s*['\"]?([a-zA-Z0-9!@#$%^&*._\-]{6,})",
                ),
                "high",
                "Password assignment",
                "Inline password assignment detected: «{matched}».",
                "Remove hardcoded secrets; use environment variables or a secrets manager.",
                confidence=0.86,
            ),
        )
