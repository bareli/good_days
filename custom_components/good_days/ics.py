"""ICS feed of family dates (and optionally holidays) for calendar apps (RFC 5545)."""
from __future__ import annotations

import datetime as dt
import hmac
import secrets
from collections.abc import Iterable
from http import HTTPStatus
from typing import TYPE_CHECKING

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from .const import DOMAIN

if TYPE_CHECKING:
    from .runtime import GoodDaysRuntime

PAST_DAYS = 30
FUTURE_DAYS = 730
REFRESH = "PT12H"
URL_PATH = "/api/good_days/ics/{entry_id}/{token}.ics"
NAMES = {"en": "Good Days", "he": "ימים טובים"}


def new_token() -> str:
    return secrets.token_urlsafe(32)


def ics_path(entry_id: str, token: str) -> str:
    return URL_PATH.format(entry_id=entry_id, token=token)


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\r", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold at 75 octets without splitting a UTF-8 character (RFC 5545 §3.1)."""
    out: list[str] = []
    current, size = "", 0
    for char in line:
        width = len(char.encode("utf-8"))
        limit = 75 if not out else 74  # continuation lines start with a space
        if size + width > limit:
            out.append(current)
            current, size = char, width
        else:
            current += char
            size += width
    out.append(current)
    return "\r\n ".join(out)


def _utc(value: dt.datetime) -> str:
    return dt_util.as_utc(value).strftime("%Y%m%dT%H%M%SZ")


def _event_lines(event, lang: str, stamp: str) -> list[str]:
    lines = [
        "BEGIN:VEVENT",
        f"UID:{event.uid}@{DOMAIN}",
        f"DTSTAMP:{stamp}",
    ]
    if event.all_day:
        end = event.first_day + dt.timedelta(days=event.days)
        lines += [
            f"DTSTART;VALUE=DATE:{event.first_day:%Y%m%d}",
            f"DTEND;VALUE=DATE:{end:%Y%m%d}",
            "TRANSP:TRANSPARENT",
        ]
    else:
        lines += [f"DTSTART:{_utc(event.start)}", f"DTEND:{_utc(event.end)}"]
    lines += [
        f"SUMMARY:{_escape(event.title(lang))}",
        f"DESCRIPTION:{_escape(event.description(lang))}",
        f"CATEGORIES:{_escape(event.category)}",
        "END:VEVENT",
    ]
    return lines


def build_ics(events: Iterable, lang: str, now: dt.datetime) -> str:
    stamp = _utc(now)
    name = NAMES.get(lang, NAMES["en"])
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Good Days//Home Assistant//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
        f"REFRESH-INTERVAL;VALUE=DURATION:{REFRESH}",
        f"X-PUBLISHED-TTL:{REFRESH}",
    ]
    for event in events:
        lines += _event_lines(event, lang, stamp)
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


async def async_feed(runtime: GoodDaysRuntime) -> str:
    """The feed body, rebuilt only when the day, the dates or the settings change."""
    now = dt_util.now()
    key = (now.date(), runtime.family_version, bool(runtime.store.ics.get("holidays")), runtime.language)
    if runtime.ics_cache and runtime.ics_cache[0] == key:
        return runtime.ics_cache[1]
    body = await _async_build(runtime, now)
    runtime.ics_cache = (key, body)
    return body


async def _async_build(runtime: GoodDaysRuntime, now: dt.datetime) -> str:
    start, end = now - dt.timedelta(days=PAST_DAYS), now + dt.timedelta(days=FUTURE_DAYS)
    events: list = list(await runtime.async_family_between(start, end))
    if runtime.store.ics.get("holidays"):
        holidays = await runtime.async_events_between(start, end)
        events += [e for e in holidays if e.category in runtime.categories]
    events.sort(key=lambda e: (e.start, e.uid))
    return build_ics(events, runtime.language, now)


class GoodDaysIcsView(HomeAssistantView):
    """Unauthenticated (calendar apps can't log in); the per-entry secret token is the key."""

    url = "/api/good_days/ics/{entry_id}/{token}.ics"
    name = "api:good_days:ics"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(self, request: web.Request, entry_id: str, token: str) -> web.Response:
        entry = self.hass.config_entries.async_get_entry(entry_id)
        runtime = getattr(entry, "runtime_data", None) if entry and entry.domain == DOMAIN else None
        expected = runtime.store.ics.get("token") if runtime is not None else None
        # Same answer for "no such entry", "sharing off" and "wrong token".
        if not expected or not hmac.compare_digest(expected.encode(), token.encode()):
            return web.Response(status=HTTPStatus.NOT_FOUND)
        body = await async_feed(runtime)
        return web.Response(
            body=body.encode("utf-8"),
            content_type="text/calendar",
            charset="utf-8",
            headers={"Cache-Control": "private, max-age=3600"},
        )
