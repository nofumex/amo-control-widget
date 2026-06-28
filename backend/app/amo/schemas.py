from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


class OAuthTokenPayload(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int = 86400
    token_type: str = "Bearer"
    scope: str = ""

    def expires_at(self, skew_seconds: int = 0) -> dt.datetime:
        return dt.datetime.now(dt.UTC) + dt.timedelta(seconds=max(0, self.expires_in - skew_seconds))


class AmoAccount(BaseModel):
    id: int
    name: str = ""
    subdomain: str = ""
    base_url: str = ""
    timezone: str = "UTC"
