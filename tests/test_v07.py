"""v0.7: haftarah per Shabbat (Ashkenazi / Sephardi) and more timer presets."""
from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.good_days.const import DOMAIN
from custom_components.good_days.engine import EngineSettings, _gematria, compute
from custom_components.good_days.haftarah import ASHKENAZI, SEPHARDI, format_parts, haftarah
from custom_components.good_days.timers import PRESETS, expand

from .conftest import make_entry, setup_entry
from .test_integration import NOW, USER_INPUT

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "hebcal_haftarah_2024_2040.json"
ISRAEL = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0)
DIASPORA = EngineSettings(40.7128, -74.0060, 0, "America/New_York", True, 18, 0)


def _shabbatot(settings: EngineSettings) -> dict[dt.date, object]:
    out = {}
    for event in compute(settings, dt.date(2024, 1, 1), dt.date(2040, 12, 31)):
        if event.is_shabbat and event.parasha:
            for i in range(event.days):
                day = event.first_day + dt.timedelta(days=i)
                if day.weekday() == 5:
                    out[day] = event
    return out


def test_haftarah_matches_hebcal_2024_2040():
    """Every Shabbat with a parasha, Israel and diaspora, both customs, against Hebcal leyning."""
    reference = json.loads(FIXTURE.read_text(encoding="utf-8"))
    by_place = {True: _shabbatot(ISRAEL), False: _shabbatot(DIASPORA)}

    def fmt(parts):
        return [f"{book} {first}-{last}" for book, first, last in parts]

    checked = 0
    for row in reference:
        day = dt.date.fromisoformat(row["date"])
        event = by_place[row["il"]].get(day)
        assert event is not None, (row["date"], row["il"], row["parsha"])
        assert fmt(haftarah(day, event.parasha, event.specials, ASHKENAZI)) == row["haft"], row
        assert fmt(haftarah(day, event.parasha, event.specials, SEPHARDI)) == row["seph"], row
        checked += 1
    assert checked == len(reference) > 1600


def test_shabbat_next_to_yom_tov_keeps_its_parasha():
    # 2024-10-05: Shabbat right after Rosh Hashana (Israel) is Shabbat Shuva, Ha'azinu.
    events = [e for e in compute(ISRAEL, dt.date(2024, 10, 3), dt.date(2024, 10, 5)) if e.is_shabbat]
    assert len(events) == 1
    event = events[0]
    assert event.parasha == "haazinu"
    assert "shuva" in event.specials
    assert event.haftarah_text("en") == "Hosea 14:2–10; Joel 2:15–27"
    # The period title is still the holiday + Shabbat one; the description names the parasha.
    assert "Rosh Hashana" in event.title("en")
    assert "Parashat Ha'Azinu · Haftarah: Hosea 14:2–10; Joel 2:15–27" in event.description("en")
    plain = [e for e in compute(ISRAEL, dt.date(2026, 10, 15), dt.date(2026, 10, 17)) if e.is_shabbat][0]
    assert "Parashat" not in plain.description("en")  # already in the title


def test_assist_names_yom_tov_periods():
    from types import SimpleNamespace

    from custom_components.good_days.intents import speech_shabbat

    event = [e for e in compute(ISRAEL, dt.date(2024, 10, 3), dt.date(2024, 10, 5)) if e.is_shabbat][0]
    runtime = SimpleNamespace(next_shabbat=lambda now: event)
    now = event.start - dt.timedelta(days=2)
    assert event.title("en") in speech_shabbat(runtime, "en", now)


def test_format_parts_hebrew_and_english():
    parts = (("Isaiah", "54:1", "55:5"), ("I Samuel", "20:18", "20:42"), ("Joshua", "6:27", "6:27"))
    assert format_parts(parts, "en", _gematria) == "Isaiah 54:1–55:5; I Samuel 20:18–42; Joshua 6:27"
    assert format_parts(parts, "he", _gematria) == "ישעיהו נד:א–נה:ה; שמואל א׳ כ:יח–מב; יהושע כז:ו".replace("כז:ו", "ו:כז")


def test_description_and_nusach():
    ashkenazi = [e for e in compute(ISRAEL, dt.date(2026, 10, 15), dt.date(2026, 10, 17)) if e.is_shabbat][0]
    assert "Haftarah: Isaiah 54:1–55:5" in ashkenazi.description("en")
    assert "הפטרה: ישעיהו נד:א–נה:ה" in ashkenazi.description("he")
    sephardi_settings = EngineSettings(31.778, 35.235, 0, "Asia/Jerusalem", False, 40, 0, nusach=SEPHARDI)
    sephardi = [e for e in compute(sephardi_settings, dt.date(2026, 10, 15), dt.date(2026, 10, 17)) if e.is_shabbat][0]
    assert sephardi.haftarah_text("en") == "Isaiah 54:1–10"


async def test_sensor_and_ws_show_haftarah(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    ws = await hass_ws_client(hass)
    freezer.move_to(NOW)
    await setup_entry(hass, make_entry(hass, language="en"))
    shabbat = hass.states.get("sensor.good_days_next_shabbat")
    # Bereshit 5787 falls on Erev Rosh Chodesh: Machar Chodesh.
    assert shabbat.attributes["haftarah"] == "I Samuel 20:18–42"
    await ws.send_json_auto_id({"type": f"{DOMAIN}/upcoming", "days": 10, "limit": 20, "language": "en"})
    items = (await ws.receive_json())["result"]["items"]
    shabbat_item = next(i for i in items if i["category"] == "shabbat")
    assert shabbat_item["haftarah"] == "I Samuel 20:18–42"
    assert all(i["haftarah"] is None for i in items if i["category"] not in ("shabbat", "yom_tov"))


async def test_options_flow_nusach(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass)
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    schema_keys = {str(k) for k in result["data_schema"].schema}
    assert "nusach" in schema_keys
    result = await hass.config_entries.options.async_configure(result["flow_id"], {**USER_INPUT, "nusach": "sephardi"})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["nusach"] == "sephardi"
    assert entry.runtime_data.settings.nusach == "sephardi"


@pytest.mark.parametrize("preset", ["water_heater", "porch_light", "bedroom_ac_night"])
def test_new_presets_expand_for_a_shabbat(preset):
    period = [e for e in compute(ISRAEL, dt.date(2026, 10, 15), dt.date(2026, 10, 17)) if e.is_shabbat][0]
    rules = [
        {"id": f"r{i}", "name": preset, "targets": ["switch.x"], "profile": "default", "enabled": True, "conditions": [], **part}
        for i, part in enumerate(PRESETS[preset])
    ]
    planned = expand(rules, [period], "Asia/Jerusalem", "default")
    assert [p.action for p in sorted(planned, key=lambda p: p.when)] == ["on", "off"]
    on, off = sorted(planned, key=lambda p: p.when)
    assert on.when < off.when
    if preset == "water_heater":
        assert on.when.date() == period.first_day - dt.timedelta(days=1)  # erev, noon
        assert off.when < period.start
    if preset == "porch_light":
        assert on.when < period.start < off.when
    if preset == "bedroom_ac_night":
        assert on.when.hour == 22 and off.when.hour == 6
