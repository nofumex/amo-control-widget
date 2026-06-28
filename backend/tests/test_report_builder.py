from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from app.reports.builder import ReportBuilder
from app.reports.renderer import render_telegram_report
from app.reports.schemas import ReportConfigSchema


def ts(hour: int, minute: int = 0) -> int:
    value = dt.datetime(2026, 6, 28, hour, minute, tzinfo=ZoneInfo("Asia/Krasnoyarsk"))
    return int(value.timestamp())


def test_report_builder_aggregates_events_and_calls() -> None:
    config = ReportConfigSchema(
        timezone="Asia/Krasnoyarsk",
        selected_user_ids=[1],
        user_groups={"1": "Продажи"},
        incoming_call_min_duration_seconds=30,
    )
    events = [
        {"id": 1, "type": "task_completed", "created_by": 1, "created_at": ts(9, 0)},
        {"id": 2, "type": "common_note_added", "created_by": 1, "created_at": ts(9, 5)},
        {
            "id": 3,
            "type": "incoming_call",
            "created_by": 1,
            "created_at": ts(9, 7),
            "entity_type": "lead",
            "entity_id": 10,
            "value_after": [{"note": {"id": 777}}],
        },
        {"id": 4, "type": "task_deadline_changed", "created_by": 1, "created_at": ts(18, 0)},
    ]
    notes = {("lead", 10, 777): {"params": {"duration": 45}}}
    snapshot = ReportBuilder(config).build(
        tenant_id=1,
        report_date=dt.date(2026, 6, 28),
        users=[{"id": 1, "name": "Иван Иванов"}],
        events=events,
        overdue_tasks_by_user={1: 2},
        note_lookup=lambda entity_type, entity_id, note_id: notes[(entity_type, entity_id, note_id)],
    )
    row = snapshot.users[0]
    assert row.group == "Продажи"
    assert row.completed_tasks_count == 1
    assert row.deadline_changes_count == 1
    assert row.incoming_calls_count == 1
    assert row.notes_count == 1
    assert row.overdue_tasks_count == 2
    assert row.continuous_work_seconds == 7 * 60


def test_call_duration_filter_excludes_short_incoming_call() -> None:
    config = ReportConfigSchema(timezone="Asia/Krasnoyarsk", selected_user_ids=[1], incoming_call_min_duration_seconds=30)
    snapshot = ReportBuilder(config).build(
        tenant_id=1,
        report_date=dt.date(2026, 6, 28),
        users=[{"id": 1, "name": "Иван"}],
        events=[
            {
                "id": 1,
                "type": "incoming_call",
                "created_by": 1,
                "created_at": ts(10),
                "entity_type": "lead",
                "entity_id": 10,
                "value_after": [{"note": {"id": 1}}],
            }
        ],
        note_lookup=lambda *_: {"params": {"duration": 30}},
    )
    assert snapshot.users[0].incoming_calls_count == 0
    assert snapshot.users[0].activity_events_count == 0


def test_render_report_contains_russian_summary() -> None:
    config = ReportConfigSchema(timezone="Asia/Krasnoyarsk", selected_user_ids=[1])
    snapshot = ReportBuilder(config).build(
        tenant_id=1,
        report_date=dt.date(2026, 6, 28),
        users=[{"id": 1, "name": "Иван"}],
        events=[],
    )
    text = render_telegram_report(snapshot)
    assert "Отчет по активности менеджеров" in text
    assert "Иван" in text
