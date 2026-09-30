"""#12 (PERF-001): good_days/upcoming renders only the items it returns, with the same result as before."""
from __future__ import annotations

import datetime as dt
from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.good_days.const import HEBREW_MONTHS
from custom_components.good_days.runtime import GoodDaysRuntime

from .test_v05 import _setup, _ws

KINDS = ["birthday", "yahrzeit", "anniversary", "custom"]


async def _seed(runtime: GoodDaysRuntime, count: int) -> None:
    for i in range(count):
        month = HEBREW_MONTHS[i % len(HEBREW_MONTHS)]
        await runtime.store.async_add(
            {"name": f"Person {i}", "kind": KINDS[i % 4], "hebrew_day": 1 + (i * 7) % 29, "hebrew_month": month,
             "original_year": 5700 + i % 80}
        )
    await runtime.async_refresh_family()


def _reference(runtime: GoodDaysRuntime, events, family, lang: str, now: dt.datetime, limit: int, categories):
    """The v0.5.0 algorithm: render everything, sort, cut."""
    periods = [e for e in events if e.period]
    items = []
    for event in events:
        if event.category in categories and event.end > now:
            items.append({**runtime.render(event, lang, now), "_sort": event.start})
    for event in family:
        if event.end > now:
            item = runtime.render(event, lang, now)
            item["conflicts_shabbat"] = any(p.overlaps(event.start, event.end) for p in periods)
            items.append({**item, "_sort": event.start})
    items.sort(key=lambda i: (i["_sort"], i["source"] != "holidays", i["source"] != "family", i["title"]))
    return [{k: v for k, v in i.items() if k != "_sort"} for i in items[:limit]]


async def test_issue_12_upcoming_renders_at_most_limit(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    runtime = entry.runtime_data
    await _seed(runtime, 60)
    now = dt_util.now()
    categories = runtime.categories | {"family"}
    events = await runtime.async_events_between(now - dt.timedelta(days=1), now + dt.timedelta(days=400))
    family = await runtime.async_family_between(now - dt.timedelta(days=1), now + dt.timedelta(days=400))

    for limit in (10, 100):
        expected = _reference(runtime, events, family, "he", now, limit, categories)
        original = GoodDaysRuntime.render
        calls = []

        def counting(self, event, lang, when, _orig=original):
            calls.append(event.uid)
            return _orig(self, event, lang, when)

        with patch.object(GoodDaysRuntime, "render", counting):
            result = await _ws(ws, type="good_days/upcoming", days=400, limit=limit, language="he")
        assert len(result["items"]) == limit
        assert result["items"] == expected
        assert len(calls) <= limit + 1  # + the "current" banner
