"""#7 (SEC-002): reminder notification buttons only act on a real date and a day in the reminder window."""
from __future__ import annotations

import copy

from homeassistant.core import HomeAssistant

from .test_v03 import WEEKDAY_BIRTHDAY, _add, _at, _setup


async def _press(hass: HomeAssistant, action: str) -> None:
    hass.bus.async_fire("mobile_app_notification_action", {"action": action})
    await hass.async_block_till_done()


async def test_issue_7_forged_actions_are_ignored(hass: HomeAssistant, israel, freezer) -> None:
    entry, _, _ = await _setup(hass, freezer)
    date = await _add(hass, {**WEEKDAY_BIRTHDAY, "reminder_days": [0, 1]})
    await _at(hass, freezer, "2026-10-13 06:00:30+00:00")
    reminders = entry.runtime_data.store.reminders
    before = copy.deepcopy({k: reminders[k] for k in ("acked", "snoozes")})

    eid = entry.entry_id
    for action in (
        f"GOODDAYS:ack:{eid}:not-a-date-id:2026-10-14",
        f"GOODDAYS:ack:{eid}:{date['id']}:9999-12-31",
        f"GOODDAYS:ack:{eid}:{date['id']}:not-a-day",
        f"GOODDAYS:ack:{eid}:{date['id']}:2020-01-01",
        f"GOODDAYS:snooze:{eid}:not-a-date-id:2026-10-14",
        f"GOODDAYS:snooze:{eid}:{date['id']}:not-a-day",
        f"GOODDAYS:snooze:{eid}:{date['id']}:9999-12-31",
    ):
        await _press(hass, action)
    assert {k: reminders[k] for k in ("acked", "snoozes")} == before

    # Real buttons still work; pressing snooze twice keeps one snooze for the occurrence.
    await _press(hass, f"GOODDAYS:snooze:{eid}:{date['id']}:2026-10-14")
    await _press(hass, f"GOODDAYS:snooze:{eid}:{date['id']}:2026-10-14")
    assert [(s["date_id"], s["day"]) for s in reminders["snoozes"]] == [(date["id"], "2026-10-14")]
    await _press(hass, f"GOODDAYS:ack:{eid}:{date['id']}:2026-10-14")
    assert reminders["acked"] == {f"{date['id']}:2026-10-14": "2026-10-14"}
