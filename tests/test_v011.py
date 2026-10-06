"""v0.11: fast times, fasting / next fast / Omer entities, fast timers, Omer reminder, Assist."""
from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import (
    async_capture_events,
    async_fire_time_changed,
    async_mock_service,
)

from custom_components.good_days import intents
from custom_components.good_days.config_flow import validate
from custom_components.good_days.engine import (
    EngineSettings,
    compute,
    make_location,
    omer_day,
    omer_switch,
    omer_text,
    _zmanim,
)
from custom_components.good_days.timers import PRESETS, expand, period_kinds

from .conftest import make_entry, setup_entry

TZ = ZoneInfo("Asia/Jerusalem")
JLM = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False)
PHONE = "mobile_app_phone"


def _fasts(settings: EngineSettings, start: dt.date, end: dt.date):
    return {e.keys[0]: e for e in compute(settings, start, end) if e.category == "fast"}


def _hm(value: dt.datetime) -> str:
    return value.astimezone(TZ).strftime("%Y-%m-%d %H:%M")


def _zman(day: dt.date, name: str, settings: EngineSettings = JLM) -> dt.datetime:
    return _zmanim(day, settings, make_location(settings)).zmanim[name].local


# Engine ------------------------------------------------------------------------------------


def test_fast_begins_match_hebcal_jerusalem():
    """Dawn (16.1°) and Tisha B'Av sunset, minute for minute as hebcal.com prints them."""
    fasts = _fasts(JLM, dt.date(2026, 9, 1), dt.date(2027, 9, 1))
    assert _hm(fasts["tzom_gedaliah"].start) == "2026-09-14 05:09"
    assert _hm(fasts["asara_btevet"].start) == "2026-12-20 05:16"
    assert _hm(fasts["taanit_esther"].start) == "2027-03-22 04:29"
    assert _hm(fasts["tzom_tammuz"].start) == "2027-07-22 04:24"
    assert _hm(fasts["tisha_bav"].start) == "2027-08-11 19:27"
    for event in fasts.values():
        assert not event.all_day and not event.period and event.is_fast


def test_fast_ends_tzeit_and_tisha_bav_havdalah():
    fasts = _fasts(JLM, dt.date(2026, 9, 1), dt.date(2027, 9, 1))
    gedaliah = fasts["tzom_gedaliah"]
    assert gedaliah.end == _zman(dt.date(2026, 9, 14), "tset_hakohavim_tsom")
    # Tisha B'Av always ends at havdalah (three stars with havdalah 0).
    assert fasts["tisha_bav"].end == _zman(dt.date(2027, 8, 12), "tset_hakohavim_shabbat")
    assert "Fast begins 05:09" in gedaliah.description("en")
    assert "סוף הצום" in gedaliah.description("he")


def test_fast_options():
    settings = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, havdalah=50, fast_start="alot_72", fast_end="havdalah")
    day = dt.date(2026, 9, 14)
    gedaliah = _fasts(settings, dt.date(2026, 9, 1), dt.date(2026, 9, 30))["tzom_gedaliah"]
    assert gedaliah.start == _zman(day, "netz_hachama", settings) - dt.timedelta(minutes=72)
    assert gedaliah.end == _zman(day, "shkia", settings) + dt.timedelta(minutes=50)
    ninety = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, fast_start="alot_90")
    assert _fasts(ninety, day, day)["tzom_gedaliah"].start == _zman(day, "netz_hachama") - dt.timedelta(minutes=90)


def test_postponed_tisha_bav_and_early_taanit_esther():
    events = compute(JLM, dt.date(2022, 8, 1), dt.date(2022, 8, 10))
    shabbat = next(e for e in events if e.period)
    tisha_bav = next(e for e in events if e.category == "fast")
    assert tisha_bav.uid == "fast-tisha_bav-2022-08-07"  # 9 Av on Shabbat: Sunday
    assert tisha_bav.start == shabbat.end  # begins at havdalah
    esther = _fasts(JLM, dt.date(2024, 3, 18), dt.date(2024, 3, 25))["taanit_esther"]
    assert esther.first_day == dt.date(2024, 3, 21)  # 13 Adar II on Shabbat: Thursday
    assert _hm(esther.start) == "2024-03-21 04:29"


def test_yom_kippur_is_a_fast_period():
    yk = next(e for e in compute(JLM, dt.date(2026, 9, 20), dt.date(2026, 9, 21)) if "yom_kippur" in e.keys)
    assert yk.period and yk.is_fast


def test_polar_fasts_stay_all_day():
    north = EngineSettings(78.22, 15.65, 0, "Arctic/Longyearbyen", False)
    fasts = _fasts(north, dt.date(2026, 6, 1), dt.date(2026, 8, 30))
    assert fasts and all(e.all_day for e in fasts.values())
    assert omer_switch(dt.date(2026, 5, 1), north) is None


