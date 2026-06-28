from __future__ import annotations

import asyncio
import time


class AsyncRateLimiter:
    def __init__(self, rps: float = 6.0) -> None:
        self.min_interval = 1.0 / max(min(rps, 7.0), 0.1)
        self._last_at = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            delay = self.min_interval - (now - self._last_at)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_at = time.monotonic()
