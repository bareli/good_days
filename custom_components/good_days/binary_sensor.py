"""binary_sensor.good_days_holiday_today: on during a holiday day (Gregorian, local).
binary_sensor.good_days_fasting: on from the start to the end of a fast (Yom Kippur too)."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .entity import GoodDaysEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([HolidayTodaySensor(entry), FastingSensor(entry)])


class HolidayTodaySensor(GoodDaysEntity, BinarySensorEntity):
    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "holiday_today")

    @property
    def is_on(self) -> bool:
        return bool(self.runtime.holidays_on(dt_util.now().date()))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        lang = self.runtime.language
        events = self.runtime.holidays_on(dt_util.now().date())
        return {
            "holidays": [e.title(lang) for e in events],
            "categories": sorted({e.category for e in events}),
        }


class FastingSensor(GoodDaysEntity, BinarySensorEntity):
    _attr_icon = "mdi:food-off-outline"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "fasting")

    @property
    def is_on(self) -> bool:
        return self.runtime.fast_at(dt_util.now()) is not None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        event = self.runtime.fast_at(dt_util.now())
        if event is None:
            return None
        return {"title": event.title(self.runtime.language), "end": event.end.isoformat()}