def test_omer_days_and_text():
    assert omer_day(dt.date(2027, 4, 22)) == 0  # 15 Nisan 5787
    assert omer_day(dt.date(2027, 4, 23)) == 1
    assert omer_day(dt.date(2027, 6, 10)) == 49  # 5 Sivan
    assert omer_day(dt.date(2027, 6, 11)) == 0
    assert omer_text(23, "en") == "Today is the twenty-third day, which are three weeks and two days of the Omer"
    assert omer_text(1, "he").startswith("היום")
    assert omer_text(0, "en") == ""
    assert omer_switch(dt.date(2027, 4, 26), JLM) == _zman(dt.date(2027, 4, 26), "tset_hakohavim_tsom")


# Timers ------------------------------------------------------------------------------------


def _rule(**kw):
    return {"id": "r", "name": "R", "targets": ["switch.urn"], "action": "on", "anchor": "havdalah",
            "offset_min": -30, "applies_to": ["fast"], "profile": "default", "enabled": True, **kw}


def test_fast_timers():
    events = compute(JLM, dt.date(2026, 9, 10), dt.date(2026, 9, 25))
    gedaliah = next(e for e in events if e.category == "fast")
    yk = next(e for e in events if "yom_kippur" in e.keys)
    assert period_kinds(gedaliah) == {"fast"}
    planned = expand([_rule()], events, "Asia/Jerusalem", "default")
    assert [p.when for p in planned] == [gedaliah.end - dt.timedelta(minutes=30)]
    # A clock rule on a minor fast stays on the fast day (it begins at dawn, not the evening before).
    planned = expand([_rule(anchor="clock", time="12:00", days="each")], events, "Asia/Jerusalem", "default")
    assert [_hm(p.when) for p in planned] == ["2026-09-14 12:00"]
    # Shabbat-only rules never fire on a fast; break_fast covers fasts and Yom Kippur.
    planned = expand([_rule(applies_to=["shabbat"])], [gedaliah], "Asia/Jerusalem", "default")
    assert planned == []
    rules = [{**_rule(id=f"b{i}"), **part} for i, part in enumerate(PRESETS["break_fast"])]
    whens = {p.when for p in expand(rules, events, "Asia/Jerusalem", "default")}
    assert gedaliah.end + dt.timedelta(minutes=60) in whens and yk.end - dt.timedelta(minutes=30) in whens


def test_options_validation():
    base = {"location": {"latitude": 31.7, "longitude": 35.2}, "candle_lighting_minutes": 40, "havdalah_minutes": 0,
            "categories": ["shabbat"], "lookahead_days": 400, "reminder_time": "09:00"}
    clean, errors = validate({**base, "fast_start": "alot_72", "fast_end": "havdalah", "omer_reminder": True,
                              "omer_reminder_offset": 15}, with_options=True)
    assert errors == {}
    assert clean["fast_start"] == "alot_72" and clean["omer_reminder"] and clean["omer_reminder_offset"] == 15
    _, errors = validate({**base, "fast_start": "noon", "fast_end": "x", "omer_reminder_offset": 999}, with_options=True)
    assert errors == {"fast_start": "invalid_choice", "fast_end": "invalid_choice",
                      "omer_reminder_offset": "invalid_omer_offset"}


# Integration -------------------------------------------------------------------------------


async def _at(hass: HomeAssistant, freezer, when: dt.datetime) -> None:
    freezer.move_to(when)
    async_fire_time_changed(hass, dt_util.utcnow())
    await hass.async_block_till_done(wait_background_tasks=True)


