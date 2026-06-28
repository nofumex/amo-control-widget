# Telegram Setup

Telegram is an optional delivery channel, not the main UI.

1. Create a bot with BotFather.
2. Ask the target admin to start the bot once.
3. In the amoCRM widget, open Telegram tab.
4. Enable delivery, enter bot token and admin chat id.
5. Press `Отправить тест`.

The backend stores `bot_token` and `admin_chat_id` encrypted. API responses return masked values only.

Common errors:

- invalid token: create/check BotFather token;
- invalid chat id: check the chat id value;
- bot was not started: ask the admin to send `/start` to the bot;
- Telegram unavailable: retry later, delivery logs keep the last error.
