"""#28 (UX-009): good_days/upcoming reports the effective categories it used."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from .test_v05 import _setup, _ws


async def test_issue_28_upcoming_reports_effective_categories(
    hass: HomeAssistant, israel, freezer, hass_ws_client
) -> None:
    _, ws = await _setup(hass, freezer, hass_ws_client)
    result = await _ws(ws, type="good_days/upcoming")
    # Integration defaults plus family dates, in canonical order.
    assert result["categories"] == ["shabbat", "yom_tov", "chol_hamoed", "minor", "fast", "modern", "family"]
    result = await _ws(ws, type="good_days/upcoming", categories=["family", "shabbat"])
    assert result["categories"] == ["shabbat", "family"]
