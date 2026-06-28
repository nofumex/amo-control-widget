from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.core.errors import ExternalServiceError


class TelegramClient:
    def __init__(self, bot_token: str) -> None:
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"

    async def send_message(self, chat_id: str | int, text: str) -> None:
        chunks = [text[index : index + 3900] for index in range(0, len(text), 3900)] or [""]
        async with httpx.AsyncClient(timeout=30, trust_env=False) as client:
            for chunk in chunks:
                await self._post(client, "sendMessage", {"chat_id": chat_id, "text": chunk, "disable_web_page_preview": True})

    async def _post(self, client: httpx.AsyncClient, method: str, payload: dict[str, Any]) -> Any:
        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                response = await client.post(f"{self.base_url}/{method}", json=payload)
                if response.status_code == 401:
                    raise ExternalServiceError("Invalid Telegram token", public_message="Telegram token неверный.")
                if response.status_code == 400:
                    raise ExternalServiceError(
                        f"Telegram bad request: {response.text[:500]}",
                        public_message="Telegram chat_id неверный или бот не был запущен пользователем.",
                    )
                if response.status_code in {429, 500, 502, 503, 504}:
                    await asyncio.sleep(2 * attempt)
                    continue
                response.raise_for_status()
                data = response.json()
                if not data.get("ok"):
                    raise ExternalServiceError(str(data), public_message="Telegram не принял сообщение.")
                return data.get("result")
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 3:
                    await asyncio.sleep(2 * attempt)
                    continue
        raise ExternalServiceError(f"Telegram {method} failed: {last_error}", public_message="Telegram API недоступен.")
