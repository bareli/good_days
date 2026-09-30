"""#9 (SEC-004): timer targets are on/off devices and scenes only; a target nothing can switch is "failed", not "done"."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.good_days.timers import validate_rule

from .test_v05 import _at, _setup, _state, _ws, rule


@pytest.mark.parametrize("target", ["script.bedtime", "automation.porch", "lock.front_door", "cover.blinds", "valve.water"])
def test_issue_9_refused_domains(target) -> None:
    assert validate_rule(rule(targets=[target]))[1] == {"targets": "invalid_targets"}


@pytest.mark.parametrize(
    "target", ["switch.a", "light.a", "input_boolean.a", "fan.a", "climate.a", "water_heater.a", "media_player.a",
               "humidifier.a", "siren.a", "vacuum.a", "scene.a"]
)
def test_issue_9_allowed_domains(target) -> None:
    assert validate_rule(rule(targets=[target]))[1] == {}


async def test_issue_9_no_done_for_a_target_nothing_switches(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    hass.states.async_set("lock.front_door", "unlocked")
    store = entry.runtime_data.timers.store
    # A rule saved by an older version (stored data is never rewritten).
    store.rules.append(rule("old", name="Door", targets=["lock.front_door", "input_boolean.plate"],
                            applies_to=["shabbat"]))
    run = await _ws(ws, type="good_days/timers/run", rule_id="old")
    assert run["errors"] == {"base": "run_failed"} and "lock.front_door" in run["message"]
    assert _state(hass) == "on"  # the device that can be switched still is

    await hass.services.async_call("input_boolean", "turn_off", {"entity_id": "input_boolean.plate"}, blocking=True)
    await entry.runtime_data.timers.async_replan()
    await _at(hass, freezer, "2026-10-09 14:34:30+00:00")  # candle lighting
    (entry_,) = [h for h in store.history if h["rule_id"] == "old"]
    assert entry_["status"] == "failed" and "lock.front_door" in entry_["reason"]
