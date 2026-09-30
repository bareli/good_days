"""#13 (PERF-002): good_days/dates/list reads the cached occurrences instead of recomputing each record."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from custom_components.good_days import family
from custom_components.good_days.websocket import _date_view

from .test_issue_12 import _seed
from .test_v05 import _setup, _ws


async def test_issue_13_dates_list_does_not_recompute_per_record(
    hass: HomeAssistant, israel, freezer, hass_ws_client
) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    runtime = entry.runtime_data
    await _seed(runtime, 50)
    # A date beyond the cached window (lookahead 30 days) still gets its next occurrence.
    now = dt_util.now()
    expected = {r["id"]: _date_view(runtime, r, "en", now) for r in runtime.store.dates}

    original = family.compute_family
    calls = []

    def counting(*args, **kwargs):
        calls.append(len(args[0]))
        return original(*args, **kwargs)

    with patch("custom_components.good_days.family.compute_family", counting):
        result = await _ws(ws, type="good_days/dates/list", language="en")
    assert len(result["dates"]) == 50
    assert {d["id"]: d for d in result["dates"]} == expected
    assert calls == []  # every record's next occurrence is in the cached 400-day window


async def test_issue_13_falls_back_outside_the_window(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    freezer.move_to("2026-10-08 07:00:00+00:00")
    from .conftest import make_entry, setup_entry

    entry = make_entry(hass, lookahead_days=30)
    runtime = await setup_entry(hass, entry)
    await _seed(runtime, 20)
    now = dt_util.now()
    expected = {r["id"]: _date_view(runtime, r, "he", now) for r in runtime.store.dates}
    result = await _ws(client, type="good_days/dates/list", language="he")
    assert {d["id"]: d for d in result["dates"]} == expected
    assert all(d["next"] for d in result["dates"])
