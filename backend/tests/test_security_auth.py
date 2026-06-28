from __future__ import annotations

import time

import pytest
from app.core.config import Settings
from app.core.security import SignedRequest, compute_request_signature, verify_request_signature
from app.widget_api.auth import _resolve_dev_or_legacy_token
from fastapi import HTTPException


def test_widget_signature_success_and_failure() -> None:
    request = SignedRequest("GET", "/api/widget/status", "", int(time.time()), 123, b"")
    signature = compute_request_signature(request, "secret")
    assert verify_request_signature(request, signature, "secret", ttl_seconds=300)
    assert not verify_request_signature(request, "bad", "secret", ttl_seconds=300)
    stale = SignedRequest("GET", "/api/widget/status", "", int(time.time()) - 1000, 123, b"")
    assert not verify_request_signature(stale, compute_request_signature(stale, "secret"), "secret", ttl_seconds=300)


@pytest.mark.asyncio
async def test_dev_auth_allowed_only_when_enabled() -> None:
    settings = Settings(app_env="development", allow_dev_auth=True, widget_dev_tenant_id=7)
    assert await _resolve_dev_or_legacy_token(settings, None, None) == 7
    settings = Settings(app_env="development", allow_dev_auth=False, widget_dev_tenant_id=7)
    assert await _resolve_dev_or_legacy_token(settings, None, 7) is None


@pytest.mark.asyncio
async def test_production_rejects_dev_auth() -> None:
    settings = Settings(
        app_env="production",
        integration_mode="public",
        public_base_url="https://app.example.com",
        amo_client_id="client",
        amo_client_secret="client-secret",
        amo_redirect_uri="https://app.example.com/api/oauth/callback",
        fernet_key="prod-fernet-secret",
        app_secret_key="prod-app-secret",
        widget_signing_secret="widget-secret",
        webhook_shared_secret="webhook-secret",
        internal_admin_token="admin-secret",
        allow_dev_auth=False,
    )
    with pytest.raises(HTTPException):
        await _resolve_dev_or_legacy_token(settings, None, 1)


def test_production_config_fails_on_placeholders() -> None:
    with pytest.raises(ValueError):
        Settings(app_env="production", public_base_url="http://localhost:8000")
