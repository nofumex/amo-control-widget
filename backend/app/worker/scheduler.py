from __future__ import annotations

import asyncio

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.worker.jobs import refresh_due_tokens
from app.worker.locks import redis_lock


async def scheduler_tick(session: AsyncSession, redis: Redis) -> None:
    async with redis_lock(redis, "worker:refresh_oauth", 300) as acquired:
        if acquired:
            await refresh_due_tokens(session)
    await asyncio.sleep(0)
