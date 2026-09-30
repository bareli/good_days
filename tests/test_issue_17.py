"""#17 (BUG-005): every WS command the panel calls accepts the fields the panel sends (language, entry_id)."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .test_v05 import _setup, _state, _ws


async def test_issue_17_timers_commands_accept_language_like_the_panel(
    hass: HomeAssistant, israel, freezer, hass_ws_client
) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    base = {"language": "he", "entry_id": entry.entry_id}
    saved = await _ws(ws, type="good_days/timers/save", **base, name="כיבוי אור בסלון בלילה",
                      targets=["input_boolean.plate"], action="on", anchor="clock", offset_min=-20, time="23:00",
                      days="each", applies_to=["shabbat", "yom_tov"], profile="default", conditions=[], enabled=True)
    assert saved["errors"] == {}
    rule_id = saved["rule"]["id"]
    edited = await _ws(ws, type="good_days/timers/save", **base, rule_id=rule_id, name="Edited",
                       targets=["input_boolean.plate"], action="on", anchor="candle_lighting", offset_min=-20,
                       time="", days="each", applies_to=["shabbat"], profile="default", conditions=[], enabled=True)
    assert edited["errors"] == {} and edited["rule"]["name"] == "Edited"
    assert (await _ws(ws, type="good_days/timers/run", **base, rule_id=rule_id))["errors"] == {}
    assert _state(hass) == "on"
    dup = await _ws(ws, type="good_days/timers/duplicate", **base, rule_id=rule_id)
    assert dup["errors"] == {}
    assert (await _ws(ws, type="good_days/timers/remove", **base, rule_id=dup["rule"]["id"]))["errors"] == {}
    assert (await _ws(ws, type="good_days/timers/settings", **base, enabled=True))["errors"] == {}
    assert (await _ws(ws, type="good_days/timers/preset", **base, preset="urn", name="Urn",
                      targets=["input_boolean.plate"]))["errors"] == {}
    assert (await _ws(ws, type="good_days/timers/get", **base))["entry_id"] == entry.entry_id


async def test_issue_17_other_commands_tolerate_language(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    base = {"language": "en", "entry_id": entry.entry_id}
    ics = await _ws(ws, type="good_days/ics/get", **base)
    assert ics["enabled"] is False
    assert (await _ws(ws, type="good_days/ics/set", **base, enabled=False, holidays=False))["enabled"] is False
    added = await _ws(ws, type="good_days/dates/add", **base, name="Dan", kind="birthday", hebrew_day=1,
                      hebrew_month="tishrei")
    assert (await _ws(ws, type="good_days/dates/remove", **base, date_id=added["date"]["id"]))["errors"] == {}
    assert (await _ws(ws, type="good_days/dates/convert", language="en", date="2026-10-01"))["errors"] == {}
