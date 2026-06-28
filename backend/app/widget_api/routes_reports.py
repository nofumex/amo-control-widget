from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.crypto import SecretBox
from app.core.errors import AppError
from app.db.models import DeliveryLog, ReportSnapshot, TelegramChannel, Tenant
from app.db.session import get_session
from app.reports.service import ReportDataService
from app.telegram.delivery import TelegramDeliveryService
from app.widget_api.auth import require_widget_auth

router = APIRouter(prefix="/api/widget/reports", tags=["widget-reports"])


@router.get("")
async def list_reports(
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=30, ge=1, le=100),
) -> list[dict]:
    rows = (
        await session.scalars(
            select(ReportSnapshot)
            .where(ReportSnapshot.tenant_id == tenant.id)
            .order_by(ReportSnapshot.report_date.desc())
            .limit(limit)
        )
    ).all()
    return [
        {
            "date": row.report_date.isoformat(),
            "status": row.status,
            "created_at": row.created_at,
            "error_message": row.error_message,
        }
        for row in rows
    ]


@router.get("/{report_date}")
async def get_report(
    report_date: dt.date,
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant.id, ReportSnapshot.report_date == report_date)
        )
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"raw_json": snapshot.raw_json, "rendered_text": snapshot.rendered_text, "status": snapshot.status}


@router.post("/{report_date}/build")
async def build_report(
    report_date: dt.date,
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    _validate_report_date(report_date)
    try:
        snapshot = await ReportDataService(session, settings).build_and_store(tenant, report_date)
    except AppError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.public_message) from exc
    return {"ok": True, "raw_json": snapshot.raw_json, "rendered_text": snapshot.rendered_text}


@router.post("/{report_date}/send-telegram")
async def send_report_to_telegram(
    report_date: dt.date,
    tenant: Tenant = Depends(require_widget_auth),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> dict:
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant.id, ReportSnapshot.report_date == report_date)
        )
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Report not found")
    channel = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant.id))).first()
    if channel is None or not channel.enabled:
        raise HTTPException(status_code=400, detail="Telegram delivery disabled")
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    idempotency_key = f"telegram:{tenant.id}:{snapshot.id}"
    existing_log = (
        await session.scalars(
            select(DeliveryLog).where(
                DeliveryLog.tenant_id == tenant.id,
                DeliveryLog.idempotency_key == idempotency_key,
                DeliveryLog.status == "sent",
            )
        )
    ).first()
    if existing_log:
        return {"ok": True, "status": "already_sent"}
    log = DeliveryLog(
        tenant_id=tenant.id,
        snapshot_id=snapshot.id,
        channel="telegram",
        status="pending",
        attempts=1,
        idempotency_key=idempotency_key,
    )
    session.add(log)
    try:
        await TelegramDeliveryService().send_report(
            box.decrypt(channel.bot_token_encrypted),
            box.decrypt(channel.admin_chat_id_encrypted),
            snapshot.rendered_text,
        )
        log.status = "sent"
        log.sent_at = dt.datetime.now(dt.UTC)
        await session.commit()
        return {"ok": True, "status": "sent"}
    except Exception as exc:
        log.status = "failed"
        log.last_error = str(exc)
        await session.commit()
        raise HTTPException(status_code=502, detail="Telegram delivery failed") from exc


def _validate_report_date(report_date: dt.date) -> None:
    if report_date > dt.datetime.now(dt.UTC).date() + dt.timedelta(days=1):
        raise HTTPException(status_code=422, detail="Report date is too far in the future")
