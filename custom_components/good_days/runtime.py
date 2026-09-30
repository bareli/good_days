"""Per-entry runtime: settings, the cached event window, refresh timers, item rendering."""
from __future__ import annotations

import datetime as dt
from collections.abc import Callable, Iterable
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_change, async_track_time_interval
from homeassistant.util import dt as dt_util

from . import engine, family
from .const import (
    CATEGORIES,
    CONF_CANDLE_LIGHTING,
    CONF_CATEGORIES,
    CONF_DIASPORA,
    CONF_HAVDALAH,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_DAYS,
    DEFAULT_CANDLE_LIGHTING,
    DEFAULT_CATEGORIES,
    DEFAULT_HAVDALAH,
    DEFAULT_LOOKAHEAD_DAYS,
    LANG_AUTO,
    NON_HOLIDAY_CATEGORIES,
    SIGNAL_UPDATED,
    SOURCE_FAMILY,
    SOURCE_HOLIDAYS,
)
from .engine import EngineSettings, HolyEvent, hebrew_date, norm_language
from .family import FamilyEvent
from .reminders import ReminderManager
from .timer_manager import TimerManager
from .storage import FamilyStore

PAST_DAYS = 7
MAX_ADHOC_DAYS = 3 * 366  # calendar panel requests outside the cached window


def settings_from_entry(hass: HomeAssistant, entry: ConfigEntry) -> EngineSettings:
    o = entry.options
    return EngineSettings(
        latitude=float(o.get(CONF_LATITUDE, hass.config.latitude)),
        longitude=float(o.get(CONF_LONGITUDE, hass.config.longitude)),
        elevation=0.0,
        time_zone=str(hass.config.time_zone),
        diaspora=bool(o.get(CONF_DIASPORA, False)),
        candle_lighting=int(o.get(CONF_CANDLE_LIGHTING, DEFAULT_CANDLE_LIGHTING)),
        havdalah=int(o.get(CONF_HAVDALAH, DEFAULT_HAVDALAH)),
    )


def _iso(value: dt.datetime | None) -> str | None:
    return value.isoformat() if value else None


