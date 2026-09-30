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

from . import engine
from .const import (
    CATEGORIES,
    CONF_CANDLE_LIGHTING,
    CONF_CATEGORIES,
    CONF_DIASPORA,
    CONF_ELEVATION,
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
    SOURCE_HOLIDAYS,
)
from .engine import EngineSettings, HolyEvent, hebrew_date, norm_language

PAST_DAYS = 7
MAX_ADHOC_DAYS = 3 * 366  # calendar panel requests outside the cached window


def settings_from_entry(hass: HomeAssistant, entry: ConfigEntry) -> EngineSettings:
    o = entry.options
    return EngineSettings(
        latitude=float(o.get(CONF_LATITUDE, hass.config.latitude)),
        longitude=float(o.get(CONF_LONGITUDE, hass.config.longitude)),
        elevation=float(o.get(CONF_ELEVATION, hass.config.elevation or 0)),
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
        self.window: tuple[dt.date, dt.date] | None = None
        self._unsubs: list[Callable[[], None]] = []

    @property
    def language(self) -> str:
        if self._language_option in (None, "", LANG_AUTO):
            return norm_language(self.hass.config.language)
        return norm_language(self._language_option)

    async def async_start(self) -> None:
        await self.async_refresh()
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

    async def _async_daily(self, _now: dt.datetime) -> None:
        await self.async_refresh()

    @callback
    def _tick(self, _now: dt.datetime) -> None:
        async_dispatcher_send(self.hass, SIGNAL_UPDATED.format(self.entry.entry_id))

    async def async_refresh(self) -> None:
        today = dt_util.now().date()
        start = today - dt.timedelta(days=PAST_DAYS)
        end = today + dt.timedelta(days=self.lookahead)
        events = await self.hass.async_add_executor_job(engine.compute, self.settings, start, end)
        self.events, self.window = events, (start, end)
        async_dispatcher_send(self.hass, SIGNAL_UPDATED.format(self.entry.entry_id))

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

    def render(self, event: HolyEvent, lang: str, now: dt.datetime) -> dict[str, Any]:
        """WebSocket / attribute shape (SPEC §7.3)."""
        return {
            "uid": event.uid,
            "source": SOURCE_HOLIDAYS,
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
            "conflicts_shabbat": False,
            "description": event.description(lang),
        }
