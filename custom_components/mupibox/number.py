"""Power-off timer for MuPiBox Classic and NG (secure API v1 only)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MuPiBoxConfigEntry
from .entity import MuPiBoxEntity, box_call
from .sleep_timer_contract import MAX_SLEEP_TIMER_MINUTES, remaining_minutes


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MuPiBoxConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    info = entry.runtime_data.coordinator.data.info
    if (entry.data.get("protocol") == "ha_v1"
            and "sleep_timer" in info.get("capabilities", [])
            and "power" in entry.data.get("scopes", [])):
        async_add_entities([MuPiBoxSleepTimerNumber(entry)])


class MuPiBoxSleepTimerNumber(MuPiBoxEntity, NumberEntity):
    """Set minutes (1..720), replace a timer, or stop it by setting zero."""

    _attr_translation_key = "sleep_timer"
    _attr_icon = "mdi:timer-outline"
    _attr_native_min_value = 0
    _attr_native_max_value = MAX_SLEEP_TIMER_MINUTES
    _attr_native_step = 1
    _attr_native_unit_of_measurement = "min"
    _attr_mode = NumberMode.BOX

    def __init__(self, entry: MuPiBoxConfigEntry) -> None:
        super().__init__(entry, "sleep_timer_minutes")

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data.sleep_timer)

    @property
    def native_value(self) -> int | None:
        timer = self.coordinator.data.sleep_timer
        return remaining_minutes(timer) if timer else None

    async def async_set_native_value(self, value: float) -> None:
        if type(value) not in (int, float) or int(value) != value or not 0 <= value <= MAX_SLEEP_TIMER_MINUTES:
            raise ValueError("Timer must be a whole number of minutes (0..720)")
        await box_call(self.api.async_set_sleep_timer(int(value)))
        await self.coordinator.async_request_refresh()
