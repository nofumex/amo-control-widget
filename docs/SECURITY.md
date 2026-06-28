# Security

## Widget authentication

Production widget endpoints fail closed. They do not accept tenant IDs from the browser.

Accepted production headers:

- `X-KOMMO-Account-Id`
- `X-KOMMO-Subdomain` optional but checked when present
- `X-KOMMO-Timestamp`
- `X-KOMMO-Signature`

The signature adapter signs:

```text
METHOD\nPATH\nCANONICAL_QUERY\nTIMESTAMP\nACCOUNT_ID\nSHA256(BODY)
```

using HMAC-SHA256 and `WIDGET_SIGNING_SECRET`, with a bounded timestamp window. This is isolated in `app.core.security` so the exact official Kommo secure-request adapter can be adjusted without touching endpoint authorization. Development headers are accepted only when `APP_ENV` is local/development/test and `ALLOW_DEV_AUTH=true`.

## Admin/internal auth

OAuth refresh/disconnect maintenance endpoints require `Authorization: Bearer INTERNAL_ADMIN_TOKEN`.

## OAuth

OAuth install creates one-time state rows in `oauth_states`. Callback rejects missing, expired or reused states. Access and refresh tokens are encrypted at rest with `SecretBox`.

## Webhooks

Production webhooks require HMAC signature headers, content-type allowlist, payload size limit, tenant lookup by account/subdomain, and deduplication by deterministic body hash. Unknown tenants are ignored without poisoning `event_inbox`.

## Data protection

Stored raw data is minimized to report snapshots, sanitized webhook inbox payloads, delivery logs and encrypted credentials. Worker retention cleanup enforces configured retention periods.

## Secret management

Production startup fails on placeholder secrets, localhost public URL, empty OAuth credentials, or enabled dev auth.
