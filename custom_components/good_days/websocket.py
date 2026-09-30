"""WS good_days/upcoming: holidays + external calendars merged, sorted and flagged for the card."""
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.util import dt as dt_util

from .const import CAT_FAMILY, CATEGORIES, DOMAIN, WS_MAX_DAYS, WS_MAX_LIMIT, WS_UPCOMING
from .engine import HolyEvent, hebrew_date, norm_language
from .family import FamilyEvent, hebrew_from_gregorian, next_occurrence
from .runtime import GoodDaysRuntime, PeriodIndex
from .ics import ics_path, new_token
from .storage import DateValidationError

CATEGORY_FAMILY = CAT_FAMILY
LOG = logging.getLogger(__name__)


def resolve_runtime(hass: HomeAssistant, entry_id: str | None = None) -> GoodDaysRuntime:
    """Runtime of entry_id, or of the first loaded entry in config order."""
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if not isinstance(runtime, GoodDaysRuntime):
            continue
        if entry_id is None or entry.entry_id == entry_id:
            return runtime
    raise HomeAssistantError(
        f"Good Days entry {entry_id} is not loaded" if entry_id else "Good Days is not loaded"
    )


def entry_label(hass: HomeAssistant, runtime: GoodDaysRuntime, lang: str) -> str:
    """Tells entries apart in pickers: title, place (HA's home name or coordinates), diaspora."""
    settings = runtime.settings
    at_home = (
        abs(settings.latitude - float(hass.config.latitude)) < 1e-4
        and abs(settings.longitude - float(hass.config.longitude)) < 1e-4
    )
    place = hass.config.location_name if at_home and hass.config.location_name else (
        f"{settings.latitude:.2f}, {settings.longitude:.2f}"
    )
    parts = [runtime.entry.title, place]
    if settings.diaspora:
        parts.append("חוץ לארץ" if lang == "he" else "Diaspora")
    return " · ".join(parts)


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (
        ws_upcoming, ws_dates_list, ws_dates_add, ws_dates_update, ws_dates_remove, ws_dates_convert,
        ws_ics_get, ws_ics_set, ws_entries,
    ):
        websocket_api.async_register_command(hass, command)


def _parse_external(raw: dict[str, Any]) -> tuple[dt.datetime, dt.datetime, bool] | None:
    start_raw, end_raw = str(raw.get("start", "")), str(raw.get("end", ""))
    if "T" not in start_raw:
        start_day, end_day = dt_util.parse_date(start_raw), dt_util.parse_date(end_raw)
        if start_day is None:
            return None
        if end_day is None or end_day <= start_day:
            end_day = start_day + dt.timedelta(days=1)
        return dt_util.start_of_local_day(start_day), dt_util.start_of_local_day(end_day), True
    start, end = dt_util.parse_datetime(start_raw), dt_util.parse_datetime(end_raw)
    if start is None:
        return None
    start = dt_util.as_local(start)
    end = dt_util.as_local(end) if end else start
    return start, max(end, start), False


async def _fetch_calendar(
    hass: HomeAssistant, context: Context, entity_id: str, start: dt.datetime, end: dt.datetime
) -> list[dict[str, Any]]:
    response = await hass.services.async_call(
        "calendar",
        "get_events",
        {"entity_id": entity_id, "start_date_time": start, "end_date_time": end},
        blocking=True,
        context=context,
        return_response=True,
    )
    return list(((response or {}).get(entity_id) or {}).get("events") or [])


def _external_item(
    entity_id: str, raw: dict[str, Any], periods: PeriodIndex, lang: str, now: dt.datetime
) -> dict[str, Any] | None:
    parsed = _parse_external(raw)
    if parsed is None:
        return None
    start, end, all_day = parsed
    probe_end = end if end > start else start + dt.timedelta(minutes=1)
    return {
        "uid": f"{entity_id}-{raw.get('uid') or start.isoformat()}-{raw.get('summary', '')}",
        "source": entity_id,
        "title": str(raw.get("summary") or ""),
        "start": start.date().isoformat() if all_day else start.isoformat(),
        "end": end.date().isoformat() if all_day else end.isoformat(),
        "all_day": all_day,
        "category": None,
        "hebrew_date": hebrew_date(start.date(), lang),
        "candle_lighting": None,
        "havdalah": None,
        "in_effect": start <= now < end,
        "conflicts_shabbat": periods.overlaps(start, probe_end),
        "description": raw.get("description") or "",
        "location": raw.get("location") or "",
        "_sort": start,
        "_end": end,
    }


