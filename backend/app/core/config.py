from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["local", "development", "test", "staging", "production"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: AppEnv = "development"
    integration_mode: Literal["private", "public"] = "private"
    public_base_url: AnyHttpUrl | str = "http://localhost:8000"

    amo_client_id: str = ""
    amo_client_secret: str = ""
    amo_redirect_uri: str = "http://localhost:8000/api/oauth/callback"

    database_url: str = "postgresql+asyncpg://amo:amo@postgres:5432/amo_control"
    redis_url: str = "redis://redis:6379/0"
    fernet_key: str = ""
    app_secret_key: str = "change-me-dev-secret"
    widget_signing_secret: str = ""
    webhook_shared_secret: str = ""
    internal_admin_token: str = ""
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    allow_dev_auth: bool = False
    widget_dev_tenant_id: int | None = None
    amo_rps_limit: float = Field(default=6.0, gt=0, le=7.0)
    widget_signature_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    webhook_signature_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    max_webhook_payload_bytes: int = Field(default=256_000, ge=1024, le=2_000_000)
    report_max_range_days: int = Field(default=31, ge=1, le=366)
    report_snapshot_retention_days: int = Field(default=180, ge=1, le=3650)
    webhook_inbox_retention_days: int = Field(default=30, ge=1, le=365)
    delivery_log_retention_days: int = Field(default=180, ge=1, le=3650)

    log_level: str = "INFO"

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @model_validator(mode="after")
    def validate_runtime_settings(self) -> Settings:
        if self.app_env == "production":
            unsafe_values = {"", "change-me", "change-me-dev-secret", "dev", "secret", "test"}
            required = {
                "AMO_CLIENT_ID": self.amo_client_id,
                "AMO_CLIENT_SECRET": self.amo_client_secret,
                "AMO_REDIRECT_URI": self.amo_redirect_uri,
                "FERNET_KEY": self.fernet_key,
                "APP_SECRET_KEY": self.app_secret_key,
                "WIDGET_SIGNING_SECRET": self.widget_signing_secret,
                "WEBHOOK_SHARED_SECRET": self.webhook_shared_secret,
                "INTERNAL_ADMIN_TOKEN": self.internal_admin_token,
            }
            missing = [name for name, value in required.items() if not value or value in unsafe_values]
            if missing:
                raise ValueError(f"Unsafe production configuration: {', '.join(missing)}")
            public_url = str(self.public_base_url)
            if "localhost" in public_url or public_url.startswith("http://"):
                raise ValueError("PUBLIC_BASE_URL must be an HTTPS public URL in production")
            if self.allow_dev_auth:
                raise ValueError("ALLOW_DEV_AUTH must be false in production")
        return self

    @property
    def is_development(self) -> bool:
        return self.app_env in {"local", "development", "test"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
