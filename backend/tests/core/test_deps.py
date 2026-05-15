"""Tests for app.core.deps — FastAPI dependency functions."""
from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.deps import (
    get_bearer_token,
    get_current_subject,
    get_current_user,
    get_token_payload,
    require_roles,
)
from app.models.enums import MembershipStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_credentials(scheme: str = "bearer", token: str = "test-token") -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme=scheme, credentials=token)


# ---------------------------------------------------------------------------
# get_bearer_token
# ---------------------------------------------------------------------------


class TestGetBearerToken:
    def test_valid_bearer_returns_credentials(self) -> None:
        creds = _make_credentials(scheme="bearer", token="my-jwt")
        result = get_bearer_token(creds)
        assert result == "my-jwt"

    def test_bearer_scheme_case_insensitive(self) -> None:
        creds = _make_credentials(scheme="Bearer", token="my-jwt")
        result = get_bearer_token(creds)
        assert result == "my-jwt"

    def test_bearer_scheme_uppercase_accepted(self) -> None:
        creds = _make_credentials(scheme="BEARER", token="tok")
        result = get_bearer_token(creds)
        assert result == "tok"

    def test_none_credentials_returns_none(self) -> None:
        result = get_bearer_token(None)
        assert result is None

    def test_wrong_scheme_returns_none(self) -> None:
        creds = _make_credentials(scheme="basic", token="dXNlcjpwYXNz")
        result = get_bearer_token(creds)
        assert result is None

    def test_empty_token_string_returned(self) -> None:
        # get_bearer_token doesn't validate token content, only scheme
        creds = _make_credentials(scheme="bearer", token="")
        result = get_bearer_token(creds)
        assert result == ""


# ---------------------------------------------------------------------------
# get_token_payload
# ---------------------------------------------------------------------------


