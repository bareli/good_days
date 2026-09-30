"""#34 (UX-012): two Good Days entries can be told apart (distinct titles, a label with the place)."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.good_days.const import DOMAIN

from .conftest import make_entry, setup_entry
from .test_integration import USER_INPUT
from .test_v05 import _ws


async def test_issue_34_second_entry_gets_a_distinct_title(hass: HomeAssistant, israel) -> None:
    titles = []
    for _ in range(3):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
        assert result["type"] is FlowResultType.CREATE_ENTRY
        titles.append(result["title"])
        await hass.async_block_till_done()
    assert titles == ["Good Days", "Good Days 2", "Good Days 3"]


async def test_issue_34_labels_tell_entries_apart(
    hass: HomeAssistant, israel, hass_ws_client, hass_read_only_access_token
) -> None:
    hass.config.location_name = "Home"
    home = await setup_entry(hass, make_entry(hass))
    parents = await setup_entry(hass, make_entry(hass, latitude=40.7128, longitude=-74.006, diaspora=True))
    member = await hass_ws_client(hass, hass_read_only_access_token)  # not an admin

    listed = await _ws(member, type="good_days/entries", language="en")
    assert [(e["entry_id"], e["label"]) for e in listed["entries"]] == [
        (home.entry.entry_id, "Good Days · Home"),
        (parents.entry.entry_id, "Good Days · 40.71, -74.01 · Diaspora"),
    ]
    he = await _ws(member, type="good_days/entries", language="he")
    assert he["entries"][1]["label"] == "Good Days · 40.71, -74.01 · חוץ לארץ"

    dates = await _ws(member, type="good_days/dates/list", entry_id=parents.entry.entry_id, language="en")
    assert dates["label"] == "Good Days · 40.71, -74.01 · Diaspora"
    timers = await _ws(member, type="good_days/timers/get", entry_id=home.entry.entry_id, language="en")
    assert timers["label"] == "Good Days · Home"
