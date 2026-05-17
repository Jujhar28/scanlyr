from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import MembershipStatus


class RegisterRequest(BaseModel):
    organization_name: str = Field(min_length=2, max_length=255)
    organization_slug: str | None = Field(default=None, max_length=128)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=255)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v) or not any(c.isalpha() for c in v):
            raise ValueError("Password must include letters and numbers")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)
    organization_id: uuid.UUID | None = None


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=10, max_length=512)


class LogoutRequest(BaseModel):
    refresh_token: str | None = None
    revoke_all: bool = False


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class OrganizationSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class UserSummary(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool


class AuthSessionResponse(BaseModel):
    user: UserSummary
    organization: OrganizationSummary
    membership_status: str = MembershipStatus.active.value
    role: str
    tokens: TokenPairResponse


class MeResponse(BaseModel):
    user: UserSummary
    organization: OrganizationSummary
    role: str
