# Private Integration Setup

1. Create a private integration in amoCRM/Kommo.
2. Set redirect URI to `PUBLIC_BASE_URL/api/oauth/callback`.
3. Copy client id and client secret into `.env`.
4. Start the backend with `docker compose up --build`.
5. Open `PUBLIC_BASE_URL/api/oauth/install` and complete authorization.
6. Build `widget-private.zip` and install it as a widget package for the target account.

For local widget testing use:

- `backend_url`: `http://localhost:8000`
- `tenant_id`: the tenant id returned after OAuth callback or `1` for local mock mode.

Private mode still stores tokens encrypted and keeps tenant-aware schema so it can be promoted to public mode later.
