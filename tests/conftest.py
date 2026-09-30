"""Shared fixtures for Good Days tests."""
from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.good_days.const import DOMAIN

JERUSALEM = {"latitude": 31.778, "longitude": 35.235, "elevation": 754}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def no_card():
    """Lovelace resource and sidebar panel need the real frontend; not under test."""
    with patch("custom_components.good_days._async_register_card", return_value=None), patch(
        "custom_components.good_days._async_register_panel", return_value=None
    ):
        yield


@pytest.fixture
async def israel(hass: HomeAssistant):
    await hass.config.async_update(
        time_zone="Asia/Jerusalem", country="IL", **{k: JERUSALEM[k] for k in ("latitude", "longitude", "elevation")}
    )
    yield


def make_entry(hass: HomeAssistant, **options) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Good Days",
        data={},
        options={**JERUSALEM, "diaspora": False, "candle_lighting_minutes": 40, "havdalah_minutes": 0, **options},
    )
    entry.add_to_hass(hass)
    return entry


async def setup_entry(hass: HomeAssistant, entry: MockConfigEntry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry.runtime_data
