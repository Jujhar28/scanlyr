"""Application startup hooks related to persistence (optional Alembic, checks)."""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations_subprocess() -> None:
    """
    Run `alembic upgrade head` in a subprocess.

    Intended for single-worker local/dev only. For production, prefer release-phase
    migrations (Railway) or `docker/entrypoint.sh` before starting uvicorn.
    """
    backend_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=backend_root,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        logger.error("Alembic upgrade failed: %s", result.stderr or result.stdout)
        raise RuntimeError("Database migrations failed")
    logger.info("Database migrations applied (alembic upgrade head)")
