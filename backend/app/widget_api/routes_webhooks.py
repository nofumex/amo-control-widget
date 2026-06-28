from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.webhooks import extract_account_hint
from app.db.models import EventInbox, Tenant
from app.db.session import get_session

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.post("/amo")
async def amo_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    payload = await _payload(request)
    return await _accept("amo", payload, session)


@router.post("/digital-pipeline")
async def digital_pipeline_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict:
    payload = await _payload(request)
    return await _accept("digital_pipeline", payload, session)


async def _payload(request: Request) -> dict[str, Any]:
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        return await request.json()
    form = await request.form()
    return dict(form)


async def _accept(source: str, payload: dict[str, Any], session: AsyncSession) -> dict:
    account_id, subdomain = extract_account_hint(payload)
    query = select(Tenant)
    if account_id:
        query = query.where(Tenant.account_id == account_id)
    elif subdomain:
        query = query.where(Tenant.subdomain == subdomain)
    tenant = (await session.scalars(query)).first()
    session.add(EventInbox(tenant_id=tenant.id if tenant else None, source=source, payload_json=payload, status="pending"))
    await session.commit()
    return {"ok": True}
