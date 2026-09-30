"""#14 (PERF-003): simultaneous timer actions share one store write and one entity update."""
from __future__ import annotations

from unittest.mock import patch

from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .test_v05 import _at, _setup, _state, rule


async def test_issue_14_simultaneous_actions_are_coalesced(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, _ = await _setup(hass, freezer, hass_ws_client)
    timers = entry.runtime_data.timers
    timers.store.rules += [
        rule(f"r{i}", name=f"Rule {i}", targets=["input_boolean.plate"], offset_min=-20, applies_to=["shabbat"])
        for i in range(50)
    ]
    await timers.store.async_save()
    await timers.async_replan()
    await _at(hass, freezer, "2026-10-09 14:13:00+00:00")

    signals = []
    async_dispatcher_connect(hass, timers.signal, lambda: signals.append(1))
    real_write = timers.store._store._async_write_data
    writes = []

    async def counting_write(*args, **kwargs):
        writes.append(1)
        return await real_write(*args, **kwargs)

    with patch.object(timers.store._store, "_async_write_data", counting_write):
        await _at(hass, freezer, "2026-10-09 14:14:00+00:00")  # all 50 fire now
        await _at(hass, freezer, "2026-10-09 14:14:10+00:00")  # after the save / signal delay
    assert _state(hass) == "on"
    assert [h["status"] for h in timers.store.history].count("done") == 50
    assert len(writes) <= 2, writes
    assert len(signals) <= 2, signals

    # The done keys reach the disk before a reload, so nothing fires twice.
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert [h["status"] for h in entry.runtime_data.timers.store.history].count("done") == 50
    assert len(entry.runtime_data.timers.store.history) == 50


async def test_issue_14_pending_write_is_flushed_on_unload(hass: HomeAssistant, israel, freezer, hass_ws_client) -> None:
    entry, _ = await _setup(hass, freezer, hass_ws_client)
    timers = entry.runtime_data.timers
    timers.store.rules.append(rule("p", name="Plate", targets=["input_boolean.plate"], offset_min=-20,
                                   applies_to=["shabbat"]))
    await timers.store.async_save()
    await timers.async_replan()
    await _at(hass, freezer, "2026-10-09 14:14:00+00:00")  # fires; the write is still pending
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.services.async_call("input_boolean", "turn_off", {"entity_id": "input_boolean.plate"}, blocking=True)
    assert await hass.config_entries.async_setup(entry.entry_id)  # within the grace window
    await hass.async_block_till_done(wait_background_tasks=True)
    assert _state(hass) == "off"  # not re-run: the done key survived
