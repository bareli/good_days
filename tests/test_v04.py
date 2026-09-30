"""v0.4: special Shabbatot, ICS feed."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.util import dt as dt_util

from custom_components.good_days.const import DOMAIN
from custom_components.good_days.engine import EngineSettings, compute
from custom_components.good_days.family import compute_family
from custom_components.good_days.ics import _escape, build_ics

from .conftest import make_entry, setup_entry

D = dt.date
ISRAEL = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0)
NOW = "2026-10-07 07:00:00+00:00"


def specials(start: dt.date, end: dt.date) -> dict[dt.date, tuple[str, ...]]:
    return {e.first_day: e.specials for e in compute(ISRAEL, start, end) if e.category == "shabbat" and e.specials}


def test_special_shabbatot_regular_year_5783():
    found = specials(D(2022, 9, 20), D(2023, 8, 10))
    expected = {
        D(2022, 10, 1): "shuva", D(2023, 2, 4): "shira", D(2023, 2, 18): "shekalim",
        D(2023, 3, 4): "zachor", D(2023, 3, 11): "parah", D(2023, 3, 18): "hachodesh",
        D(2023, 4, 1): "hagadol", D(2023, 7, 22): "chazon", D(2023, 7, 29): "nachamu",
        D(2022, 10, 15): "chol_hamoed", D(2023, 4, 8): "chol_hamoed",
        D(2022, 12, 24): "chanukah", D(2023, 4, 22): "rosh_chodesh", D(2023, 5, 20): "machar_chodesh",
    }
    for day, key in expected.items():
        assert key in found.get(day, ()), (day, key, found.get(day))
    # Each four-parshiyot Shabbat is found exactly once.
    for key in ("shekalim", "zachor", "parah", "hachodesh", "hagadol", "shuva", "chazon", "nachamu"):
        assert sum(key in v for v in found.values()) == 1, key


def test_special_shabbatot_leap_year_follow_adar_ii():
    found = specials(D(2024, 2, 1), D(2024, 4, 30))
    assert "shekalim" in found[D(2024, 3, 9)]
    assert "zachor" in found[D(2024, 3, 23)]
    assert "parah" in found[D(2024, 3, 30)]
    assert "hachodesh" in found[D(2024, 4, 6)]
    assert "hagadol" in found[D(2024, 4, 20)]


def test_chazon_on_tisha_bav_itself_when_it_falls_on_shabbat():
    found = specials(D(2022, 7, 25), D(2022, 8, 20))
    assert "chazon" in found[D(2022, 8, 6)]  # 9 Av 5782 was Shabbat (fast moved to Sunday)
    assert "nachamu" in found[D(2022, 8, 13)]


def test_titles_and_mevarchim_note():
    events = {e.first_day: e for e in compute(ISRAEL, D(2023, 2, 10), D(2023, 3, 5)) if e.category == "shabbat"}
    shekalim = events[D(2023, 2, 18)]
    assert shekalim.title("en") == "Shabbat Parashat Mishpatim (Shekalim)"
    assert shekalim.title("he") == "שבת פרשת משפטים (שקלים)"
    assert "Mevarchim Chodesh Adar" in shekalim.description("en")
    chol = [e for e in compute(ISRAEL, D(2023, 4, 7), D(2023, 4, 9)) if e.category == "shabbat"][0]
    assert chol.title("en") == "Shabbat Chol HaMoed"


def test_build_ics_format():
    family = compute_family(
        [{"id": "x", "name": "נועה, \"הקטנה\"; " + "א" * 60, "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan"}],
        ISRAEL, D(2026, 10, 1), D(2026, 10, 31),
    )
    shabbat = [e for e in compute(ISRAEL, D(2026, 10, 5), D(2026, 10, 11)) if e.category == "shabbat"]
    text = build_ics([*family, *shabbat], "he", dt.datetime(2026, 10, 7, 7, tzinfo=dt.UTC))
    assert text.startswith("BEGIN:VCALENDAR\r\n") and text.endswith("END:VCALENDAR\r\n")
    assert all(len(line.encode("utf-8")) <= 75 for line in text.split("\r\n"))
    unfolded = text.replace("\r\n ", "")
    assert "DTSTART;VALUE=DATE:20261014\r\nDTEND;VALUE=DATE:20261015" in unfolded
    assert "SUMMARY:יום הולדת לנועה\\, \"הקטנה\"\\; " in unfolded
    assert "DTSTART:20261009T143400Z\r\nDTEND:20261010T154900Z" in unfolded  # 17:34 / 18:49 IDT
    assert "UID:family-x-2026-10-14@good_days" in unfolded


async def test_ics_feed_is_off_by_default_and_token_protected(
    hass: HomeAssistant, israel, freezer, hass_ws_client, hass_client_no_auth
) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    await hass.services.async_call(
        DOMAIN, "add_date", {"name": "Noa", "kind": "birthday", "hebrew_day": 3, "hebrew_month": "marcheshvan"},
        blocking=True, return_response=True,
    )
    client = await hass_client_no_auth()

    await ws.send_json_auto_id({"type": "good_days/ics/get"})
    state = (await ws.receive_json())["result"]
    assert state["enabled"] is False and state["path"] is None
    resp = await client.get(f"/api/good_days/ics/{entry.entry_id}/anything.ics")
    assert resp.status == 404

    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True, "holidays": False})
    state = (await ws.receive_json())["result"]
    path = state["path"]
    assert state["enabled"] and path.startswith(f"/api/good_days/ics/{entry.entry_id}/")
    resp = await client.get(path)
    assert resp.status == 200
    assert resp.headers["Content-Type"].startswith("text/calendar")
    body = await resp.text()
    assert "SUMMARY:Noa's birthday" in body and "Shabbat" not in body

    assert (await client.get(path.replace(".ics", "x.ics"))).status == 404
    assert (await client.get(f"/api/good_days/ics/other/{path.rsplit('/', 1)[1]}")).status == 404

    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True, "holidays": True, "new_link": True})
    new = (await ws.receive_json())["result"]
    assert new["path"] != path
    assert (await client.get(path)).status == 404
    body = await (await client.get(new["path"])).text()
    assert "SUMMARY:Shabbat Parashat Bereshit" in body

    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": False})
    assert (await ws.receive_json())["result"]["enabled"] is False
    assert (await client.get(new["path"])).status == 404

    # Survives a reload (stored with the family dates).
    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True})
    kept = (await ws.receive_json())["result"]["path"]
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert (await client.get(kept)).status == 200


async def test_ics_settings_need_admin(
    hass: HomeAssistant, israel, hass_ws_client, hass_read_only_access_token
) -> None:
    await setup_entry(hass, make_entry(hass))
    ws = await hass_ws_client(hass, hass_read_only_access_token)
    await ws.send_json_auto_id({"type": "good_days/ics/set", "enabled": True})
    msg = await ws.receive_json()
    assert msg["success"] is False and msg["error"]["code"] == "unauthorized"


async def test_next_shabbat_special_attribute(hass: HomeAssistant, israel, freezer) -> None:
    freezer.move_to("2023-02-14 10:00:00+00:00")
    await setup_entry(hass, make_entry(hass))
    state = hass.states.get("sensor.good_days_next_shabbat")
    assert state.attributes["special_shabbat"] == ["Shekalim", "Mevarchim Chodesh Adar"]
    assert state.attributes["title"] == "Shabbat Parashat Mishpatim (Shekalim)"
    assert dt_util.parse_datetime(state.state).date() == D(2023, 2, 17)


def test_ics_escape_bare_carriage_return():
    assert _escape("a\rb\r\nc\nd") == "a\\nb\\nc\\nd"


async def test_upcoming_survives_a_calendar_raising_any_error(
    hass: HomeAssistant, israel, freezer, hass_ws_client
) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass))

    async def broken(call: ServiceCall):
        raise TimeoutError("caldav timeout")

    hass.services.async_remove("calendar", "get_events")
    hass.services.async_register("calendar", "get_events", broken, supports_response=SupportsResponse.ONLY)
    await ws.send_json_auto_id({"type": "good_days/upcoming", "calendars": ["calendar.remote"], "days": 7})
    msg = await ws.receive_json()
    assert msg["success"], msg
    assert [e["entity_id"] for e in msg["result"]["errors"]] == ["calendar.remote"]
    assert any(i["source"] == "holidays" for i in msg["result"]["items"])

