from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import SecretBox, mask_secret
from app.db.models import TelegramChannel
from app.db.session import get_session
from app.telegram.delivery import TelegramDeliveryService
from app.telegram.schemas import TelegramSettings
from app.widget_api.auth import current_tenant_id

router = APIRouter(prefix="/api/widget/telegram", tags=["widget-telegram"])


def _box() -> SecretBox:
    settings = get_settings()
    return SecretBox(settings.fernet_key or settings.app_secret_key)


@router.get("")
async def get_telegram(
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    channel = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant_id))).first()
    if channel is None:
        return TelegramSettings().model_dump()
    box = _box()
    token = box.decrypt(channel.bot_token_encrypted)
    chat_id = box.decrypt(channel.admin_chat_id_encrypted)
    return TelegramSettings(
        enabled=channel.enabled,
        bot_token_masked=mask_secret(token),
        admin_chat_id_masked=mask_secret(chat_id, visible_prefix=4),
        admin_username=channel.admin_username,
        last_test_status=channel.last_test_status,
    ).model_dump()


@router.put("")
async def put_telegram(
    payload: TelegramSettings,
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    channel = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant_id))).first()
    if channel is None:
        channel = TelegramChannel(tenant_id=tenant_id)
        session.add(channel)
    box = _box()
    channel.enabled = payload.enabled
    if payload.bot_token:
        channel.bot_token_encrypted = box.encrypt(payload.bot_token)
    if payload.admin_chat_id:
        channel.admin_chat_id_encrypted = box.encrypt(payload.admin_chat_id)
    channel.admin_username = payload.admin_username
    await session.commit()
    return {"ok": True}


@router.post("/test")
async def test_telegram(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> dict:
    channel = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant_id))).first()
    if channel is None:
        raise HTTPException(status_code=400, detail="Telegram settings not configured")
    box = _box()
    try:
        await TelegramDeliveryService().test_channel(
            box.decrypt(channel.bot_token_encrypted),
            box.decrypt(channel.admin_chat_id_encrypted),
        )
        channel.last_test_status = "sent"
        channel.last_test_at = dt.datetime.now(dt.UTC)
        await session.commit()
        return {"ok": True, "status": "sent"}
    except Exception as exc:
        channel.last_test_status = str(exc)
        channel.last_test_at = dt.datetime.now(dt.UTC)
        await session.commit()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
