from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    integration_mode: Literal["private", "public"] = "private"
    public_base_url: AnyHttpUrl | str = "http://localhost:8000"

    amo_client_id: str = ""
    amo_client_secret: str = ""
    amo_redirect_uri: str = "http://localhost:8000/api/oauth/callback"

    database_url: str = "postgresql+asyncpg://amo:amo@postgres:5432/amo_control"
    redis_url: str = "redis://redis:6379/0"
    fernet_key: str = ""
    app_secret_key: str = "change-me-dev-secret"
    cors_allowed_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    log_level: str = "INFO"
    widget_dev_tenant_id: int = 1
    amo_rps_limit: float = 6.0

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
