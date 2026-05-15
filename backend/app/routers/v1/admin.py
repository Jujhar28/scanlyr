from fastapi import APIRouter

from app.schemas.admin import AdminPingResponse

router = APIRouter()


@router.get(
    "/ping",
    response_model=AdminPingResponse,
    summary="Admin ping",
    description="Smoke check for authenticated admin users (router enforces the admin role).",
)
async def admin_ping() -> AdminPingResponse:
    return AdminPingResponse(status="ok")
