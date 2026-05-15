import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.core.openapi_metadata import API_DESCRIPTION, API_VERSION, OPENAPI_TAGS
from app.core.public_api import collect_public_api_route_keys
from app.db.bootstrap import run_migrations_subprocess
from app.db.engine import engine
from app.db.health import ping_database
from app.health.readiness import assess_readiness
from app.schemas.health import HealthResponse, ReadinessResponse
from app.middleware.api_auth import APIAuthMiddleware
from app.middleware.request_id import RequestIDMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers.v1.api import api_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    if settings.run_db_migrations_on_startup:
        await asyncio.to_thread(run_migrations_subprocess)

    if not settings.db_skip_startup_ping:
        ok = await asyncio.to_thread(ping_database, engine)
        if not ok and settings.db_require_at_startup:
            raise RuntimeError("PostgreSQL is unreachable (set DB_SKIP_STARTUP_PING=1 only for diagnostics)")
        if not ok:
            logger.warning(
                "PostgreSQL ping failed at startup; process continues for /health — see /ready",
            )

    yield

    engine.dispose()


def create_application() -> FastAPI:
    application = FastAPI(
        title=settings.app_name,
        description=API_DESCRIPTION.strip(),
        version=API_VERSION,
        openapi_tags=OPENAPI_TAGS,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_openapi_docs else None,
        redoc_url="/redoc" if settings.enable_openapi_docs else None,
    )

    register_exception_handlers(application)

    application.include_router(api_router, prefix="/api/v1")

    @application.get(
        "/health",
        tags=["health"],
        response_model=HealthResponse,
        summary="Root liveness",
    )
    async def liveness() -> HealthResponse:
        """Process-level liveness (does not check PostgreSQL)."""
        return HealthResponse(status="ok")

    @application.get(
        "/ready",
        tags=["health"],
        response_model=ReadinessResponse,
        summary="Readiness probe",
        responses={
            503: {
                "description": "One or more critical checks failed (see `checks` and `critical_ok`).",
                "model": ReadinessResponse,
            },
        },
    )
    async def readiness() -> JSONResponse:
        """Readiness: database, Alembic migrations at head, report storage, and security hints."""
        payload, status_code = await asyncio.to_thread(assess_readiness, engine)
        return JSONResponse(status_code=status_code, content=payload.model_dump())

    public_route_keys = collect_public_api_route_keys(application)
    if ("POST", "/api/v1/auth/login") not in public_route_keys:
        raise RuntimeError(
            "Auth middleware public route set is empty or missing login; "
            "check @public_api_route on public /api/v1 handlers.",
        )

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(APIAuthMiddleware, public_route_keys=public_route_keys)
    application.add_middleware(RequestIDMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return application


app = create_application()
