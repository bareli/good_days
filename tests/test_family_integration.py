"""Family dates through services, WebSocket, entities and storage."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from custom_components.good_days.const import DOMAIN

from .conftest import make_entry, setup_entry

NOW = "2026-10-07 07:00:00+00:00"  # Wednesday; Shabbat Bereshit Fri 9th evening to Sat 10th
# 29 Tishrei 5787 = Shabbat 2026-10-10; 3 Cheshvan 5787 = Wed 2026-10-14.
SHABBAT_BIRTHDAY = {"name": "Noa", "kind": "birthday", "hebrew_day": 29, "hebrew_month": "tishrei", "original_year": 5780}
WEEKDAY_YAHRZEIT = {"name": "Saba", "kind": "yahrzeit", "hebrew_day": 3, "hebrew_month": "marcheshvan"}


async def add(hass: HomeAssistant, **data) -> dict:
    resp = await hass.services.async_call(DOMAIN, "add_date", data, blocking=True, return_response=True)
    await hass.async_block_till_done()
    return resp["date"]


async def test_services_crud_and_entities(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to(NOW)
    entry = make_entry(hass)
    await setup_entry(hass, entry)

    noa = await add(hass, **SHABBAT_BIRTHDAY)
    await add(hass, **WEEKDAY_YAHRZEIT)

    listed = await hass.services.async_call(DOMAIN, "list_dates", {}, blocking=True, return_response=True)
    assert [d["name"] for d in listed["dates"]] == ["Noa", "Saba"]
    assert listed["dates"][0]["next"]["start"] == "2026-10-10"
    assert listed["dates"][0]["next"]["years"] == 7

    state = hass.states.get("sensor.good_days_next_family_date")
    assert state.state == "\u2068Noa\u2069's birthday (7)"
    assert state.attributes["days_until"] == 3
    assert state.attributes["conflicts_shabbat"] is True

    resp = await hass.services.async_call(
        "calendar", "get_events",
        {"entity_id": "calendar.good_days_family", "start_date_time": "2026-10-05T00:00:00+03:00",
         "end_date_time": "2026-10-20T00:00:00+03:00"},
        blocking=True, return_response=True,
    )
    events = resp["calendar.good_days_family"]["events"]
    assert [e["summary"] for e in events] == ["\u2068Noa\u2069's birthday (7)", "Yahrzeit: \u2068Saba\u2069"]
    assert events[0]["start"] == "2026-10-10"
    assert events[1]["start"] == "2026-10-13T18:09:00+03:00"  # sea-level sunset the evening before

    await hass.services.async_call(DOMAIN, "update_date", {"date_id": noa["id"], "name": "Noa B."}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.good_days_next_family_date").state == "\u2068Noa B.\u2069's birthday (7)"

    await hass.services.async_call(DOMAIN, "remove_date", {"date_id": noa["id"]}, blocking=True)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.good_days_next_family_date").state == "Yahrzeit: \u2068Saba\u2069"


async def test_service_validation(hass: HomeAssistant, israel) -> None:
    await setup_entry(hass, make_entry(hass))
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "add_date", {"name": "X", "kind": "birthday", "hebrew_day": 30, "hebrew_month": "tevet"}, blocking=True
        )
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(DOMAIN, "remove_date", {"date_id": "nope"}, blocking=True)


async def test_add_from_gregorian_date(hass: HomeAssistant, israel) -> None:
    await setup_entry(hass, make_entry(hass))
    date = await add(hass, name="Dan", kind="birthday", gregorian_date="2024-03-23", after_sunset=True)
    assert (date["hebrew_day"], date["hebrew_month"], date["original_year"]) == (14, "adar_ii", 5784)


async def test_dates_persist_per_entry(hass: HomeAssistant, israel, hass_storage) -> None:
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    await add(hass, **SHABBAT_BIRTHDAY)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert [d["name"] for d in entry.runtime_data.store.dates] == ["Noa"]
    assert f"{DOMAIN}.{entry.entry_id}" in hass_storage


async def test_ws_dates_crud_with_inline_errors(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))

    await client.send_json_auto_id({"type": "good_days/dates/add", "name": "", "kind": "birthday", "hebrew_day": 31, "hebrew_month": "nisan"})
    msg = await client.receive_json()
    assert msg["success"] and msg["result"]["errors"] == {"name": "invalid_name", "hebrew_day": "invalid_day"}

    await client.send_json_auto_id({"type": "good_days/dates/add", "language": "he", **SHABBAT_BIRTHDAY})
    msg = await client.receive_json()
    date = msg["result"]["date"]
    assert msg["result"]["errors"] == {}
    assert date["next"]["title"] == "יום הולדת 7 ל\u2068Noa\u2069"
    assert date["next"]["days_until"] == 3

    await client.send_json_auto_id({"type": "good_days/dates/update", "date_id": date["id"], "hebrew_day": 30, "hebrew_month": "elul"})
    assert (await client.receive_json())["result"]["errors"] == {"hebrew_day": "invalid_day"}

    await client.send_json_auto_id({"type": "good_days/dates/list"})
    msg = await client.receive_json()
    assert [d["name"] for d in msg["result"]["dates"]] == ["Noa"]

    await client.send_json_auto_id({"type": "good_days/dates/convert", "date": "2024-03-23", "after_sunset": True})
    msg = await client.receive_json()
    assert msg["result"]["hebrew_month"] == "adar_ii"
    assert msg["result"]["display"] == {"he": "י״ד אדר ב׳ תשפ״ד", "en": "14 Adar II 5784"}

    await client.send_json_auto_id({"type": "good_days/upcoming", "calendars": [], "days": 7, "language": "en"})
    items = (await client.receive_json())["result"]["items"]
    family = [i for i in items if i["source"] == "family"]
    assert [i["title"] for i in family] == ["\u2068Noa\u2069's birthday (7)"]
    assert family[0]["conflicts_shabbat"] is True and family[0]["kind"] == "birthday"

    await client.send_json_auto_id({"type": "good_days/upcoming", "calendars": [], "days": 7, "categories": ["shabbat"]})
    items = (await client.receive_json())["result"]["items"]
    assert all(i["source"] == "holidays" for i in items)

    await client.send_json_auto_id({"type": "good_days/dates/remove", "date_id": date["id"]})
    assert (await client.receive_json())["result"]["errors"] == {}
    await client.send_json_auto_id({"type": "good_days/dates/remove", "date_id": date["id"]})
    assert (await client.receive_json())["result"]["errors"] == {"id": "not_found"}
