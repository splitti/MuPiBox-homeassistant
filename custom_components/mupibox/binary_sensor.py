"""Binary sensors for MuPiBox-NG."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MuPiBox binary sensors."""
    async_add_entities(
        [
            MuPiBoxOnlineBinarySensor(entry),
            MuPiBoxWiFiBinarySensor(entry),
            MuPiBoxChargingBinarySensor(entry),
            MuPiBoxSpotifyBinarySensor(entry),
            MuPiBoxTTSBinarySensor(entry),
        ]
    )


class MuPiBoxOnlineBinarySensor(MuPiBoxEntity, BinarySensorEntity):
    _attr_name = "Network online"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "network_online")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.system.get("online"))


class MuPiBoxWiFiBinarySensor(MuPiBoxEntity, BinarySensorEntity):
    _attr_name = "Wi-Fi connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "wifi_connected")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.system.get("wifi", {}).get("connected"))


class MuPiBoxChargingBinarySensor(MuPiBoxEntity, BinarySensorEntity):
    _attr_name = "Charging"
    _attr_device_class = BinarySensorDeviceClass.BATTERY_CHARGING

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "battery_charging")

    @property
    def available(self) -> bool:
        return super().available and bool(
            self.coordinator.data.system.get("battery", {}).get("available")
        )

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.system.get("battery", {}).get("charging"))


class MuPiBoxSpotifyBinarySensor(MuPiBoxEntity, BinarySensorEntity):
    _attr_name = "Spotify connected"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "spotify_connected")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.spotify.get("connected"))


class MuPiBoxTTSBinarySensor(MuPiBoxEntity, BinarySensorEntity):
    _attr_name = "TTS enabled"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "tts_enabled")

    @property
    def is_on(self) -> bool:
        return bool(self.coordinator.data.info.get("tts", {}).get("enabled"))
