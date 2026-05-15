"""Tests for app.core.errors — error helpers and exception handlers."""
from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.authentication import AuthenticationError

from app.core.errors import (
    ErrorResponse,
    _code_for_http_status,
    _http_exception_message,
    error_payload,
    register_exception_handlers,
)
from app.integrations.microsoft_graph.errors import (
    MicrosoftGraphApiError,
    MicrosoftGraphIntegrationError,
    MicrosoftGraphNotConfiguredError,
    MicrosoftGraphOAuthError,
)
from app.services.compliance_report_service import ComplianceReportError
from app.services.shadow_ai_detection_service import ShadowAIDetectionError


# ---------------------------------------------------------------------------
# ErrorResponse model
# ---------------------------------------------------------------------------


class TestErrorResponse:
    def test_basic_construction(self) -> None:
        r = ErrorResponse(code="not_found", message="Not found")
        assert r.code == "not_found"
        assert r.message == "Not found"
        assert r.details is None
        assert r.request_id is None

    def test_with_details(self) -> None:
        r = ErrorResponse(code="validation_error", message="Bad input", details={"field": "name"})
        assert r.details == {"field": "name"}

    def test_with_request_id(self) -> None:
        r = ErrorResponse(code="http_error", message="Error", request_id="req-123")
        assert r.request_id == "req-123"

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises((ValidationError, Exception)):
            ErrorResponse(code="x", message="y", unexpected_field="z")  # type: ignore[call-arg]

    def test_model_dump_contains_all_fields(self) -> None:
        r = ErrorResponse(code="test", message="msg", details=None, request_id=None)
        dumped = r.model_dump()
        assert "code" in dumped
        assert "message" in dumped
        assert "details" in dumped
        assert "request_id" in dumped


# ---------------------------------------------------------------------------
# _code_for_http_status
# ---------------------------------------------------------------------------


class TestCodeForHttpStatus:
    @pytest.mark.parametrize(
        "status_code, expected_code",
        [
            (401, "authentication_error"),
            (403, "authorization_error"),
            (404, "not_found"),
            (405, "method_not_allowed"),
            (409, "conflict"),
            (413, "payload_too_large"),
            (429, "rate_limited"),
        ],
    )
    def test_known_status_codes(self, status_code: int, expected_code: str) -> None:
        assert _code_for_http_status(status_code) == expected_code

    @pytest.mark.parametrize("status_code", [400, 500, 503, 502, 418])
    def test_unknown_status_codes_return_http_error(self, status_code: int) -> None:
        assert _code_for_http_status(status_code) == "http_error"

    def test_200_returns_http_error(self) -> None:
        assert _code_for_http_status(200) == "http_error"


# ---------------------------------------------------------------------------
# _http_exception_message
# ---------------------------------------------------------------------------


class TestHttpExceptionMessage:
    def test_string_detail_returns_detail_and_none(self) -> None:
        msg, details = _http_exception_message("Not found")
        assert msg == "Not found"
        assert details is None

    def test_list_detail_returns_request_error(self) -> None:
        items = [{"loc": ["body"], "msg": "required"}]
        msg, details = _http_exception_message(items)
        assert msg == "Request error"
        assert details == {"detail": items}

    def test_dict_with_message_key(self) -> None:
        msg, details = _http_exception_message({"message": "Custom error", "extra": "data"})
        assert msg == "Custom error"
        assert details == {"extra": "data"}

    def test_dict_with_msg_key(self) -> None:
        msg, details = _http_exception_message({"msg": "Field required"})
        assert msg == "Field required"
        assert details is None

    def test_dict_message_preferred_over_msg(self) -> None:
        msg, details = _http_exception_message({"message": "preferred", "msg": "not this"})
        assert msg == "preferred"

    def test_dict_without_message_or_msg_returns_request_error(self) -> None:
        msg, details = _http_exception_message({"code": 123})
        assert msg == "Request error"
        assert details == {"detail": {"code": 123}}

    def test_none_detail_returns_request_error(self) -> None:
        msg, details = _http_exception_message(None)
        assert msg == "Request error"
        assert details is None

    def test_integer_detail_returns_request_error(self) -> None:
        msg, details = _http_exception_message(42)
        assert msg == "Request error"
        assert details is None

    def test_dict_with_only_message_key_no_rest(self) -> None:
        msg, details = _http_exception_message({"message": "Only message"})
        assert msg == "Only message"
        assert details is None