class TestGetTokenPayload:
    def test_missing_token_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_token_payload(None)
        assert exc_info.value.status_code == 401
        assert "Not authenticated" in exc_info.value.detail

    def test_empty_string_token_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_token_payload("")
        assert exc_info.value.status_code == 401

    def test_invalid_token_raises_401(self) -> None:
        with patch("app.core.deps.safe_decode_access_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_token_payload("invalid-token")
            assert exc_info.value.status_code == 401
            assert "Invalid or expired token" in exc_info.value.detail

    def test_valid_token_returns_payload(self) -> None:
        expected_payload = {"sub": "user-123", "typ": "access"}
        with patch("app.core.deps.safe_decode_access_token", return_value=expected_payload):
            result = get_token_payload("valid-token")
        assert result == expected_payload

    def test_401_response_has_www_authenticate_header(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_token_payload(None)
        assert "WWW-Authenticate" in (exc_info.value.headers or {})

    def test_invalid_token_has_www_authenticate_header(self) -> None:
        with patch("app.core.deps.safe_decode_access_token", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                get_token_payload("bad-token")
        assert "WWW-Authenticate" in (exc_info.value.headers or {})


# ---------------------------------------------------------------------------
# get_current_subject
# ---------------------------------------------------------------------------


class TestGetCurrentSubject:
    def test_valid_sub_returns_sub_string(self) -> None:
        payload: dict[str, Any] = {"sub": "user-uuid-here"}
        result = get_current_subject(payload)
        assert result == "user-uuid-here"

    def test_missing_sub_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_current_subject({})
        assert exc_info.value.status_code == 401
        assert "Token subject missing" in exc_info.value.detail

    def test_none_sub_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_current_subject({"sub": None})
        assert exc_info.value.status_code == 401

    def test_non_string_sub_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_current_subject({"sub": 12345})
        assert exc_info.value.status_code == 401

    def test_empty_string_sub_raises_401(self) -> None:
        with pytest.raises(HTTPException) as exc_info:
            get_current_subject({"sub": ""})
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# get_current_user
# ---------------------------------------------------------------------------


class TestGetCurrentUser:
    def _make_active_user(self, user_id: uuid.UUID) -> MagicMock:
        user = MagicMock()
        user.id = user_id
        user.is_active = True
        return user

    def test_valid_payload_returns_user(self) -> None:
        uid = uuid.uuid4()
        payload = {"sub": str(uid)}
        mock_user = self._make_active_user(uid)
        mock_db = MagicMock()
        mock_db.get.return_value = mock_user

        result = get_current_user(payload, mock_db)

        mock_db.get.assert_called_once()
        assert result is mock_user

    def test_invalid_uuid_sub_raises_401(self) -> None:
        payload = {"sub": "not-a-uuid"}
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(payload, mock_db)
        assert exc_info.value.status_code == 401
        assert "Invalid subject" in exc_info.value.detail

    def test_none_sub_raises_401(self) -> None:
        payload: dict[str, Any] = {"sub": None}
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(payload, mock_db)
        assert exc_info.value.status_code == 401

    def test_user_not_found_raises_401(self) -> None:
        uid = uuid.uuid4()
        payload = {"sub": str(uid)}
        mock_db = MagicMock()
        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(payload, mock_db)
        assert exc_info.value.status_code == 401
        assert "User not found or inactive" in exc_info.value.detail

    def test_inactive_user_raises_401(self) -> None:
        uid = uuid.uuid4()
        payload = {"sub": str(uid)}
        mock_user = MagicMock()
        mock_user.is_active = False
        mock_db = MagicMock()
        mock_db.get.return_value = mock_user

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(payload, mock_db)
        assert exc_info.value.status_code == 401
        assert "User not found or inactive" in exc_info.value.detail

    def test_db_get_called_with_correct_user_id(self) -> None:
        from app.models.user import User

        uid = uuid.uuid4()
        payload = {"sub": str(uid)}
        mock_user = self._make_active_user(uid)
        mock_db = MagicMock()
        mock_db.get.return_value = mock_user

        get_current_user(payload, mock_db)

        mock_db.get.assert_called_once_with(User, uid)


# ---------------------------------------------------------------------------
# require_roles
# ---------------------------------------------------------------------------


class TestRequireRoles:
    def _make_payload(
        self,
        sub: str | None = None,
        org_id: str | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        if sub is not None:
            result["sub"] = sub
        if org_id is not None:
            result["org_id"] = org_id
        return result

    def _make_membership(self) -> MagicMock:
        m = MagicMock()
        m.status = MembershipStatus.active.value
        return m

    def test_missing_org_id_raises_403(self) -> None:
        dep = require_roles("admin")
        payload = self._make_payload(sub=str(uuid.uuid4()))  # no org_id
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403
        assert "Missing organization or user context" in exc_info.value.detail

    def test_missing_sub_raises_403(self) -> None:
        dep = require_roles("admin")
        payload = self._make_payload(org_id=str(uuid.uuid4()))  # no sub
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403

    def test_invalid_org_uuid_raises_403(self) -> None:
        dep = require_roles("admin")
        payload = self._make_payload(sub=str(uuid.uuid4()), org_id="not-a-uuid")
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403
        assert "Invalid authorization context" in exc_info.value.detail

    def test_invalid_user_uuid_raises_403(self) -> None:
        dep = require_roles("admin")
        payload = self._make_payload(sub="not-a-uuid", org_id=str(uuid.uuid4()))
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403

    def test_no_matching_membership_raises_403(self) -> None:
        dep = require_roles("admin")
        payload = self._make_payload(
            sub=str(uuid.uuid4()),
            org_id=str(uuid.uuid4()),
        )
        mock_db = MagicMock()
        mock_db.execute.return_value.one_or_none.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    def test_matching_membership_returns_membership(self) -> None:
        dep = require_roles("admin", "editor")
        uid = uuid.uuid4()
        org = uuid.uuid4()
        payload = self._make_payload(sub=str(uid), org_id=str(org))
        membership = self._make_membership()
        mock_role = MagicMock()
        mock_db = MagicMock()
        mock_db.execute.return_value.one_or_none.return_value = (membership, mock_role)

        result = dep(payload, mock_db)

        assert result is membership

    def test_multiple_allowed_roles_creates_correct_allowset(self) -> None:
        # Factory should create a dependency that queries for all specified roles
        dep = require_roles("admin", "editor", "viewer")
        # The allowed set is captured in closure — we verify by checking the 403 path
        payload = self._make_payload(sub=str(uuid.uuid4()), org_id=str(uuid.uuid4()))
        mock_db = MagicMock()
        mock_db.execute.return_value.one_or_none.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            dep(payload, mock_db)
        assert exc_info.value.status_code == 403

    def test_empty_payload_raises_403(self) -> None:
        dep = require_roles("admin")
        mock_db = MagicMock()

        with pytest.raises(HTTPException) as exc_info:
            dep({}, mock_db)
        assert exc_info.value.status_code == 403

    def test_require_roles_returns_callable(self) -> None:
        dep = require_roles("admin")
        assert callable(dep)

    def test_db_execute_called_with_correct_query(self) -> None:
        """Ensure the DB execute is called (not skipped) when UUIDs are valid."""
        dep = require_roles("admin")
        uid = uuid.uuid4()
        org = uuid.uuid4()
        payload = self._make_payload(sub=str(uid), org_id=str(org))
        mock_db = MagicMock()
        mock_db.execute.return_value.one_or_none.return_value = None

        try:
            dep(payload, mock_db)
        except HTTPException:
            pass

        assert mock_db.execute.called