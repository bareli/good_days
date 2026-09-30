"""v0.3: reminders, Assist intents, blueprint."""
from __future__ import annotations

import os

from homeassistant import config_entries
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import intent
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml_dict
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.good_days.const import DOMAIN

from .conftest import make_entry, setup_entry

NOW = "2026-10-07 07:00:00+00:00"  # Wed 10:00 Israel; Shabbat Bereshit Fri 9th 17:34 - Sat 10th 18:49
PHONE = "mobile_app_phone"
# 3 Cheshvan 5787 = Wed 2026-10-14 (weekday); 30 Tishrei = Sun 2026-10-11 (day after Shabbat).
WEEKDAY_BIRTHDAY = {"name": "Noa", "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan", "original_year": 5780}
SUNDAY_BIRTHDAY = {"name": "Dan", "kind": "birthday", "hebrew_day": 30, "hebrew_month": "tishrei"}
YAHRZEIT = {"name": "Saba", "kind": "yahrzeit", "hebrew_day": 3, "hebrew_month": "marcheshvan", "reminder_days": [0]}
BLUEPRINT = os.path.join(
    os.path.dirname(__file__), "..", "blueprints", "automation", "good_days", "candle_lighting_light.yaml"
)


async def _setup(hass: HomeAssistant, freezer, **options):
    freezer.move_to(NOW)
    calls = async_mock_service(hass, "notify", PHONE)
    events = async_capture_events(hass, "good_days_reminder")
    entry = make_entry(hass, notify_targets=[PHONE], reminder_time="09:00", **options)
    await setup_entry(hass, entry)
    return entry, calls, events


async def _add(hass: HomeAssistant, data: dict) -> dict:
    resp = await hass.services.async_call(DOMAIN, "add_date", data, blocking=True, return_response=True)
    await hass.async_block_till_done()
    return resp["date"]


async def _at(hass: HomeAssistant, freezer, when: str) -> None:
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_reminder_day_before_once_with_buttons(hass: HomeAssistant, israel, freezer) -> None:
    entry, calls, events = await _setup(hass, freezer)
    date = await _add(hass, WEEKDAY_BIRTHDAY)

    await _at(hass, freezer, "2026-10-13 05:59:00+00:00")  # 08:59 local, not yet
    assert calls == []
    await _at(hass, freezer, "2026-10-13 06:00:30+00:00")  # 09:00 the day before
    assert len(calls) == 1
    assert calls[0].data["message"] == "Tomorrow: Noa's birthday (7)"
    actions = calls[0].data["data"]["actions"]
    assert actions[0]["action"] == f"GOODDAYS:ack:{entry.entry_id}:{date['id']}:2026-10-14"
    assert actions[1]["action"].startswith("GOODDAYS:snooze:")
    assert events[0].data["name"] == "Noa" and events[0].data["day"] == "2026-10-14"

    await _at(hass, freezer, "2026-10-13 06:05:00+00:00")
    assert len(calls) == 1  # sent once


async def test_no_burst_of_old_reminders_on_install(hass: HomeAssistant, israel, freezer) -> None:
    _, calls, _ = await _setup(hass, freezer)
    # Reminder for the 2026-10-08 occurrence (4 Tishrei ... ) would have been due before setup.
    await _add(hass, {**WEEKDAY_BIRTHDAY, "hebrew_day": 26, "hebrew_month": "tishrei", "reminder_days": [1]})
    await _at(hass, freezer, "2026-10-07 07:02:00+00:00")
    assert calls == []


async def test_reminder_held_during_shabbat(hass: HomeAssistant, israel, freezer) -> None:
    _, calls, _ = await _setup(hass, freezer)
    await _add(hass, SUNDAY_BIRTHDAY)
    await _at(hass, freezer, "2026-10-10 06:00:30+00:00")  # Shabbat 09:00
    assert calls == []
    await _at(hass, freezer, "2026-10-10 16:00:00+00:00")  # 19:00, after havdalah 18:49
    assert [c.data["message"] for c in calls] == ["Tomorrow: Dan's birthday"]


