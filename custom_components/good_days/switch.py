"""Shabbat timers master switch and "skip the next Shabbat / Chag"."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import GoodDaysEntity
from .websocket_timers import async_apply_settings


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TimersSwitch(entry), SkipNextSwitch(entry)])


class TimersSwitch(GoodDaysEntity, SwitchEntity):
    """All Shabbat timers on / off (rules stay; nothing fires while off)."""

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "shabbat_timers")

    @property
    def is_on(self) -> bool:
        return self.runtime.timers.store.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await async_apply_settings(self.runtime, {"enabled": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await async_apply_settings(self.runtime, {"enabled": False})


class SkipNextSwitch(GoodDaysEntity, SwitchEntity):
    """Skip the timers of the current or next Shabbat / Chag only (resets by itself)."""

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "skip_next")

    @property
    def is_on(self) -> bool:
        periods = self.runtime.timers.periods(dt_util.now(), 1)
        return bool(periods) and periods[0].uid in self.runtime.timers.store.skip

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        periods = self.runtime.timers.periods(dt_util.now(), 1)
        if not periods:
            return None
        return {"period": periods[0].title(self.runtime.language), "start": periods[0].start.isoformat()}

    async def async_turn_on(self, **kwargs: Any) -> None:
        await async_apply_settings(self.runtime, {"skip_next": True})

    async def async_turn_off(self, **kwargs: Any) -> None:
        await async_apply_settings(self.runtime, {"skip_next": False})
