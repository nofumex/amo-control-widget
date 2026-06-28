from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.client import AmoClient
from app.core.config import Settings
from app.core.crypto import SecretBox
from app.core.errors import AppError
from app.db.models import OAuthToken, Tenant


@asynccontextmanager
async def amo_client_for_tenant(
    session: AsyncSession,
    tenant: Tenant,
    settings: Settings,
) -> AsyncIterator[AmoClient]:
    if tenant.status != "active":
        raise AppError("Tenant is not active", public_message="amoCRM OAuth требует переподключения.")
    token = (await session.scalars(select(OAuthToken).where(OAuthToken.tenant_id == tenant.id))).first()
    if token is None:
        raise AppError("OAuth token missing", public_message="amoCRM OAuth token отсутствует.")
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    client = AmoClient(tenant.base_url, box.decrypt(token.access_token_encrypted), rps_limit=settings.amo_rps_limit)
    try:
        yield client
    finally:
        await client.aclose()
