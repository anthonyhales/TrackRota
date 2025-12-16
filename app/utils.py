from __future__ import annotations
from datetime import date, datetime, timedelta
import os
import pytz

def get_timezone_name() -> str:
    return os.getenv("APP_TIMEZONE", "Europe/London")

def now_local() -> datetime:
    tz = pytz.timezone(get_timezone_name())
    return datetime.now(tz)

def start_of_week(d: date) -> date:
    # Monday as start of week
    return d - timedelta(days=d.weekday())

def week_dates(d: date) -> list[date]:
    start = start_of_week(d)
    return [start + timedelta(days=i) for i in range(7)]
