"""Selectable audio output for MuPiBox-NG."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up selectable MuPiBox output routing."""
    async_add_entities([MuPiBoxAudioOutputSelect(entry)])


class MuPiBoxAudioOutputSelect(MuPiBoxEntity, SelectEntity):
    """Choose where the MuPiBox sends audio."""

    _attr_translation_key = "audio_output"
    _attr_has_entity_name = True

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "audio_output")

    def _targets(self) -> list[dict[str, Any]]:
        raw = self.coordinator.data.output_targets.get("targets")
        if not isinstance(raw, list):
            return []
        return [target for target in raw if isinstance(target, dict)]

    def _option_map(self) -> dict[str, str]:
        candidates = [
            target
            for target in self._targets()
            if target.get("selectable") and (target.get("available") or target.get("active"))
        ]
        counts: dict[str, int] = {}
        for target in candidates:
            name = str(target.get("name") or target.get("id") or "Output")
            counts[name] = counts.get(name, 0) + 1

        result: dict[str, str] = {}
        used: set[str] = set()
        for target in candidates:
            target_id = str(target.get("id") or "").strip()
            if not target_id:
                continue
            name = str(target.get("name") or target_id)
            label = name
            if counts.get(name, 0) > 1:
                subtitle = str(target.get("subtitle") or "").strip()
                if subtitle:
                    label = f"{name} · {subtitle}"
            if label in used:
                suffix = target_id.split(":")[-1][-8:]
                label = f"{label} · {suffix}"
            used.add(label)
            result[label] = target_id
        return result

    @property
    def options(self) -> list[str]:
        return list(self._option_map())

    @property
    def current_option(self) -> str | None:
        active_id = None
        for target in self._targets():
            if target.get("active"):
                active_id = str(target.get("id") or "")
                break
        if not active_id:
            return None
        for label, target_id in self._option_map().items():
            if target_id == active_id:
                return label
        return None

    async def async_select_option(self, option: str) -> None:
        target_id = self._option_map().get(option)
        if target_id is None:
            raise ValueError(f"Unknown MuPiBox audio output: {option}")
        await self.api.async_select_output_target(target_id)
        await self.coordinator.async_request_refresh()
