"""Versioned Classic discovery and API-v1 contract helpers.

This module deliberately does not alter the working NG API client.  Classic is
only enabled once a real Classic firmware implements the documented contract.
"""

from __future__ import annotations

from typing import Any, Mapping

COMMON_SERVICE = "_mupibox._tcp.local."
CLASSIC_GENERATION = "classic"
NG_GENERATION = "ng"
CLASSIC_API_VERSION = 1
CLASSIC_BASE_PATH = "/api/ha/v1"


def discovery_generation(properties: Mapping[str, Any]) -> str:
    """Recognize explicit Classic advertisements; unspecified = legacy NG.

    A pre-existing NG broadcast does not need any TXT record changes.
    """
    value = properties.get("generation", "")
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value).strip().lower() or NG_GENERATION


def classic_identity(properties: Mapping[str, Any]) -> str:
    """Return the new persistent Classic ID without borrowing an NG identity."""
    value = properties.get("device_id", "")
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    return str(value).strip()


def validate_classic_info(info: Mapping[str, Any], expected_id: str = "") -> str:
    """Validate minimum API-v1 identity before provisioning any HA device."""
    if str(info.get("generation", "")).lower() != CLASSIC_GENERATION:
        raise ValueError("Not a Classic API device")
    if info.get("api_version") != CLASSIC_API_VERSION:
        raise ValueError("Unsupported Classic API version")
    device_id = str(info.get("device_id", "")).strip()
    if not device_id or (expected_id and expected_id != device_id):
        raise ValueError("Missing or inconsistent Classic device identity")
    return device_id


def normalize_classic_state(state: Mapping[str, Any]) -> dict[str, Any]:
    """Convert documented Classic playback into a safe NG-shaped player state.

    This is an internal adapter input; it must not change existing NG behavior.
    """
    playback = state.get("playback")
    if not isinstance(playback, dict):
        raise ValueError("Classic response lacks playback object")
    mode = str(playback.get("state") or "idle").lower()
    mode = {"idle": "stopped", "unavailable": "error"}.get(mode, mode)
    if mode not in {"playing", "paused", "stopped", "buffering", "error"}:
        mode = "error"
    volume = playback.get("volume")
    track = {
        "id": playback.get("media_id"),
        "title": playback.get("title"),
        "artist": playback.get("artist"),
        "provider": playback.get("provider") or "local",
    }
    return {
        "state": mode,
        "queue": [track] if playback.get("title") else [],
        "index": 0 if playback.get("title") else -1,
        "duration": playback.get("duration"),
        "position": playback.get("position"),
        "cover": playback.get("cover_url"),
        "volume": volume if isinstance(volume, (int, float)) else None,
        "max_volume": 100,
    }
