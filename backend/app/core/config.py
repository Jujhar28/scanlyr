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

    # --- Production security ---
    log_level: str = Field(default="INFO")
    log_json: bool | None = Field(
        default=None,
        description="Emit JSON logs. Default: true when app_env=production.",
    )
    trust_proxy_headers: bool = Field(
        default=False,
        description="Trust X-Forwarded-For / X-Real-IP when behind a reverse proxy.",
    )
    max_request_body_bytes: int = Field(
        default=1_048_576,
        ge=1024,
        le=52_428_800,
        description="Reject requests with Content-Length above this (default 1 MiB).",
    )
    rate_limit_enabled: bool = Field(default=True)
    rate_limit_default_per_minute: int = Field(default=120, ge=1, le=10_000)
    rate_limit_auth_per_minute: int = Field(default=20, ge=1, le=1000)
    rate_limit_scan_per_minute: int = Field(default=30, ge=1, le=1000)
    security_hsts_max_age: int = Field(default=31_536_000, ge=0)
    expose_error_details: bool | None = Field(
        default=None,
        description="Include exception details in 500 responses. Default false in production.",
    )
    uvicorn_workers: int = Field(default=1, ge=1, le=32)

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

    # --- External AI providers (optional hybrid layer on POST /scan) ---
    scan_ai_fusion_enabled: bool = Field(
        default=True,
        description="When true and API keys are set, blend AI analysis with rule-engine scores.",
    )
    scan_rules_weight: float = Field(default=0.4, ge=0.0, le=1.0)
    scan_ai_weight: float = Field(default=0.6, ge=0.0, le=1.0)
    scan_strictness: str = Field(
        default="balanced",
        description="Detector calibration: permissive | balanced | strict.",
    )

    @field_validator("scan_strictness")
    @classmethod
    def validate_scan_strictness(cls, v: str) -> str:
        allowed = {"permissive", "balanced", "strict"}
        normalized = (v or "balanced").strip().lower()
        if normalized not in allowed:
            raise ValueError(f"scan_strictness must be one of: {', '.join(sorted(allowed))}")
        return normalized
    scan_ai_provider_timeout_seconds: float = Field(
        default=10.0,
        ge=5.0,
        le=10.0,
        description="Per-provider HTTP timeout for POST /scan AI layer (seconds).",
    )
    scan_ai_max_retries: int = Field(
        default=1,
        ge=1,
        le=3,
        description="HTTP retries per provider during scan (keep low to respect scan timeout).",
    )
    ai_provider: str = Field(
        default="auto",
        description="Default provider: auto (Gemini + Groq fallback) | gemini | groq.",
    )
    ai_provider_timeout_seconds: float = Field(default=60.0, ge=5.0, le=300.0)
    gemini_api_key: str | None = Field(
        default=None,
        description="Google AI Studio API key (https://aistudio.google.com/apikey).",
    )
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Gemini Flash model id (free tier: gemini-2.0-flash or gemini-2.0-flash-lite).",
    )
    gemini_api_base_url: str = Field(default="https://generativelanguage.googleapis.com")
    gemini_max_retries: int = Field(default=3, ge=1, le=8)
    gemini_retry_backoff_seconds: float = Field(default=1.0, ge=0.1, le=30.0)
    groq_api_key: str | None = Field(
        default=None,
        description="Groq API key (https://console.groq.com/keys). Used as fallback when Gemini fails.",
    )
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Fast Groq model for classification fallback (e.g. llama-3.1-8b-instant).",
    )
    groq_api_base_url: str = Field(default="https://api.groq.com/openai/v1")
    groq_timeout_seconds: float = Field(default=30.0, ge=5.0, le=120.0)
    groq_max_retries: int = Field(default=2, ge=1, le=8)
    groq_retry_backoff_seconds: float = Field(default=0.5, ge=0.1, le=30.0)

    @property
    def is_production(self) -> bool:
        return self.app_env.strip().lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env.strip().lower() in ("development", "dev", "local")

    @property
    def effective_log_json(self) -> bool:
        if self.log_json is not None:
            return self.log_json
        return self.is_production

    @property
    def effective_expose_error_details(self) -> bool:
        if self.expose_error_details is not None:
            return self.expose_error_details
        return not self.is_production

    @model_validator(mode="after")
    def default_enable_openapi_docs(self) -> Settings:
        if self.enable_openapi_docs is not None:
            return self
        enabled = self.is_development or self.debug
        object.__setattr__(self, "enable_openapi_docs", enabled)
        return self

    @model_validator(mode="after")
    def production_safety_checks(self) -> Settings:
        if not self.is_production:
            return self
        key = (self.secret_key or "").lower()
        if len(self.secret_key) < 32 or "change-me" in key or key == "secret":
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and not a placeholder when APP_ENV=production",
            )
        if self.debug:
            raise ValueError("DEBUG must be false when APP_ENV=production")
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
