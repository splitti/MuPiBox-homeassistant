"""Shared entity helpers for MuPiBox-NG."""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, TypeVar
from urllib.parse import urlsplit

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from yarl import URL

from . import MuPiBoxConfigEntry
from .api import MuPiBoxApiError
from .const import DOMAIN
from .coordinator import MuPiBoxCoordinator

_T = TypeVar("_T")

# Names that only describe the product, not one particular box.
_GENERIC_NAMES = {"", "mupibox", "mupibox ng", "mupibox-ng", "mupibox classic"}


def box_display_name(title: str, info: dict[str, Any]) -> str:
    """Prefer the box's own name from /info over the setup title with its IP."""
    name = str(info.get("name") or "").strip()
    return name if name.lower() not in _GENERIC_NAMES else title


def box_web_url(api: Any, info: dict[str, Any]) -> str | None:
    """Where "Visit" should lead: the box's web UI, never the HTTPS API port."""
    candidate = str(info.get("web_url") or "")
    parsed = urlsplit(candidate)
    if parsed.scheme in {"http", "https"} and parsed.hostname:
        return candidate
    if info.get("generation") == "ng":
        return str(URL.build(scheme="http", host=api.host, port=8090, path="/"))
    return None


async def box_call(call: Awaitable[_T]) -> _T:
    """Run a box request and show its rejection reason in Home Assistant."""
    try:
        return await call
    except MuPiBoxApiError as err:
        raise HomeAssistantError(str(err) or "MuPiBox request failed") from err


class MuPiBoxEntity(CoordinatorEntity[MuPiBoxCoordinator]):
    """Base class for entities belonging to one MuPiBox."""

    _attr_has_entity_name = True

    def __init__(self, entry: MuPiBoxConfigEntry, suffix: str) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self.entry = entry
        self.api = entry.runtime_data.api
        stable_id = entry.unique_id or entry.entry_id
        self._attr_unique_id = f"{stable_id}_{suffix}"

    @property
    def device_info(self) -> DeviceInfo:
        info = self.coordinator.data.info if self.coordinator.data else {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.unique_id or self.entry.entry_id)},
            name=box_display_name(self.entry.title, info),
            manufacturer="MuPiBox",
            model="MuPiBox Classic" if info.get("generation") == "classic" else "MuPiBox-NG",
            sw_version=str(info.get("version", "")) or None,
            configuration_url=box_web_url(self.api, info),
        )
