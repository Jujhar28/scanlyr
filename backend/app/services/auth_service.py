from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token_value,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.enums import MembershipStatus, OrganizationStatus
from app.models.membership import Membership
from app.models.organization import Organization
from app.models.refresh_token import RefreshToken
from app.models.role import Role
from app.models.user import User
from app.schemas.auth import (
    AuthSessionResponse,
    LoginRequest,
    MeResponse,
    OrganizationSummary,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
    UserSummary,
)
from app.services.security_audit_service import record_security_audit
from app.utils.slug import slugify


DEFAULT_ROLES: tuple[tuple[str, str, bool], ...] = (
    ("admin", "Administrator", True),
    ("analyst", "Analyst", True),
    ("viewer", "Viewer", True),
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _issue_tokens(*, user: User, organization: Organization, role_slug: str) -> TokenPairResponse:
    expires_in = int(timedelta(minutes=settings.access_token_expire_minutes).total_seconds())
    access = create_access_token(
        str(user.id),
        additional_claims={
            "org_id": str(organization.id),
            "role": role_slug,
        },
    )
    refresh_plain = generate_refresh_token_value()
    return TokenPairResponse(
        access_token=access,
        refresh_token=refresh_plain,
        expires_in=expires_in,
    )


def _persist_refresh_token(
    session: Session,
    *,
    user: User,
    raw_refresh: str,
    user_agent: str | None,
    ip_address: str | None,
) -> None:
    expires_at = datetime.now(tz=UTC) + timedelta(days=settings.refresh_token_expire_days)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(raw_refresh),
            expires_at=expires_at,
            user_agent=user_agent,
            ip_address=ip_address,
        )
    )


def _seed_org_roles(session: Session, organization: Organization) -> None:
    for slug, name, is_system in DEFAULT_ROLES:
        session.add(
            Role(
                organization_id=organization.id,
                slug=slug,
                name=name,
                description=None,
                is_system=is_system,
            )
        )


def _unique_org_slug(session: Session, desired: str) -> str:
    base = slugify(desired)
    candidate = base
    suffix = 0
    while True:
        exists = session.execute(
            select(Organization.id).where(Organization.slug == candidate).limit(1)
        ).scalar_one_or_none()
        if exists is None:
            return candidate
        suffix += 1
        extra = f"-{suffix}"
        candidate = f"{base[: max(1, 96 - len(extra))]}{extra}"


