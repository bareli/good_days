"""WS good_days/upcoming: holidays + external calendars merged, sorted and flagged for the card."""
from __future__ import annotations

import asyncio
import datetime as dt
from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import Context, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, entity_registry as er
from homeassistant.util import dt as dt_util

from .const import CATEGORIES, DOMAIN, WS_MAX_DAYS, WS_MAX_LIMIT, WS_UPCOMING
from .engine import HolyEvent, hebrew_date, norm_language
from .runtime import GoodDaysRuntime

CATEGORY_FAMILY = "family"  # v0.2; accepted now so card configs stay valid


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


@callback
def async_register(hass: HomeAssistant) -> None:
    websocket_api.async_register_command(hass, ws_upcoming)


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
    entity_id: str, raw: dict[str, Any], periods: list[HolyEvent], lang: str, now: dt.datetime
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
        "conflicts_shabbat": any(p.overlaps(start, probe_end) for p in periods),
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
    categories = set(msg["categories"]) & set(CATEGORIES) if "categories" in msg else runtime.categories

    events = await runtime.async_events_between(now - dt.timedelta(days=1), end)
    periods = [e for e in events if e.period]
    items: list[dict[str, Any]] = []
    for event in events:
        if event.category in categories and event.end > now:
            item = runtime.render(event, lang, now)
            items.append({**item, "_sort": event.start, "_end": event.end})

    # Our own calendars are already merged above; never list them twice.
    registry = er.async_get(hass)
    external = []
    for entity_id in dict.fromkeys(msg["calendars"]):
        reg = registry.async_get(entity_id)
        if reg is None or reg.platform != DOMAIN:
            external.append(entity_id)

    context = connection.context(msg)
    results = await asyncio.gather(
        *(_fetch_calendar(hass, context, eid, now, end) for eid in external),
        return_exceptions=True,
    )
    errors = []
    for entity_id, result in zip(external, results):
        if isinstance(result, BaseException):
            if not isinstance(result, (HomeAssistantError, vol.Invalid)):
                raise result
            errors.append({"entity_id": entity_id, "error": str(result) or type(result).__name__})
            continue
        for raw in result:
            item = _external_item(entity_id, raw, periods, lang, now)
            if item and item["_end"] > now:
                items.append(item)

    items.sort(key=lambda i: (i["_sort"], i["source"] != "holidays", i["title"]))
    items = items[: msg["limit"]]
    for item in items:
        item.pop("_sort")
        item.pop("_end")

    current = runtime.in_effect(now)
    connection.send_result(
        msg["id"],
        {
            "items": items,
            "now": now.isoformat(),
            "language": lang,
            "current": runtime.render(current, lang, now) if current else None,
            "errors": errors,
        },
    )
