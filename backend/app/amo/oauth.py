from __future__ import annotations

import datetime as dt
from urllib.parse import urlencode

import httpx

from app.amo.schemas import OAuthTokenPayload
from app.core.config import Settings


def authorization_url(settings: Settings, *, state: str = "") -> str:
    query = {
        "client_id": settings.amo_client_id,
        "mode": "post_message",
        "redirect_uri": settings.amo_redirect_uri,
        "response_type": "code",
    }
    if state:
        query["state"] = state
    return f"https://www.amocrm.ru/oauth?{urlencode(query)}"


def token_expires_soon(expires_at: dt.datetime, *, now: dt.datetime | None = None, threshold_seconds: int = 600) -> bool:
    current = now or dt.datetime.now(dt.UTC)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=dt.UTC)
    return expires_at <= current + dt.timedelta(seconds=threshold_seconds)


async def exchange_code(settings: Settings, base_url: str, code: str) -> OAuthTokenPayload:
    payload = {
        "client_id": settings.amo_client_id,
        "client_secret": settings.amo_client_secret,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.amo_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{base_url.rstrip('/')}/oauth2/access_token", json=payload)
        response.raise_for_status()
        return OAuthTokenPayload.model_validate(response.json())


async def refresh_token(settings: Settings, base_url: str, refresh_token_value: str) -> OAuthTokenPayload:
    payload = {
        "client_id": settings.amo_client_id,
        "client_secret": settings.amo_client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token_value,
        "redirect_uri": settings.amo_redirect_uri,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(f"{base_url.rstrip('/')}/oauth2/access_token", json=payload)
        response.raise_for_status()
        return OAuthTokenPayload.model_validate(response.json())
