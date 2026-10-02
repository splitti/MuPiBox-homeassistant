"""Notification entities for MuPiBox-NG."""

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
    """Set up MuPiBox notification entities."""
    async_add_entities(
        [
            MuPiBoxDisplayMessageEntity(entry),
            MuPiBoxAnnouncementEntity(entry),
        ]
    )


class MuPiBoxDisplayMessageEntity(MuPiBoxEntity, NotifyEntity):
    """Show a transient message on the MuPiBox display."""

    _attr_name = "Display message"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "display_message")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        await self.api.async_show_message(message, title=title)


class MuPiBoxAnnouncementEntity(MuPiBoxEntity, NotifyEntity):
    """Use MuPiBox TTS for Home Assistant announcements."""

    _attr_name = "TTS announcement"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        # Keep the previous suffix for registry compatibility.
        super().__init__(entry, "announcements")

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        del title
        await self.api.async_speak(message, source_ref=f"home-assistant:{self.entry.entry_id}")
        await self.coordinator.async_request_refresh()
