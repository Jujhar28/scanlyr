"""Tests for app.core.public_api — route marking and collection utilities."""
from __future__ import annotations

import pytest
from fastapi import FastAPI

from app.core.public_api import (
    PUBLIC_API_ROUTE_ATTR,
    collect_public_api_route_keys,
    public_api_route,
)


# ---------------------------------------------------------------------------
# public_api_route decorator
# ---------------------------------------------------------------------------


class TestPublicApiRouteDecorator:
    def test_decorator_sets_attribute(self) -> None:
        async def my_handler() -> None:
            pass

        decorated = public_api_route(my_handler)
        assert getattr(decorated, PUBLIC_API_ROUTE_ATTR) is True

    def test_decorator_returns_original_function(self) -> None:
        async def my_handler() -> None:
            pass

        decorated = public_api_route(my_handler)
        assert decorated is my_handler

    def test_decorator_preserves_callable(self) -> None:
        async def my_handler() -> dict:
            return {}

        decorated = public_api_route(my_handler)
        assert callable(decorated)

    def test_undecorated_function_lacks_attribute(self) -> None:
        async def my_handler() -> None:
            pass

        assert not getattr(my_handler, PUBLIC_API_ROUTE_ATTR, False)

    def test_attribute_name_constant(self) -> None:
        assert PUBLIC_API_ROUTE_ATTR == "__shadow_public_api_route__"

    def test_attribute_is_truthy(self) -> None:
        async def handler() -> None:
            pass

        public_api_route(handler)
        assert bool(getattr(handler, PUBLIC_API_ROUTE_ATTR))

    def test_can_be_applied_to_sync_function(self) -> None:
        def sync_handler() -> None:
            pass

        decorated = public_api_route(sync_handler)
        assert getattr(decorated, PUBLIC_API_ROUTE_ATTR) is True

    def test_idempotent_double_decoration(self) -> None:
        async def handler() -> None:
            pass

        # Applying twice should still result in attribute set to True
        public_api_route(public_api_route(handler))
        assert getattr(handler, PUBLIC_API_ROUTE_ATTR) is True


# ---------------------------------------------------------------------------
# collect_public_api_route_keys
# ---------------------------------------------------------------------------


class TestCollectPublicApiRouteKeys:
    def _make_app_with_routes(self) -> FastAPI:
        app = FastAPI()

        @public_api_route
        @app.get("/api/v1/auth/login")
        async def login_handler() -> dict:
            return {}

        @public_api_route
        @app.post("/api/v1/auth/register")
        async def register_handler() -> dict:
            return {}

        @app.get("/api/v1/users/me")
        async def me_handler() -> dict:
            return {}

        return app

    def test_returns_frozenset(self) -> None:
        app = FastAPI()
        result = collect_public_api_route_keys(app)
        assert isinstance(result, frozenset)

    def test_empty_app_returns_empty_frozenset(self) -> None:
        app = FastAPI()
        # FastAPI adds some default routes (e.g. openapi.json) but none are marked public
        result = collect_public_api_route_keys(app)
        assert result == frozenset()

    def test_collects_marked_get_route(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.get("/public-endpoint")
        async def public_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("GET", "/public-endpoint") in result

    def test_collects_marked_post_route(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.post("/public-post")
        async def public_post_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("POST", "/public-post") in result

    def test_does_not_collect_unmarked_route(self) -> None:
        app = FastAPI()

        @app.get("/private-endpoint")
        async def private_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("GET", "/private-endpoint") not in result

    def test_collects_only_marked_routes_not_unmarked(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.get("/public")
        async def public_handler() -> dict:
            return {}

        @app.get("/private")
        async def private_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("GET", "/public") in result
        assert ("GET", "/private") not in result

    def test_options_method_excluded(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.get("/endpoint")
        async def handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        # OPTIONS should never be in the result
        assert ("OPTIONS", "/endpoint") not in result

    def test_multiple_marked_routes_all_collected(self) -> None:
        app = _make_multi_route_app()
        result = collect_public_api_route_keys(app)
        assert len(result) >= 3

    def test_tuples_contain_method_and_path_strings(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.get("/check")
        async def check() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        for item in result:
            assert len(item) == 2
            method, path = item
            assert isinstance(method, str)
            assert isinstance(path, str)

    def test_result_is_immutable_frozenset(self) -> None:
        app = FastAPI()
        result = collect_public_api_route_keys(app)
        with pytest.raises(AttributeError):
            result.add(("GET", "/new"))  # type: ignore[attr-defined]

    def test_delete_method_marked_route_collected(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.delete("/resource/{id}")
        async def delete_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("DELETE", "/resource/{id}") in result

    def test_put_method_marked_route_collected(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.put("/resource/{id}")
        async def put_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("PUT", "/resource/{id}") in result

    def test_path_with_parameters_collected_correctly(self) -> None:
        app = FastAPI()

        @public_api_route
        @app.get("/api/v1/integrations/microsoft/callback")
        async def callback_handler() -> dict:
            return {}

        result = collect_public_api_route_keys(app)
        assert ("GET", "/api/v1/integrations/microsoft/callback") in result

    def test_marked_route_with_no_methods_edge_case(self) -> None:
        """collect_public_api_route_keys should handle routes gracefully."""
        app = FastAPI()
        result = collect_public_api_route_keys(app)
        # Just ensure no exception is raised
        assert isinstance(result, frozenset)


def _make_multi_route_app() -> FastAPI:
    app = FastAPI()

    @public_api_route
    @app.post("/api/v1/auth/login")
    async def login() -> dict:
        return {}

    @public_api_route
    @app.post("/api/v1/auth/register")
    async def register() -> dict:
        return {}

    @public_api_route
    @app.get("/api/v1/health")
    async def health() -> dict:
        return {}

    @app.get("/api/v1/users/me")
    async def me() -> dict:
        return {}

    return app
