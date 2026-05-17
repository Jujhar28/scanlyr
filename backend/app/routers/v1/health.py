from fastapi import APIRouter

from app.core.public_api import public_api_route
from app.schemas.health import HealthResponse

router = APIRouter()


@router.api_route(
    "/health",
    methods=["GET", "HEAD"],
    response_model=HealthResponse,
    summary="API liveness",
    description="Lightweight health check under `/api/v1` (process up; does not verify database).",
)
@public_api_route
async def health() -> HealthResponse:
    return HealthResponse(status="ok")
