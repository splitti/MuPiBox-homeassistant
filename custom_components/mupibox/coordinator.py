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
    METRICS_UPDATE_INTERVAL_SECONDS,
    PROVIDER_UPDATE_INTERVAL_SECONDS,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MuPiBoxData:
    """Combined state fetched from the MuPiBox API."""

    status: dict[str, Any] = field(default_factory=dict)
    system: dict[str, Any] = field(default_factory=dict)
    spotify: dict[str, Any] = field(default_factory=dict)
    mupihat: dict[str, Any] = field(default_factory=dict)
    providers: dict[str, Any] = field(default_factory=dict)
    output_targets: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    info: dict[str, Any] = field(default_factory=dict)
    auth: dict[str, Any] = field(default_factory=dict)
    library: list[dict[str, Any]] = field(default_factory=list)
    update: dict[str, Any] = field(default_factory=dict)


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
        self._is_v1 = entry.data.get("protocol") == "ha_v1"
        self._cached = MuPiBoxData()
        self._last_library = 0.0
        self._last_info = 0.0
        self._last_auth = 0.0
        self._last_providers = 0.0
        self._last_metrics = 0.0
        self._last_update_check = 0.0

    async def _async_update_data(self) -> MuPiBoxData:
        now = time.monotonic()
        try:
            status_task = self.api.async_get_status()
            system_task = self.api.async_get_system()
            spotify_task = self.api.async_get_spotify_status()
            mupihat_task = self.api.async_get_mupihat_status()
            status, system, spotify, mupihat = await asyncio.gather(
                status_task, system_task, spotify_task, mupihat_task
            )

            output_targets = self._cached.output_targets
            try:
                output_targets = await self.api.async_get_output_targets()
            except MuPiBoxApiError as err:
                _LOGGER.debug("Could not refresh optional output targets: %s", err)

            metrics = self._cached.metrics
            if not metrics or now - self._last_metrics >= METRICS_UPDATE_INTERVAL_SECONDS:
                try:
                    metrics = await self.api.async_get_system_metrics()
                    self._last_metrics = now
                except MuPiBoxApiError as err:
                    _LOGGER.debug("Could not refresh optional system metrics: %s", err)

            providers = self._cached.providers
            if not providers or now - self._last_providers >= PROVIDER_UPDATE_INTERVAL_SECONDS:
                try:
                    providers = await self.api.async_get_provider_status()
                    self._last_providers = now
                except MuPiBoxApiError as err:
                    _LOGGER.debug("Could not refresh optional provider status: %s", err)

            info = self._cached.info
            if not info or now - self._last_info >= INFO_UPDATE_INTERVAL_SECONDS:
                info = await self.api.async_get_info()
                self._last_info = now

            auth = self._cached.auth
            if not auth or now - self._last_auth >= AUTH_UPDATE_INTERVAL_SECONDS:
                auth = await self.api.async_get_admin_auth()
                self._last_auth = now

            update = self._cached.update
            if (self._is_v1
                    and (not update or now - self._last_update_check >= 600)):
                try:
                    update = await self.api.async_get_update()
                    self._last_update_check = now
                except MuPiBoxApiError as err:
                    _LOGGER.debug("Update check unavailable: %s", err)
                    self._last_update_check = now

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
            mupihat=mupihat,
            providers=providers,
            output_targets=output_targets,
            metrics=metrics,
            info=info,
            auth=auth,
            library=library,
            update=update,
        )
        return self._cached

    async def async_refresh_library(self) -> None:
        """Force the library to be fetched on the next update."""
        self._last_library = 0.0
        await self.async_request_refresh()
