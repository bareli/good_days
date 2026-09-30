"""Config flow, entities, calendar window and the upcoming WebSocket command."""
from __future__ import annotations

import datetime as dt

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.good_days.const import DOMAIN

from .conftest import JERUSALEM, make_entry, setup_entry

# Wednesday 2026-10-07 10:00 Israel time. Shabbat Bereshit: Fri 9th 17:34 to Sat 10th.
NOW = "2026-10-07 07:00:00+00:00"

USER_INPUT = {
    "location": {"latitude": JERUSALEM["latitude"], "longitude": JERUSALEM["longitude"]},
    "elevation": 754,
    "diaspora": False,
    "candle_lighting_minutes": 40,
    "havdalah_minutes": 0,
    "language": "auto",
}


async def test_config_flow_creates_entry(hass: HomeAssistant, israel) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    options = result["options"]
    assert options["latitude"] == JERUSALEM["latitude"]
    assert options["candle_lighting_minutes"] == 40
    assert "shabbat" in options["categories"]
    assert options["lookahead_days"] == 400


@pytest.mark.parametrize(
    ("patch", "field", "error"),
    [
        ({"candle_lighting_minutes": 500}, "candle_lighting_minutes", "invalid_minutes"),
        ({"havdalah_minutes": 12.5}, "havdalah_minutes", "invalid_minutes"),
        ({"location": {"latitude": 95, "longitude": 35}}, "location", "invalid_location"),
        ({"elevation": 20000}, "elevation", "invalid_elevation"),
        ({"language": "fr"}, "language", "invalid_language"),
    ],
)
async def test_config_flow_validates_server_side(hass: HomeAssistant, israel, patch, field, error) -> None:
    from custom_components.good_days.config_flow import validate

    _, errors = validate({**USER_INPUT, **patch}, with_options=False)
    assert errors == {field: error}


async def test_config_flow_imports_jewish_calendar_defaults(hass: HomeAssistant, israel) -> None:
    MockConfigEntry(
        domain="jewish_calendar",
        data={"diaspora": True, "latitude": 40.7, "longitude": -74.0, "elevation": 10},
        options={"candle_lighting_minutes_before_sunset": 22, "havdalah_minutes_after_sunset": 50},
    ).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert result["description_placeholders"] == {"source": "Jewish Calendar"}
    defaults = {str(k): k.default() for k in result["data_schema"].schema}
    assert defaults["diaspora"] is True
    assert defaults["candle_lighting_minutes"] == 22
    assert defaults["havdalah_minutes"] == 50
    assert defaults["location"] == {"latitude": 40.7, "longitude": -74.0}


async def test_options_flow_merges_and_validates(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass, custom_key="keep")
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    bad = {**USER_INPUT, "categories": [], "lookahead_days": 400}
    result = await hass.config_entries.options.async_configure(result["flow_id"], bad)
    assert result["errors"] == {"categories": "no_categories"}
    good = {**USER_INPUT, "categories": ["yom_tov", "shabbat"], "lookahead_days": 60}
    result = await hass.config_entries.options.async_configure(result["flow_id"], good)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["custom_key"] == "keep"
    assert entry.options["categories"] == ["shabbat", "yom_tov"]  # canonical order
    assert entry.runtime_data.lookahead == 60


async def test_entities(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))

    shabbat = hass.states.get("sensor.good_days_next_shabbat")
    assert shabbat is not None
    start = dt_util.parse_datetime(shabbat.state)
    assert dt_util.as_local(start).date() == dt.date(2026, 10, 9)
    assert shabbat.attributes["parasha"] == "Bereshit"
    assert shabbat.attributes["days_until"] == 2
    assert shabbat.attributes["in_effect"] is False

    holiday = hass.states.get("sensor.good_days_next_holiday")
    assert holiday.state == "Chanukah"
    assert holiday.attributes["start"] == "2026-12-05"

    assert hass.states.get("binary_sensor.good_days_holiday_today").state == "off"

    calendar = hass.states.get("calendar.good_days_holidays")
    assert calendar.state == "off"
    assert calendar.attributes["message"] == "Shabbat Parashat Bereshit"


