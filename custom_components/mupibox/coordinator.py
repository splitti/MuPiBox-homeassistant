"""Data coordinator for MuPiBox-NG."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import logging
import time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MuPiBoxApiClient, MuPiBoxApiError
from .const import (
    AUTH_UPDATE_INTERVAL_SECONDS,
    DOMAIN,
    INFO_UPDATE_INTERVAL_SECONDS,
    LIBRARY_UPDATE_INTERVAL_SECONDS,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MuPiBoxData:
    """Combined state fetched from the MuPiBox API."""

    status: dict[str, Any] = field(default_factory=dict)
    system: dict[str, Any] = field(default_factory=dict)
    spotify: dict[str, Any] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    auth: dict[str, Any] = field(default_factory=dict)
    library: list[dict[str, Any]] = field(default_factory=list)


class MuPiBoxCoordinator(DataUpdateCoordinator[MuPiBoxData]):
    """Poll MuPiBox once and share the result with all entities."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: MuPiBoxApiClient,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            config_entry=entry,
            update_interval=UPDATE_INTERVAL,
        )
        self.api = api
        self._cached = MuPiBoxData()
        self._last_library = 0.0
        self._last_info = 0.0
        self._last_auth = 0.0

    async def _async_update_data(self) -> MuPiBoxData:
        now = time.monotonic()
        try:
            status_task = self.api.async_get_status()
            system_task = self.api.async_get_system()
            spotify_task = self.api.async_get_spotify_status()
            status, system, spotify = await asyncio.gather(
                status_task, system_task, spotify_task
            )

            info = self._cached.info
            if not info or now - self._last_info >= INFO_UPDATE_INTERVAL_SECONDS:
                info = await self.api.async_get_info()
                self._last_info = now

            auth = self._cached.auth
            if not auth or now - self._last_auth >= AUTH_UPDATE_INTERVAL_SECONDS:
                auth = await self.api.async_get_admin_auth()
                self._last_auth = now

            library = self._cached.library
            if not library or now - self._last_library >= LIBRARY_UPDATE_INTERVAL_SECONDS:
                library = await self.api.async_get_library()
                self._last_library = now

        except MuPiBoxApiError as err:
            raise UpdateFailed(str(err)) from err

        self._cached = MuPiBoxData(
            status=status,
            system=system,
            spotify=spotify,
            info=info,
            auth=auth,
            library=library,
        )
        return self._cached

    async def async_refresh_library(self) -> None:
        """Force the library to be fetched on the next update."""
        self._last_library = 0.0
        await self.async_request_refresh()
