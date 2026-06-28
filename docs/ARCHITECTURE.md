# Architecture

The product is split into four layers:

1. Widget UI: plain TypeScript rendered inside amoCRM settings/card locations.
2. Widget API: FastAPI endpoints, tenant-aware auth, settings, report snapshots, Telegram actions.
3. Domain services: report builder, event catalog, renderer, metrics. This layer is testable without amoCRM.
4. Integrations: amoCRM/Kommo client, OAuth token lifecycle, Telegram delivery, Redis locks, PostgreSQL storage.

Historical reports use pull-based amoCRM APIs as source of truth:

- `/api/v4/events`
- `/api/v4/tasks`
- `/api/v4/users`
- `/api/v4/account`
- note lookup for call `params.duration`

Webhooks and Digital Pipeline are acceleration inputs only. They write to `event_inbox`; worker processing must still
reconcile with pull-based report builds.

Tenant isolation is done at every table with `tenant_id`. Widget requests are resolved to a tenant through
`widget_api/auth.py`; local private mode allows a dev header, while public mode should validate Kommo secure widget
request tokens before production Marketplace submission.
