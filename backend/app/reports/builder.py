from __future__ import annotations

import datetime as dt
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable
from typing import Any

from app.core.time import day_bounds
from app.reports.metrics import (
    call_duration_from_note,
    continuous_work_seconds,
    event_local_time,
    extract_event_note_id,
)
from app.reports.schemas import AmoEvent, AmoUserSchema, ReportConfigSchema, ReportSnapshotPayload, ReportUserStats

NoteLookup = Callable[[str, int, int], dict[str, Any] | None]


class ReportBuilder:
    def __init__(self, config: ReportConfigSchema) -> None:
        self.config = config

    def build(
        self,
        *,
        tenant_id: int,
        report_date: dt.date,
        users: Iterable[AmoUserSchema | dict[str, Any]],
        events: Iterable[AmoEvent | dict[str, Any]],
        overdue_tasks_by_user: dict[int, int] | None = None,
        note_lookup: NoteLookup | None = None,
        account_id: int | None = None,
    ) -> ReportSnapshotPayload:
        start, end = day_bounds(report_date, self.config.timezone)
        selected = set(self.config.selected_user_ids)
        excluded = set(self.config.excluded_user_ids)
        normalized_users = [self._user(item) for item in users]
        if selected:
            normalized_users = [user for user in normalized_users if user.id in selected]
        normalized_users = [user for user in normalized_users if user.id not in excluded]
        events_by_user: dict[int, list[AmoEvent]] = defaultdict(list)
        for item in events:
            event = self._event(item)
            if int(start.timestamp()) <= event.created_at <= int(end.timestamp()):
                events_by_user[event.created_by].append(event)

        overdue_tasks_by_user = overdue_tasks_by_user or {}
        rows = [
            self._stats_for_user(user, events_by_user.get(user.id, []), overdue_tasks_by_user.get(user.id, 0), note_lookup)
            for user in normalized_users
        ]
        totals = {
            "users_count": len(rows),
            "activity_events_count": sum(row.activity_events_count for row in rows),
            "completed_tasks_count": sum(row.completed_tasks_count for row in rows),
            "deadline_changes_count": sum(row.deadline_changes_count for row in rows),
            "overdue_tasks_count": sum(row.overdue_tasks_count for row in rows),
            "incoming_calls_count": sum(row.incoming_calls_count for row in rows),
            "outgoing_calls_count": sum(row.outgoing_calls_count for row in rows),
            "notes_count": sum(row.notes_count for row in rows),
        }
        return ReportSnapshotPayload(
            tenant_id=tenant_id,
            account_id=account_id,
            report_date=report_date,
            timezone=self.config.timezone,
            config_version=self.config.version,
            source_window_start=start,
            source_window_end=end,
            users=rows,
            totals=totals,
            generated_at=dt.datetime.now(dt.UTC),
        )

    def _stats_for_user(
        self,
        user: AmoUserSchema,
        events: list[AmoEvent],
        overdue_tasks_count: int,
        note_lookup: NoteLookup | None,
    ) -> ReportUserStats:
        timestamps: list[int] = []
        breakdown: Counter[str] = Counter()
        incoming_calls = 0
        outgoing_calls = 0
        notes = 0
        completed = 0
        deadline_changes = 0

        for event in sorted(events, key=lambda item: (item.created_at, str(item.id))):
            breakdown[event.type] += 1
            if event.type == "task_completed":
                completed += 1
            if event.type == "task_deadline_changed":
                deadline_changes += 1
            if not self._is_activity_event(event, note_lookup):
                continue
            timestamps.append(event.created_at)
            if event.type == "incoming_call":
                incoming_calls += 1
            elif event.type == "outgoing_call":
                outgoing_calls += 1
            elif event.type == "common_note_added":
                notes += 1

        ordered = sorted(set(timestamps))
        return ReportUserStats(
            user_id=user.id,
            name=user.name,
            group=self.config.user_groups.get(str(user.id), "Без отдела"),
            continuous_work_seconds=continuous_work_seconds(ordered, self.config.work_session_gap_minutes * 60),
            activity_events_count=len(ordered),
            completed_tasks_count=completed,
            deadline_changes_count=deadline_changes,
            overdue_tasks_count=overdue_tasks_count,
            incoming_calls_count=incoming_calls,
            outgoing_calls_count=outgoing_calls,
            notes_count=notes,
            first_activity_at=event_local_time(ordered[0], self.config.timezone) if ordered else None,
            last_activity_at=event_local_time(ordered[-1], self.config.timezone) if ordered else None,
            event_breakdown=dict(sorted(breakdown.items())),
        )

    def _is_activity_event(self, event: AmoEvent, note_lookup: NoteLookup | None) -> bool:
        if not self.config.enabled_activity_events.get(event.type, False):
            return False
        if event.type not in {"incoming_call", "outgoing_call"}:
            return True
        note_id = extract_event_note_id(event.model_dump())
        if note_id is None:
            return False
        note = note_lookup(event.entity_type, event.entity_id, note_id) if note_lookup else None
        duration = call_duration_from_note(note)
        threshold = (
            self.config.incoming_call_min_duration_seconds
            if event.type == "incoming_call"
            else self.config.outgoing_call_min_duration_seconds
        )
        return duration > threshold

    @staticmethod
    def _event(item: AmoEvent | dict[str, Any]) -> AmoEvent:
        return item if isinstance(item, AmoEvent) else AmoEvent.model_validate(item)

    @staticmethod
    def _user(item: AmoUserSchema | dict[str, Any]) -> AmoUserSchema:
        return item if isinstance(item, AmoUserSchema) else AmoUserSchema.model_validate(item)