async def test_in_effect_during_shabbat(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2026-10-10 09:00:00+00:00")  # Shabbat morning
    await setup_entry(hass, make_entry(hass))
    assert hass.states.get("calendar.good_days_holidays").state == "on"
    assert hass.states.get("sensor.good_days_next_shabbat").attributes["in_effect"] is True


async def test_holiday_today_on_chol_hamoed(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2026-09-28 09:00:00+00:00")
    await setup_entry(hass, make_entry(hass, language="he"))
    state = hass.states.get("binary_sensor.good_days_holiday_today")
    assert state.state == "on"
    assert state.attributes["holidays"] == ["חול המועד סוכות"]


async def test_calendar_get_events_window_and_categories(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass, categories=["shabbat", "yom_tov", "minor"]))

    async def events(start: str, end: str) -> list[dict]:
        resp = await hass.services.async_call(
            "calendar", "get_events",
            {"entity_id": "calendar.good_days_holidays", "start_date_time": start, "end_date_time": end},
            blocking=True, return_response=True,
        )
        return resp["calendar.good_days_holidays"]["events"]

    week = await events("2026-10-05T00:00:00+03:00", "2026-10-12T00:00:00+03:00")
    assert [e["summary"] for e in week] == ["Shabbat Parashat Bereshit"]  # rosh chodesh filtered out

    # Starts inside Shabbat: the period is still returned (overlap, not start-in-window).
    inside = await events("2026-10-10T12:00:00+03:00", "2026-10-10T13:00:00+03:00")
    assert [e["summary"] for e in inside] == ["Shabbat Parashat Bereshit"]

    # Ends exactly at candle lighting: not included.
    before = await events("2026-10-09T12:00:00+03:00", week[0]["start"])
    assert before == []

    # Far outside the cached window is computed on demand.
    far = await events("2030-12-01T00:00:00+02:00", "2030-12-31T00:00:00+02:00")
    assert any(e["summary"] == "Chanukah" and e["start"] == "2030-12-21" for e in far)


async def test_ws_upcoming_merges_external_calendar(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)  # authenticate before the clock jumps (token expiry)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))

    async def fake_get_events(call: ServiceCall):
        entity_id = call.data["entity_id"]
        if isinstance(entity_id, list):
            entity_id = entity_id[0]
        return {
            entity_id: {
                "events": [
                    {"start": "2026-10-08T16:00:00+03:00", "end": "2026-10-08T17:00:00+03:00", "summary": "Dentist"},
                    {"start": "2026-10-10T10:00:00+03:00", "end": "2026-10-10T12:00:00+03:00", "summary": "Party"},
                    {"start": "2026-10-07", "end": "2026-10-08", "summary": "Trip"},
                ]
            }
        }

    hass.services.async_remove("calendar", "get_events")
    hass.services.async_register(
        "calendar", "get_events", fake_get_events, supports_response=SupportsResponse.ONLY
    )

    await client.send_json_auto_id(
        {
            "type": "good_days/upcoming",
            "calendars": ["calendar.family", "calendar.good_days_holidays"],
            "days": 7,
            "limit": 10,
            "language": "en",
        }
    )
    msg = await client.receive_json()
    assert msg["success"], msg
    items = msg["result"]["items"]
    # Rosh Chodesh (Oct 11-12) is not in the default categories.
    assert [i["title"] for i in items] == ["Trip", "Dentist", "Shabbat Parashat Bereshit", "Party"]
    by_title = {i["title"]: i for i in items}
    assert by_title["Party"]["conflicts_shabbat"] is True
    assert by_title["Dentist"]["conflicts_shabbat"] is False
    assert by_title["Trip"]["all_day"] is True and by_title["Trip"]["source"] == "calendar.family"
    shabbat = by_title["Shabbat Parashat Bereshit"]
    assert shabbat["source"] == "holidays" and shabbat["candle_lighting"] and shabbat["havdalah"]
    assert sum(1 for i in items if i["source"] == "holidays" and i["category"] == "shabbat") == 1
    assert msg["result"]["current"] is None
    assert msg["result"]["errors"] == []

    await client.send_json_auto_id(
        {"type": "good_days/upcoming", "calendars": ["calendar.family"], "days": 7, "limit": 2, "categories": ["shabbat"]}
    )
    msg = await client.receive_json()
    assert [i["title"] for i in msg["result"]["items"]] == ["Trip", "Dentist"]


async def test_ws_upcoming_reports_broken_calendar(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)  # authenticate before the clock jumps (token expiry)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))
    await client.send_json_auto_id(
        {"type": "good_days/upcoming", "calendars": ["calendar.missing"], "days": 3, "language": "he"}
    )
    msg = await client.receive_json()
    assert msg["success"], msg
    assert [e["entity_id"] for e in msg["result"]["errors"]] == ["calendar.missing"]
    assert msg["result"]["language"] == "he"
    assert msg["result"]["items"][0]["title"] == "שבת פרשת בראשית"


async def test_ws_upcoming_rejects_bad_input(hass: HomeAssistant, israel, hass_ws_client) -> None:
    await setup_entry(hass, make_entry(hass))
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": "good_days/upcoming", "days": 0})
    assert (await client.receive_json())["success"] is False
    await client.send_json_auto_id({"type": "good_days/upcoming", "calendars": ["sensor.x"]})
    assert (await client.receive_json())["success"] is False
    await client.send_json_auto_id({"type": "good_days/upcoming", "entry_id": "nope"})
    msg = await client.receive_json()
    assert msg["error"]["code"] == "not_loaded"


async def test_unload(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
