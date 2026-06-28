from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from typing import Any
from zoneinfo import ZoneInfo


def continuous_work_seconds(timestamps: Iterable[int], max_gap_seconds: int) -> int:
    if max_gap_seconds <= 0:
        return 0
    ordered = sorted(set(int(item) for item in timestamps))
    if len(ordered) < 2:
        return 0
    total = 0
    previous = ordered[0]
    for current in ordered[1:]:
        gap = current - previous
        if 0 < gap <= max_gap_seconds:
            total += gap
        previous = current
    return total


def extract_event_note_id(event: dict[str, Any]) -> int | None:
    for item in event.get("value_after") or []:
        note = item.get("note") or {}
        if note.get("id"):
            return int(note["id"])
    return None


def call_duration_from_note(note: dict[str, Any] | None) -> int:
    if not note:
        return 0
    return int((note.get("params") or {}).get("duration") or 0)


def event_local_time(created_at: int, timezone_name: str) -> str:
    return dt.datetime.fromtimestamp(created_at, ZoneInfo(timezone_name)).strftime("%H:%M")


def format_duration(seconds: int) -> str:
    minutes = max(0, seconds) // 60
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}ч {mins}м"
    if hours:
        return f"{hours}ч"
    return f"{mins}м"
