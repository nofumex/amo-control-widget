from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.core.config import get_settings
from app.core.security import verify_tenant_token


async def current_tenant_id(
    x_widget_token: str | None = Header(default=None),
    x_tenant_id: int | None = Header(default=None),
) -> int:
    settings = get_settings()
    if x_widget_token:
        try:
            return verify_tenant_token(x_widget_token, settings.app_secret_key)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid widget token") from exc
    if settings.app_env == "local" and x_tenant_id:
        return int(x_tenant_id)
    if settings.app_env == "local":
        return settings.widget_dev_tenant_id
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Widget authentication required")
