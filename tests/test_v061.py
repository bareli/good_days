"""v0.6.1: family notes leave Home Assistant through the calendar link only on opt-in."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant

from custom_components.good_days.const import DOMAIN
from custom_components.good_days.engine import EngineSettings
from custom_components.good_days.family import compute_family
from custom_components.good_days.ics import build_ics

from .conftest import make_entry, setup_entry

ISRAEL = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0)
NOW = "2026-10-07 07:00:00+00:00"
SECRET = "Allergic to penicillin"


def test_build_ics_leaves_notes_out_unless_asked():
    events = compute_family(
        [{"id": "x", "name": "Noa", "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan", "notes": SECRET}],
        ISRAEL, dt.date(2026, 10, 1), dt.date(2026, 10, 31),
    )
    now = dt.datetime(2026, 10, 7, 7, tzinfo=dt.UTC)
    assert SECRET not in build_ics(events, "en", now)
    assert SECRET in build_ics(events, "en", now, include_notes=True).replace("\r\n ", "")
    # The Hebrew date stays in the description either way.
    assert "Marcheshvan 5787" in build_ics(events, "en", now)


async def test_feed_notes_option(hass: HomeAssistant, israel, freezer, hass_ws_client, hass_client_no_auth) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    await hass.services.async_call(
        DOMAIN, "add_date",
        {"name": "Noa", "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan", "notes": SECRET},
        blocking=True, return_response=True,
    )
    client = await hass_client_no_auth()

    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True, "holidays": False})
    state = (await ws.receive_json())["result"]
    assert state["notes"] is False
    body = await (await client.get(state["path"])).text()
    # Names are wrapped in bidi isolates since v0.6.0 (#32).
    assert "SUMMARY:\u2068Noa\u2069's birthday" in body and SECRET not in body.replace("\r\n ", "")

    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True, "holidays": False, "notes": True})
    state = (await ws.receive_json())["result"]
    assert state["notes"] is True
    body = await (await client.get(state["path"])).text()  # cache keyed on the option
    assert SECRET in body.replace("\r\n ", "")

    # Stored with the other feed settings, survives a reload.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await ws.send_json_auto_id({"type": "good_days/ics/get"})
    assert (await ws.receive_json())["result"]["notes"] is True
