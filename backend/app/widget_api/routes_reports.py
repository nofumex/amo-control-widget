from __future__ import annotations

import datetime as dt
import hashlib
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.crypto import SecretBox
from app.db.models import DeliveryLog, ReportConfig, ReportSnapshot, TelegramChannel, Tenant
from app.db.session import get_session
from app.reports.builder import ReportBuilder
from app.reports.renderer import render_telegram_report
from app.reports.schemas import ReportConfigSchema
from app.telegram.delivery import TelegramDeliveryService
from app.widget_api.auth import current_tenant_id

router = APIRouter(prefix="/api/widget/reports", tags=["widget-reports"])


@router.get("")
async def list_reports(tenant_id: int = Depends(current_tenant_id), session: AsyncSession = Depends(get_session)) -> list[dict]:
    rows = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant_id).order_by(ReportSnapshot.report_date.desc()).limit(30)
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
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant_id, ReportSnapshot.report_date == report_date)
        )
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"raw_json": snapshot.raw_json, "rendered_text": snapshot.rendered_text, "status": snapshot.status}


@router.post("/{report_date}/build")
async def build_report(
    report_date: dt.date,
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    tenant = await session.get(Tenant, tenant_id)
    config_row = (await session.scalars(select(ReportConfig).where(ReportConfig.tenant_id == tenant_id))).first()
    config = ReportConfigSchema.model_validate(config_row.__dict__) if config_row else ReportConfigSchema()
    snapshot_payload = ReportBuilder(config).build(
        tenant_id=tenant_id,
        account_id=tenant.account_id if tenant else None,
        report_date=report_date,
        users=[],
        events=[],
        overdue_tasks_by_user={},
    )
    rendered = render_telegram_report(snapshot_payload)
    raw_json = snapshot_payload.model_dump(mode="json")
    config_hash = hashlib.sha256(json.dumps(config.model_dump(), sort_keys=True, default=str).encode()).hexdigest()
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant_id, ReportSnapshot.report_date == report_date)
        )
    ).first()
    if snapshot is None:
        snapshot = ReportSnapshot(tenant_id=tenant_id, report_date=report_date)
        session.add(snapshot)
    snapshot.timezone = config.timezone
    snapshot.config_version = config.version
    snapshot.config_hash = config_hash
    snapshot.raw_json = raw_json
    snapshot.rendered_text = rendered
    snapshot.status = "built"
    snapshot.error_message = ""
    snapshot.source_window_start = snapshot_payload.source_window_start
    snapshot.source_window_end = snapshot_payload.source_window_end
    await session.commit()
    return {"ok": True, "raw_json": raw_json, "rendered_text": rendered}


@router.post("/{report_date}/send-telegram")
async def send_report_to_telegram(
    report_date: dt.date,
    tenant_id: int = Depends(current_tenant_id),
    session: AsyncSession = Depends(get_session),
) -> dict:
    snapshot = (
        await session.scalars(
            select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant_id, ReportSnapshot.report_date == report_date)
        )
    ).first()
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Report not found")
    channel = (await session.scalars(select(TelegramChannel).where(TelegramChannel.tenant_id == tenant_id))).first()
    if channel is None or not channel.enabled:
        raise HTTPException(status_code=400, detail="Telegram delivery disabled")
    settings = get_settings()
    box = SecretBox(settings.fernet_key or settings.app_secret_key)
    log = DeliveryLog(tenant_id=tenant_id, snapshot_id=snapshot.id, channel="telegram", status="pending", attempts=1)
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
        raise HTTPException(status_code=502, detail=str(exc)) from exc
