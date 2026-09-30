"""v0.5: Shabbat Home timers."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.good_days.engine import EngineSettings, compute
from custom_components.good_days.timers import conflicts, expand, period_kinds, validate_rule

from .conftest import make_entry, setup_entry

D = dt.date
ISRAEL = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0)
TZ = "Asia/Jerusalem"


def periods(start: dt.date, end: dt.date):
    return [e for e in compute(ISRAEL, start, end) if e.period]


def rule(rule_id="r", **kw):
    base = {"id": rule_id, "name": rule_id, "targets": ["switch.plate"], "action": "on", "anchor": "candle_lighting",
            "offset_min": 0, "applies_to": ["shabbat", "yom_tov", "yom_kippur"], "profile": "default", "enabled": True}
    return {**base, **kw}


def local(action) -> str:
    return action.when.astimezone(dt_util.get_time_zone(TZ)).strftime("%a %d %H:%M")


# Pure expansion -----------------------------------------------------------------

def test_hot_plate_around_shabbat():
    shabbat = periods(D(2026, 10, 5), D(2026, 10, 11))  # Bereshit: 17:34 - 18:49
    plan = expand(
        [rule("on", offset_min=-20), rule("off", action="off", anchor="havdalah", offset_min=30)],
        shabbat, TZ, "default",
    )
    assert [(p.rule_id, local(p)) for p in plan] == [("on", "Fri 09 17:14"), ("off", "Sat 10 19:19")]
    assert all(p.outside for p in plan)  # before candle lighting / after havdalah


def test_clock_times_belong_to_the_right_night_and_day():
    shabbat = periods(D(2026, 10, 5), D(2026, 10, 11))
    plan = expand(
        [rule("night", anchor="clock", time="23:00"), rule("morning", anchor="clock", time="07:00"),
         rule("noon", anchor="clock", time="13:00"), rule("late", anchor="clock", time="00:30"),
         rule("erev", anchor="clock", time="14:00", days="erev")],
        shabbat, TZ, "default",
    )
    got = {p.rule_id: local(p) for p in plan}
    assert got == {"night": "Fri 09 23:00", "morning": "Sat 10 07:00", "noon": "Sat 10 13:00",
                   "late": "Sat 10 00:30", "erev": "Fri 09 14:00"}


def test_three_day_rosh_hashana_and_shabbat():
    (rh,) = [p for p in periods(D(2026, 9, 8), D(2026, 9, 15)) if p.category == "yom_tov"]
    assert period_kinds(rh) == {"yom_tov", "shabbat"}
    plan = expand(
        [rule("night", anchor="clock", time="23:00"), rule("morning", anchor="clock", time="07:00"),
         rule("first", anchor="clock", time="07:00", days="first"), rule("last", anchor="clock", time="07:00", days="last")],
        [rh], TZ, "default",
    )
    got = {}
    for p in plan:
        got.setdefault(p.rule_id, []).append(local(p))
    assert got["night"] == ["Fri 11 23:00", "Sat 12 23:00"]
    assert got["morning"] == ["Sat 12 07:00", "Sun 13 07:00"]
    assert got["first"] == ["Sat 12 07:00"] and got["last"] == ["Sun 13 07:00"]


def test_yom_kippur_only_rules_that_apply():
    (yk,) = [p for p in periods(D(2026, 9, 18), D(2026, 9, 22)) if "yom_kippur" in p.keys]
    assert period_kinds(yk) == {"yom_kippur"}
    plan = expand(
        [rule("plate", applies_to=["shabbat", "yom_tov"]), rule("lights", applies_to=["shabbat", "yom_tov", "yom_kippur"])],
        [yk], TZ, "default",
    )
    assert [p.rule_id for p in plan] == ["lights"]


def test_profiles_disabled_and_conflicts():
    shabbat = periods(D(2026, 10, 5), D(2026, 10, 11))
    rules = [rule("a"), rule("b", action="off"), rule("c", profile="guests"), rule("d", enabled=False)]
    plan = expand(rules, shabbat, TZ, "default")
    assert [p.rule_id for p in plan] == ["a", "b"]
    assert conflicts(plan) == [{"target": "switch.plate", "when": plan[0].when.isoformat(), "rules": ["a", "b"]}]
    assert [p.rule_id for p in expand(rules, shabbat, TZ, "guests")] == ["c"]


def test_validate_rule():
    ok, errors = validate_rule(rule(time="ignored"))
    assert errors == {} and ok["time"] is None and ok["days"] == "each"
    _, errors = validate_rule(rule(anchor="clock", time="25:00"))
    assert errors == {"time": "invalid_time"}
    _, errors = validate_rule(rule(offset_min=800, targets=["sensor.x"], applies_to=[], action="toggle"))
    assert errors == {"offset_min": "invalid_offset", "targets": "invalid_targets",
                      "applies_to": "invalid_applies_to", "action": "invalid_action"}
    _, errors = validate_rule(rule(), known_entities={"switch.other"})
    assert errors == {"targets": "unknown_targets"}
    _, errors = validate_rule(rule(profile="nope"))
    assert errors == {"profile": "invalid_profile"}


# Live ---------------------------------------------------------------------------

NOW = "2026-10-08 07:00:00+00:00"  # Thursday; Shabbat Bereshit Fri 17:34 - Sat 18:49


async def _at(hass: HomeAssistant, freezer, when: str) -> None:
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)


async def _setup(hass: HomeAssistant, freezer, hass_ws_client, when: str = NOW):
    client = await hass_ws_client(hass)  # before the clock jumps (token expiry)
    freezer.move_to(when)
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(
        hass, "input_boolean", {"input_boolean": {"plate": {"initial": False}, "guests": {"initial": False}}}
    )
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    return entry, client


async def _ws(client, **msg):
    await client.send_json_auto_id(msg)
    reply = await client.receive_json()
    assert reply["success"], reply
    return reply["result"]


def _state(hass, entity="input_boolean.plate"):
    return hass.states.get(entity).state


async def test_rule_fires_once_and_does_not_fight_manual_change(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    result = await _ws(ws, type="good_days/timers/save", name="Plate", targets=["input_boolean.plate"],
                       action="on", anchor="candle_lighting", offset_min=-20, applies_to=["shabbat", "yom_tov"])
    assert result["errors"] == {}
    view = await _ws(ws, type="good_days/timers/get", language="en")
    (action,) = view["preview"][0]["actions"]
    assert action["when"] == "2026-10-09T17:14:00+03:00" and action["outside"] is True
    assert view["next_action"]["rule_name"] == "Plate"
    assert dt_util.parse_datetime(hass.states.get("sensor.good_days_next_timer_action").state) == dt_util.parse_datetime(action["when"])

    await _at(hass, freezer, "2026-10-09 14:13:00+00:00")
    assert _state(hass) == "off"
    await _at(hass, freezer, "2026-10-09 14:14:00+00:00")
    assert _state(hass) == "on"
    await hass.services.async_call("input_boolean", "turn_off", {"entity_id": "input_boolean.plate"}, blocking=True)
    await _at(hass, freezer, "2026-10-09 14:20:00+00:00")
    assert _state(hass) == "off"  # fired once, never re-asserted
    history = entry.runtime_data.timers.store.history
    assert [h["status"] for h in history] == ["done"]


async def test_master_off_skip_and_conditions(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    await _ws(ws, type="good_days/timers/save", name="Plate", targets=["input_boolean.plate"], action="on",
              anchor="candle_lighting", offset_min=0, applies_to=["shabbat"],
              conditions=[{"condition": "state", "entity_id": "input_boolean.guests", "state": "on"}])
    await _at(hass, freezer, "2026-10-09 14:34:30+00:00")  # candle lighting, guests off
    assert _state(hass) == "off"
    assert entry.runtime_data.timers.store.history[-1]["reason"] == "Conditions not met"

    # After havdalah the "next" is Noach (16 Oct): skip it, then master off for the one after.
    await _at(hass, freezer, "2026-10-10 16:00:00+00:00")
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.good_days_skip_next_shabbat_or_chag"}, blocking=True)
    await hass.services.async_call("input_boolean", "turn_on", {"entity_id": "input_boolean.guests"}, blocking=True)
    await _at(hass, freezer, "2026-10-16 14:26:30+00:00")  # 17:26 candle lighting
    assert _state(hass) == "off"
    assert entry.runtime_data.timers.store.history[-1]["reason"] == "This Shabbat / Chag is skipped"
    assert hass.states.get("switch.good_days_skip_next_shabbat_or_chag").state == "on"  # still this Shabbat
    await _at(hass, freezer, "2026-10-17 16:00:00+00:00")  # after havdalah
    assert hass.states.get("switch.good_days_skip_next_shabbat_or_chag").state == "off"  # resets by itself

    await hass.services.async_call("switch", "turn_off", {"entity_id": "switch.good_days_shabbat_timers"}, blocking=True)
    assert hass.states.get("sensor.good_days_next_timer_action").state == "unknown"
    await _at(hass, freezer, "2026-10-23 14:18:30+00:00")  # 17:18 candle lighting
    assert _state(hass) == "off"
    await hass.services.async_call("switch", "turn_on", {"entity_id": "switch.good_days_shabbat_timers"}, blocking=True)
    await _at(hass, freezer, "2026-10-30 14:11:30+00:00")  # 16:11 after DST
    assert _state(hass) == "on"


async def test_restart_grace_and_missed(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    for name, offset in (("Soon", -20), ("Earlier", -60)):
        await _ws(ws, type="good_days/timers/save", name=name, targets=["input_boolean.plate"], action="on",
                  anchor="candle_lighting", offset_min=offset, applies_to=["shabbat"])
    assert await hass.config_entries.async_unload(entry.entry_id)
    # Home Assistant "down" from before 16:34 until 17:20: Earlier (16:34) missed, Soon (17:14) within grace.
    freezer.move_to("2026-10-09 14:20:00+00:00")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert _state(hass) == "on"
    statuses = {h["rule_name"]: h["status"] for h in entry.runtime_data.timers.store.history}
    assert statuses == {"Earlier": "missed", "Soon": "late"}


async def test_profiles_presets_duplicate_run_and_admin(
    hass: HomeAssistant, israel, freezer, hass_ws_client, hass_read_only_access_token
) -> None:
    reader = await hass_ws_client(hass, hass_read_only_access_token)  # before the clock jumps
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    created = await _ws(ws, type="good_days/timers/preset", preset="hot_plate", name="פלטה",
                        targets=["input_boolean.plate"], language="he")
    assert [r["name"] for r in created["rules"]] == ["פלטה (הדלקה)", "פלטה (כיבוי)"]
    view = await _ws(ws, type="good_days/timers/settings", add_profile="Guests", copy_from="default")
    assert view["profiles"] == ["default", "Guests"] and len(view["rules"]) == 4
    await hass.services.async_call("select", "select_option", {"entity_id": "select.good_days_timer_profile", "option": "Guests"}, blocking=True)
    assert (await _ws(ws, type="good_days/timers/get"))["active_profile"] == "Guests"

    dup = await _ws(ws, type="good_days/timers/duplicate", rule_id=created["rules"][0]["id"])
    assert dup["rule"]["name"] == "פלטה (הדלקה) (2)"
    assert (await _ws(ws, type="good_days/timers/run", rule_id=dup["rule"]["id"]))["errors"] == {}
    assert _state(hass) == "on"

    bad = await _ws(ws, type="good_days/timers/save", name="Scene", targets=["scene.dinner"], action="off",
                    anchor="candle_lighting", offset_min=0, applies_to=["shabbat"])
    assert bad["errors"]["targets"] in ("scene_off", "unknown_targets")
    bad = await _ws(ws, type="good_days/timers/save", name="X", targets=["input_boolean.plate"], action="on",
                    anchor="candle_lighting", offset_min=0, applies_to=["shabbat"], conditions=[{"condition": "nope"}])
    assert bad["errors"] == {"conditions": "invalid_conditions"}

    view = await _ws(ws, type="good_days/timers/settings", remove_profile="Guests")
    assert view["profiles"] == ["default"] and view["active_profile"] == "default"

    await reader.send_json_auto_id({"type": "good_days/timers/get"})
    assert (await reader.receive_json())["success"] is True
    await reader.send_json_auto_id({"type": "good_days/timers/settings", "enabled": False})
    msg = await reader.receive_json()
    assert msg["success"] is False and msg["error"]["code"] == "unauthorized"
