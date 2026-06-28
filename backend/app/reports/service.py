from __future__ import annotations

import datetime as dt
import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.amo.client import AmoClient
from app.core.config import Settings
from app.core.crypto import SecretBox
from app.core.errors import AppError
from app.core.time import day_bounds
from app.db.models import OAuthToken, ReportConfig, ReportSnapshot, Tenant
from app.reports.builder import ReportBuilder
from app.reports.event_catalog import EVENT_CATALOG
from app.reports.metrics import extract_event_note_id
from app.reports.renderer import render_telegram_report
from app.reports.schemas import ReportConfigSchema


class ReportDataService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings

    async def build_and_store(self, tenant: Tenant, report_date: dt.date) -> ReportSnapshot:
        if tenant.status != "active":
            raise AppError("Tenant is not connected", public_message="amoCRM OAuth не подключен или требует переподключения.")
        token_row = (await self.session.scalars(select(OAuthToken).where(OAuthToken.tenant_id == tenant.id))).first()
        if token_row is None:
            raise AppError("OAuth token is missing", public_message="amoCRM OAuth token отсутствует.")
        config_row = (await self.session.scalars(select(ReportConfig).where(ReportConfig.tenant_id == tenant.id))).first()
        config = ReportConfigSchema.model_validate(config_row.__dict__) if config_row else ReportConfigSchema()
        start, end = day_bounds(report_date, config.timezone)
        box = SecretBox(self.settings.fernet_key or self.settings.app_secret_key)
        amo = AmoClient(tenant.base_url, box.decrypt(token_row.access_token_encrypted), rps_limit=self.settings.amo_rps_limit)
        try:
            users = await amo.get_users()
            user_ids = _selected_user_ids(users, config)
            events = await amo.get_events(
                int(start.timestamp()),
                int(end.timestamp()),
                _enabled_event_types(config),
                user_ids,
            )
            notes_by_key = await self._fetch_call_notes(amo, events)
            overdue = {
                user_id: len(await amo.get_incomplete_tasks_due_to(user_id, int(end.timestamp())))
                for user_id in user_ids
            }
        finally:
            await amo.aclose()

        snapshot_payload = ReportBuilder(config).build(
            tenant_id=tenant.id,
            account_id=tenant.account_id,
            report_date=report_date,
            users=users,
            events=events,
            overdue_tasks_by_user=overdue,
            note_lookup=lambda entity_type, entity_id, note_id: notes_by_key.get((entity_type, entity_id, note_id)),
        )
        rendered = render_telegram_report(snapshot_payload)
        raw_json = snapshot_payload.model_dump(mode="json")
        config_hash = hashlib.sha256(json.dumps(config.model_dump(), sort_keys=True, default=str).encode()).hexdigest()
        snapshot = (
            await self.session.scalars(
                select(ReportSnapshot).where(ReportSnapshot.tenant_id == tenant.id, ReportSnapshot.report_date == report_date)
            )
        ).first()
        if snapshot is None:
            snapshot = ReportSnapshot(tenant_id=tenant.id, report_date=report_date)
            self.session.add(snapshot)
        snapshot.timezone = config.timezone
        snapshot.config_version = config.version
        snapshot.config_hash = config_hash
        snapshot.raw_json = raw_json
        snapshot.rendered_text = rendered
        snapshot.status = "built"
        snapshot.error_message = ""
        snapshot.source_window_start = start
        snapshot.source_window_end = end
        await self.session.commit()
        await self.session.refresh(snapshot)
        return snapshot

    async def _fetch_call_notes(self, amo: AmoClient, events: list[dict[str, Any]]) -> dict[tuple[str, int, int], dict[str, Any]]:
        result: dict[tuple[str, int, int], dict[str, Any]] = {}
        for event in events:
            if event.get("type") not in {"incoming_call", "outgoing_call"}:
                continue
            note_id = extract_event_note_id(event)
            entity_type = str(event.get("entity_type") or "")
            entity_id = int(event.get("entity_id") or 0)
            if not note_id or not entity_type or not entity_id:
                continue
            key = (entity_type, entity_id, note_id)
            if key not in result:
                result[key] = await amo.get_note(entity_type, entity_id, note_id)
        return result


def _enabled_event_types(config: ReportConfigSchema) -> list[str]:
    configured = set(config.enabled_activity_events) | set(config.enabled_counter_events) | set(config.enabled_penalty_events)
    defaults = {item.code for item in EVENT_CATALOG}
    return sorted(configured & defaults)


def _selected_user_ids(users: list[dict[str, Any]], config: ReportConfigSchema) -> list[int]:
    available = {int(user["id"]) for user in users if user.get("id")}
    selected = set(config.selected_user_ids) or available
    excluded = set(config.excluded_user_ids)
    return sorted((selected & available) - excluded)
