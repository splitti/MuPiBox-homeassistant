"""MuPiBox-NG integration for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MuPiBoxApiClient
from .v1_api import MuPiBoxV1Client
from .const import CONF_ADMIN_PASSWORD, CONF_USE_SSL, DOMAIN, PLATFORMS
from .coordinator import MuPiBoxCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class MuPiBoxRuntimeData:
    """Runtime objects owned by one MuPiBox config entry."""

    api: MuPiBoxApiClient
    coordinator: MuPiBoxCoordinator


MuPiBoxConfigEntry = ConfigEntry[MuPiBoxRuntimeData]


def _identity_from_info(info: dict[str, Any]) -> str:
    """Return the stable MuPiBox identity supplied by the box."""
    return str(info.get("box_id", "")).strip()


def _other_entry_uses_identity(
    hass: HomeAssistant, entry: MuPiBoxConfigEntry, identity: str
) -> bool:
    return any(
        other.entry_id != entry.entry_id and other.unique_id == identity
        for other in hass.config_entries.async_entries(DOMAIN)
    )


def _migrate_registry_identity(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    old_identity: str,
    new_identity: str,
) -> bool:
    """Migrate existing registry keys without changing entity IDs/customizations."""
    entity_reg = er.async_get(hass)
    prefix = f"{old_identity}_"

    try:
        for entity in er.async_entries_for_config_entry(entity_reg, entry.entry_id):
            if not entity.unique_id.startswith(prefix):
                continue
            new_unique_id = f"{new_identity}_{entity.unique_id[len(prefix):]}"
            entity_reg.async_update_entity(
                entity.entity_id,
                new_unique_id=new_unique_id,
            )

        device_reg = dr.async_get(hass)
        for device in dr.async_entries_for_config_entry(device_reg, entry.entry_id):
            old_identifier = (DOMAIN, old_identity)
            if old_identifier not in device.identifiers:
                continue
            new_identifiers = set(device.identifiers)
            new_identifiers.discard(old_identifier)
            new_identifiers.add((DOMAIN, new_identity))
            device_reg.async_update_device(
                device.id,
                new_identifiers=new_identifiers,
            )
    except (ValueError, dr.DeviceIdentifierCollisionError) as err:
        _LOGGER.error(
            "Could not migrate MuPiBox registry identity from %s to %s: %s",
            old_identity,
            new_identity,
            err,
        )
        return False
    return True


def _remove_obsolete_entities(hass: HomeAssistant, entry: MuPiBoxConfigEntry) -> None:
    """Remove entities retired by the provider-neutral player model."""
    entity_reg = er.async_get(hass)
    for entity in list(er.async_entries_for_config_entry(entity_reg, entry.entry_id)):
        if entity.unique_id.endswith("_spotify_connect"):
            entity_reg.async_remove(entity.entity_id)
            _LOGGER.info("Removed obsolete separate Spotify media player %s", entity.entity_id)
            continue
        if entity.domain == "sensor" and entity.unique_id.endswith("_audio_output"):
            entity_reg.async_remove(entity.entity_id)
            _LOGGER.info("Removed obsolete read-only audio output sensor %s", entity.entity_id)


def _migrate_config_entry_identity(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    info: dict[str, Any],
) -> None:
    """Replace legacy URL-based identity with the persistent MuPiBox box_id."""
    new_identity = _identity_from_info(info)
    if not new_identity or entry.unique_id == new_identity:
        return
    if _other_entry_uses_identity(hass, entry, new_identity):
        _LOGGER.error(
            "Cannot migrate MuPiBox config entry %s to box_id %s because another "
            "entry already uses it",
            entry.entry_id,
            new_identity,
        )
        return

    old_identity = entry.unique_id or entry.entry_id
    if not _migrate_registry_identity(hass, entry, old_identity, new_identity):
        return

    hass.config_entries.async_update_entry(entry, unique_id=new_identity)
    _LOGGER.info(
        "Migrated MuPiBox identity from legacy endpoint key %s to box_id %s",
        old_identity,
        new_identity,
    )


async def async_setup_entry(hass: HomeAssistant, entry: MuPiBoxConfigEntry) -> bool:
    """Set up MuPiBox-NG from a config entry."""
    if entry.data.get("protocol") == "ha_v1":
        api = MuPiBoxV1Client(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data["ca_pem"],
            entry.data["access_token"],
        )
    else:
        api = MuPiBoxApiClient(
            async_get_clientsession(hass),
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data.get(CONF_USE_SSL, False),
            entry.data.get(CONF_ADMIN_PASSWORD, ""),
        )
    coordinator = MuPiBoxCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()

    _migrate_config_entry_identity(hass, entry, coordinator.data.info)
    if entry.data.get("protocol") != "ha_v1":
        _remove_obsolete_entities(hass, entry)

    entry.runtime_data = MuPiBoxRuntimeData(api=api, coordinator=coordinator)
    platforms = ["media_player", "sensor"] if entry.data.get("protocol") == "ha_v1" else PLATFORMS
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MuPiBoxConfigEntry) -> bool:
    """Unload a MuPiBox-NG config entry."""
    platforms = ["media_player", "sensor"] if entry.data.get("protocol") == "ha_v1" else PLATFORMS
    return await hass.config_entries.async_unload_platforms(entry, platforms)
