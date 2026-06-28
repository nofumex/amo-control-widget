from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.base import Base
from app.db.session import engine
from app.widget_api.routes_oauth import router as oauth_router
from app.widget_api.routes_reports import router as reports_router
from app.widget_api.routes_settings import router as settings_router
from app.widget_api.routes_status import router as status_router
from app.widget_api.routes_status_extra import router as status_extra_router
from app.widget_api.routes_telegram import router as telegram_router
from app.widget_api.routes_webhooks import router as webhooks_router

settings = get_settings()
configure_logging(settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if settings.app_env == "local":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="amo-control-widget", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in settings.cors_allowed_origins if "*" not in origin],
    allow_origin_regex=r"https://.*\.(amocrm\.ru|kommo\.com)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.get("/ready")
async def ready() -> dict:
    return {"status": "ready"}


app.include_router(oauth_router)
app.include_router(status_router)
app.include_router(settings_router)
app.include_router(reports_router)
app.include_router(telegram_router)
app.include_router(status_extra_router)
app.include_router(webhooks_router)
