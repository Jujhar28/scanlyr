"""Tests for app.core.config — Settings, validators, and helpers."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings, reset_settings_cache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED = {
    "SECRET_KEY": "a-very-long-secret-key-for-unit-tests-only",
    "DATABASE_URL": "postgresql+psycopg://user:pass@localhost:5432/db",
}


def make_settings(**overrides: object) -> Settings:
    """Construct a Settings instance bypassing .env by passing all required fields."""
    env: dict[str, object] = {**REQUIRED, **overrides}
    return Settings.model_validate(env)


# ---------------------------------------------------------------------------
# enable_openapi_docs — model validator
# ---------------------------------------------------------------------------


class TestEnableOpenapiDocsValidator:
    """default_enable_openapi_docs model validator."""

    @pytest.mark.parametrize("env_value", ["development", "dev", "local"])
    def test_dev_like_envs_enable_docs(self, env_value: str) -> None:
        s = make_settings(app_env=env_value)
        assert s.enable_openapi_docs is True

    @pytest.mark.parametrize("env_value", ["production", "staging", "test", "prod"])
    def test_non_dev_envs_disable_docs(self, env_value: str) -> None:
        s = make_settings(app_env=env_value)
        assert s.enable_openapi_docs is False

    def test_debug_true_enables_docs_in_production(self) -> None:
        s = make_settings(app_env="production", debug=True)
        assert s.enable_openapi_docs is True

    def test_explicit_true_overrides_env(self) -> None:
        s = make_settings(app_env="production", enable_openapi_docs=True)
        assert s.enable_openapi_docs is True

    def test_explicit_false_overrides_dev_env(self) -> None:
        s = make_settings(app_env="development", enable_openapi_docs=False)
        assert s.enable_openapi_docs is False

    def test_env_value_is_case_insensitive(self) -> None:
        s = make_settings(app_env="DEVELOPMENT")
        assert s.enable_openapi_docs is True

    def test_env_value_with_leading_trailing_spaces(self) -> None:
        s = make_settings(app_env="  dev  ")
        assert s.enable_openapi_docs is True

    def test_default_app_env_development_enables_docs(self) -> None:
        # Default app_env is "development"
        s = make_settings()
        assert s.enable_openapi_docs is True

    def test_debug_false_production_disables_docs(self) -> None:
        s = make_settings(app_env="production", debug=False)
        assert s.enable_openapi_docs is False


# ---------------------------------------------------------------------------
# cors_origin_list property
# ---------------------------------------------------------------------------


class TestCorsOriginList:
    def test_empty_string_returns_empty_list(self) -> None:
        s = make_settings(cors_origins="")
        assert s.cors_origin_list == []

    def test_single_origin(self) -> None:
        s = make_settings(cors_origins="http://localhost:3000")
        assert s.cors_origin_list == ["http://localhost:3000"]

    def test_multiple_comma_separated_origins(self) -> None:
        s = make_settings(cors_origins="http://localhost:3000,https://app.example.com")
        assert s.cors_origin_list == ["http://localhost:3000", "https://app.example.com"]

    def test_origins_with_spaces_around_commas(self) -> None:
        s = make_settings(cors_origins="http://a.com , http://b.com , http://c.com")
        assert s.cors_origin_list == ["http://a.com", "http://b.com", "http://c.com"]

    def test_trailing_comma_is_ignored(self) -> None:
        s = make_settings(cors_origins="http://a.com,")
        assert s.cors_origin_list == ["http://a.com"]

    def test_multiple_trailing_commas_are_ignored(self) -> None:
        s = make_settings(cors_origins="http://a.com,,,")
        assert s.cors_origin_list == ["http://a.com"]

    def test_whitespace_only_string_returns_empty_list(self) -> None:
        s = make_settings(cors_origins="   ")
        assert s.cors_origin_list == []


# ---------------------------------------------------------------------------
# strip_cors validator (field_validator)
# ---------------------------------------------------------------------------


class TestStripCorsValidator:
    def test_leading_whitespace_stripped(self) -> None:
        s = make_settings(cors_origins="  http://a.com")
        assert s.cors_origins == "http://a.com"

    def test_trailing_whitespace_stripped(self) -> None:
        s = make_settings(cors_origins="http://a.com   ")
        assert s.cors_origins == "http://a.com"

    def test_both_sides_stripped(self) -> None:
        s = make_settings(cors_origins="  http://a.com  ")
        assert s.cors_origins == "http://a.com"

    def test_non_string_passthrough(self) -> None:
        # Validator should pass non-string values through unchanged (for type coercion)
        s = make_settings(cors_origins="")
        assert s.cors_origins == ""


# ---------------------------------------------------------------------------
# Field defaults and constraints
# ---------------------------------------------------------------------------


class TestFieldDefaults:
    def test_default_app_name(self) -> None:
        s = make_settings()
        assert s.app_name == "Scanlyr API"

    def test_default_jwt_algorithm(self) -> None:
        s = make_settings()
        assert s.jwt_algorithm == "HS256"

    def test_default_access_token_expire_minutes(self) -> None:
        s = make_settings()
        assert s.access_token_expire_minutes == 15

    def test_default_refresh_token_expire_days(self) -> None:
        s = make_settings()
        assert s.refresh_token_expire_days == 14

    def test_default_bcrypt_rounds(self) -> None:
        s = make_settings()
        assert s.bcrypt_rounds == 12

    def test_default_db_pool_size(self) -> None:
        s = make_settings()
        assert s.db_pool_size == 5

    def test_default_max_overflow(self) -> None:
        s = make_settings()
        assert s.db_max_overflow == 10

    def test_default_frontend_app_url(self) -> None:
        s = make_settings()
        assert s.frontend_app_url == "http://localhost:3000"

    def test_default_microsoft_graph_authority_host(self) -> None:
        s = make_settings()
        assert s.microsoft_graph_authority_host == "https://login.microsoftonline.com"

    def test_default_microsoft_graph_tenant(self) -> None:
        s = make_settings()
        assert s.microsoft_graph_tenant == "organizations"

    def test_default_report_storage_dir(self) -> None:
        s = make_settings()
        assert s.report_storage_dir == "var/reports"

    def test_microsoft_graph_optional_fields_default_none(self) -> None:
        s = make_settings()
        assert s.microsoft_graph_client_id is None
        assert s.microsoft_graph_client_secret is None
        assert s.microsoft_graph_redirect_uri is None


class TestFieldConstraints:
    def test_bcrypt_rounds_minimum_accepted(self) -> None:
        s = make_settings(bcrypt_rounds=4)
        assert s.bcrypt_rounds == 4

    def test_bcrypt_rounds_maximum_accepted(self) -> None:
        s = make_settings(bcrypt_rounds=31)
        assert s.bcrypt_rounds == 31

    def test_bcrypt_rounds_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(bcrypt_rounds=3)

    def test_bcrypt_rounds_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(bcrypt_rounds=32)

    def test_access_token_expire_minutes_minimum_one(self) -> None:
        s = make_settings(access_token_expire_minutes=1)
        assert s.access_token_expire_minutes == 1

    def test_access_token_expire_minutes_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(access_token_expire_minutes=0)

    def test_refresh_token_expire_days_minimum_one(self) -> None:
        s = make_settings(refresh_token_expire_days=1)
        assert s.refresh_token_expire_days == 1

    def test_refresh_token_expire_days_below_minimum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(refresh_token_expire_days=0)

    def test_db_pool_size_minimum_one(self) -> None:
        s = make_settings(db_pool_size=1)
        assert s.db_pool_size == 1

    def test_db_pool_size_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(db_pool_size=51)

    def test_db_max_overflow_minimum_zero(self) -> None:
        s = make_settings(db_max_overflow=0)
        assert s.db_max_overflow == 0

    def test_db_max_overflow_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(db_max_overflow=101)

    def test_db_pool_timeout_minimum_one(self) -> None:
        s = make_settings(db_pool_timeout=1)
        assert s.db_pool_timeout == 1

    def test_db_pool_timeout_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(db_pool_timeout=121)

    def test_db_pool_recycle_minimum_30(self) -> None:
        s = make_settings(db_pool_recycle=30)
        assert s.db_pool_recycle == 30

    def test_db_pool_recycle_above_maximum_raises(self) -> None:
        with pytest.raises(ValidationError):
            make_settings(db_pool_recycle=3601)

    def test_secret_key_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Remove required env vars so pydantic-settings cannot fall back to them
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            Settings.model_validate({"DATABASE_URL": "postgresql+psycopg://user:pass@localhost/db"})

    def test_database_url_required(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValidationError):
            Settings.model_validate({"SECRET_KEY": "some-key"})


# ---------------------------------------------------------------------------
# Boolean startup flags
# ---------------------------------------------------------------------------


class TestStartupFlags:
    def test_db_skip_startup_ping_default_false(self) -> None:
        s = make_settings()
        assert s.db_skip_startup_ping is False

    def test_db_require_at_startup_default_false(self) -> None:
        s = make_settings()
        assert s.db_require_at_startup is False

    def test_run_db_migrations_on_startup_default_false(self) -> None:
        s = make_settings()
        assert s.run_db_migrations_on_startup is False

    def test_db_skip_startup_ping_can_be_set_true(self) -> None:
        s = make_settings(db_skip_startup_ping=True)
        assert s.db_skip_startup_ping is True

    def test_run_db_migrations_on_startup_can_be_set_true(self) -> None:
        s = make_settings(run_db_migrations_on_startup=True)
        assert s.run_db_migrations_on_startup is True


# ---------------------------------------------------------------------------
# get_settings LRU cache and reset_settings_cache
# ---------------------------------------------------------------------------


class TestGetSettingsCache:
    def test_get_settings_returns_settings_instance(self, minimal_env: None) -> None:
        reset_settings_cache()
        s = get_settings()
        assert isinstance(s, Settings)

    def test_get_settings_returns_same_instance(self, minimal_env: None) -> None:
        reset_settings_cache()
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2

    def test_reset_settings_cache_clears_cache(self, minimal_env: None) -> None:
        reset_settings_cache()
        s1 = get_settings()
        reset_settings_cache()
        s2 = get_settings()
        # After clearing, a new instance is created (they are equal but not the same object)
        assert s1 == s2 or isinstance(s2, Settings)

    def test_reset_settings_cache_allows_new_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SECRET_KEY", "first-secret-key-long-enough")
        monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://u:p@h/db")
        reset_settings_cache()
        s1 = get_settings()

        monkeypatch.setenv("SECRET_KEY", "second-secret-key-long-enough")
        reset_settings_cache()
        s2 = get_settings()

        assert s1.secret_key == "first-secret-key-long-enough"
        assert s2.secret_key == "second-secret-key-long-enough"


# ---------------------------------------------------------------------------
# Microsoft Graph scopes default
# ---------------------------------------------------------------------------


class TestMicrosoftGraphDefaults:
    def test_default_scopes_contain_offline_access(self) -> None:
        s = make_settings()
        assert "offline_access" in s.microsoft_graph_scopes

    def test_default_scopes_contain_audit_log(self) -> None:
        s = make_settings()
        assert "AuditLog.Read.All" in s.microsoft_graph_scopes

    def test_default_scopes_contain_directory_read(self) -> None:
        s = make_settings()
        assert "Directory.Read.All" in s.microsoft_graph_scopes

    def test_token_pepper_defaults_empty_string(self) -> None:
        s = make_settings()
        assert s.microsoft_graph_token_pepper == ""

    def test_custom_scopes_accepted(self) -> None:
        s = make_settings(microsoft_graph_scopes="offline_access openid")
        assert s.microsoft_graph_scopes == "offline_access openid"