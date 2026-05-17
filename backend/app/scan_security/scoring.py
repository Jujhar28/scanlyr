"""Backward-compatible re-export — prefer ``app.scan_security.services.scoring``."""

from app.scan_security.services.scoring import aggregate_findings, risk_level_from_score

__all__ = ["aggregate_findings", "risk_level_from_score"]
