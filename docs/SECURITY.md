# Security

- OAuth access and refresh tokens are encrypted at rest through `SecretBox`.
- Telegram token and chat id are encrypted at rest.
- Secrets are masked in widget API responses.
- No hardcoded Telegram admin id, amoCRM token, company users, or account id.
- CORS is restricted to configured dev origins and amoCRM/Kommo origins.
- amoCRM API calls use rate limiting capped below 7 RPS and retries for 429/5xx.
- Widget API never trusts arbitrary `tenant_id` in production mode.
- Webhooks are accepted quickly into `event_inbox`; processing happens out of request path.
- Logs should not include decrypted secrets.

Production hardening before Marketplace:

- replace local dev tenant header with official secure widget request verification;
- rotate `APP_SECRET_KEY`/`FERNET_KEY`;
- enable HTTPS only;
- add WAF or reverse-proxy rate limits for public endpoints;
- add audit retention policy for delivery logs and webhook inbox.
