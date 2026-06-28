from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ReportConfig, Tenant
from app.reports.schemas import ReportConfigSchema


async def get_or_create_tenant(
    session: AsyncSession,
    *,
    account_id: int | None,
    subdomain: str,
    base_url: str,
    mode: str,
) -> Tenant:
    stmt = select(Tenant).where(Tenant.account_id == account_id) if account_id else select(Tenant).where(Tenant.subdomain == subdomain)
    tenant = (await session.scalars(stmt)).first()
    if tenant is None:
        tenant = Tenant(account_id=account_id, subdomain=subdomain, base_url=base_url, mode=mode, status="active")
        session.add(tenant)
        await session.flush()
        session.add(ReportConfig(tenant_id=tenant.id, **ReportConfigSchema().model_dump()))
    else:
        tenant.subdomain = subdomain or tenant.subdomain
        tenant.base_url = base_url or tenant.base_url
        tenant.status = "active"
    await session.commit()
    await session.refresh(tenant)
    return tenant
