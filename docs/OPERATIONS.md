# Operations

## Health and readiness

- `/health`: shallow process health.
- `/ready`: checks database, Redis and config load.

## Migrations

```bash
cd backend
alembic -c app/db/alembic.ini upgrade head
```

## Worker

Run one or more worker instances safely. Redis locks prevent concurrent token refresh and cleanup jobs. Worker handles SIGINT/SIGTERM graceful shutdown.

```bash
make run-worker
```

## Logs

Production logs are structured JSON through `structlog`. Do not log tokens, OAuth codes, Telegram tokens, signatures or raw payloads.

## Retention

Configured by:

- `REPORT_SNAPSHOT_RETENTION_DAYS`
- `WEBHOOK_INBOX_RETENTION_DAYS`
- `DELIVERY_LOG_RETENTION_DAYS`

Worker cleanup enforces these values.

## Backups

Back up PostgreSQL and keep the encryption key material separately. Losing `FERNET_KEY`/`APP_SECRET_KEY` makes stored OAuth/Telegram secrets unrecoverable.

## Incident response

1. Rotate affected Kommo/OAuth credentials or Telegram bot token.
2. Rotate signing/webhook/admin secrets.
3. Disable affected tenant by setting `tenants.status=disabled`.
4. Review `delivery_logs`, `event_inbox`, application logs and reverse-proxy logs by request id.