async def test_reminder_on_shabbat_when_not_quiet(hass: HomeAssistant, israel, freezer) -> None:
    _, calls, _ = await _setup(hass, freezer, quiet_on_shabbat=False)
    await _add(hass, SUNDAY_BIRTHDAY)
    await _at(hass, freezer, "2026-10-10 06:00:30+00:00")
    assert len(calls) == 1


async def test_ack_stops_and_snooze_repeats(hass: HomeAssistant, israel, freezer) -> None:
    entry, calls, _ = await _setup(hass, freezer)
    date = await _add(hass, {**WEEKDAY_BIRTHDAY, "reminder_days": [0, 1]})
    await _at(hass, freezer, "2026-10-13 06:00:30+00:00")
    assert len(calls) == 1

    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": f"GOODDAYS:snooze:{entry.entry_id}:{date['id']}:2026-10-14"},
    )
    await hass.async_block_till_done()
    # Same-day reminder (days 0) fires at 09:00; the snooze (due 09:00:30 + 1 day) is merged into it.
    await _at(hass, freezer, "2026-10-14 06:01:00+00:00")
    assert [c.data["message"] for c in calls][1:] == ["Today: Noa's birthday (7)"]

    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": f"GOODDAYS:ack:{entry.entry_id}:{date['id']}:2026-10-14"},
    )
    await hass.async_block_till_done()
    assert f"{date['id']}:2026-10-14" in entry.runtime_data.store.reminders["acked"]
    await _at(hass, freezer, "2026-10-14 10:00:00+00:00")
    assert len(calls) == 2


async def test_snooze_fires_next_day(hass: HomeAssistant, israel, freezer) -> None:
    entry, calls, _ = await _setup(hass, freezer)
    date = await _add(hass, {**WEEKDAY_BIRTHDAY, "reminder_days": [3]})
    await _at(hass, freezer, "2026-10-11 06:00:30+00:00")  # Sunday, 3 days before
    assert [c.data["message"] for c in calls] == ["In 3 days: Noa's birthday (7)"]
    hass.bus.async_fire(
        "mobile_app_notification_action",
        {"action": f"GOODDAYS:snooze:{entry.entry_id}:{date['id']}:2026-10-14"},
    )
    await hass.async_block_till_done()
    await _at(hass, freezer, "2026-10-12 06:00:00+00:00")
    assert len(calls) == 1
    await _at(hass, freezer, "2026-10-12 06:02:00+00:00")
    assert [c.data["message"] for c in calls][1:] == ["In 2 days: Noa's birthday (7)"]


async def test_yahrzeit_evening_reminder_with_candle_time(hass: HomeAssistant, israel, freezer) -> None:
    _, calls, _ = await _setup(hass, freezer, language="he")
    await _add(hass, YAHRZEIT)
    await _at(hass, freezer, "2026-10-13 13:00:00+00:00")  # 16:00, before sunset - 60 min
    assert calls == []
    await _at(hass, freezer, "2026-10-13 14:15:00+00:00")  # 17:15, after sunset (18:09 / 18:12) - 60 min
    assert len(calls) == 1
    message = calls[0].data["message"]
    assert message.startswith("מחר: יום השנה: Saba. הדליקו נר לפני 18:")


