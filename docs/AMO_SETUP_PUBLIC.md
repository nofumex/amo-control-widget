# Public Marketplace Setup

Public mode requires:

- production HTTPS `PUBLIC_BASE_URL`;
- stable OAuth redirect `PUBLIC_BASE_URL/api/oauth/callback`;
- no account-specific hardcode;
- encrypted token storage;
- clear uninstall/disconnect flow;
- moderation-ready widget zip and security documents.

Set:

```env
INTEGRATION_MODE=public
PUBLIC_BASE_URL=https://your-domain.example
AMO_CLIENT_ID=...
AMO_CLIENT_SECRET=...
AMO_REDIRECT_URI=https://your-domain.example/api/oauth/callback
```

Before submitting to amoMarket/Kommo Marketplace, validate secure widget request/disposable token handling against the
current official Marketplace rules for your region.
