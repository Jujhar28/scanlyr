"""PEM-encoded private key material."""

from __future__ import annotations

import re

from app.scan_security.detectors.base import PatternListDetector, PatternSpec


class PrivateKeyPemDetector(PatternListDetector):
    detector_id = "private_key_pem"
    default_finding_type = "private_key_exposure"
    default_category = "credential_exposure"
    default_risk_category = "credential_exposure"

    @property
    def patterns(self) -> tuple[PatternSpec, ...]:
        return (
            PatternSpec(
                re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
                "critical",
                "Private key (PEM)",
                "PEM private key block detected in text.",
                "Revoke associated certificates, rotate keys, and purge from chat logs and repos.",
                confidence=0.97,
            ),
            PatternSpec(
                re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----"),
                "critical",
                "PGP private key",
                "PGP private key block detected in text.",
                "Treat as compromised; rotate and remove from shared channels.",
                confidence=0.96,
            ),
        )
