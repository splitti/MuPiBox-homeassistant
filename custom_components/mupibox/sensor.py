"""Sensors for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import EntityCategory, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MuPiBox sensors."""
    async_add_entities(
        [
            MuPiBoxBatterySensor(entry),
            MuPiBoxWiFiSignalSensor(entry),
            MuPiBoxWiFiQualitySensor(entry),
            MuPiBoxVersionSensor(entry),
            MuPiBoxBackendSensor(entry),
        ]
    )


class MuPiBoxBatterySensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "battery")

    @property
    def available(self) -> bool:
        battery = self.coordinator.data.system.get("battery", {})
        return super().available and bool(battery.get("available"))

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.system.get("battery", {}).get("percent")
        return int(value) if isinstance(value, (int, float)) else None


class MuPiBoxWiFiSignalSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Wi-Fi signal"
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = "dBm"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "wifi_signal")

    @property
    def available(self) -> bool:
        wifi = self.coordinator.data.system.get("wifi", {})
        return super().available and bool(wifi.get("connected"))

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.system.get("wifi", {}).get("signal_dbm")
        return int(value) if isinstance(value, (int, float)) else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        interface = self.coordinator.data.system.get("wifi", {}).get("interface")
        return {"interface": interface} if interface else {}


class MuPiBoxWiFiQualitySensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Wi-Fi quality"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "wifi_quality")

    @property
    def available(self) -> bool:
        wifi = self.coordinator.data.system.get("wifi", {})
        return super().available and bool(wifi.get("connected"))

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.system.get("wifi", {}).get("quality_percent")
        return int(value) if isinstance(value, (int, float)) else None


class MuPiBoxVersionSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "version")

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.info.get("version")
        return str(value) if value else None


class MuPiBoxBackendSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Audio backend"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "audio_backend")

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.status.get("backend") or self.coordinator.data.info.get("backend")
        return str(value) if value else None
