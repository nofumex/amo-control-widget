from __future__ import annotations

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import SignedRequest, verify_request_signature, verify_tenant_token
from app.db.models import Tenant
from app.db.session import get_session


async def require_widget_auth(
    request: Request,
    x_widget_token: str | None = Header(default=None),
    x_dev_tenant_id: int | None = Header(default=None),
    x_kommo_account_id: int | None = Header(default=None),
    x_kommo_subdomain: str | None = Header(default=None),
    x_kommo_timestamp: int | None = Header(default=None),
    x_kommo_signature: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> Tenant:
    tenant_id = await _resolve_dev_or_legacy_token(settings, x_widget_token, x_dev_tenant_id)
    if tenant_id is not None:
        tenant = await session.get(Tenant, tenant_id)
        if tenant is None or tenant.status not in {"active", "oauth_error"}:
            raise _auth_error()
        return tenant

    if not all([x_kommo_account_id, x_kommo_timestamp, x_kommo_signature]):
        raise _auth_error()

    body = await request.body()
    signed = SignedRequest(
        method=request.method,
        path=request.url.path,
        query=request.url.query,
        timestamp=int(x_kommo_timestamp or 0),
        account_id=int(x_kommo_account_id or 0),
        body=body,
    )
    if not verify_request_signature(
        signed,
        x_kommo_signature or "",
        settings.widget_signing_secret,
        ttl_seconds=settings.widget_signature_ttl_seconds,
    ):
        raise _auth_error()

    tenant = (
        await session.scalars(
            select(Tenant).where(Tenant.account_id == int(x_kommo_account_id or 0), Tenant.status != "deleted")
        )
    ).first()
    if tenant is None:
        raise _auth_error()
    if x_kommo_subdomain and tenant.subdomain and tenant.subdomain != x_kommo_subdomain:
        raise _auth_error()
    return tenant


async def current_tenant_id(tenant: Tenant = Depends(require_widget_auth)) -> int:
    return tenant.id


async def require_internal_admin(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    if not settings.internal_admin_token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Internal auth is not configured")
    expected = f"Bearer {settings.internal_admin_token}"
    if authorization != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


async def _resolve_dev_or_legacy_token(
    settings: Settings,
    x_widget_token: str | None,
    x_dev_tenant_id: int | None,
) -> int | None:
    if settings.allow_dev_auth and settings.is_development:
        if x_dev_tenant_id is not None:
            return int(x_dev_tenant_id)
        if settings.widget_dev_tenant_id is not None:
            return settings.widget_dev_tenant_id
        if x_widget_token:
            try:
                return verify_tenant_token(x_widget_token, settings.app_secret_key)
            except ValueError as exc:
                raise _auth_error() from exc
    if settings.app_env == "production" and (x_dev_tenant_id is not None or x_widget_token):
        raise _auth_error()
    return None


def _auth_error() -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Widget authentication failed")