async def test_fast_entities(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2026-09-13 09:00:00+00:00")
    runtime = await setup_entry(hass, make_entry(hass))
    gedaliah = runtime.next_fast(dt_util.now())
    assert gedaliah.uid == "fast-tzom_gedaliah-2026-09-14"
    state = hass.states.get("sensor.good_days_next_fast")
    assert dt_util.parse_datetime(state.state) == gedaliah.start
    assert state.attributes["end"] == gedaliah.end.isoformat() and not state.attributes["in_effect"]
    assert hass.states.get("binary_sensor.good_days_fasting").state == "off"

    await _at(hass, freezer, gedaliah.start + dt.timedelta(minutes=1))
    fasting = hass.states.get("binary_sensor.good_days_fasting")
    assert fasting.state == "on" and fasting.attributes["end"] == gedaliah.end.isoformat()
    await _at(hass, freezer, gedaliah.end + dt.timedelta(minutes=1))
    assert hass.states.get("binary_sensor.good_days_fasting").state == "off"
    # Next: Yom Kippur, from candle lighting.
    assert "yom_kippur" in runtime.next_fast(dt_util.now()).keys


async def test_omer_sensor_moves_at_tzeit(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2027-04-26 09:00:00+00:00")  # Monday 19 Nisan: day 4 (counted Sunday night)
    runtime = await setup_entry(hass, make_entry(hass))
    state = hass.states.get("sensor.good_days_omer")
    assert state.state == "4" and state.attributes["weeks"] == 0 and state.attributes["counted"] is False
    tzeit = omer_switch(dt.date(2027, 4, 26), runtime.settings)
    assert state.attributes["next_count"] == tzeit.isoformat()
    await _at(hass, freezer, tzeit + dt.timedelta(minutes=1))
    assert hass.states.get("sensor.good_days_omer").state == "5"
    await _at(hass, freezer, dt.datetime(2027, 6, 11, 12, tzinfo=TZ))  # 6 Sivan: over
    state = hass.states.get("sensor.good_days_omer")
    assert state.state == "unknown" and state.attributes["next_count"] is None
    # 15 Nisan 5788 by day: no count yet, the first one is tonight.
    await _at(hass, freezer, dt.datetime(2028, 4, 11, 12, tzinfo=TZ))
    state = hass.states.get("sensor.good_days_omer")
    assert state.state == "unknown" and state.attributes["next_count"] is not None


async def test_omer_reminder_quiet_on_shabbat_and_yom_tov(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2027-04-22 06:00:00+00:00")  # Thursday, 1st day of Pesach
    calls = async_mock_service(hass, "notify", PHONE)
    events = async_capture_events(hass, "good_days_omer")
    entry = make_entry(hass, notify_targets=[PHONE], omer_reminder=True, omer_reminder_offset=10)
    runtime = await setup_entry(hass, entry)
    reminders = runtime.reminders
    now = dt_util.now()
    pesach = runtime.in_effect(now)
    thu, fri, sat, mon = (dt.date(2027, 4, d) for d in (22, 23, 24, 26))
    shabbat = runtime.period_at(dt.datetime(2027, 4, 24, 12, tzinfo=TZ))

    # Night 1 is motzei Yom Tov: after havdalah. Night 2 is Shabbat: an hour before candle lighting.
    assert reminders.omer_due(thu) == pesach.end
    assert reminders.omer_due(fri) == shabbat.start - dt.timedelta(hours=1)
    assert reminders.omer_due(sat) == shabbat.end
    assert reminders.omer_due(mon) == omer_switch(mon, runtime.settings) + dt.timedelta(minutes=10)

    await _at(hass, freezer, pesach.end - dt.timedelta(minutes=1))
    assert calls == []
    await _at(hass, freezer, pesach.end + dt.timedelta(seconds=30))
    assert len(calls) == 1
    message = calls[0].data["message"]
    assert message.startswith("Tonight: day 1 of the Omer") and "first day" in message
    action = calls[0].data["data"]["actions"][0]
    assert action["action"] == f"GOODDAYS:counted:{entry.entry_id}:omer:2027-04-22"
    assert events[-1].data["day"] == 1 and events[-1].data["counted"] is False

    await _at(hass, freezer, shabbat.start - dt.timedelta(minutes=59))
    assert len(calls) == 2 and calls[1].data["message"].startswith("Tonight: day 2 of the Omer")
    await _at(hass, freezer, shabbat.start + dt.timedelta(hours=2))
    assert len(calls) == 2  # nothing during Shabbat

    # "Counted" button: remembered for the sensor, announced on the bus.
    hass.bus.async_fire("mobile_app_notification_action", {"action": f"GOODDAYS:counted:{entry.entry_id}:omer:2027-04-23"})
    await hass.async_block_till_done()
    assert events[-1].data["counted"] is True and events[-1].data["night"] == "2027-04-23"
    assert hass.states.get("sensor.good_days_omer").attributes["counted"] is True

    await _at(hass, freezer, shabbat.end + dt.timedelta(seconds=30))
    assert len(calls) == 3 and calls[2].data["message"].startswith("Tonight: day 3 of the Omer")


async def test_omer_reminder_off_by_default(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2027-04-26 09:00:00+00:00")
    calls = async_mock_service(hass, "notify", PHONE)
    runtime = await setup_entry(hass, make_entry(hass, notify_targets=[PHONE]))
    await _at(hass, freezer, omer_switch(dt.date(2027, 4, 26), runtime.settings) + dt.timedelta(minutes=1))
    assert calls == []


async def test_upcoming_ws_and_assist(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    freezer.move_to("2027-04-26 09:00:00+00:00")
    runtime = await setup_entry(hass, make_entry(hass))
    await client.send_json({"id": 1, "type": "good_days/upcoming", "days": 30, "language": "en"})
    result = (await client.receive_json())["result"]
    assert result["omer"]["day"] == 4 and result["omer"]["text"].startswith("Today is the fourth day")
    now = dt_util.now()
    assert intents.speech_omer(runtime, "en", now) == "Today is the fourth day of the Omer."
    assert intents.speech_omer(runtime, "he", now).startswith("היום")
    # Pesach Sheni is a minor holiday, not a fast: the next fast is 17 Tammuz.
    speech = intents.speech_fast(runtime, "en", now)
    assert speech.startswith("Tzom Tammuz begins in 87 days") and speech.endswith("and ends at 20:12.")

    freezer.move_to("2027-07-22 08:00:00+00:00")
    assert intents.speech_fast(runtime, "en", dt_util.now()) == "Tzom Tammuz ends at 20:12."
