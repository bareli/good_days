"""Family-date reminders: notify services, mobile_app buttons, and a bus event for automations."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import TYPE_CHECKING, Any

from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    ACTION_ACK,
    ACTION_PREFIX,
    ACTION_SNOOZE,
    CONF_NOTIFY_TARGETS,
    CONF_QUIET_ON_SHABBAT,
    CONF_REMINDER_TIME,
    DEFAULT_REMINDER_TIME,
    DOMAIN,
    EVENT_REMINDER,
    KIND_YAHRZEIT,
    MAX_REMINDER_DAYS,
    REMINDER_LOOKBACK_DAYS,
    YAHRZEIT_EVENING_LEAD_MIN,
)
from .family import FamilyEvent, compute_family

if TYPE_CHECKING:
    from .runtime import GoodDaysRuntime

LOG = logging.getLogger(__name__)
ACTIONS_REGISTERED_KEY = f"{DOMAIN}_actions_registered"
PRUNE_DAYS = 10

TEXT = {
    "title": ("Good Days", "ימים טובים"),
    "today": ("Today: {t}", "היום: {t}"),
    "tomorrow": ("Tomorrow: {t}", "מחר: {t}"),
    "in_days": ("In {n} days: {t}", "בעוד {n} ימים: {t}"),
    "in_2_days": ("In 2 days: {t}", "בעוד יומיים: {t}"),
    "tonight": ("Tonight: {t}", "הערב: {t}"),
    "candle": ("Light a candle before {time}.", "הדליקו נר לפני {time}."),
    "candle_after": ("Light a candle after havdalah ({time}).", "הדליקו נר אחרי ההבדלה ({time})."),
    "ack": ("Got it", "הבנתי"),
    "snooze": ("Remind me tomorrow", "תזכירו לי מחר"),
}


def _t(key: str, lang: str, **kw: Any) -> str:
    en, he = TEXT[key]
    return (he if lang == "he" else en).format(**kw)


def parse_time(value: str | None) -> dt.time:
    try:
        hours, minutes = str(value or DEFAULT_REMINDER_TIME).split(":")[:2]
        return dt.time(int(hours), int(minutes))
    except (TypeError, ValueError):
        return dt.time(9, 0)


def candle_time(event: FamilyEvent, period) -> tuple[str, dt.datetime]:
    """When to light a yahrzeit candle: ("before", t) or ("after", havdalah).

    The yahrzeit begins at sunset; if that falls in Shabbat / Yom Tov, light before candle
    lighting when the yahrzeit day is part of it, or after havdalah when it begins as it ends.
    """
    if period is None:
        return "before", event.start
    if period.covers_day(event.first_day):
        return "before", period.start
    return "after", period.end


def reminder_message(
    event: FamilyEvent, lang: str, now: dt.datetime, candle: tuple[str, dt.datetime] | None = None
) -> str:
    """Text by the real distance at send time."""
    title = event.title(lang)
    days = (event.first_day - dt_util.as_local(now).date()).days
    evening = event.kind == KIND_YAHRZEIT and days == 1 and dt_util.as_local(now).hour >= 12
    if days <= 0:
        text = _t("today", lang, t=title)
    elif evening:
        text = _t("tonight", lang, t=title)
    elif days == 1:
        text = _t("tomorrow", lang, t=title)
    elif days == 2:
        text = _t("in_2_days", lang, t=title)
    else:
        text = _t("in_days", lang, n=days, t=title)
    if event.kind == KIND_YAHRZEIT and not event.all_day and candle and days <= 1:
        when, at = candle
        if now < at or when == "after":
            key = "candle" if when == "before" else "candle_after"
            text = f"{text}. {_t(key, lang, time=dt_util.as_local(at).strftime('%H:%M'))}"
    return text


class ReminderManager:
    """Checks every minute (runtime tick) which reminders are due and sends them once."""

    def __init__(self, runtime: GoodDaysRuntime) -> None:
        self.runtime = runtime
        self.hass: HomeAssistant = runtime.hass
        options = runtime.entry.options
        self.targets: list[str] = [t for t in options.get(CONF_NOTIFY_TARGETS, []) if t]
        self.time = parse_time(options.get(CONF_REMINDER_TIME))
        self.quiet = bool(options.get(CONF_QUIET_ON_SHABBAT, True))
        self._lock = asyncio.Lock()
        self._cache_key: tuple | None = None
        self._events: list[FamilyEvent] = []

    def candle(self, event: FamilyEvent) -> tuple[str, dt.datetime]:
        return candle_time(event, self.runtime.period_at(event.start))

    def due_at(self, event: FamilyEvent, days_before: int) -> dt.datetime:
        if event.kind == KIND_YAHRZEIT and days_before == 0 and not event.all_day:
            when, at = self.candle(event)
            if when == "after":
                return at  # right after havdalah
            due = at - dt.timedelta(minutes=YAHRZEIT_EVENING_LEAD_MIN)
        else:
            day = event.first_day - dt.timedelta(days=days_before)
            due = dt.datetime.combine(day, self.time, dt_util.get_default_time_zone())
        if self.quiet and (period := self.runtime.period_at(due)) is not None:
            # Due on Shabbat / Yom Tov: send it before candle lighting instead.
            due = period.start - dt.timedelta(minutes=YAHRZEIT_EVENING_LEAD_MIN)
        return due

    async def _occurrences(self, now: dt.datetime) -> list[FamilyEvent]:
        today = dt_util.as_local(now).date()
        key = (today, self.runtime.family_version)
        if key != self._cache_key:
            self._events = await self.hass.async_add_executor_job(
                compute_family,
                list(self.runtime.store.dates),
                self.runtime.settings,
                today - dt.timedelta(days=REMINDER_LOOKBACK_DAYS + 1),
                today + dt.timedelta(days=MAX_REMINDER_DAYS + 1),
            )
            self._cache_key = key
        return self._events

    async def async_check(self, now: dt.datetime | None = None) -> None:
        async with self._lock:
            await self._async_check(now or dt_util.now())

    async def _async_check(self, now: dt.datetime) -> None:
        store = self.runtime.store
        if not store.dates and not store.reminders.get("snoozes"):
            return
        state = store.reminders
        since = dt_util.parse_datetime(state["since"]) or now
        low = max(since, now - dt.timedelta(days=REMINDER_LOOKBACK_DAYS))
        events = await self._occurrences(now)
        by_occurrence = {(e.date_id, e.first_day.isoformat()): e for e in events}

        # Per occurrence, the latest due reminder wins; earlier ones are marked sent with it.
        due: dict[tuple[str, str], tuple[dt.datetime, list[str]]] = {}
        for event in events:
            record = store.get(event.date_id)
            occ = (event.date_id, event.first_day.isoformat())
            if record is None or now >= event.end or ":".join(occ) in state["acked"]:
                continue
            created = dt_util.parse_datetime(record.get("created_at") or "")
            for days_before in record.get("reminder_days") or []:
                when = self.due_at(event, int(days_before))
                key = f"{occ[0]}:{occ[1]}:{days_before}"
                if not low < when <= now or key in state["sent"] or (created and when < created):
                    continue
                latest, keys = due.get(occ, (when, []))
                due[occ] = (max(latest, when), [*keys, key])

        fired_snoozes = []
        for snooze in state["snoozes"]:
            when = dt_util.parse_datetime(snooze.get("due", ""))
            occ = (snooze.get("date_id", ""), snooze.get("day", ""))
            if when is None or when > now:
                continue
            fired_snoozes.append(snooze)
            if occ in by_occurrence and ":".join(occ) not in state["acked"] and now < by_occurrence[occ].end:
                latest, keys = due.get(occ, (when, []))
                due[occ] = (max(latest, when), keys)

        if not due and not fired_snoozes:
            self._prune(now)
            return
        if self.quiet and self.runtime.in_effect(now):
            return  # hold until havdalah; the lookback window keeps them due

        for occ, (_when, keys) in sorted(due.items(), key=lambda item: item[1][0]):
            await self._send(by_occurrence[occ], now)
            for key in keys:
                state["sent"][key] = occ[1]
        state["snoozes"] = [s for s in state["snoozes"] if s not in fired_snoozes]
        self._prune(now)
        await store.async_save_reminders()

    def _prune(self, now: dt.datetime) -> None:
        cutoff = (dt_util.as_local(now).date() - dt.timedelta(days=PRUNE_DAYS)).isoformat()
        for bucket in ("sent", "acked"):
            state = self.runtime.store.reminders[bucket]
            for key in [k for k, day in state.items() if day < cutoff]:
                del state[key]

    async def _send(self, event: FamilyEvent, now: dt.datetime) -> None:
        lang = self.runtime.language
        title = _t("title", lang)
        candle = self.candle(event) if event.kind == KIND_YAHRZEIT and not event.all_day else None
        message = reminder_message(event, lang, now, candle)
        entry_id = self.runtime.entry.entry_id
        self.hass.bus.async_fire(
            EVENT_REMINDER,
            {
                "entry_id": entry_id,
                "date_id": event.date_id,
                "name": event.name,
                "kind": event.kind,
                "day": event.first_day.isoformat(),
                "years": event.years,
                "title": event.title(lang),
                "message": message,
            },
        )
        occurrence = f"{entry_id}:{event.date_id}:{event.first_day.isoformat()}"
        for target in self.targets:
            if not self.hass.services.has_service("notify", target):
                LOG.warning("Good Days reminder: notify.%s does not exist", target)
                continue
            payload: dict[str, Any] = {"title": title, "message": message}
            # Only the companion app understands action buttons.
            if target.startswith("mobile_app_"):
                payload["data"] = {
                    "tag": f"good_days_{event.date_id}_{event.first_day.isoformat()}",
                    "actions": [
                        {"action": f"{ACTION_PREFIX}:{ACTION_ACK}:{occurrence}", "title": _t("ack", lang)},
                        {"action": f"{ACTION_PREFIX}:{ACTION_SNOOZE}:{occurrence}", "title": _t("snooze", lang)},
                    ],
                }
            try:
                await self.hass.services.async_call("notify", target, payload, blocking=False)
            except Exception as err:  # noqa: BLE001 - one broken notifier must not block the others
                LOG.warning("Good Days reminder via notify.%s failed: %s", target, err)

    async def async_ack(self, date_id: str, day: str) -> None:
        self.runtime.store.reminders["acked"][f"{date_id}:{day}"] = day
        await self.runtime.store.async_save_reminders()

    async def async_snooze(self, date_id: str, day: str, now: dt.datetime | None = None) -> None:
        due = (now or dt_util.now()) + dt.timedelta(days=1)
        state = self.runtime.store.reminders
        # One snooze per occurrence: pressing again moves it, never piles up.
        state["snoozes"] = [
            s for s in state["snoozes"] if (s.get("date_id"), s.get("day")) != (date_id, day)
        ] + [{"date_id": date_id, "day": day, "due": due.isoformat()}]
        await self.runtime.store.async_save_reminders()

    def is_valid_action(self, date_id: str, day: str, now: dt.datetime | None = None) -> bool:
        """A button press names an existing date and an ISO day inside the reminder window."""
        if self.runtime.store.get(date_id) is None:
            return False
        try:
            occurrence = dt.date.fromisoformat(day)
        except ValueError:
            return False
        today = dt_util.as_local(now or dt_util.now()).date()
        low = today - dt.timedelta(days=REMINDER_LOOKBACK_DAYS + 1)
        high = today + dt.timedelta(days=MAX_REMINDER_DAYS + 1)
        return low <= occurrence <= high


@callback
def async_register_actions(hass: HomeAssistant) -> None:
    """Handle the buttons of reminder notifications (all entries)."""
    if hass.data.get(ACTIONS_REGISTERED_KEY):
        return
    hass.data[ACTIONS_REGISTERED_KEY] = True

    async def _on_action(event: Event) -> None:
        parts = str(event.data.get("action", "")).split(":")
        if len(parts) != 5 or parts[0] != ACTION_PREFIX:
            return
        _, command, entry_id, date_id, day = parts
        entry = hass.config_entries.async_get_entry(entry_id)
        runtime = getattr(entry, "runtime_data", None) if entry else None
        manager = getattr(runtime, "reminders", None)
        if manager is None or not manager.is_valid_action(date_id, day):
            return
        if command == ACTION_ACK:
            await manager.async_ack(date_id, day)
        elif command == ACTION_SNOOZE:
            await manager.async_snooze(date_id, day)

    hass.bus.async_listen("mobile_app_notification_action", _on_action)
