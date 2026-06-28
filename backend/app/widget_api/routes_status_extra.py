from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.widget_api.auth import current_tenant_id

router = APIRouter(prefix="/api/widget", tags=["widget-amo-data"])


@router.get("/users")
async def users(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    _ = (tenant_id, session)
    return []


@router.get("/pipelines")
async def pipelines(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    _ = (tenant_id, session)
    return []


@router.get("/custom-fields")
async def custom_fields(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    _ = (tenant_id, session)
    return []


@router.post("/sync")
async def sync_now(tenant_id: int = Depends(current_tenant_id)) -> dict:
    return {"ok": True, "tenant_id": tenant_id, "status": "queued"}


@router.post("/disconnect")
async def disconnect(tenant_id: int = Depends(current_tenant_id)) -> dict:
    return {"ok": True, "tenant_id": tenant_id}
