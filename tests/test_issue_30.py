"""#30 (UX-011): options form: reminder time without seconds, no raw unit codes, no internal names in help."""
from __future__ import annotations

import json
import pathlib

from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from .conftest import make_entry, setup_entry

ROOT = pathlib.Path(__file__).resolve().parent.parent / "custom_components" / "good_days"


async def test_issue_30_options_form(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass, reminder_time="09:00")
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    fields = {str(key): value for key, value in result["data_schema"].schema.items()}
    assert fields["reminder_time"].serialize() == {"selector": {"time": {"no_second": True}}}
    assert fields["reminder_time"]("07:30") == "07:30"
    for name in ("candle_lighting_minutes", "havdalah_minutes", "lookahead_days"):
        assert "unit_of_measurement" not in fields[name].config, name

    # An HH:MM answer (what the seconds-less input sends) is accepted and stored as HH:MM.
    done = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {**{k: v for k, v in entry.options.items() if k not in ("latitude", "longitude", "elevation")},
         "location": {"latitude": 31.778, "longitude": 35.235}, "language": "auto",
         "categories": ["shabbat"], "lookahead_days": 400, "reminder_time": "07:30", "quiet_on_shabbat": True},
    )
    assert done["type"] is FlowResultType.CREATE_ENTRY and entry.options["reminder_time"] == "07:30"


def test_issue_30_help_text_has_no_internal_service_names() -> None:
    for lang in ("en", "he"):
        init = json.loads((ROOT / "translations" / f"{lang}.json").read_text(encoding="utf-8"))["options"]["step"]["init"]
        help_text = init["data_description"]["notify_targets"]
        assert "mobile_app" not in help_text, lang
        # Units are words in the labels, not codes next to the box.
        assert ("minutes" in init["data"]["candle_lighting_minutes"]) or ("דקות" in init["data"]["candle_lighting_minutes"])
        assert ("minutes" in init["data"]["havdalah_minutes"]) or ("דקות" in init["data"]["havdalah_minutes"])
        assert ("Days" in init["data"]["lookahead_days"]) or ("ימים" in init["data"]["lookahead_days"])
