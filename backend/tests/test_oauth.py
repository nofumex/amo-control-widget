from __future__ import annotations

import datetime as dt

from app.amo.oauth import token_expires_soon


def test_oauth_token_expiry_helper() -> None:
    now = dt.datetime(2026, 6, 28, 9, tzinfo=dt.UTC)
    assert token_expires_soon(now + dt.timedelta(minutes=5), now=now)
    assert not token_expires_soon(now + dt.timedelta(hours=2), now=now)
