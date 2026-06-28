from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.webhooks import extract_account_hint
from app.core.config import Settings, get_settings
from app.core.security import SignedRequest, verify_request_signature, webhook_dedup_key
from app.db.models import EventInbox, Tenant
from app.db.session import get_session

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/amo")
async def amo_webhook(
    request: Request,
    x_webhook_timestamp: int | None = Header(default=None),
    x_webhook_signature: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await _handle_webhook("amo", request, x_webhook_timestamp, x_webhook_signature, settings, session)


@router.post("/digital-pipeline")
async def digital_pipeline_webhook(
    request: Request,
    x_webhook_timestamp: int | None = Header(default=None),
    x_webhook_signature: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> dict:
    return await _handle_webhook("digital_pipeline", request, x_webhook_timestamp, x_webhook_signature, settings, session)


async def _handle_webhook(
    source: str,
    request: Request,
    timestamp: int | None,
    signature: str | None,
    settings: Settings,
    session: AsyncSession,
) -> dict:
    body = await request.body()
    if len(body) > settings.max_webhook_payload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large")
    if not _is_allowed_content_type(request.headers.get("content-type", "")):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported content type")
    if not _webhook_auth_ok(request, body, timestamp, signature, settings):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Webhook authentication failed")
    payload = await _payload(request, body)
    account_id, subdomain = extract_account_hint(payload)
    tenant = await _tenant_for_hint(session, account_id, subdomain)
    if tenant is None:
        if settings.app_env == "production":
            return {"ok": True, "status": "ignored_unknown_tenant"}
        return {"ok": True, "status": "ignored_unknown_tenant"}
    dedup_key = webhook_dedup_key(source, body)
    event = EventInbox(
        tenant_id=tenant.id,
        source=source,
        dedup_key=dedup_key,
        payload_json=_safe_payload(payload),
        status="received",
    )
    session.add(event)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        return {"ok": True, "status": "duplicate"}
    return {"ok": True, "status": "received"}


def _webhook_auth_ok(
    request: Request,
    body: bytes,
    timestamp: int | None,
    signature: str | None,
    settings: Settings,
) -> bool:
    if settings.allow_dev_auth and settings.is_development and not signature:
        return True
    if not timestamp or not signature:
        return False
    signed = SignedRequest(
        method=request.method,
        path=request.url.path,
        query=request.url.query,
        timestamp=int(timestamp),
        account_id=0,
        body=body,
    )
    return verify_request_signature(
        signed,
        signature,
        settings.webhook_shared_secret,
        ttl_seconds=settings.webhook_signature_ttl_seconds,
    )


def _is_allowed_content_type(content_type: str) -> bool:
    lowered = content_type.lower()
    return "application/json" in lowered or "application/x-www-form-urlencoded" in lowered or "multipart/form-data" in lowered


async def _payload(request: Request, body: bytes) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Malformed JSON") from exc
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="Webhook JSON must be an object")
        return payload
    form = await request.form()
    return dict(form)


async def _tenant_for_hint(session: AsyncSession, account_id: int | None, subdomain: str) -> Tenant | None:
    if account_id:
        return (await session.scalars(select(Tenant).where(Tenant.account_id == account_id, Tenant.status != "deleted"))).first()
    if subdomain:
        return (await session.scalars(select(Tenant).where(Tenant.subdomain == subdomain, Tenant.status != "deleted"))).first()
    return None


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = dict(payload)
    for key in ("access_token", "refresh_token", "authorization", "token"):
        if key in redacted:
            redacted[key] = "***"
    return redacted
