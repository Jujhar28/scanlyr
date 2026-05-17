"""Backward-compatible re-export — prefer ``app.scan_security.services.engine``."""

from app.scan_security.services.engine import ENGINE_VERSION, run_security_scan

__all__ = ["ENGINE_VERSION", "run_security_scan"]
