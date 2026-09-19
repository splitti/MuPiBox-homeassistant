"""Display screenshot camera for MuPiBox-NG."""

from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the MuPiBox display screenshot camera."""
    async_add_entities([MuPiBoxDisplayCamera(entry)])


class MuPiBoxDisplayCamera(MuPiBoxEntity, Camera):
    """Expose the current MuPiBox display as a still-image camera."""

    _attr_name = "Display"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        MuPiBoxEntity.__init__(self, entry, "display")
        Camera.__init__(self)

    @property
    def available(self) -> bool:
        auth = self.coordinator.data.auth
        protected_without_password = bool(auth.get("protected")) and not self.api.has_admin_password
        return super().available and not protected_without_password

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return a fresh screenshot from the MuPiBox display."""
        del width, height
        return await self.api.async_admin_get_bytes("/api/admin/screenshot")
