from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.tenant_client import amo_client_for_tenant
from app.core.config import Settings, get_settings
from app.core.errors import AppError
from app.db.models import Tenant
from app.db.session import get_session
from app.widget_api.auth import require_widget_auth

router = APIRouter(prefix="/api/widget", tags=["widget-amo-data"])


@router.get("/users")
async def users(
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    try:
        async with amo_client_for_tenant(session, tenant, settings) as amo:
            return await amo.get_users()
    except AppError as exc:
        raise HTTPException(status_code=409, detail=exc.public_message) from exc


@router.get("/pipelines")
async def pipelines(
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    try:
        async with amo_client_for_tenant(session, tenant, settings) as amo:
            return await amo.get_pipelines()
    except AppError as exc:
        raise HTTPException(status_code=409, detail=exc.public_message) from exc


@router.get("/custom-fields")
async def custom_fields(
    entity_type: str = "leads",
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[dict]:
    if entity_type not in {"leads", "contacts", "companies", "customers"}:
        raise HTTPException(status_code=422, detail="Unsupported entity_type")
    try:
        async with amo_client_for_tenant(session, tenant, settings) as amo:
            return await amo.get_custom_fields(entity_type)
    except AppError as exc:
        raise HTTPException(status_code=409, detail=exc.public_message) from exc


@router.post("/sync")
async def sync_now(tenant: Tenant = Depends(require_widget_auth)) -> dict:
    return {"ok": True, "tenant_id": tenant.id, "status": "queued"}


@router.post("/disconnect")
async def disconnect(
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tenant.status = "disabled"
    await session.commit()
    return {"ok": True, "tenant_id": tenant.id}
