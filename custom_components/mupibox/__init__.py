"""MuPiBox-NG integration for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MuPiBoxApiClient
from .const import CONF_ADMIN_PASSWORD, CONF_USE_SSL, PLATFORMS
from .coordinator import MuPiBoxCoordinator


@dataclass(slots=True)
class MuPiBoxRuntimeData:
    """Runtime objects owned by one MuPiBox config entry."""

    api: MuPiBoxApiClient
    coordinator: MuPiBoxCoordinator


MuPiBoxConfigEntry = ConfigEntry[MuPiBoxRuntimeData]


async def async_setup_entry(hass: HomeAssistant, entry: MuPiBoxConfigEntry) -> bool:
    """Set up MuPiBox-NG from a config entry."""
    api = MuPiBoxApiClient(
        async_get_clientsession(hass),
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
        entry.data.get(CONF_USE_SSL, False),
        entry.data.get(CONF_ADMIN_PASSWORD, ""),
    )
    coordinator = MuPiBoxCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MuPiBoxRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MuPiBoxConfigEntry) -> bool:
    """Unload a MuPiBox-NG config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
