from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.oauth import refresh_token as refresh_oauth_token
from app.amo.oauth import token_expires_soon
from app.core.config import Settings
from app.core.crypto import SecretBox
from app.db.models import DeliveryLog, EventInbox, OAuthToken, ReportSnapshot, Tenant


async def refresh_due_tokens(session: AsyncSession, settings: Settings) -> int:
    rows = (await session.scalars(select(OAuthToken))).all()
    due = [row for row in rows if token_expires_soon(row.expires_at, threshold_seconds=900)]
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    refreshed = 0
    for row in due:
        tenant = await session.get(Tenant, row.tenant_id)
        if tenant is None or tenant.status in {"disabled", "deleted"}:
            continue
        try:
            payload = await refresh_oauth_token(settings, tenant.base_url, box.decrypt(row.refresh_token_encrypted))
            row.access_token_encrypted = box.encrypt(payload.access_token)
            row.refresh_token_encrypted = box.encrypt(payload.refresh_token)
            row.expires_at = payload.expires_at(300)
            row.scope = payload.scope
            tenant.status = "active"
            refreshed += 1
        except Exception as exc:
            tenant.status = "oauth_error"
            session.add(EventInbox(tenant_id=tenant.id, source="worker", payload_json={}, status="failed", error_message=str(exc)))
    await session.commit()
    return refreshed


async def cleanup_retention(session: AsyncSession, settings: Settings) -> None:
    now = dt.datetime.now(dt.UTC)
    await session.execute(
        delete(ReportSnapshot).where(
            ReportSnapshot.created_at < now - dt.timedelta(days=settings.report_snapshot_retention_days)
        )
    )
    await session.execute(
        delete(EventInbox).where(EventInbox.received_at < now - dt.timedelta(days=settings.webhook_inbox_retention_days))
    )
    await session.execute(
        delete(DeliveryLog).where(DeliveryLog.created_at < now - dt.timedelta(days=settings.delivery_log_retention_days))
    )
    await session.commit()


def should_run_hour(now: dt.datetime, hour: int) -> bool:
    return now.hour == hour and now.minute < 5
