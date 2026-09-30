"""#6 (SEC-001): the timer switch / select entities need an admin, like the timers/settings WS command."""
from __future__ import annotations

import pytest
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import Unauthorized

from .test_v05 import _setup

SKIP = "switch.good_days_skip_next_shabbat_or_chag"
MASTER = "switch.good_days_shabbat_timers"
PROFILE = "select.good_days_timer_profile"


async def test_issue_6_entities_refuse_non_admin(
    hass: HomeAssistant, israel, freezer, hass_ws_client, hass_admin_user
) -> None:
    entry, ws = await _setup(hass, freezer, hass_ws_client)
    store = entry.runtime_data.timers.store
    store.profiles.append("Guests")
    # An ordinary household member: non-admin, but allowed to control entities (HA's default).
    member = await hass.auth.async_create_user("qa_user", group_ids=["system-users"])
    assert not member.is_admin
    user = Context(user_id=member.id)

    calls = (
        ("switch", "turn_off", {"entity_id": MASTER}),
        ("switch", "turn_on", {"entity_id": SKIP}),
        ("select", "select_option", {"entity_id": PROFILE, "option": "Guests"}),
    )
    for domain, service, data in calls:
        with pytest.raises(Unauthorized):
            await hass.services.async_call(domain, service, data, blocking=True, context=user)
    assert store.enabled is True and store.skip == [] and store.active_profile == "default"
    assert hass.states.get(MASTER).state == "on"

    # Admins and automations / scripts (no user) still can.
    admin = Context(user_id=hass_admin_user.id)
    await hass.services.async_call("switch", "turn_off", {"entity_id": MASTER}, blocking=True, context=admin)
    assert store.enabled is False
    await hass.services.async_call("switch", "turn_on", {"entity_id": MASTER}, blocking=True)
    await hass.services.async_call("switch", "turn_on", {"entity_id": SKIP}, blocking=True, context=Context())
    await hass.services.async_call("select", "select_option", {"entity_id": PROFILE, "option": "Guests"}, blocking=True)
    assert store.enabled is True and len(store.skip) == 1 and store.active_profile == "Guests"
