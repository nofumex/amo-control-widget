from __future__ import annotations

import datetime as dt
import hashlib
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import OAuthState


def hash_state(state: str) -> str:
    return hashlib.sha256(state.encode("utf-8")).hexdigest()


async def create_oauth_state(
    session: AsyncSession,
    *,
    referer: str = "",
    account_id_hint: int | None = None,
    subdomain_hint: str = "",
    ttl_seconds: int = 600,
) -> str:
    state = secrets.token_urlsafe(32)
    session.add(
        OAuthState(
            state_hash=hash_state(state),
            account_id_hint=account_id_hint,
            subdomain_hint=subdomain_hint,
            referer=referer,
            expires_at=dt.datetime.now(dt.UTC) + dt.timedelta(seconds=ttl_seconds),
            status="pending",
        )
    )
    await session.commit()
    return state


async def consume_oauth_state(session: AsyncSession, state: str) -> OAuthState:
    row = (await session.scalars(select(OAuthState).where(OAuthState.state_hash == hash_state(state)))).first()
    now = dt.datetime.now(dt.UTC)
    if row is None or row.status != "pending":
        raise ValueError("Invalid OAuth state")
    expires_at = row.expires_at if row.expires_at.tzinfo else row.expires_at.replace(tzinfo=dt.UTC)
    if expires_at <= now:
        row.status = "expired"
        await session.commit()
        raise ValueError("Expired OAuth state")
    row.status = "used"
    row.used_at = now
    await session.commit()
    return row