# ---------------------------------------------------------------------------
# error_payload
# ---------------------------------------------------------------------------


class TestErrorPayload:
    def test_basic_payload_structure(self) -> None:
        result = error_payload(code="test_code", message="test message")
        assert result["code"] == "test_code"
        assert result["message"] == "test message"
        assert result["details"] is None
        assert result["request_id"] is None

    def test_payload_with_details(self) -> None:
        result = error_payload(code="err", message="msg", details={"key": "val"})
        assert result["details"] == {"key": "val"}

    def test_payload_with_request_has_request_id(self) -> None:
        mock_request = MagicMock(spec=Request)
        mock_request.state.request_id = "req-abc-123"
        result = error_payload(code="err", message="msg", request=mock_request)
        assert result["request_id"] == "req-abc-123"

    def test_payload_without_request_has_no_request_id(self) -> None:
        result = error_payload(code="err", message="msg")
        assert result["request_id"] is None

    def test_payload_with_request_missing_state_attr(self) -> None:
        mock_request = MagicMock(spec=Request)
        # state has no request_id attribute
        mock_request.state = MagicMock(spec=[])
        result = error_payload(code="err", message="msg", request=mock_request)
        assert result["request_id"] is None

    def test_payload_returns_dict(self) -> None:
        result = error_payload(code="c", message="m")
        assert isinstance(result, dict)


# ---------------------------------------------------------------------------
# register_exception_handlers — integration tests via TestClient
# ---------------------------------------------------------------------------


def _make_app_with_handlers() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)
    return app


