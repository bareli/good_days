"""Shared entity base for Good Days platforms."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity

from .const import DOMAIN, SIGNAL_UPDATED
from .timer_manager import SIGNAL_TIMERS
from .runtime import GoodDaysRuntime


class GoodDaysEntity(Entity):
    """One service device per config entry; state pushed by the runtime (refresh + 1 min tick)."""

    _attr_should_poll = False
    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, key: str) -> None:
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Good Days",
            model="Jewish calendar",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def runtime(self) -> GoodDaysRuntime:
        return self._entry.runtime_data

    async def async_added_to_hass(self) -> None:
        for signal in (SIGNAL_UPDATED, SIGNAL_TIMERS):
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass, signal.format(self._entry.entry_id), self._handle_update
                )
            )

    @callback
    def _handle_update(self) -> None:
        self.async_write_ha_state()
