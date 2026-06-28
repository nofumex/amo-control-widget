from __future__ import annotations

import datetime as dt

from app.amo.oauth import token_expires_soon
from app.amo.oauth_state import hash_state


def test_oauth_token_expiry_helper() -> None:
    now = dt.datetime(2026, 6, 28, 9, tzinfo=dt.UTC)
    assert token_expires_soon(now + dt.timedelta(minutes=5), now=now)
    assert not token_expires_soon(now + dt.timedelta(hours=2), now=now)


def test_oauth_state_hash_is_stable_and_not_plaintext() -> None:
    state = "state-value"
    assert hash_state(state) == hash_state(state)
    assert hash_state(state) != state
