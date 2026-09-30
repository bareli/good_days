"""Good Days: upcoming Shabbat, Jewish holidays and family events, with a Lovelace card."""
from __future__ import annotations

import json
import logging
import os

from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from . import websocket
from .const import DOMAIN
from .runtime import GoodDaysRuntime

LOG = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.CALENDAR, Platform.SENSOR, Platform.BINARY_SENSOR]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

STATIC_URL = "/good_days_static"
CARD_RESOURCE_URL = f"{STATIC_URL}/card.js"
CARD_REGISTERED_KEY = f"{DOMAIN}_card_registered"

type GoodDaysConfigEntry = ConfigEntry[GoodDaysRuntime]

_INTEGRATION_VERSION_CACHE: str | None = None


def _read_version_sync() -> str:
    try:
        with open(os.path.join(os.path.dirname(__file__), "manifest.json"), encoding="utf-8") as f:
            return json.load(f).get("version", "0")
    except (OSError, ValueError):
        return "0"


async def _integration_version(hass: HomeAssistant) -> str:
    global _INTEGRATION_VERSION_CACHE
    if _INTEGRATION_VERSION_CACHE is None:
        _INTEGRATION_VERSION_CACHE = await hass.async_add_executor_job(_read_version_sync)
    return _INTEGRATION_VERSION_CACHE


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    websocket.async_register(hass)
    return True


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve www/ and add the card as a Lovelace module resource (stale versions removed)."""
    if hass.data.get(CARD_REGISTERED_KEY):
        return
    hass.data[CARD_REGISTERED_KEY] = True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, os.path.join(os.path.dirname(__file__), "www"), False)]
    )
    try:
        lovelace = hass.data.get("lovelace")
        resources = getattr(lovelace, "resources", None)
        if resources is None or not hasattr(resources, "async_create_item"):
            return  # YAML-mode dashboards: user adds the resource manually
        if not resources.loaded:
            await resources.async_load()
        target = f"{CARD_RESOURCE_URL}?v={await _integration_version(hass)}"
        for item in list(resources.async_items()):
            url = item.get("url", "")
            if url.startswith(CARD_RESOURCE_URL) and url != target:
                await resources.async_delete_item(item["id"])
        if not any(item.get("url") == target for item in resources.async_items()):
            await resources.async_create_item({"res_type": "module", "url": target})
    except Exception as err:  # noqa: BLE001 - the card is optional, never block setup
        LOG.debug("card resource auto-register skipped: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: GoodDaysConfigEntry) -> bool:
    runtime = GoodDaysRuntime(hass, entry)
    entry.runtime_data = runtime
    await runtime.async_start()
    entry.async_on_unload(runtime.async_stop)

    await _async_register_card(hass)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: GoodDaysConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GoodDaysConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