def register(
    session: Session,
    payload: RegisterRequest,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthSessionResponse:
    email = _normalize_email(str(payload.email))
    existing = session.execute(select(User.id).where(User.email == email).limit(1)).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    slug_source = payload.organization_slug or payload.organization_name
    org_slug = _unique_org_slug(session, slug_source)

    organization = Organization(
        name=payload.organization_name.strip(),
        slug=org_slug,
        status=OrganizationStatus.active.value,
        settings=None,
    )
    session.add(organization)
    session.flush()

    _seed_org_roles(session, organization)
    session.flush()

    admin_role = session.execute(
        select(Role).where(Role.organization_id == organization.id, Role.slug == "admin").limit(1)
    ).scalar_one()

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name.strip() if payload.full_name else None,
        is_active=True,
        is_platform_admin=False,
    )
    session.add(user)
    session.flush()

    session.add(
        Membership(
            organization_id=organization.id,
            user_id=user.id,
            role_id=admin_role.id,
            status=MembershipStatus.active.value,
        )
    )

    tokens = _issue_tokens(user=user, organization=organization, role_slug=admin_role.slug)
    _persist_refresh_token(
        session,
        user=user,
        raw_refresh=tokens.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    record_security_audit(
        session,
        action="auth.register",
        organization_id=organization.id,
        actor_user_id=user.id,
        resource_type="user",
        resource_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.commit()
    session.refresh(user)
    session.refresh(organization)

    return AuthSessionResponse(
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
        organization=OrganizationSummary(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
        ),
        role=admin_role.slug,
        tokens=tokens,
    )


def login(
    session: Session,
    payload: LoginRequest,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthSessionResponse:
    email = _normalize_email(str(payload.email))
    user = session.execute(select(User).where(User.email == email).limit(1)).scalar_one_or_none()
    if user is None or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    membership: Membership
    role: Role
    organization: Organization

    if payload.organization_id is not None:
        row = session.execute(
            select(Membership, Role)
            .join(Role, Role.id == Membership.role_id)
            .where(
                Membership.user_id == user.id,
                Membership.organization_id == payload.organization_id,
                Membership.status == MembershipStatus.active.value,
            )
            .limit(1)
        ).one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active membership for the selected organization",
            )
        membership, role = row
        organization = session.get(Organization, membership.organization_id)
        if organization is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Organization missing",
            )
    else:
        row = session.execute(
            select(Membership, Role, Organization)
            .join(Role, Role.id == Membership.role_id)
            .join(Organization, Organization.id == Membership.organization_id)
            .where(
                Membership.user_id == user.id,
                Membership.status == MembershipStatus.active.value,
            )
            .order_by(Membership.created_at.asc())
            .limit(1)
        ).one_or_none()
        if row is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not assigned to any organization",
            )
        membership, role, organization = row

    user.last_login_at = datetime.now(tz=UTC)

    tokens = _issue_tokens(user=user, organization=organization, role_slug=role.slug)
    _persist_refresh_token(
        session,
        user=user,
        raw_refresh=tokens.refresh_token,
        user_agent=user_agent,
        ip_address=ip_address,
    )

    record_security_audit(
        session,
        action="auth.login",
        organization_id=organization.id,
        actor_user_id=user.id,
        resource_type="session",
        resource_id=str(user.id),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.commit()
    session.refresh(user)
    session.refresh(organization)

    return AuthSessionResponse(
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
        organization=OrganizationSummary(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
        ),
        membership_status=membership.status,
        role=role.slug,
        tokens=tokens,
    )


def _revoke_all_refresh_tokens(session: Session, user_id: uuid.UUID, *, now: datetime) -> None:
    session.execute(
        update(RefreshToken)
        .where(RefreshToken.user_id == user_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )


def refresh_session(
    session: Session,
    payload: RefreshRequest,
    *,
    user_agent: str | None,
    ip_address: str | None,
) -> AuthSessionResponse:
    token_hash = hash_refresh_token(payload.refresh_token)
    row = session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    now = datetime.now(tz=UTC)
    if row.revoked_at is not None:
        _revoke_all_refresh_tokens(session, row.user_id, now=now)
        record_security_audit(
            session,
            action="auth.refresh_token_reuse",
            actor_user_id=row.user_id,
            resource_type="session",
            resource_id=str(row.id),
            payload={"reason": "revoked_token_reused"},
            ip_address=ip_address,
            user_agent=user_agent,
        )
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token reuse detected; all sessions revoked",
        )
    if row.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or revoked")

    user = session.get(User, row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not available")

    membership_row = session.execute(
        select(Membership, Role, Organization)
        .join(Role, Role.id == Membership.role_id)
        .join(Organization, Organization.id == Membership.organization_id)
        .where(
            Membership.user_id == user.id,
            Membership.status == MembershipStatus.active.value,
        )
        .order_by(Membership.created_at.asc())
        .limit(1)
    ).one_or_none()
    if membership_row is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No active organization context")

    membership, role, organization = membership_row

    row.revoked_at = now
    new_tokens = _issue_tokens(user=user, organization=organization, role_slug=role.slug)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(new_tokens.refresh_token),
            expires_at=now + timedelta(days=settings.refresh_token_expire_days),
            user_agent=user_agent,
            ip_address=ip_address,
            rotated_from_id=row.id,
        )
    )

    record_security_audit(
        session,
        action="auth.refresh",
        organization_id=organization.id,
        actor_user_id=user.id,
        resource_type="session",
        resource_id=str(row.id),
        ip_address=ip_address,
        user_agent=user_agent,
    )
    session.commit()
    session.refresh(user)
    session.refresh(organization)

    return AuthSessionResponse(
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
        organization=OrganizationSummary(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
        ),
        membership_status=membership.status,
        role=role.slug,
        tokens=new_tokens,
    )


def logout(session: Session, user: User, refresh_token: str | None, revoke_all: bool) -> None:
    if revoke_all:
        _revoke_all_refresh_tokens(session, user.id, now=datetime.now(tz=UTC))
        record_security_audit(
            session,
            action="auth.logout_all",
            actor_user_id=user.id,
            resource_type="session",
            resource_id=str(user.id),
        )
        session.commit()
        return

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="refresh_token is required unless revoke_all is true",
        )

    token_hash = hash_refresh_token(refresh_token)
    row = session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).limit(1)
    ).scalar_one_or_none()
    if row is None or row.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown refresh token")

    row.revoked_at = datetime.now(tz=UTC)
    record_security_audit(
        session,
        action="auth.logout",
        actor_user_id=user.id,
        resource_type="session",
        resource_id=str(row.id),
    )
    session.commit()


def build_me_response(session: Session, user: User, payload: dict) -> MeResponse:
    org_id = payload.get("org_id")
    if not org_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization context missing in token")

    organization = session.get(Organization, uuid.UUID(str(org_id)))
    if organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Organization not found")

    role_slug = str(payload.get("role") or "")
    membership = session.execute(
        select(Membership, Role)
        .join(Role, Role.id == Membership.role_id)
        .where(
            Membership.user_id == user.id,
            Membership.organization_id == organization.id,
            Membership.status == MembershipStatus.active.value,
        )
        .limit(1)
    ).one_or_none()
    if membership is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Membership is no longer valid")

    _membership_obj, role = membership
    if role.slug != role_slug:
        role_slug = role.slug

    return MeResponse(
        user=UserSummary(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
        ),
        organization=OrganizationSummary(
            id=organization.id,
            name=organization.name,
            slug=organization.slug,
        ),
        role=role_slug,
    )
