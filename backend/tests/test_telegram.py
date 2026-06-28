from __future__ import annotations

import pytest
from app.telegram.delivery import TelegramDeliveryService


class FakeClient:
    sent: list[tuple[str | int, str]] = []

    def __init__(self, token: str) -> None:
        self.token = token

    async def send_message(self, chat_id: str | int, text: str) -> None:
        self.sent.append((chat_id, text))


@pytest.mark.asyncio
async def test_telegram_delivery_uses_send_message(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.telegram import delivery

    monkeypatch.setattr(delivery, "TelegramClient", FakeClient)
    result = await TelegramDeliveryService().test_channel("token", "42")
    assert result.ok is True
    assert FakeClient.sent[-1][0] == "42"
