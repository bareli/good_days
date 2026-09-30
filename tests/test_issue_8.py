"""#8 (SEC-003): non-finite numbers ("nan", "inf", "1e400") are field errors, never exceptions."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.good_days.storage import validate_date
from custom_components.good_days.timers import validate_rule

from .test_v05 import _setup, _ws, rule

BAD = ["nan", "inf", "-inf", "1e400", float("nan"), float("inf")]
DATE = {"name": "Dan", "kind": "birthday", "hebrew_day": 1, "hebrew_month": "tishrei"}


@pytest.mark.parametrize("value", BAD)
def test_issue_8_validate_date_non_finite(value) -> None:
    assert validate_date({**DATE, "hebrew_day": value})[1] == {"hebrew_day": "invalid_day"}
    assert validate_date({**DATE, "original_year": value})[1] == {"original_year": "invalid_year"}
    assert validate_date({**DATE, "reminder_days": [value]})[1] == {"reminder_days": "invalid_reminder_days"}


@pytest.mark.parametrize("value", BAD)
def test_issue_8_validate_rule_non_finite(value) -> None:
    assert validate_rule(rule(offset_min=value))[1] == {"offset_min": "invalid_offset"}


async def test_issue_8_ws_returns_field_errors(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    _, ws = await _setup(hass, freezer, hass_ws_client)
    added = await _ws(ws, type="good_days/dates/add", **{**DATE, "hebrew_day": "nan"})
    assert added["errors"] == {"hebrew_day": "invalid_day"}
    saved = await _ws(ws, type="good_days/timers/save", name="X", targets=["input_boolean.plate"], action="on",
                      anchor="candle_lighting", offset_min="inf", applies_to=["shabbat"])
    assert saved["errors"] == {"offset_min": "invalid_offset"}
