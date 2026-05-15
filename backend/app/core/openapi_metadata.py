"""OpenAPI tag metadata for Swagger UI / ReDoc."""

OPENAPI_TAGS: list[dict[str, str]] = [
    {
        "name": "health",
        "description": "Liveness and readiness probes (orchestrator-friendly).",
    },
    {
        "name": "auth",
        "description": "Registration, login, JWT refresh, session context (`/me`).",
    },
    {
        "name": "detections",
        "description": "AI detection runs, events, and scan pipelines.",
    },
    {
        "name": "reports",
        "description": "Compliance PDF reports: generate, list, download.",
    },
    {
        "name": "integrations-microsoft",
        "description": "Microsoft 365 / Microsoft Graph OAuth and sync.",
    },
    {
        "name": "admin",
        "description": "Tenant-admin-only utilities (role enforced on the router).",
    },
]

API_DESCRIPTION = """
Scanlyr API — multi-tenant governance, shadow-AI detection, and compliance reporting.

**Auth:** Most `/api/v1/*` routes require `Authorization: Bearer <access_token>`.
Public paths include `/api/v1/auth/register`, `/api/v1/auth/login`, `/api/v1/auth/refresh`,
`/api/v1/health`, and the Microsoft OAuth callback.
"""

API_VERSION = "1.0.0"
