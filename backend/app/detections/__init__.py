"""Shadow AI detection: rule engine, Microsoft normalization, scoring (ML-ready)."""

from app.detections.engine import run_engine_on_events, run_rule_engine

__all__ = ["run_rule_engine", "run_engine_on_events"]
