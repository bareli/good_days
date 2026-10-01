"""Good Days: upcoming Shabbat, Jewish holidays and family events, with a Lovelace card."""
from __future__ import annotations

import json
import logging
import os

from homeassistant.components import panel_custom
from homeassistant.components.frontend import async_remove_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from . import websocket, websocket_timers
from .ics import GoodDaysIcsView
from .intents import async_register_intents
from .reminders import async_register_actions
from .services import async_register_services
from .const import CONF_LANGUAGE, DOMAIN, LANG_AUTO
from .runtime import GoodDaysRuntime

LOG = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.CALENDAR,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

STATIC_URL = "/good_days_static"
CARD_RESOURCE_URL = f"{STATIC_URL}/card.js"
CARD_REGISTERED_KEY = f"{DOMAIN}_card_registered"
STATIC_REGISTERED_KEY = f"{DOMAIN}_static_registered"
PANEL_REGISTERED_KEY = f"{DOMAIN}_panel_registered"
PANEL_URL_PATH = "good-days"

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
    websocket_timers.async_register(hass)
    async_register_services(hass)
    async_register_actions(hass)
    async_register_intents(hass)
    hass.http.register_view(GoodDaysIcsView(hass))
    return True


async def _async_register_static(hass: HomeAssistant) -> None:
    if hass.data.get(STATIC_REGISTERED_KEY):
        return
    hass.data[STATIC_REGISTERED_KEY] = True
    await hass.http.async_register_static_paths(
        [StaticPathConfig(STATIC_URL, os.path.join(os.path.dirname(__file__), "www"), False)]
    )


def panel_title(hass: HomeAssistant, entry: ConfigEntry) -> str:
    """Sidebar title. Home Assistant shows one title to every user (it cannot follow each user's
    language), so it follows the entry's "Event names language" option; "auto" = system language."""
    language = entry.options.get(CONF_LANGUAGE, LANG_AUTO)
    if language == LANG_AUTO:
        language = str(hass.config.language or "")
    return "ימים טובים" if language.startswith("he") else "Good Days"


async def _async_register_panel(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Sidebar panel for family dates (all users; household data)."""
    if hass.data.get(PANEL_REGISTERED_KEY):
        return
    hass.data[PANEL_REGISTERED_KEY] = True
    await _async_register_static(hass)
    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="good-days-panel",
        frontend_url_path=PANEL_URL_PATH,
        module_url=f"{STATIC_URL}/panel.js?v={await _integration_version(hass)}",
        sidebar_title=panel_title(hass, entry),
        sidebar_icon="mdi:calendar-star",
        require_admin=False,
        config={},
    )


async def _async_register_card(hass: HomeAssistant) -> None:
    """Serve www/ and add the card as a Lovelace module resource (stale versions removed)."""
    if hass.data.get(CARD_REGISTERED_KEY):
        return
    hass.data[CARD_REGISTERED_KEY] = True
    await _async_register_static(hass)
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
    await _async_register_panel(hass, entry)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(hass: HomeAssistant, entry: GoodDaysConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: GoodDaysConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data.timers.async_flush()  # a timer run's delayed write
    others = [
        e
        for e in hass.config_entries.async_entries(DOMAIN)
        if e.entry_id != entry.entry_id and e.state is ConfigEntryState.LOADED
    ]
    if unloaded and not others and hass.data.pop(PANEL_REGISTERED_KEY, False):
        async_remove_panel(hass, PANEL_URL_PATH)
    return unloaded
