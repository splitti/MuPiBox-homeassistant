"""TTS announcement entity for MuPiBox-NG."""

from __future__ import annotations

from homeassistant.components.notify import NotifyEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the MuPiBox announcement notify entity."""
    async_add_entities([MuPiBoxAnnouncementEntity(entry)])


class MuPiBoxAnnouncementEntity(MuPiBoxEntity, NotifyEntity):
    """Use MuPiBox local TTS for Home Assistant announcements."""

    _attr_name = "Announcements"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "announcements")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        del title
        await self.api.async_speak(message, source_ref=f"home-assistant:{self.entry.entry_id}")
        await self.coordinator.async_request_refresh()
