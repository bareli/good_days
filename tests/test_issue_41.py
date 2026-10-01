"""#41 (UX-016): new installs default to Sephardi; entries saved without the option keep Ashkenazi."""
from __future__ import annotations

import json
import pathlib

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.good_days.const import DEFAULT_NUSACH, DOMAIN, LEGACY_NUSACH

from .conftest import make_entry, setup_entry
from .test_integration import USER_INPUT

TRANSLATIONS = pathlib.Path(__file__).parent.parent / "custom_components" / "good_days" / "translations"


def _default(result, name):
    key = next(k for k in result["data_schema"].schema if str(k) == name)
    return key.default()


def test_issue_41_two_defaults():
    assert DEFAULT_NUSACH == "sephardi"
    assert LEGACY_NUSACH == "ashkenazi"


async def test_issue_41_new_install_defaults_to_sephardi(hass: HomeAssistant, israel) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})
    assert _default(result, "nusach") == "sephardi"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    entry = hass.config_entries.async_get_entry(result["result"].entry_id)
    assert entry.options["nusach"] == "sephardi"
    assert entry.runtime_data.settings.nusach == "sephardi"


async def test_issue_41_entry_without_option_keeps_ashkenazi(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass)  # saved before v0.7: no "nusach" key
    assert "nusach" not in entry.options
    runtime = await setup_entry(hass, entry)
    assert runtime.settings.nusach == "ashkenazi"
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert _default(result, "nusach") == "ashkenazi"  # the dialog shows what the entry gets
    result = await hass.config_entries.options.async_configure(result["flow_id"], USER_INPUT)
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.options["nusach"] == "ashkenazi"  # saving other options does not switch the custom


async def test_issue_41_saved_choice_is_shown(hass: HomeAssistant, israel) -> None:
    entry = make_entry(hass, nusach="sephardi")
    await setup_entry(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert _default(result, "nusach") == "sephardi"


def test_issue_41_description_says_how_often_it_matters():
    en = json.loads((TRANSLATIONS / "en.json").read_text(encoding="utf-8"))
    he = json.loads((TRANSLATIONS / "he.json").read_text(encoding="utf-8"))
    for step in (en["config"]["step"]["user"], en["options"]["step"]["init"]):
        assert "one Shabbat in four" in step["data_description"]["nusach"]
    for step in (he["config"]["step"]["user"], he["options"]["step"]["init"]):
        assert "בשבת אחת מכל ארבע" in step["data_description"]["nusach"]
