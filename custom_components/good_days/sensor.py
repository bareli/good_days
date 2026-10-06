"""Next Shabbat (candle lighting timestamp), next holiday and next family date sensors."""
from __future__ import annotations

import datetime as dt
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .engine import hebrew_date, omer_text
from .entity import GoodDaysEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities(
        [
            NextShabbatSensor(entry),
            NextHolidaySensor(entry),
            NextFamilySensor(entry),
            NextCandleLightingSensor(entry),
            NextTimerActionSensor(entry),
            NextFastSensor(entry),
            OmerSensor(entry),
        ]
    )


def _iso(value: dt.datetime | None) -> str | None:
    return value.isoformat() if value else None


class NextShabbatSensor(GoodDaysEntity, SensorEntity):
    """Candle lighting of the current or next Shabbat (merged with Yom Tov when adjacent)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_shabbat")

    @property
    def native_value(self) -> dt.datetime | None:
        event = self.runtime.next_shabbat(dt_util.now())
        if event is None:
            return None
        return event.candle_lighting or event.start

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        now = dt_util.now()
        event = self.runtime.next_shabbat(now)
        if event is None:
            return None
        lang = self.runtime.language
        return {
            "title": event.title(lang),
            "havdalah": _iso(event.havdalah),
            "parasha": event.parasha_name(lang),
            "haftarah": event.haftarah_reading(lang),
            "special_shabbat": [event.special_name(k, lang) for k in event.specials],
            "hebrew_date": hebrew_date(event.last_day, lang),
            "days_until": self.runtime.days_until(event, now),
            "in_effect": event.start <= now < event.end,
            "uid": event.uid,
        }


class NextHolidaySensor(GoodDaysEntity, SensorEntity):
    """Name of the current or next holiday (categories from the entry options, no plain Shabbat)."""

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_holiday")

    @property
    def native_value(self) -> str | None:
        event = self.runtime.next_holiday(dt_util.now())
        return event.title(self.runtime.language)[:255] if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        now = dt_util.now()
        event = self.runtime.next_holiday(now)
        if event is None:
            return None
        item = self.runtime.render(event, self.runtime.language, now)
        return {
            "start": item["start"],
            "end": item["end"],
            "all_day": event.all_day,
            "category": event.category,
            "days_until": self.runtime.days_until(event, now),
            "hebrew_date": item["hebrew_date"],
            "candle_lighting": item["candle_lighting"],
            "havdalah": item["havdalah"],
            "in_effect": item["in_effect"],
            "uid": event.uid,
        }


class NextFamilySensor(GoodDaysEntity, SensorEntity):
    """Title of the current or next family date."""

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_family")

    @property
    def native_value(self) -> str | None:
        event = self.runtime.next_family(dt_util.now())
        return event.title(self.runtime.language)[:255] if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        now = dt_util.now()
        event = self.runtime.next_family(now)
        if event is None:
            return None
        item = self.runtime.render(event, self.runtime.language, now)
        return {
            "name": event.name,
            "kind": event.kind,
            "years": event.years,
            "start": item["start"],
            "end": item["end"],
            "all_day": event.all_day,
            "days_until": self.runtime.days_until(event, now),
            "hebrew_date": item["hebrew_date"],
            "in_effect": item["in_effect"],
            "conflicts_shabbat": item["conflicts_shabbat"],
            "uid": event.uid,
        }


class NextCandleLightingSensor(GoodDaysEntity, SensorEntity):
    """Candle lighting of the current or next Shabbat or Yom Tov (whatever else is on the calendar)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_candle_lighting")

    @property
    def native_value(self) -> dt.datetime | None:
        event = self.runtime.next_period(dt_util.now())
        if event is None:
            return None
        return event.candle_lighting or event.start

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        now = dt_util.now()
        event = self.runtime.next_period(now)
        if event is None:
            return None
        lang = self.runtime.language
        return {
            "title": event.title(lang),
            "category": event.category,
            "havdalah": _iso(event.havdalah or event.end),
            "days_until": self.runtime.days_until(event, now),
            "in_effect": event.start <= now < event.end,
            "uid": event.uid,
        }


class NextTimerActionSensor(GoodDaysEntity, SensorEntity):
    """When the next Shabbat timer fires (none while timers are off)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_timer_action")

    @property
    def native_value(self) -> dt.datetime | None:
        action = self.runtime.timers.next_action(dt_util.now())
        return action.when if action else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        action = self.runtime.timers.next_action(dt_util.now())
        if action is None:
            return None
        return {"rule": action.rule_name, "action": action.action, "targets": list(action.targets)}


class NextFastSensor(GoodDaysEntity, SensorEntity):
    """Start of the current or next fast (minor fasts from dawn, Tisha B'Av and Yom Kippur from the evening)."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:food-off-outline"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "next_fast")

    @property
    def native_value(self) -> dt.datetime | None:
        event = self.runtime.next_fast(dt_util.now())
        return event.start if event else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        now = dt_util.now()
        event = self.runtime.next_fast(now)
        if event is None:
            return None
        lang = self.runtime.language
        return {
            "title": event.title(lang),
            "end": _iso(event.end),
            "all_day": event.all_day,
            "hebrew_date": hebrew_date(event.last_day, lang),
            "days_until": self.runtime.days_until(event, now),
            "in_effect": event.start <= now < event.end,
            "uid": event.uid,
        }


class OmerSensor(GoodDaysEntity, SensorEntity):
    """Day of the Omer (1-49) for the Hebrew day in progress: it moves on at tzeit. Unknown outside the Omer."""

    _attr_icon = "mdi:sprout-outline"

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "omer")

    @property
    def native_value(self) -> int | None:
        day, _, _ = self.runtime.omer(dt_util.now())
        return day or None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        day, night, next_count = self.runtime.omer(dt_util.now())
        weeks, days = divmod(day, 7)
        return {
            "weeks": weeks,
            "days": days,
            "text": omer_text(day, self.runtime.language, self.runtime.settings.nusach) or None,
            "next_count": _iso(next_count),
            # "Counted" pressed on this night's reminder (an automation can remind again if not).
            "counted": bool(day) and self.runtime.reminders.omer_counted(night),
        }
