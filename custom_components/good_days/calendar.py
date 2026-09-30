"""calendar.good_days_holidays: Shabbatot, holidays, fasts (filtered by the entry's categories)."""
from __future__ import annotations

import datetime as dt

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import dt as dt_util

from .engine import HolyEvent
from .entity import GoodDaysEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([HolidaysCalendar(entry)])


class HolidaysCalendar(GoodDaysEntity, CalendarEntity):
    """Timed events for Shabbat / Yom Tov (candle lighting to havdalah), all-day for the rest."""

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "holidays")

    def _to_event(self, event: HolyEvent) -> CalendarEvent:
        lang = self.runtime.language
        if event.all_day:
            start: dt.date | dt.datetime = event.first_day
            end: dt.date | dt.datetime = event.last_day + dt.timedelta(days=1)
        else:
            start, end = event.start, event.end
        return CalendarEvent(
            start=start,
            end=end,
            summary=event.title(lang),
            description=event.description(lang),
            uid=event.uid,
        )

    @property
    def event(self) -> CalendarEvent | None:
        found = self.runtime.current_or_next(dt_util.now())
        return self._to_event(found) if found else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: dt.datetime, end_date: dt.datetime
    ) -> list[CalendarEvent]:
        events = await self.runtime.async_events_between(start_date, end_date)
        cats = self.runtime.categories
        return [self._to_event(e) for e in events if e.category in cats]
