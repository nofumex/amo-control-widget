from __future__ import annotations

from dataclasses import dataclass

from app.telegram.client import TelegramClient


@dataclass(frozen=True)
class DeliveryResult:
    ok: bool
    status: str


class TelegramDeliveryService:
    async def test_channel(self, bot_token: str, chat_id: str | int) -> DeliveryResult:
        await TelegramClient(bot_token).send_message(chat_id, "Тест amo-control-widget: канал Telegram подключен.")
        return DeliveryResult(ok=True, status="sent")

    async def send_report(self, bot_token: str, chat_id: str | int, rendered_text: str) -> DeliveryResult:
        await TelegramClient(bot_token).send_message(chat_id, rendered_text)
        return DeliveryResult(ok=True, status="sent")
