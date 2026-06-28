from __future__ import annotations

from pydantic import BaseModel


class TenantPublic(BaseModel):
    id: int
    account_id: int | None = None
    subdomain: str = ""
    base_url: str = ""
    mode: str = "private"
    status: str = "active"
