# amo-control-widget

amo-control-widget is a FastAPI + TypeScript amoCRM/Kommo widget for manager activity reporting. The widget is the primary UI for settings and report viewing; Telegram is an optional tenant-scoped delivery channel.

## Architecture

- `backend/app/widget_api`: tenant-aware widget API, OAuth, webhooks.
- `backend/app/amo`: Kommo/amoCRM OAuth, API client, rate limiting, tenant client factory.
- `backend/app/reports`: testable report domain logic and renderer.
- `backend/app/worker`: Redis-locked worker jobs for token refresh and retention cleanup.
- `widget`: lightweight TypeScript widget package and deterministic zip builder.
- `docs`: security, deployment, marketplace and operations docs.

## Local setup

```bash
cp .env.example .env
make install
cd widget && npm install
```

For local API/widget development set:

```env
APP_ENV=development
ALLOW_DEV_AUTH=true
WIDGET_DEV_TENANT_ID=1
```

Production must set `APP_ENV=production`, `ALLOW_DEV_AUTH=false`, HTTPS `PUBLIC_BASE_URL`, OAuth credentials, `FERNET_KEY`, `APP_SECRET_KEY`, `WIDGET_SIGNING_SECRET`, `WEBHOOK_SHARED_SECRET`, and `INTERNAL_ADMIN_TOKEN`.

## Run

```bash
make run-api
make run-worker
```

Docker:

```bash
docker compose up --build
curl http://localhost:8000/health
curl http://localhost:8000/ready
```

## Quality gates

```bash
make lint
make typecheck
make test
make widget-build
make package-widget
make ci
```

## Widget packaging

```bash
cd widget
npm install
npm run typecheck
npm run build
npm run zip:private
npm run zip:public
```

Public archive: `widget/widget-public.zip`.
Private/dev archive: `widget/widget-private.zip`.

## OAuth

1. Configure redirect URL as `https://your-domain.example/api/oauth/callback`.
2. Open `/api/oauth/install` to create a signed OAuth state and redirect to Kommo/amoCRM authorization.
3. Callback validates state, exchanges code, fetches account info, creates/updates tenant, and stores encrypted tokens.

Internal maintenance endpoints `/api/oauth/refresh/{tenant_id}` and `/api/oauth/disconnect/{tenant_id}` require `Authorization: Bearer INTERNAL_ADMIN_TOKEN`.

## Report flow

Report build endpoint uses the authenticated tenant, decrypts its amoCRM token, fetches users/events/tasks/notes through `AmoClient`, applies configured filters, stores `report_snapshots`, and returns rendered text plus JSON.

## Public Marketplace checklist

See `docs/MARKETPLACE.md`. Manual Marketplace steps still required: configure production HTTPS URL, OAuth app settings, widget signing secret delivery/verification format if Kommo changes it, moderation metadata and support contacts.
