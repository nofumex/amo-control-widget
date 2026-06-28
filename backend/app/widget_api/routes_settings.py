from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReportConfig
from app.db.session import get_session
from app.reports.event_catalog import EVENT_CATALOG
from app.reports.schemas import ReportConfigSchema
from app.widget_api.auth import current_tenant_id

router = APIRouter(prefix="/api/widget", tags=["widget-settings"])


@router.get("/event-catalog")
async def event_catalog() -> list[dict]:
    return [item.model_dump() for item in EVENT_CATALOG]


@router.get("/settings")
async def get_settings_route(
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    config = (await session.scalars(select(ReportConfig).where(ReportConfig.tenant_id == tenant_id))).first()
    if config is None:
        return ReportConfigSchema().model_dump()
    return ReportConfigSchema.model_validate(config.__dict__).model_dump()


@router.put("/settings")
async def put_settings_route(
    payload: ReportConfigSchema,
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    config = (await session.scalars(select(ReportConfig).where(ReportConfig.tenant_id == tenant_id))).first()
    data = payload.model_dump()
    if config is None:
        config = ReportConfig(tenant_id=tenant_id, **data)
        session.add(config)
    else:
        for key, value in data.items():
            setattr(config, key, value)
        config.version += 1
    await session.commit()
    return {"ok": True, "version": config.version}
