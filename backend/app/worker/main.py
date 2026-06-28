from __future__ import annotations

import asyncio
import signal

from redis.asyncio import Redis

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.worker.scheduler import scheduler_tick


async def run() -> None:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    stop = asyncio.Event()

    def request_stop() -> None:
        stop.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, request_stop)
        except NotImplementedError:
            pass
    try:
        while not stop.is_set():
            async with AsyncSessionLocal() as session:
                await scheduler_tick(session, redis, settings)
            try:
                await asyncio.wait_for(stop.wait(), timeout=20)
            except TimeoutError:
                pass
    finally:
        await redis.aclose()


if __name__ == "__main__":
    asyncio.run(run())