async def test_options_validate_reminders(hass: HomeAssistant, israel) -> None:
    async_mock_service(hass, "notify", PHONE)
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    base = {
        "location": {"latitude": 31.778, "longitude": 35.235}, "diaspora": False,
        "candle_lighting_minutes": 40, "havdalah_minutes": 0, "language": "auto",
        "categories": ["shabbat"], "lookahead_days": 400, "quiet_on_shabbat": True,
    }
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**base, "notify_targets": ["mobile_app_nope"], "reminder_time": "09:00"}
    )
    assert result["errors"] == {"notify_targets": "invalid_notify"}
    # The time selector rejects bad times in the UI; the server-side check covers services / YAML.
    from custom_components.good_days.config_flow import validate

    _, errors = validate({**base, "reminder_time": "25:00"}, with_options=True, notify_services=set())
    assert errors == {"reminder_time": "invalid_time"}
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {**base, "notify_targets": [f"notify.{PHONE}"], "reminder_time": "08:30:00"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["notify_targets"] == [PHONE]
    assert entry.options["reminder_time"] == "08:30"


async def _speech(hass: HomeAssistant, intent_type: str, language: str) -> str:
    response = await intent.async_handle(hass, "test", intent_type, {}, language=language)
    return response.speech["plain"]["speech"]


async def test_intents(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))
    await _add(hass, WEEKDAY_BIRTHDAY)

    assert await _speech(hass, "GoodDaysShabbatTimes", "en") == (
        "Candle lighting on Friday at 17:34, havdalah on Saturday at 18:49. Parashat Bereshit."
    )
    assert await _speech(hass, "GoodDaysShabbatTimes", "he") == (
        "הדלקת נרות ביום שישי ב-17:34, הבדלה בשבת ב-18:49. פרשת בראשית."
    )
    assert await _speech(hass, "GoodDaysNextHoliday", "en") == "Chanukah, in 59 days, on Saturday."
    assert await _speech(hass, "GoodDaysUpcoming", "en") == (
        "Coming up: Shabbat Parashat Bereshit on Friday evening and Noa's birthday (7) on Wednesday."
    )
    assert await _speech(hass, "GoodDaysUpcoming", "he") == (
        "בשבוע הקרוב: שבת פרשת בראשית ביום שישי בערב ויום הולדת 7 לNoa ביום רביעי."
    )

    freezer.move_to("2026-10-10 09:00:00+00:00")
    assert await _speech(hass, "GoodDaysShabbatTimes", "he") == "שבת פרשת בראשית יוצאת ב-18:49."


async def test_blueprint_turns_light_on_before_candle_lighting(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2026-10-09 14:00:00+00:00")  # Friday 17:00
    await setup_entry(hass, make_entry(hass))
    await async_setup_component(hass, "homeassistant", {})  # homeassistant.turn_on
    await async_setup_component(hass, "input_boolean", {"input_boolean": {"porch": {"initial": False}}})

    blueprint = Blueprint(
        load_yaml_dict(BLUEPRINT), expected_domain="automation", schema=AUTOMATION_BLUEPRINT_SCHEMA
    )
    inputs = BlueprintInputs(
        blueprint,
        {"use_blueprint": {"path": "good_days/candle_lighting_light.yaml", "input": {
            "lights": {"entity_id": "input_boolean.porch"}, "minutes_before": 10,
            "turn_off_after": True, "minutes_after": 0,
        }}},
    )
    config = {**inputs.async_substitute(), "id": "porch", "alias": "porch"}
    assert await async_setup_component(hass, "automation", {"automation": [config]})
    await hass.async_block_till_done()

    await _at(hass, freezer, "2026-10-09 14:20:00+00:00")  # 17:20, candle lighting 17:34
    assert hass.states.get("input_boolean.porch").state == "off"
    await _at(hass, freezer, "2026-10-09 14:24:00+00:00")  # 17:24 = 10 min before 17:34
    assert hass.states.get("input_boolean.porch").state == "on"

    # Calendar end trigger at havdalah (18:49 Saturday). A non-zero delay is plain HA script
    # behaviour and would block async_block_till_done under a frozen clock.
    for when in ("2026-10-10 09:00:00+00:00", "2026-10-10 15:30:00+00:00", "2026-10-10 15:48:00+00:00"):
        await _at(hass, freezer, when)
    assert hass.states.get("input_boolean.porch").state == "on"
    await _at(hass, freezer, "2026-10-10 15:49:30+00:00")
    assert hass.states.get("input_boolean.porch").state == "off"
