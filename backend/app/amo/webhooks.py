from __future__ import annotations

from typing import Any


def extract_account_hint(payload: dict[str, Any]) -> tuple[int | None, str]:
    account = payload.get("account") or payload.get("account_info") or {}
    account_id = account.get("id") or payload.get("account_id")
    subdomain = account.get("subdomain") or payload.get("subdomain") or ""
    return (int(account_id) if account_id else None, str(subdomain))
