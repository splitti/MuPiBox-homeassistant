"""Dependency-free validation of the shared Classic/NG power-off timer API."""

from __future__ import annotations

from datetime import datetime
from math import ceil
from typing import Any, Mapping

MAX_SLEEP_TIMER_MINUTES = 720


def normalize_sleep_timer(raw: Any) -> dict[str, Any]:
    """Validate the optional v1 state without confusing a broken API with stopped."""
    if not isinstance(raw, Mapping) or type(raw.get("active")) is not bool:
        raise ValueError("Missing or invalid sleep_timer.active")
    if not raw["active"]:
        if raw.get("ends_at") is not None or raw.get("remaining_s") != 0:
            raise ValueError("Inactive sleep_timer must have null ends_at and zero remaining_s")
        return {"active": False, "ends_at": None, "remaining_s": 0}

    ends_at = raw.get("ends_at")
    remaining_s = raw.get("remaining_s")
    if type(remaining_s) is not int or remaining_s < 0:
        raise ValueError("Invalid sleep_timer.remaining_s")
    if not isinstance(ends_at, str):
        raise ValueError("Missing sleep_timer.ends_at")
    date = datetime.fromisoformat(ends_at.replace("Z", "+00:00"))
    if date.tzinfo is None or date.utcoffset() is None:
        raise ValueError("sleep_timer.ends_at must be timezone-aware")
    return {"active": True, "ends_at": ends_at, "remaining_s": remaining_s}


def remaining_minutes(timer: Mapping[str, Any]) -> int:
    """Display a countdown rounded upward to a whole minute (0 also means stop)."""
    if not timer.get("active"):
        return 0
    return min(MAX_SLEEP_TIMER_MINUTES, ceil(timer["remaining_s"] / 60))


def end_datetime(timer: Mapping[str, Any]) -> datetime | None:
    """Home Assistant timestamp sensors require a tz-aware datetime."""
    if not timer.get("active"):
        return None
    return datetime.fromisoformat(timer["ends_at"].replace("Z", "+00:00"))