@websocket_api.websocket_command(
    {
        vol.Required("type"): WS_UPCOMING,
        vol.Optional("entry_id"): cv.string,
        vol.Optional("calendars", default=[]): vol.All(cv.ensure_list, [cv.entity_domain("calendar")]),
        vol.Optional("days", default=30): vol.All(vol.Coerce(int), vol.Range(min=1, max=WS_MAX_DAYS)),
        vol.Optional("limit", default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=WS_MAX_LIMIT)),
        vol.Optional("categories"): vol.All(
            cv.ensure_list, [vol.In([*CATEGORIES, CATEGORY_FAMILY])]
        ),
        vol.Optional("language"): cv.string,
    }
)
@websocket_api.async_response
async def ws_upcoming(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    try:
        runtime = resolve_runtime(hass, msg.get("entry_id"))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return

    lang = norm_language(msg.get("language") or runtime.language)
    now = dt_util.now()
    end = now + dt.timedelta(days=msg["days"])
    if "categories" in msg:
        categories = set(msg["categories"])
    else:
        categories = runtime.categories | {CATEGORY_FAMILY}

    events = await runtime.async_events_between(now - dt.timedelta(days=1), end)
    periods = PeriodIndex(events)
    # (start, rank) now; titles and full items only for what can make the cut (below).
    # rank orders equal starts: holidays, then family, then external calendars.
    ours: list[tuple[dt.datetime, tuple[bool, bool], HolyEvent | FamilyEvent]] = [
        (e.start, (False, True), e) for e in events if e.category in categories and e.end > now
    ]
    if CATEGORY_FAMILY in categories:
        ours += [
            (e.start, (True, False), e)
            for e in await runtime.async_family_between(now - dt.timedelta(days=1), end)
            if e.end > now
        ]

    # This entry's own calendars are already merged above; never list them twice. Another
    # Good Days entry's calendar (e.g. the parents' city) is read like any other calendar.
    registry = er.async_get(hass)
    external = []
    for entity_id in dict.fromkeys(msg["calendars"]):
        reg = registry.async_get(entity_id)
        if reg is None or reg.platform != DOMAIN or reg.config_entry_id != runtime.entry.entry_id:
            external.append(entity_id)

    context = connection.context(msg)
    results = await asyncio.gather(
        *(_fetch_calendar(hass, context, eid, now, end) for eid in external),
        return_exceptions=True,
    )
    errors = []
    items: list[dict[str, Any]] = []
    for entity_id, result in zip(external, results):
        if isinstance(result, BaseException):
            if not isinstance(result, Exception):
                raise result  # cancellation and friends
            # Any calendar failure (timeouts, CalDAV errors...) only drops that calendar.
            if not isinstance(result, (HomeAssistantError, vol.Invalid)):
                LOG.warning("Good Days: reading %s failed: %r", entity_id, result)
            errors.append({"entity_id": entity_id, "error": str(result) or type(result).__name__})
            continue
        for raw in result:
            item = _external_item(entity_id, raw, periods, lang, now)
            if item and item["_end"] > now:
                items.append(item)

    limit = msg["limit"]
    entries = ours + [(i["_sort"], (True, True), i) for i in items]
    entries.sort(key=lambda e: (e[0], e[1]))
    if len(entries) > limit:
        # Keep everything tied with the last kept entry: the title decides among those.
        edge = entries[limit - 1][:2]
        cut = limit
        while cut < len(entries) and entries[cut][:2] == edge:
            cut += 1
        entries = entries[:cut]

    def title(value: Any) -> str:
        return value["title"] if isinstance(value, dict) else value.title(lang)

    entries.sort(key=lambda e: (e[0], e[1], title(e[2])))
    items = []
    for _start, _rank, value in entries[:limit]:
        if isinstance(value, dict):
            value.pop("_sort")
            value.pop("_end")
            items.append(value)
            continue
        item = runtime.render(value, lang, now)
        if isinstance(value, FamilyEvent):
            item["conflicts_shabbat"] = periods.overlaps(value.start, value.end)
        items.append(item)

    current = runtime.in_effect(now)
    connection.send_result(
        msg["id"],
        {
            "items": items,
            "now": now.isoformat(),
            "language": lang,
            "current": runtime.render(current, lang, now) if current else None,
            "errors": errors,
            # The effective set used for this reply (the card editor shows it when unset).
            "categories": [c for c in (*CATEGORIES, CATEGORY_FAMILY) if c in categories],
        },
    )


# Family dates (sidebar panel) ------------------------------------------------

_DATE_FIELDS = {
    vol.Optional("name"): cv.string,
    vol.Optional("kind"): cv.string,
    vol.Optional("hebrew_day"): vol.Any(int, cv.string),
    vol.Optional("hebrew_month"): cv.string,
    vol.Optional("original_year"): vol.Any(None, int, cv.string),
    vol.Optional("adar_rule"): vol.Any(None, cv.string),
    vol.Optional("day30_rule"): vol.Any(None, cv.string),
    vol.Optional("reminder_days"): vol.Any(None, [vol.Any(int, cv.string)]),
    vol.Optional("notes"): vol.Any(None, cv.string),
    vol.Optional("gregorian_date"): vol.Any(None, cv.string),
    vol.Optional("after_sunset"): bool,
}
_DATE_FIELD_NAMES = {str(key) for key in _DATE_FIELDS}


def _fields(msg: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in msg.items() if k in _DATE_FIELD_NAMES}


def _date_view(
    runtime: GoodDaysRuntime,
    record: dict[str, Any],
    lang: str,
    now: dt.datetime,
    cached: FamilyEvent | None = None,
) -> dict[str, Any]:
    """The stored record plus its current or next occurrence (runs in the executor)."""
    nxt = cached or next_occurrence(record, runtime.settings, now)
    view: dict[str, Any] = {**record, "next": None}
    if nxt:
        view["next"] = {**runtime.render(nxt, lang, now), "days_until": runtime.days_until(nxt, now)}
    return view


def _runtime_or_error(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> GoodDaysRuntime | None:
    try:
        return resolve_runtime(hass, msg.get("entry_id"))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return None


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dates/list",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
    }
)
@websocket_api.async_response
async def ws_dates_list(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    if (runtime := _runtime_or_error(hass, connection, msg)) is None:
        return
    lang = norm_language(msg.get("language") or runtime.language)
    now = dt_util.now()
    records = list(runtime.store.dates)
    # The cached window already holds each date's next occurrence; compute only the rest.
    cached: dict[str, FamilyEvent] = {}
    for event in runtime.family_events:
        if event.end > now:
            cached.setdefault(event.date_id, event)
    views = await hass.async_add_executor_job(
        lambda: [_date_view(runtime, r, lang, now, cached.get(r["id"])) for r in records]
    )
    views.sort(key=lambda v: (v["next"] is None, (v["next"] or {}).get("start", ""), v["name"]))
    connection.send_result(
        msg["id"],
        {"entry_id": runtime.entry.entry_id, "label": entry_label(hass, runtime, lang), "dates": views},
    )


@websocket_api.websocket_command(
    {vol.Required("type"): f"{DOMAIN}/entries", vol.Optional("language"): cv.string}
)
@callback
def ws_entries(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Loaded entries for the panel's instance picker (every user; no settings exposed)."""
    result = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        runtime = getattr(entry, "runtime_data", None)
        if isinstance(runtime, GoodDaysRuntime):
            lang = norm_language(msg.get("language") or runtime.language)
            result.append({"entry_id": entry.entry_id, "title": entry.title, "label": entry_label(hass, runtime, lang)})
    connection.send_result(msg["id"], {"entries": result})


async def _mutate(hass, connection, msg, action) -> None:
    """Run a store change; validation problems come back as {"errors": {field: code}}."""
    if (runtime := _runtime_or_error(hass, connection, msg)) is None:
        return
    try:
        record = await action(runtime)
    except DateValidationError as err:
        connection.send_result(msg["id"], {"errors": err.errors})
        return
    await runtime.async_refresh_family()
    result: dict[str, Any] = {"errors": {}}
    if record is not None:
        lang = norm_language(msg.get("language") or runtime.language)
        result["date"] = await hass.async_add_executor_job(
            _date_view, runtime, record, lang, dt_util.now()
        )
    connection.send_result(msg["id"], result)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dates/add",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        **_DATE_FIELDS,
    }
)
@websocket_api.async_response
async def ws_dates_add(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    await _mutate(hass, connection, msg, lambda runtime: runtime.store.async_add(_fields(msg)))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dates/update",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("date_id"): cv.string,
        **_DATE_FIELDS,
    }
)
@websocket_api.async_response
async def ws_dates_update(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    await _mutate(
        hass, connection, msg, lambda runtime: runtime.store.async_update(msg["date_id"], _fields(msg))
    )


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dates/remove",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("date_id"): cv.string,
    }
)
@websocket_api.async_response
async def ws_dates_remove(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    async def remove(runtime: GoodDaysRuntime) -> None:
        await runtime.store.async_remove(msg["date_id"])

    await _mutate(hass, connection, msg, remove)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/dates/convert",
        vol.Required("date"): cv.string,
        vol.Optional("after_sunset", default=False): bool,
        vol.Optional("language"): cv.string,
    }
)
@callback
def ws_dates_convert(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Gregorian birth / death date to a Hebrew date (the panel's converter)."""
    try:
        day = dt.date.fromisoformat(msg["date"])
    except ValueError:
        connection.send_result(msg["id"], {"errors": {"gregorian_date": "invalid_date"}})
        return
    shown = day + dt.timedelta(days=1) if msg["after_sunset"] else day
    connection.send_result(
        msg["id"],
        {
            "errors": {},
            **hebrew_from_gregorian(day, msg["after_sunset"]),
            "display": {"he": hebrew_date(shown, "he"), "en": hebrew_date(shown, "en")},
        },
    )


# Calendar subscription (ICS) ---------------------------------------------------


def _ics_view(hass: HomeAssistant, runtime: GoodDaysRuntime) -> dict[str, Any]:
    token = runtime.store.ics.get("token")
    result: dict[str, Any] = {
        "entry_id": runtime.entry.entry_id,
        "enabled": bool(token),
        "holidays": bool(runtime.store.ics.get("holidays")),
        "path": ics_path(runtime.entry.entry_id, token) if token else None,
        "url": None,
    }
    if token:
        try:
            base = get_url(hass, allow_internal=True, prefer_external=True)
        except NoURLAvailableError:
            base = None
        result["url"] = f"{base}{result['path']}" if base else None
    return result


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/ics/get",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
    }
)
@websocket_api.require_admin
@callback
def ws_ics_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (runtime := _runtime_or_error(hass, connection, msg)) is None:
        return
    connection.send_result(msg["id"], _ics_view(hass, runtime))


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/ics/set",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("enabled"): bool,
        vol.Optional("holidays", default=False): bool,
        vol.Optional("new_link", default=False): bool,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_ics_set(
    hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]
) -> None:
    """Turn the feed on / off, include holidays, or replace the link (old one stops working)."""
    if (runtime := _runtime_or_error(hass, connection, msg)) is None:
        return
    token = runtime.store.ics.get("token")
    if not msg["enabled"]:
        token = None
    elif token is None or msg["new_link"]:
        token = new_token()
    await runtime.store.async_set_ics(token, msg["holidays"])
    connection.send_result(msg["id"], _ics_view(hass, runtime))

