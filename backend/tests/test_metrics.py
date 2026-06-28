from __future__ import annotations

import datetime as dt

from app.core.time import day_bounds
from app.reports.metrics import continuous_work_seconds, format_duration


def test_continuous_work_counts_only_small_gaps() -> None:
    assert continuous_work_seconds([0, 60, 600, 1201, 1261], 600) == 60 + 540 + 60


def test_continuous_work_edge_cases() -> None:
    assert continuous_work_seconds([], 600) == 0
    assert continuous_work_seconds([100], 600) == 0
    assert continuous_work_seconds([60, 0, 60, 600], 600) == 600
    assert continuous_work_seconds([0, 600], 600) == 600
    assert continuous_work_seconds([0, 601], 600) == 0


def test_timezone_day_boundaries() -> None:
    start, end = day_bounds(dt.date(2026, 6, 28), "Asia/Krasnoyarsk")
    assert start.isoformat() == "2026-06-28T00:00:00+07:00"
    assert end.isoformat() == "2026-06-28T23:59:59+07:00"


def test_format_duration() -> None:
    assert format_duration(0) == "0м"
    assert format_duration(95 * 60) == "1ч 35м"
