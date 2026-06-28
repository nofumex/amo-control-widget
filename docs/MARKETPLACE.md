# Marketplace Readiness

## Public manifest/package

Build with:

```bash
cd widget
npm install
npm run build
npm run zip:public
```

The public package must not include localhost URLs or dev tenant IDs. Operators provide the backend HTTPS URL through widget settings or Marketplace configuration.

## Required production configuration

- `APP_ENV=production`
- `INTEGRATION_MODE=public`
- HTTPS `PUBLIC_BASE_URL`
- OAuth client id/secret and redirect URL
- strong `FERNET_KEY`, `APP_SECRET_KEY`, `WIDGET_SIGNING_SECRET`, `WEBHOOK_SHARED_SECRET`, `INTERNAL_ADMIN_TOKEN`
- `ALLOW_DEV_AUTH=false`

## Pre-submission checklist

- OAuth install/callback tested on a clean Kommo/amoCRM account.
- Widget auth signature format validated against current Kommo Marketplace requirements.
- Webhooks configured with the same shared secret used by backend.
- Public zip generated and inspected.
- Security, privacy, retention and support docs prepared.
- Uninstall/disconnect lifecycle verified.
- API usage stays below 7 RPS and handles 429/5xx retries.
- No generated artifacts, node_modules, caches or local env files committed.
