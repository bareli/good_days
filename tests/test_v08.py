"""v0.8: yahrzeit candle blueprint."""
from __future__ import annotations

import datetime as dt
import os

from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml_dict
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.good_days.const import DOMAIN

from .conftest import make_entry, setup_entry

BLUEPRINT = os.path.join(
    os.path.dirname(__file__), "..", "blueprints", "automation", "good_days", "yahrzeit_candle.yaml"
)
# 3 Cheshvan 5787 = Wed 2026-10-14: the yahrzeit runs Tue 13th sunset to Wed 14th sunset.
YAHRZEIT = {"name": "Saba Moshe", "kind": "yahrzeit", "hebrew_day": 3, "hebrew_month": "marcheshvan"}
BIRTHDAY = {"name": "Noa", "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan"}


async def _at(hass: HomeAssistant, freezer, when: dt.datetime) -> None:
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)


def _automation(blueprint: Blueprint, auto_id: str, entity: str, **inputs) -> dict:
    bp_inputs = BlueprintInputs(
        blueprint,
        {"use_blueprint": {"path": "good_days/yahrzeit_candle.yaml",
                           "input": {"candle": {"entity_id": entity}, **inputs}}},
    )
    return {**bp_inputs.async_substitute(), "id": auto_id, "alias": auto_id}


async def test_blueprint_lights_yahrzeit_candle(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2026-10-13 06:00:00+00:00")
    await setup_entry(hass, make_entry(hass))
    for data in (YAHRZEIT, BIRTHDAY):
        await hass.services.async_call(DOMAIN, "add_date", data, blocking=True, return_response=True)
    await async_setup_component(hass, "homeassistant", {})
    await async_setup_component(hass, "input_boolean", {"input_boolean": {
        "saba": {"initial": False}, "noa": {"initial": False}, "every": {"initial": False},
    }})
    await hass.async_block_till_done()

    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": "calendar.good_days_family", "start_date_time": "2026-10-13T00:00:00+03:00",
         "end_date_time": "2026-10-15T00:00:00+03:00"},
        blocking=True, return_response=True,
    )
    timed = [e for e in resp["calendar.good_days_family"]["events"] if "T" in e["start"]]
    assert len(timed) == 1
    start = dt_util.parse_datetime(timed[0]["start"])
    end = dt_util.parse_datetime(timed[0]["end"])
    assert start.date() == dt.date(2026, 10, 13) and end.date() == dt.date(2026, 10, 14)

    blueprint = Blueprint(load_yaml_dict(BLUEPRINT), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA)
    automations = [
        # Part of the name, other case, 15 minutes early.
        _automation(blueprint, "saba", "input_boolean.saba", person="saba moshe", lead="-0:15:00"),
        # Birthdays are all-day: never lit.
        _automation(blueprint, "noa", "input_boolean.noa", person="Noa"),
        # Every yahrzeit, kept on after the end.
        _automation(blueprint, "every", "input_boolean.every", turn_off=False),
    ]
    assert await async_setup_component(hass, "automation", {"automation": automations})
    await hass.async_block_till_done()

    def state(name: str) -> str:
        return hass.states.get(f"input_boolean.{name}").state

    async def walk(first: dt.datetime, last: dt.datetime) -> None:
        # Minute by minute, as the clock really moves: the calendar trigger polls 15-minute windows.
        when = first
        while when <= last:
            await _at(hass, freezer, when)
            when += dt.timedelta(minutes=1)

    await walk(start - dt.timedelta(minutes=40), start - dt.timedelta(minutes=16))
    assert (state("saba"), state("every")) == ("off", "off")
    await walk(start - dt.timedelta(minutes=15), start - dt.timedelta(minutes=1))
    assert (state("saba"), state("every")) == ("on", "off")
    await walk(start, start + dt.timedelta(minutes=2))
    assert state("every") == "on"

    # Midnight: the birthday (all-day) starts and must not light Noa's candle.
    midnight = dt_util.parse_datetime("2026-10-14 00:00:00+03:00")
    await walk(midnight - dt.timedelta(minutes=20), midnight + dt.timedelta(minutes=2))
    assert state("noa") == "off"

    await walk(end - dt.timedelta(minutes=20), end - dt.timedelta(minutes=1))
    assert (state("saba"), state("every")) == ("on", "on")
    await walk(end, end + dt.timedelta(minutes=2))
    assert (state("saba"), state("every"), state("noa")) == ("off", "on", "off")

    await hass.services.async_call("automation", "turn_off", {"entity_id": "all"}, blocking=True)
    await hass.async_block_till_done()
