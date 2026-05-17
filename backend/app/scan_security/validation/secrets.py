"""Classify how strongly a matched substring resembles a real secret."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from app.scan_security.validation.entropy import is_placeholder_value, looks_like_secret_material

# Provider-specific high-confidence formats (industry common prefixes).
_KNOWN_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_access_key"),
    (re.compile(r"\bsk-[a-zA-Z0-9]{20,}\b"), "openai_api_key"),
    (re.compile(r"\bsk-proj-[a-zA-Z0-9_-]{20,}\b"), "openai_project_key"),
    (re.compile(r"\bghp_[a-zA-Z0-9]{36,}\b"), "github_pat"),
    (re.compile(r"\bgho_[a-zA-Z0-9]{36,}\b"), "github_oauth"),
    (re.compile(r"\bxox[baprs]-[0-9a-zA-Z-]{10,}\b"), "slack_token"),
    (re.compile(r"\bAIza[0-9A-Za-z\-_]{35}\b"), "google_api_key"),
    (re.compile(r"\beyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b"), "jwt_compact"),
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"), "private_key_pem"),
)


class SecretStrength(str, Enum):
    confirmed = "confirmed"
    likely = "likely"
    weak = "weak"
    benign = "benign"


@dataclass(frozen=True)
class SecretClassification:
    strength: SecretStrength
    kind: str | None = None
    confidence_multiplier: float = 1.0


def classify_secret_match(matched: str, *, finding_type: str | None = None) -> SecretClassification:
    text = matched.strip()
    if not text:
        return SecretClassification(SecretStrength.benign, confidence_multiplier=0.2)

    for pattern, kind in _KNOWN_SECRET_PATTERNS:
        if pattern.search(text):
            return SecretClassification(
                SecretStrength.confirmed,
                kind=kind,
                confidence_multiplier=1.0,
            )

    if is_placeholder_value(text):
        return SecretClassification(SecretStrength.benign, confidence_multiplier=0.15)

    assignment = re.search(
        r"(?i)(password|passwd|api[_-]?key|secret|token)\s*[:=]\s*['\"]?([^'\"\s]{4,})",
        text,
    )
    if assignment:
        value = assignment.group(2)
        if is_placeholder_value(value):
            return SecretClassification(SecretStrength.benign, confidence_multiplier=0.2)
        if looks_like_secret_material(value):
            return SecretClassification(
                SecretStrength.likely,
                kind="assigned_secret",
                confidence_multiplier=0.88,
            )
        return SecretClassification(SecretStrength.weak, confidence_multiplier=0.45)

    if looks_like_secret_material(text):
        return SecretClassification(
            SecretStrength.likely,
            kind="high_entropy_blob",
            confidence_multiplier=0.82,
        )

    pwd_is = re.search(
        r"(?i)\b(?:password|passwd|pwd)\s+is\s+['\"]?([^\s'\",;]{4,})",
        text,
    )
    if pwd_is:
        disclosed = pwd_is.group(1).strip().strip("\"'")
        if is_placeholder_value(disclosed):
            return SecretClassification(
                SecretStrength.benign,
                kind="example_password",
                confidence_multiplier=0.12,
            )
        if looks_like_secret_material(disclosed):
            return SecretClassification(
                SecretStrength.likely,
                kind="disclosed_password",
                confidence_multiplier=0.88,
            )
        return SecretClassification(
            SecretStrength.weak,
            kind="disclosed_password",
            confidence_multiplier=0.45,
        )

    if finding_type == "secret_password" and re.search(r"(?i)\b(password|passwd|pwd)\b", text):
        return SecretClassification(SecretStrength.weak, confidence_multiplier=0.35)

    return SecretClassification(SecretStrength.weak, confidence_multiplier=0.5)
