from __future__ import annotations

import asyncio

from redis.asyncio import Redis

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.worker.scheduler import scheduler_tick


async def run() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        while True:
            async with AsyncSessionLocal() as session:
                await scheduler_tick(session, redis)
            await asyncio.sleep(20)
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(run())
