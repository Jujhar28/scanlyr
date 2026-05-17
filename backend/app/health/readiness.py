"""Aggregate readiness: database, Alembic migrations, and critical local dependencies."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import ProgrammingError

from app.core.config import settings
from app.db.health import ping_database
from app.schemas.health import ReadinessCheck, ReadinessResponse

logger = logging.getLogger(__name__)


def _backend_root() -> Path:
    # app/health/readiness.py -> parents[2] == backend/
    return Path(__file__).resolve().parents[2]


def _alembic_script_directory() -> ScriptDirectory:
    ini_path = _backend_root() / "alembic.ini"
    cfg = Config(str(ini_path))
    return ScriptDirectory.from_config(cfg)


def _read_alembic_version_rows(engine: Engine) -> tuple[list[str] | None, str | None]:
    """Return (version_nums, error_message). None rows means could not read (table missing or DB down)."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            rows = [str(r[0]) for r in result.fetchall()]
            return rows, None
    except ProgrammingError as exc:
        return None, f"alembic_version not available: {exc}"
    except Exception as exc:
        logger.exception("Unexpected error reading alembic_version")
        return None, str(exc)


def _check_migrations(engine: Engine, *, database_ok: bool) -> ReadinessCheck:
    if not database_ok:
        return ReadinessCheck(
            status="skipped",
            message="Skipped because the database is not reachable.",
            details=None,
        )

    rows, err = _read_alembic_version_rows(engine)
    if err is not None:
        return ReadinessCheck(status="fail", message=err, details=None)
    if not rows:
        return ReadinessCheck(
            status="fail",
            message="No rows in alembic_version; run alembic upgrade head.",
            details={"current_revision": None},
        )
    if len(rows) > 1:
        return ReadinessCheck(
            status="fail",
            message="Multiple rows in alembic_version; resolve migration branches manually.",
            details={"revisions": rows},
        )

    current = rows[0]
    try:
        script = _alembic_script_directory()
        heads = script.get_heads()
    except Exception as exc:
        logger.exception("Failed to load Alembic scripts")
        return ReadinessCheck(
            status="unknown",
            message=f"Could not read migration scripts: {exc}",
            details={"current_revision": current},
        )

    at_head = current in heads
    details: dict[str, Any] = {"current_revision": current, "head_revisions": list(heads)}
    if at_head:
        return ReadinessCheck(
            status="pass",
            message="Database revision matches Alembic head.",
            details=details,
        )
    return ReadinessCheck(
        status="fail",
        message="Database is not at Alembic head; apply pending migrations.",
        details=details,
    )


def _check_report_storage() -> ReadinessCheck:
    try:
        root = Path(settings.report_storage_dir).expanduser()
        if not root.is_absolute():
            root = Path.cwd() / root
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".readiness_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return ReadinessCheck(
            status="pass",
            message="Report storage directory is writable.",
            details={"path": str(root)},
        )
    except OSError as exc:
        return ReadinessCheck(
            status="fail",
            message=f"Report storage is not usable: {exc}",
            details={"path": str(settings.report_storage_dir)},
        )


def _check_app_config() -> ReadinessCheck:
    env = settings.app_env.strip().lower()
    details: dict[str, Any] = {
        "app_env": env,
        "rate_limit_enabled": settings.rate_limit_enabled,
        "max_request_body_bytes": settings.max_request_body_bytes,
        "trust_proxy_headers": settings.trust_proxy_headers,
    }
    if settings.is_production and settings.debug:
        return ReadinessCheck(
            status="fail",
            message="DEBUG must be false in production.",
            details=details,
        )
    if settings.is_production and not settings.cors_origin_list:
        return ReadinessCheck(
            status="warn",
            message="CORS_ORIGINS is empty in production; browser clients may fail.",
            details=details,
        )
    return ReadinessCheck(status="pass", message="Application configuration OK.", details=details)


def _check_security() -> ReadinessCheck:
    key = settings.secret_key or ""
    if len(key) < 32:
        return ReadinessCheck(
            status="warn",
            message="SECRET_KEY is shorter than 32 characters; use a strong key in production.",
            details={"length": len(key)},
        )
    low = key.lower()
    if "change-me" in low or key == "secret":
        return ReadinessCheck(
            status="warn",
            message="SECRET_KEY appears to be a placeholder; rotate before production.",
            details=None,
        )
    return ReadinessCheck(status="pass", message="Secret key length OK.", details=None)


def assess_readiness(engine: Engine) -> tuple[ReadinessResponse, int]:
    """
    Evaluate readiness checks.

    Returns ``(ReadinessResponse, http_status)`` with ``http_status`` 200 if aggregate
    ``status`` is ``ready``, else 503.
    """
    checks: dict[str, ReadinessCheck] = {}

    db_ok = ping_database(engine)
    checks["database"] = ReadinessCheck(
        status="pass" if db_ok else "fail",
        message="PostgreSQL accepted a trivial query." if db_ok else "PostgreSQL is unreachable or query failed.",
        details=None,
    )

    checks["migrations"] = _check_migrations(engine, database_ok=db_ok)
    checks["report_storage"] = _check_report_storage() if db_ok else ReadinessCheck(
        status="skipped",
        message="Skipped because the database is not reachable.",
        details=None,
    )
    checks["security"] = _check_security()
    checks["app_config"] = _check_app_config()

    critical_ok = (
        checks["database"].status == "pass"
        and checks["migrations"].status == "pass"
        and checks["report_storage"].status == "pass"
    )
    has_warn = any(c.status == "warn" for c in checks.values())

    if not critical_ok:
        overall = "not_ready"
        http_status = 503
    elif has_warn:
        overall = "degraded"
        http_status = 200
    else:
        overall = "ready"
        http_status = 200

    body = ReadinessResponse(
        status=overall,
        critical_ok=critical_ok,
        checks=checks,
    )
    return body, http_status
