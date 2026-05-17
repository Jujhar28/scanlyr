from fastapi import APIRouter, Depends

from app.core.deps import require_roles
from app.routers.v1 import admin, auth, detections, health, integrations_microsoft, reports, scan, scans

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(integrations_microsoft.router)
api_router.include_router(detections.router)
api_router.include_router(scan.router)
api_router.include_router(scans.router)
api_router.include_router(reports.router)

admin_router = APIRouter(dependencies=[Depends(require_roles("admin"))])
admin_router.include_router(admin.router, tags=["admin"])
api_router.include_router(admin_router, prefix="/admin")