class TestRegisterExceptionHandlers:
    """Integration-style tests using FastAPI TestClient."""

    def test_http_exception_404_returns_json(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-404")
        async def _raise_404() -> None:
            raise HTTPException(status_code=404, detail="Resource not found")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-404")
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "not_found"
        assert body["message"] == "Resource not found"

    def test_http_exception_401_returns_auth_error_code(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-401")
        async def _raise_401() -> None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-401")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "authentication_error"

    def test_http_exception_403_returns_authorization_error_code(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-403")
        async def _raise_403() -> None:
            raise HTTPException(status_code=403, detail="Forbidden")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-403")
        assert resp.status_code == 403
        body = resp.json()
        assert body["code"] == "authorization_error"

    def test_http_exception_with_headers_preserved(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-auth-header")
        async def _raise_with_header() -> None:
            raise HTTPException(
                status_code=401,
                detail="Unauthorized",
                headers={"WWW-Authenticate": "Bearer"},
            )

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-auth-header")
        assert resp.status_code == 401
        assert "www-authenticate" in resp.headers

    def test_sqlalchemy_error_returns_503(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-db-error")
        async def _raise_db_error() -> None:
            raise SQLAlchemyError("DB failure")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-db-error")
        assert resp.status_code == 503
        body = resp.json()
        assert body["code"] == "database_error"
        assert body["message"] == "A database error occurred"

    def test_microsoft_graph_not_configured_returns_503(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-ms-not-configured")
        async def _raise_not_configured() -> None:
            raise MicrosoftGraphNotConfiguredError("Missing creds")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-ms-not-configured")
        assert resp.status_code == 503
        body = resp.json()
        assert body["code"] == "microsoft_graph_not_configured"

    def test_microsoft_graph_oauth_error_returns_400(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-ms-oauth")
        async def _raise_oauth_error() -> None:
            raise MicrosoftGraphOAuthError("Invalid state")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-ms-oauth")
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "microsoft_graph_oauth_error"

    def test_microsoft_graph_api_error_returns_502(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-ms-api-error")
        async def _raise_api_error() -> None:
            raise MicrosoftGraphApiError("Upstream failure", status_code=429)

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-ms-api-error")
        assert resp.status_code == 502
        body = resp.json()
        assert body["code"] == "microsoft_graph_upstream_error"

    def test_microsoft_graph_base_error_returns_500(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-ms-base-error")
        async def _raise_base_error() -> None:
            raise MicrosoftGraphIntegrationError("Generic graph error")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-ms-base-error")
        assert resp.status_code == 500
        body = resp.json()
        assert body["code"] == "microsoft_graph_error"

    def test_compliance_report_error_returns_400(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-report-error")
        async def _raise_report_error() -> None:
            raise ComplianceReportError("Report generation failed")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-report-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "compliance_report_error"
        assert "Report generation failed" in body["message"]

    def test_shadow_ai_detection_error_returns_400(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-detection-error")
        async def _raise_detection_error() -> None:
            raise ShadowAIDetectionError("Detection pipeline error")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-detection-error")
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "shadow_ai_detection_error"
        assert "Detection pipeline error" in body["message"]

    def test_error_response_has_expected_keys(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-keys")
        async def _raise() -> None:
            raise HTTPException(status_code=404, detail="Missing")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-keys")
        body = resp.json()
        assert "code" in body
        assert "message" in body
        assert "details" in body
        assert "request_id" in body

    def test_http_exception_dict_detail_with_message_key(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-dict-detail")
        async def _raise_dict() -> None:
            raise HTTPException(status_code=400, detail={"message": "Custom message", "field": "email"})

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-dict-detail")
        assert resp.status_code == 400
        body = resp.json()
        assert body["message"] == "Custom message"

    def test_authentication_error_returns_401(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-auth-error")
        async def _raise_auth_error() -> None:
            raise AuthenticationError("Invalid credentials")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-auth-error")
        assert resp.status_code == 401
        body = resp.json()
        assert body["code"] == "authentication_error"

    def test_authentication_error_has_www_authenticate_header(self) -> None:
        app = _make_app_with_handlers()

        @app.get("/test-auth-header-2")
        async def _raise_auth() -> None:
            raise AuthenticationError("bad token")

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-auth-header-2")
        assert "www-authenticate" in resp.headers

    def test_validation_error_returns_422(self) -> None:
        """FastAPI validation errors return 422 via the handler."""
        app = _make_app_with_handlers()

        @app.get("/test-validate")
        async def _validate_endpoint(q: int) -> dict[str, Any]:
            return {"q": q}

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/test-validate?q=not-an-int")
        assert resp.status_code == 422
        body = resp.json()
        assert body["code"] == "validation_error"
        assert "errors" in body["details"]


# ---------------------------------------------------------------------------
# Microsoft Graph error hierarchy coverage
# ---------------------------------------------------------------------------


class TestMicrosoftGraphErrorHierarchy:
    def test_not_configured_is_integration_error(self) -> None:
        exc = MicrosoftGraphNotConfiguredError("missing")
        assert isinstance(exc, MicrosoftGraphIntegrationError)

    def test_oauth_error_is_integration_error(self) -> None:
        exc = MicrosoftGraphOAuthError("bad state")
        assert isinstance(exc, MicrosoftGraphIntegrationError)

    def test_api_error_is_integration_error(self) -> None:
        exc = MicrosoftGraphApiError("upstream", status_code=500)
        assert isinstance(exc, MicrosoftGraphIntegrationError)

    def test_api_error_stores_status_code(self) -> None:
        exc = MicrosoftGraphApiError("msg", status_code=429)
        assert exc.status_code == 429

    def test_api_error_status_code_can_be_none(self) -> None:
        exc = MicrosoftGraphApiError("msg")
        assert exc.status_code is None