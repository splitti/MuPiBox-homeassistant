"""Administrative buttons for MuPiBox-NG."""

from __future__ import annotations

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Set up MuPiBox admin buttons."""
    async_add_entities(
        [
            MuPiBoxRescanLibraryButton(entry),
            MuPiBoxRestartUIButton(entry),
            MuPiBoxRebootButton(entry),
            MuPiBoxPowerOffButton(entry),
        ]
    )


class MuPiBoxAdminButton(MuPiBoxEntity, ButtonEntity):
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        auth = self.coordinator.data.auth
        protected_without_password = bool(auth.get("protected")) and not self.api.has_admin_password
        return super().available and not protected_without_password


class MuPiBoxRescanLibraryButton(MuPiBoxAdminButton):
    _attr_name = "Rescan library"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "rescan_library")

    async def async_press(self) -> None:
        await self.api.async_admin_post("/api/admin/library/rescan")
        await self.coordinator.async_refresh_library()


class MuPiBoxRestartUIButton(MuPiBoxAdminButton):
    _attr_name = "Restart UI"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "restart_ui")

    async def async_press(self) -> None:
        await self.api.async_admin_post("/api/admin/ui/restart")
        await self.coordinator.async_request_refresh()


class MuPiBoxRebootButton(MuPiBoxAdminButton):
    _attr_name = "Reboot"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "reboot")

    async def async_press(self) -> None:
        await self.api.async_admin_post(
            "/api/admin/system/power", {"action": "reboot"}
        )


class MuPiBoxPowerOffButton(MuPiBoxAdminButton):
    _attr_name = "Power off"

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "power_off")

    async def async_press(self) -> None:
        await self.api.async_admin_post(
            "/api/admin/system/power", {"action": "poweroff"}
        )
