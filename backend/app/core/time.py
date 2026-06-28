from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo


def day_bounds(report_date: dt.date, timezone_name: str) -> tuple[dt.datetime, dt.datetime]:
    tz = ZoneInfo(timezone_name)
    start = dt.datetime.combine(report_date, dt.time.min, tzinfo=tz)
    end = dt.datetime.combine(report_date, dt.time.max.replace(microsecond=0), tzinfo=tz)
    return start, end


def utc_timestamp(value: dt.datetime) -> int:
    return int(value.timestamp())


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.UTC)
