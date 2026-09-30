"""binary_sensor.good_days_holiday_today: on during a holiday day (Gregorian, local)."""
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
    async_add_entities([HolidayTodaySensor(entry)])


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
