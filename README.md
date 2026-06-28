# amo-control-widget

amo-control-widget переносит отчеты `control-agent` из Telegram-first бота в amoCRM/Kommo widget с backend-first архитектурой.
Виджет становится главным UI для настроек и просмотра отчетов, Telegram остается опциональным каналом доставки.

## Что внутри

- FastAPI backend: health, OAuth, widget API, webhooks.
- Async worker: Redis locks, OAuth refresh/scheduler foundation.
- PostgreSQL schema: tenants, OAuth tokens, report configs, snapshots, Telegram channels, delivery logs, call-note cache, sync state, webhook inbox.
- Report domain logic: непрерывная работа, call duration filtering через note `params.duration`, overdue task counters, русский Telegram renderer.
- Widget package: lightweight TypeScript UI, private/public manifests, zip build.

## Private и public

- `private` подходит для MVP в одном amoCRM аккаунте, но БД и API все равно multi-tenant.
- `public` готовит ту же кодовую базу к Marketplace: OAuth lifecycle, tenant isolation, encrypted tokens, moderation/security docs.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
```

Для реального OAuth заполните `AMO_CLIENT_ID`, `AMO_CLIENT_SECRET`, `AMO_REDIRECT_URI`, `PUBLIC_BASE_URL`,
`FERNET_KEY` или `APP_SECRET_KEY`.

## Тесты и проверки

```bash
make install
make test
make lint
make typecheck
```

## Widget build

```bash
cd widget
npm install
npm run build
npm run zip:private
npm run zip:public
```

Архивы появятся как `widget/widget-private.zip` и `widget/widget-public.zip`.

## Backend

Backend лежит в `backend/app`. Основные точки:

- `reports/` - доменная логика отчетов.
- `amo/` - async amoCRM client, OAuth helpers, rate limiting.
- `telegram/` - Telegram client and delivery service.
- `widget_api/` - endpoints для виджета.
- `db/` - SQLAlchemy models and Alembic migrations.
- `worker/` - polling worker, Redis locks, scheduled jobs.

## Что требует реального amoCRM аккаунта

- OAuth install/callback.
- Pull `/api/v4/events`, `/api/v4/tasks`, `/api/v4/users`, `/api/v4/account`.
- Проверка call-note lookup на реальных звонках.
- Проверка widget install внутри amoCRM settings.
- Финальная валидация public-mode disposable token/JWT требований для Marketplace.

## Документация

Смотрите `docs/ARCHITECTURE.md`, `docs/AMO_SETUP_PRIVATE.md`, `docs/AMO_SETUP_PUBLIC.md`,
`docs/TELEGRAM_SETUP.md`, `docs/SECURITY.md`, `docs/DEPLOYMENT.md`, `docs/MODERATION_CHECKLIST.md`.
