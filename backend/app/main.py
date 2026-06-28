from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.core.errors import AppError
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
    if settings.is_development:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(title="amo-control-widget", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin for origin in settings.cors_allowed_origins if "*" not in origin],
    allow_origin_regex=r"https://.*\.(amocrm\.ru|kommo\.com)$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_and_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    started = time.monotonic()
    try:
        response = await call_next(request)
    except AppError as exc:
        response = JSONResponse(status_code=400, content={"error": {"message": exc.public_message}})
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-Response-Time-Ms"] = str(round((time.monotonic() - started) * 1000, 2))
    return response


@app.get("/health")
async def health() -> dict:
    return {"status": "healthy"}


@app.get("/ready")
async def ready() -> JSONResponse | dict:
    checks: dict[str, str] = {}
    try:
        async with engine.connect() as conn:
            await conn.execute(text("select 1"))
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "failed"
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "failed"
    finally:
        await redis.aclose()
    checks["config"] = "ok"
    ok = all(value == "ok" for value in checks.values())
    payload = {"status": "ready" if ok else "not_ready", "checks": checks}
    if not ok:
        return JSONResponse(status_code=503, content=payload)
    return payload


app.include_router(oauth_router)
app.include_router(status_router)
app.include_router(settings_router)
app.include_router(reports_router)
app.include_router(telegram_router)
app.include_router(status_extra_router)
app.include_router(webhooks_router)
