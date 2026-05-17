"""Orchestrates the modular security scanning engine for API and persistence layers."""

from __future__ import annotations

import logging

from app.core.config import get_settings
from app.scan_security.context import ContentKind
from app.scan_security.schemas.results import ScanAnalysisResult
from app.scan_security.services.engine import ENGINE_VERSION, run_security_scan
from app.scan_security.services.finding_refiner import ScanStrictness

logger = logging.getLogger(__name__)


def analyze_security_text(
    input_text: str,
    *,
    content_type: ContentKind = "auto",
) -> ScanAnalysisResult:
    """Run the production security scan engine and return structured analysis."""
    logger.info(
        "security_scan_requested",
        extra={
            "engine": ENGINE_VERSION,
            "content_type": content_type,
            "input_length": len(input_text),
        },
    )
    cfg = get_settings()
    strictness: ScanStrictness = cfg.scan_strictness  # type: ignore[assignment]
    return run_security_scan(input_text, content_type=content_type, strictness=strictness)
