"""Active Shabbat timer profile (e.g. Regular / Guests)."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import GoodDaysEntity
from .websocket_timers import async_apply_settings


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TimerProfileSelect(entry)])


class TimerProfileSelect(GoodDaysEntity, SelectEntity):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, entry: ConfigEntry) -> None:
        super().__init__(entry, "timer_profile")

    @property
    def options(self) -> list[str]:  # the select's own options, not the integration's
        return list(self.runtime.timers.store.profiles)

    @property
    def current_option(self) -> str | None:
        return self.runtime.timers.store.active_profile

    async def async_select_option(self, option: str) -> None:
        await self.async_require_admin()
        await async_apply_settings(self.runtime, {"active_profile": option})
