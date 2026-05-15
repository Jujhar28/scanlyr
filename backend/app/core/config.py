from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Scanlyr API")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    enable_openapi_docs: bool | None = Field(
        default=None,
        description="If set, controls /docs and /redoc. If unset, enabled when app_env is development/dev/local or DEBUG is true.",
    )

    secret_key: str
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15, ge=1)
    refresh_token_expire_days: int = Field(default=14, ge=1)
    bcrypt_rounds: int = Field(default=12, ge=4, le=31)

    database_url: str
    database_echo: bool = Field(default=False)

    db_pool_pre_ping: bool = Field(default=True)
    db_pool_size: int = Field(default=5, ge=1, le=50)
    db_max_overflow: int = Field(default=10, ge=0, le=100)
    db_pool_timeout: int = Field(default=30, ge=1, le=120)
    db_pool_recycle: int = Field(default=280, ge=30, le=3600)

    db_skip_startup_ping: bool = Field(default=False)
    db_require_at_startup: bool = Field(default=False)
    run_db_migrations_on_startup: bool = Field(default=False)

    cors_origins: str = Field(default="")

    frontend_app_url: str = Field(
        default="http://localhost:3000",
        description="Used to redirect the browser after Microsoft OAuth completes.",
    )

    microsoft_graph_client_id: str | None = Field(default=None)
    microsoft_graph_client_secret: str | None = Field(default=None)
    microsoft_graph_redirect_uri: str | None = Field(
        default=None,
        description="Backend callback URL registered in Entra ID (e.g. https://api.example.com/api/v1/integrations/microsoft/callback).",
    )
    microsoft_graph_authority_host: str = Field(default="https://login.microsoftonline.com")
    microsoft_graph_tenant: str = Field(
        default="organizations",
        description="Entra authority tenant segment: organizations, common, or a specific tenant GUID.",
    )
    microsoft_graph_scopes: str = Field(
        default=(
            "offline_access openid profile "
            "AuditLog.Read.All SignInLogs.Read.All Directory.Read.All Application.Read.All"
        ),
    )
    microsoft_graph_token_pepper: str = Field(
        default="",
        description="Optional extra secret material (from env) mixed into token encryption key derivation.",
    )

    report_storage_dir: str = Field(
        default="var/reports",
        description="Directory for generated PDF files (created on demand). Use an absolute path in production.",
    )

    @model_validator(mode="after")
    def default_enable_openapi_docs(self) -> "Settings":
        if self.enable_openapi_docs is not None:
            return self
        env = self.app_env.strip().lower()
        dev_like = env in ("development", "dev", "local")
        # Treat DEBUG as development mode for interactive API docs.
        enabled = dev_like or self.debug
        object.__setattr__(self, "enable_openapi_docs", enabled)
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_cors(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v

    @property
    def cors_origin_list(self) -> list[str]:
        if not self.cors_origins:
            return []
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Clear settings cache (tests / dynamic reload)."""
    get_settings.cache_clear()


settings = get_settings()