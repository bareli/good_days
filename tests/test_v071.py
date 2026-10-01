"""v0.7.1: the sidebar title follows the "Event names language" option."""
from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.good_days import panel_title

from .conftest import make_entry


@pytest.mark.parametrize(
    ("system", "option", "title"),
    [
        ("he", "auto", "ימים טובים"),
        ("en", "auto", "Good Days"),
        ("he", "en", "Good Days"),  # Hebrew system, English chosen for Good Days
        ("en", "he", "ימים טובים"),
        ("de", "auto", "Good Days"),
    ],
)
async def test_panel_title(hass: HomeAssistant, system: str, option: str, title: str) -> None:
    hass.config.language = system
    entry = make_entry(hass, language=option)
    assert panel_title(hass, entry) == title


async def test_panel_title_without_option(hass: HomeAssistant) -> None:
    hass.config.language = "he"
    entry = make_entry(hass)
    entry_options = dict(entry.options)
    entry_options.pop("language", None)
    hass.config_entries.async_update_entry(entry, options=entry_options)
    assert panel_title(hass, entry) == "ימים טובים"
