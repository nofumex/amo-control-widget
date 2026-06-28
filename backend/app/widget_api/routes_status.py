from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DeliveryLog, ReportConfig, ReportSnapshot, SyncState, TelegramChannel, Tenant
from app.db.session import get_session
from app.widget_api.auth import current_tenant_id

router = APIRouter(prefix="/api/widget", tags=["widget-status"])


@router.get("/status")
async def status(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> dict:
    tenant = await session.get(Tenant, tenant_id)
    config = (await session.scalars(select(ReportConfig).where(ReportConfig.tenant_id == tenant_id))).first()
    sync = (await session.scalars(select(SyncState).where(SyncState.tenant_id == tenant_id))).first()
    telegram = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant_id))).first()
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant_id).order_by(desc(ReportSnapshot.created_at))
        )
    ).first()
    delivery = (
        await session.scalars(select(DeliveryLog).where(DeliveryLog.tenant_id == tenant_id).order_by(desc(DeliveryLog.created_at)))
    ).first()
    return {
        "oauth_connected": bool(tenant and tenant.status == "active"),
        "mode": tenant.mode if tenant else "private",
        "tenant_id": tenant_id,
        "account_id": tenant.account_id if tenant else None,
        "last_sync": sync.last_success_at if sync else None,
        "next_sync": sync.next_sync_at if sync else None,
        "last_report_build": snapshot.created_at if snapshot else None,
        "last_delivery": delivery.sent_at if delivery else None,
        "latest_error": (sync.last_error if sync else "") or (snapshot.error_message if snapshot else ""),
        "enabled_users": len(config.selected_user_ids) if config else 0,
        "telegram_enabled": bool(telegram and telegram.enabled),
    }