class GoodDaysRuntime:
    """Holds the pre-computed events for one config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.settings = settings_from_entry(hass, entry)
        self.categories: set[str] = set(entry.options.get(CONF_CATEGORIES, DEFAULT_CATEGORIES)) & set(CATEGORIES)
        self.lookahead = int(entry.options.get(CONF_LOOKAHEAD_DAYS, DEFAULT_LOOKAHEAD_DAYS))
        self._language_option = entry.options.get(CONF_LANGUAGE, LANG_AUTO)
        self.events: list[HolyEvent] = []
        self.store = FamilyStore(hass, entry.entry_id)
        self.family_events: list[FamilyEvent] = []
        self.family_version = 0  # bumped whenever dates or the window change
        self.reminders = ReminderManager(self)
        self.timers = TimerManager(self)
        self.ics_cache: tuple | None = None  # (key, body), see ics.async_feed
        self.window: tuple[dt.date, dt.date] | None = None
        self._unsubs: list[Callable[[], None]] = []

    @property
    def language(self) -> str:
        if self._language_option in (None, "", LANG_AUTO):
            return norm_language(self.hass.config.language)
        return norm_language(self._language_option)

    async def async_start(self) -> None:
        await self.store.async_load()
        await self.async_refresh()
        await self.timers.async_start()
        self._unsubs.append(
            async_track_time_change(self.hass, self._async_daily, hour=0, minute=5, second=0)
        )
        # Countdowns, "in effect" flags and next-event sensors move with the clock.
        self._unsubs.append(
            async_track_time_interval(self.hass, self._tick, dt.timedelta(minutes=1))
        )

    @callback
    def async_stop(self) -> None:
        while self._unsubs:
            self._unsubs.pop()()
        self.timers.async_stop()

    async def _async_daily(self, _now: dt.datetime) -> None:
        await self.async_refresh()

    @callback
    def _tick(self, now: dt.datetime) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATED.format(self.entry.entry_id))
        self.entry.async_create_background_task(
            self.hass, self.reminders.async_check(now), f"{self.entry.entry_id} reminders"
        )
        # Cheap when nothing changed; picks up the next period as soon as one ends.
        self.entry.async_create_background_task(
            self.hass, self.timers.async_replan(), f"{self.entry.entry_id} timers"
        )

    async def async_refresh(self) -> None:
        today = dt_util.now().date()
        start = today - dt.timedelta(days=PAST_DAYS)
        end = today + dt.timedelta(days=self.lookahead)
        events = await self.hass.async_add_executor_job(engine.compute, self.settings, start, end)
        family_events = await self.hass.async_add_executor_job(
            family.compute_family, list(self.store.dates), self.settings, start, end
        )
        self.events, self.family_events, self.window = events, family_events, (start, end)
        self.family_version += 1
        async_dispatcher_send(self.hass, SIGNAL_UPDATED.format(self.entry.entry_id))

    async def async_refresh_family(self) -> None:
        """Recompute family occurrences after a date was added, changed or removed."""
        if self.window is None:
            return
        start, end = self.window
        self.family_events = await self.hass.async_add_executor_job(
            family.compute_family, list(self.store.dates), self.settings, start, end
        )
        self.family_version += 1
        async_dispatcher_send(self.hass, SIGNAL_UPDATED.format(self.entry.entry_id))

    async def async_family_between(self, start: dt.datetime, end: dt.datetime) -> list[FamilyEvent]:
        if end <= start:
            return []
        first, last = dt_util.as_local(start).date(), dt_util.as_local(end).date()
        if self.window and self.window[0] <= first and last <= self.window[1]:
            events: Iterable[FamilyEvent] = self.family_events
        else:
            last = min(last, first + dt.timedelta(days=MAX_ADHOC_DAYS))
            events = await self.hass.async_add_executor_job(
                family.compute_family, list(self.store.dates), self.settings, first, last
            )
        return [e for e in events if e.overlaps(start, end)]

    def next_family(self, now: dt.datetime) -> FamilyEvent | None:
        return next((e for e in self.family_events if e.end > now), None)

    def periods_overlapping(self, start: dt.datetime, end: dt.datetime) -> bool:
        """True when [start, end) touches any Shabbat / Yom Tov period in the cached window."""
        probe_end = end if end > start else start + dt.timedelta(minutes=1)
        return any(e.period and e.overlaps(start, probe_end) for e in self.events)

    async def async_events_between(self, start: dt.datetime, end: dt.datetime) -> list[HolyEvent]:
        """All events (every category) overlapping [start, end)."""
        if end <= start:
            return []
        first, last = dt_util.as_local(start).date(), dt_util.as_local(end).date()
        if self.window and self.window[0] <= first and last <= self.window[1]:
            events: Iterable[HolyEvent] = self.events
        else:
            last = min(last, first + dt.timedelta(days=MAX_ADHOC_DAYS))
            events = await self.hass.async_add_executor_job(
                engine.compute, self.settings, first, last
            )
        return [e for e in events if e.overlaps(start, end)]

    # Entity helpers (cached window only; entities look at most a year ahead).

    def visible(self, categories: set[str] | None = None) -> list[HolyEvent]:
        cats = self.categories if categories is None else categories
        return [e for e in self.events if e.category in cats]

    def current_or_next(self, now: dt.datetime, categories: set[str] | None = None) -> HolyEvent | None:
        return next((e for e in self.visible(categories) if e.end > now), None)

    def next_period(self, now: dt.datetime) -> HolyEvent | None:
        """Current or next Shabbat / Yom Tov (candle lighting to havdalah), any category."""
        return next((e for e in self.events if e.period and e.end > now), None)

    def period_at(self, when: dt.datetime) -> HolyEvent | None:
        return next((e for e in self.events if e.period and e.start <= when < e.end), None)

    def next_shabbat(self, now: dt.datetime) -> HolyEvent | None:
        return next((e for e in self.events if e.period and e.is_shabbat and e.end > now), None)

    def next_holiday(self, now: dt.datetime) -> HolyEvent | None:
        return self.current_or_next(now, self.categories - NON_HOLIDAY_CATEGORIES)

    def holidays_on(self, day: dt.date) -> list[HolyEvent]:
        cats = self.categories - NON_HOLIDAY_CATEGORIES
        return [e for e in self.events if e.category in cats and e.covers_day(day)]

    def in_effect(self, now: dt.datetime) -> HolyEvent | None:
        """The Shabbat / Yom Tov period in effect right now, if any."""
        return next((e for e in self.events if e.period and e.start <= now < e.end), None)

    @staticmethod
    def days_until(event: HolyEvent, now: dt.datetime) -> int:
        if event.start <= now:
            return 0
        return (dt_util.as_local(event.start).date() - dt_util.as_local(now).date()).days

    def render(self, event: HolyEvent | FamilyEvent, lang: str, now: dt.datetime) -> dict[str, Any]:
        """WebSocket / attribute shape (SPEC §7.3)."""
        is_family = isinstance(event, FamilyEvent)
        item = {
            "uid": event.uid,
            "source": SOURCE_FAMILY if is_family else SOURCE_HOLIDAYS,
            "title": event.title(lang),
            "start": event.first_day.isoformat() if event.all_day else event.start.isoformat(),
            "end": (event.last_day + dt.timedelta(days=1)).isoformat()
            if event.all_day
            else event.end.isoformat(),
            "all_day": event.all_day,
            "category": event.category,
            "hebrew_date": hebrew_date(event.first_day, lang),
            "candle_lighting": _iso(event.candle_lighting),
            "havdalah": _iso(event.havdalah),
            "in_effect": event.start <= now < event.end,
            "conflicts_shabbat": is_family and self.periods_overlapping(event.start, event.end),
            "description": event.description(lang),
        }
        if is_family:
            item.update(
                kind=event.kind, name=event.name, years=event.years, date_id=event.date_id,
                day=event.first_day.isoformat(),
            )
        return item
