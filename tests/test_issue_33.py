"""#33 (BUG-010): a second Good Days entry's calendar listed in `calendars` is merged, not silently dropped."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import make_entry, setup_entry
from .test_v05 import _ws

NOW = "2026-10-01 07:00:00+00:00"


def _calendars(hass: HomeAssistant, entry_id: str) -> dict[str, str]:
    registry = er.async_get(hass)
    return {
        e.unique_id.rsplit("_", 1)[-1]: e.entity_id
        for e in er.async_entries_for_config_entry(registry, entry_id)
        if e.domain == "calendar"
    }


async def test_issue_33_other_entry_calendar_is_merged(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    client = await hass_ws_client(hass)
    freezer.move_to(NOW)
    home = await setup_entry(hass, make_entry(hass))
    parents = await setup_entry(hass, make_entry(hass, latitude=40.71, longitude=-74.0, diaspora=True))
    await parents.store.async_add({"name": "Grandpa Sam", "kind": "birthday", "hebrew_day": 25, "hebrew_month": "tishrei"})
    await parents.async_refresh_family()
    own, other = _calendars(hass, home.entry.entry_id), _calendars(hass, parents.entry.entry_id)

    result = await _ws(client, type="good_days/upcoming", entry_id=home.entry.entry_id, days=30, limit=50,
                       calendars=[other["family"], own["family"], own["holidays"], "calendar.missing"],
                       categories=["family", "yom_tov"])
    sam = [i for i in result["items"] if "Grandpa Sam" in i["title"]]
    assert [(i["source"], i["start"]) for i in sam] == [(other["family"], "2026-10-06")]
    assert [e["entity_id"] for e in result["errors"]] == ["calendar.missing"]
    # The requesting entry's own calendars are still not listed twice.
    assert not any(i["source"] in (own["family"], own["holidays"]) for i in result["items"])
