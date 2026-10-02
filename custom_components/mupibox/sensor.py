"""Sensors for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


PROVIDER_NAMES = {
    "spotify": "Spotify",
    "music-assistant": "Music Assistant",
    "jellyfin": "Jellyfin",
    "audible": "Audible",
    "sendspin": "Sendspin",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MuPiBox sensors."""
    entities: list[SensorEntity] = [
        MuPiBoxBatterySensor(entry),
        MuPiBoxBatteryVoltageSensor(entry),
        MuPiBoxBatteryCurrentSensor(entry),
        MuPiBoxMuPiHATTemperatureSensor(entry),
        MuPiBoxWiFiSignalSensor(entry),
        MuPiBoxWiFiQualitySensor(entry),
        MuPiBoxCPUUsageSensor(entry),
        MuPiBoxCPUTemperatureSensor(entry),
        MuPiBoxRAMUsageSensor(entry),
        MuPiBoxStorageUsageSensor(entry),
        MuPiBoxActiveProviderSensor(entry),
        MuPiBoxTTSProviderSensor(entry),
        MuPiBoxVersionSensor(entry),
        MuPiBoxPlaybackEngineSensor(entry),
        MuPiBoxAudioOutputSensor(entry),
    ]
    entities.extend(MuPiBoxProviderStatusSensor(entry, provider) for provider in PROVIDER_NAMES)
    async_add_entities(entities)


class MuPiBoxBatterySensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Battery"
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "battery")

    @property
    def available(self) -> bool:
        hat = self.coordinator.data.mupihat
        if hat:
            return super().available and bool(hat.get("battery_present"))
        battery = self.coordinator.data.system.get("battery", {})
        return super().available and bool(battery.get("available"))

    @property
    def native_value(self) -> int | None:
        hat_value = self.coordinator.data.mupihat.get("battery_percent")
        if isinstance(hat_value, (int, float)):
            return int(hat_value)
        value = self.coordinator.data.system.get("battery", {}).get("percent")
        return int(value) if isinstance(value, (int, float)) else None


class MuPiBoxMuPiHATSensor(MuPiBoxEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        status = self.coordinator.data.mupihat
        return super().available and bool(status.get("hardware_available"))


class MuPiBoxBatteryVoltageSensor(MuPiBoxMuPiHATSensor):
    _attr_name = "Battery voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "battery_voltage")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.mupihat.get("battery_voltage_mv")
        return round(float(value) / 1000, 3) if isinstance(value, (int, float)) else None


class MuPiBoxBatteryCurrentSensor(MuPiBoxMuPiHATSensor):
    _attr_name = "Battery current"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.MILLIAMPERE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "battery_current")

    @property
    def native_value(self) -> int | None:
        value = self.coordinator.data.mupihat.get("battery_current_ma")
        return int(value) if isinstance(value, (int, float)) else None


class MuPiBoxMuPiHATTemperatureSensor(MuPiBoxMuPiHATSensor):
    _attr_name = "MuPiHAT temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "mupihat_temperature")

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.mupihat.get("temperature_c")
        return float(value) if isinstance(value, (int, float)) else None


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
        wifi = self.coordinator.data.system.get("wifi", {})
        attributes: dict[str, Any] = {}
        if wifi.get("interface"):
            attributes["interface"] = wifi["interface"]
        if wifi.get("ipv4"):
            attributes["ipv4"] = wifi["ipv4"]
        return attributes


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


class MuPiBoxMetricSensor(MuPiBoxEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _metric_key: str

    @property
    def available(self) -> bool:
        return super().available and self._metric_key in self.coordinator.data.metrics

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.metrics.get(self._metric_key)
        return float(value) if isinstance(value, (int, float)) else None


class MuPiBoxCPUUsageSensor(MuPiBoxMetricSensor):
    _attr_name = "CPU usage"
    _metric_key = "cpu_percent"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "cpu_usage")


class MuPiBoxCPUTemperatureSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "CPU temperature"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "cpu_temperature")

    @property
    def available(self) -> bool:
        return super().available and "temperature_c" in self.coordinator.data.metrics

    @property
    def native_value(self) -> float | None:
        value = self.coordinator.data.metrics.get("temperature_c")
        return float(value) if isinstance(value, (int, float)) else None


class MuPiBoxRAMUsageSensor(MuPiBoxMetricSensor):
    _attr_name = "RAM usage"
    _metric_key = "ram_percent"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "ram_usage")


class MuPiBoxStorageUsageSensor(MuPiBoxMetricSensor):
    _attr_name = "Storage usage"
    _metric_key = "disk_percent"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "storage_usage")


class MuPiBoxActiveProviderSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Active provider"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "active_provider")

    @property
    def native_value(self) -> str:
        spotify = self.coordinator.data.spotify
        if spotify.get("connected") and (
            spotify.get("playing") or spotify.get("paused") or spotify.get("buffering")
        ):
            return "spotify"
        status = self.coordinator.data.status
        queue = status.get("queue")
        index = status.get("index", -1)
        if isinstance(queue, list) and isinstance(index, int) and 0 <= index < len(queue):
            track = queue[index]
            if isinstance(track, dict) and track.get("provider"):
                return str(track["provider"])
            return "local"
        return "idle"


class MuPiBoxTTSProviderSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "TTS provider"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "tts_provider")

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.info.get("tts", {}).get("provider")
        return str(value) if value else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        tts = self.coordinator.data.info.get("tts", {})
        return {
            key: tts[key]
            for key in ("language", "voice_id", "quality", "pre_rendering_enabled")
            if key in tts
        }


class MuPiBoxProviderStatusSensor(MuPiBoxEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry, provider: str) -> None:
        self._provider = provider
        self._attr_name = f"{PROVIDER_NAMES[provider]} status"
        super().__init__(entry, f"provider_{provider.replace('-', '_')}")

    @property
    def available(self) -> bool:
        return super().available and self._provider in self.coordinator.data.providers

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.providers.get(self._provider, {}).get("state")
        return str(value) if value else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        state = self.coordinator.data.providers.get(self._provider, {})
        return {
            key: state[key]
            for key in ("enabled", "configured", "connected", "active", "backend", "error")
            if key in state
        }


class MuPiBoxVersionSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Version"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "version")

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.info.get("version")
        return str(value) if value else None


class MuPiBoxPlaybackEngineSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Playback engine"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        # Preserve the original unique-id suffix from <=0.3.0 so an existing
        # entity is renamed in place instead of being recreated.
        super().__init__(entry, "audio_backend")

    @property
    def native_value(self) -> str | None:
        value = self.coordinator.data.status.get("backend") or self.coordinator.data.info.get("backend")
        return str(value) if value else None


class MuPiBoxAudioOutputSensor(MuPiBoxEntity, SensorEntity):
    _attr_name = "Audio output"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "audio_output")

    def _active_target(self) -> dict[str, Any] | None:
        targets = self.coordinator.data.output_targets.get("targets")
        if not isinstance(targets, list):
            return None
        for target in targets:
            if isinstance(target, dict) and target.get("active"):
                return target
        return None

    @property
    def available(self) -> bool:
        return super().available and self._active_target() is not None

    @property
    def native_value(self) -> str | None:
        target = self._active_target()
        return str(target.get("name")) if target and target.get("name") else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        target = self._active_target() or {}
        return {
            key: target[key]
            for key in ("id", "kind", "subtitle", "available", "selectable", "paired")
            if key in target
        }
