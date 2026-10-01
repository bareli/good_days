"""#42 (UX-017): the timers view carries each preset's rules so the panel can summarise them before saving."""
from __future__ import annotations

import pathlib

from homeassistant.core import HomeAssistant

from custom_components.good_days.timers import PRESETS

from .conftest import make_entry, setup_entry
from .test_v05 import _ws

PANEL = pathlib.Path(__file__).parent.parent / "custom_components" / "good_days" / "www" / "panel.js"


async def test_issue_42_view_has_preset_rules(hass: HomeAssistant, israel, hass_ws_client) -> None:
    await setup_entry(hass, make_entry(hass))
    ws = await hass_ws_client(hass)
    view = await _ws(ws, type="good_days/timers/get", language="en")
    assert set(view["preset_rules"]) == set(view["presets"]) == set(PRESETS)
    heater = view["preset_rules"]["water_heater"]
    assert [(p["action"], p.get("time"), p.get("days"), p.get("offset_min")) for p in heater] == [
        ("on", "12:00", "erev", None), ("off", None, None, -15),
    ]
    assert heater[0]["applies_to"] == ["shabbat", "yom_tov", "yom_kippur"]


def test_issue_42_panel_has_summary_strings():
    text = PANEL.read_text(encoding="utf-8")
    assert text.count("preset_note_water_heater:") == 2  # en + he
    assert "_presetSummary(preset.value)" in text  # refreshed on change
