from pydantic import BaseModel, Field


class AdminPingResponse(BaseModel):
    """Minimal payload for admin smoke checks."""

    status: str = Field(..., examples=["ok"])
