from __future__ import annotations

import datetime as dt

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.oauth import token_expires_soon
from app.db.models import OAuthToken, Tenant


async def refresh_due_tokens(session: AsyncSession) -> int:
    rows = (await session.scalars(select(OAuthToken))).all()
    due = [row for row in rows if token_expires_soon(row.expires_at, threshold_seconds=900)]
    for row in due:
        tenant = await session.get(Tenant, row.tenant_id)
        if tenant:
            tenant.status = "oauth_error"
    await session.commit()
    return len(due)


def should_run_hour(now: dt.datetime, hour: int) -> bool:
    return now.hour == hour and now.minute < 5
