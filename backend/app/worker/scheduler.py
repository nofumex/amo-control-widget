from __future__ import annotations

import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.worker.jobs import cleanup_retention, refresh_due_tokens
from app.worker.locks import redis_lock


async def scheduler_tick(session: AsyncSession, redis: Redis, settings: Settings) -> None:
    async with redis_lock(redis, "worker:refresh_oauth", 300) as acquired:
        if acquired:
            await refresh_due_tokens(session, settings)
    async with redis_lock(redis, "worker:cleanup_retention", 3600) as acquired:
        if acquired:
            await cleanup_retention(session, settings)
    await asyncio.sleep(0)
