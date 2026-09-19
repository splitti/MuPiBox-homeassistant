"""Shared entity helpers for MuPiBox-NG."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MuPiBoxConfigEntry
from .const import DOMAIN
from .coordinator import MuPiBoxCoordinator


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
            name=self.entry.title,
            manufacturer="MuPiBox",
            model="MuPiBox-NG",
            sw_version=str(info.get("version", "")) or None,
            configuration_url=self.api.base_url,
        )
