"""v0.10: a card's own location and times (WS good_days/upcoming overrides)."""
from __future__ import annotations

import datetime as dt

from homeassistant.core import HomeAssistant

from custom_components.good_days.const import DOMAIN

from .conftest import make_entry, setup_entry
from .test_integration import NOW

CAESAREA = {"latitude": 32.5, "longitude": 34.892}


async def _shabbat(ws, **extra) -> dict:
    await ws.send_json_auto_id({"type": f"{DOMAIN}/upcoming", "days": 10, "limit": 20, "language": "en", **extra})
    reply = await ws.receive_json()
    assert reply["success"], reply
    return next(i for i in reply["result"]["items"] if i["category"] == "shabbat")


def _minutes(a: str, b: str) -> float:
    return (dt.datetime.fromisoformat(a) - dt.datetime.fromisoformat(b)).total_seconds() / 60


async def test_card_location_and_times(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    runtime = await setup_entry(hass, make_entry(hass, language="en"))  # Jerusalem, 40 min
    own = await _shabbat(ws)

    # Same settings as the entry: the shared cache answers, nothing custom is computed.
    same = await _shabbat(ws, latitude=runtime.settings.latitude, longitude=runtime.settings.longitude,
                          candle_lighting=40)
    assert same == own
    assert not runtime._custom

    # Caesarea, 30 min: candle lighting = sunset - 30 there, havdalah unchanged rule.
    caesarea = await _shabbat(ws, **CAESAREA, candle_lighting=30)
    assert caesarea["candle_lighting"] != own["candle_lighting"]
    caesarea_18 = await _shabbat(ws, **CAESAREA, candle_lighting=18)
    assert _minutes(caesarea_18["candle_lighting"], caesarea["candle_lighting"]) == 12
    assert caesarea["havdalah"] == caesarea_18["havdalah"] != own["havdalah"]
    assert caesarea["start"] == caesarea["candle_lighting"]

    # Havdalah offset alone (entry location), cached between calls.
    later = await _shabbat(ws, havdalah=50)
    assert later["havdalah"] != own["havdalah"]
    assert later["candle_lighting"] == own["candle_lighting"]
    count = len(runtime._custom)
    await _shabbat(ws, havdalah=50)
    assert len(runtime._custom) == count


async def test_card_diaspora_two_day_yom_tov(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to("2027-04-20 07:00:00+00:00")  # Pesach 5787 starts on 2027-04-21 evening
    await setup_entry(hass, make_entry(hass, language="en"))

    async def days_off(**extra) -> list[str]:
        await ws.send_json_auto_id({"type": f"{DOMAIN}/upcoming", "days": 10, "limit": 30, "language": "en",
                                    "categories": ["yom_tov"], **extra})
        items = (await ws.receive_json())["result"]["items"]
        return [i["end"] for i in items]

    israel_ends, diaspora_ends = await days_off(), await days_off(diaspora=True)
    assert israel_ends and diaspora_ends
    assert diaspora_ends[0] > israel_ends[0]  # two-day Yom Tov ends a day later


async def test_card_override_validation(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass, language="en"))
    for bad in ({"latitude": 32.5}, {"latitude": 95, "longitude": 34}, {"candle_lighting": 500}, {"havdalah": -1}):
        await ws.send_json_auto_id({"type": f"{DOMAIN}/upcoming", **bad})
        reply = await ws.receive_json()
        assert not reply["success"], bad
        assert reply["error"]["code"] == "invalid_format"
