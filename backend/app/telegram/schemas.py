from __future__ import annotations

from pydantic import BaseModel


class TelegramSettings(BaseModel):
    enabled: bool = False
    bot_token: str | None = None
    bot_token_masked: str = ""
    admin_chat_id: str | None = None
    admin_chat_id_masked: str = ""
    admin_username: str = ""
    last_test_status: str = ""
