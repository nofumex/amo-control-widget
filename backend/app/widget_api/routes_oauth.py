from __future__ import annotations

from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.client import AmoClient
from app.amo.oauth import authorization_url, exchange_code, refresh_token
from app.amo.oauth_state import consume_oauth_state, create_oauth_state
from app.core.config import Settings, get_settings
from app.core.crypto import SecretBox
from app.db.models import OAuthToken, ReportConfig, Tenant
from app.db.session import get_session
from app.reports.schemas import ReportConfigSchema
from app.widget_api.auth import require_internal_admin

router = APIRouter(prefix="/api/oauth", tags=["oauth"])


@router.get("/install")
async def oauth_install(
    referer: str | None = None,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    state = await create_oauth_state(session, referer=referer or "")
    return RedirectResponse(authorization_url(settings, state=state))


@router.get("/callback", response_class=HTMLResponse)
async def oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    referer: str | None = None,
    from_widget: str | None = None,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> str:
    try:
        state_row = await consume_oauth_state(session, state)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc

    base_url = _base_url_from_referer(referer or state_row.referer)
    token = await exchange_code(settings, base_url, code)
    amo = AmoClient(base_url, token.access_token, rps_limit=settings.amo_rps_limit)
    try:
        account = await amo.get_account()
    finally:
        await amo.aclose()
    account_id = int(account.get("id") or 0) or None
    subdomain = account.get("subdomain") or urlparse(base_url).hostname or ""
    tenant = await _upsert_tenant(
        session,
        account_id,
        subdomain,
        base_url,
        settings.integration_mode,
        settings.amo_client_id,
    )
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    existing = (await session.scalars(select(OAuthToken).where(OAuthToken.tenant_id == tenant.id))).first()
    if existing is None:
        existing = OAuthToken(
            tenant_id=tenant.id,
            access_token_encrypted="",
            refresh_token_encrypted="",
            expires_at=token.expires_at(300),
        )
        session.add(existing)
    existing.access_token_encrypted = box.encrypt(token.access_token)
    existing.refresh_token_encrypted = box.encrypt(token.refresh_token)
    existing.expires_at = token.expires_at(300)
    existing.scope = token.scope
    await session.commit()
    source = "из виджета" if from_widget else "из OAuth"
    return f"<html><body><h1>amo-control-widget подключен</h1><p>Tenant #{tenant.id} создан {source}.</p></body></html>"


@router.post("/refresh/{tenant_id}", dependencies=[Depends(require_internal_admin)])
async def oauth_refresh(
    tenant_id: int,
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tenant = await session.get(Tenant, tenant_id)
    token_row = (await session.scalars(select(OAuthToken).where(OAuthToken.tenant_id == tenant_id))).first()
    if tenant is None or token_row is None or tenant.status == "disabled":
        return {"ok": False, "status": "not_connected"}
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    try:
        payload = await refresh_token(settings, tenant.base_url, box.decrypt(token_row.refresh_token_encrypted))
        token_row.access_token_encrypted = box.encrypt(payload.access_token)
        token_row.refresh_token_encrypted = box.encrypt(payload.refresh_token)
        token_row.expires_at = payload.expires_at(300)
        token_row.scope = payload.scope
        tenant.status = "active"
        await session.commit()
        return {"ok": True, "expires_at": token_row.expires_at}
    except Exception:
        tenant.status = "oauth_error"
        await session.commit()
        raise


@router.post("/disconnect/{tenant_id}", dependencies=[Depends(require_internal_admin)])
async def oauth_disconnect(tenant_id: int, session: AsyncSession = Depends(get_session)) -> dict:
    tenant = await session.get(Tenant, tenant_id)
    if tenant:
        tenant.status = "disabled"
        await session.commit()
    return {"ok": True}


def _base_url_from_referer(referer: str | None) -> str:
    if not referer:
        return "https://www.amocrm.ru"
    parsed = urlparse(referer if referer.startswith("http") else f"https://{referer}")
    return f"{parsed.scheme}://{parsed.netloc}".rstrip("/")


async def _upsert_tenant(
    session: AsyncSession,
    account_id: int | None,
    subdomain: str,
    base_url: str,
    mode: str,
    integration_client_id: str,
) -> Tenant:
    stmt = (
        select(Tenant).where(Tenant.account_id == account_id, Tenant.integration_client_id == integration_client_id)
        if account_id
        else select(Tenant).where(Tenant.subdomain == subdomain, Tenant.integration_client_id == integration_client_id)
    )
    tenant = (await session.scalars(stmt)).first()
    if tenant is None:
        tenant = Tenant(
            account_id=account_id,
            subdomain=subdomain,
            base_url=base_url,
            integration_client_id=integration_client_id,
            mode=mode,
            status="active",
        )
        session.add(tenant)
        await session.flush()
        session.add(ReportConfig(tenant_id=tenant.id, **ReportConfigSchema().model_dump()))
    else:
        tenant.base_url = base_url
        tenant.subdomain = subdomain
        tenant.status = "active"
    await session.commit()
    await session.refresh(tenant)
    return tenant
