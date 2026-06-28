from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.reports.event_catalog import default_event_map


class ReportConfigSchema(BaseModel):
    version: int = 1
    enabled: bool = True
    timezone: str = "UTC"
    work_session_gap_minutes: int = Field(default=10, ge=1, le=180)
    incoming_call_min_duration_seconds: int = Field(default=30, ge=0, le=86400)
    outgoing_call_min_duration_seconds: int = Field(default=0, ge=0, le=86400)
    enabled_activity_events: dict[str, bool] = Field(default_factory=lambda: default_event_map("default_enabled_as_activity"))
    enabled_counter_events: dict[str, bool] = Field(default_factory=lambda: default_event_map("default_enabled_as_counter"))
    enabled_penalty_events: dict[str, bool] = Field(default_factory=lambda: default_event_map("default_enabled_as_penalty"))
    stage_transition_filters: dict[str, Any] = Field(default_factory=dict)
    selected_user_ids: list[int] = Field(default_factory=list)
    user_groups: dict[str, str] = Field(default_factory=dict)
    excluded_user_ids: list[int] = Field(default_factory=list)
    build_hour: int = Field(default=1, ge=0, le=23)
    send_hour: int = Field(default=9, ge=0, le=23)
    auto_send_enabled: bool = False
    live_sync_interval_seconds: int = Field(default=900, ge=60, le=86400)

    @field_validator("selected_user_ids", "excluded_user_ids")
    @classmethod
    def dedupe_ids(cls, value: list[int]) -> list[int]:
        return sorted(set(int(item) for item in value))


class AmoEvent(BaseModel):
    id: int | str
    type: str
    created_at: int
    created_by: int = 0
    entity_type: str = ""
    entity_id: int = 0
    value_after: list[dict[str, Any]] = Field(default_factory=list)


class AmoUserSchema(BaseModel):
    id: int
    name: str
    email: str = ""


class ReportUserStats(BaseModel):
    user_id: int
    name: str
    group: str = "Без отдела"
    continuous_work_seconds: int = 0
    activity_events_count: int = 0
    completed_tasks_count: int = 0
    deadline_changes_count: int = 0
    overdue_tasks_count: int = 0
    incoming_calls_count: int = 0
    outgoing_calls_count: int = 0
    notes_count: int = 0
    first_activity_at: str | None = None
    last_activity_at: str | None = None
    event_breakdown: dict[str, int] = Field(default_factory=dict)


class ReportSnapshotPayload(BaseModel):
    tenant_id: int
    account_id: int | None = None
    report_date: dt.date
    timezone: str
    config_version: int
    source_window_start: dt.datetime
    source_window_end: dt.datetime
    users: list[ReportUserStats]
    totals: dict[str, int]
    generated_at: dt.datetime
