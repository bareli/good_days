"""WS commands for Shabbat Home timers (reads for everyone, changes for admins)."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MAX_NAME_LENGTH
from .engine import norm_language
from .runtime import GoodDaysRuntime
from .timers import MAX_PROFILES, MAX_RULES, PRESETS, validate_rule
from .websocket import entry_label, resolve_runtime

PROFILE_NAME = vol.All(cv.string, vol.Strip, vol.Length(min=1, max=40))


def _runtime(hass: HomeAssistant, connection, msg) -> GoodDaysRuntime | None:
    try:
        return resolve_runtime(hass, msg.get("entry_id"))
    except HomeAssistantError as err:
        connection.send_error(msg["id"], "not_loaded", str(err))
        return None


def _view(runtime: GoodDaysRuntime, lang: str) -> dict[str, Any]:
    timers = runtime.timers
    store = timers.store
    now = dt_util.now()
    nxt = timers.next_action(now)
    periods = timers.periods(now, 1)
    return {
        "entry_id": runtime.entry.entry_id,
        "label": entry_label(runtime.hass, runtime, lang),
        "enabled": store.enabled,
        "profiles": store.profiles,
        "active_profile": store.active_profile,
        "skip_next": bool(periods) and periods[0].uid in store.skip,
        "rules": store.rules,
        "presets": list(PRESETS),
        "preview": timers.preview(now, lang),
        "next_action": {
            "when": nxt.when.isoformat(), "action": nxt.action, "targets": list(nxt.targets),
            "rule_name": nxt.rule_name,
        } if nxt else None,
        "history": list(reversed(store.history[-30:])),
    }


async def _changed(runtime: GoodDaysRuntime) -> None:
    await runtime.timers.store.async_save()
    await runtime.timers.async_replan()


def _entities(hass: HomeAssistant) -> set[str]:
    return set(hass.states.async_entity_ids())


async def _validate(hass, runtime, data, existing=None) -> tuple[dict[str, Any], dict[str, str]]:
    clean, errors = validate_rule(data, existing, _entities(hass), runtime.timers.store.profiles)
    if clean.get("action") == "off" and any(t.startswith("scene.") for t in clean.get("targets", [])):
        errors["targets"] = "scene_off"
    if clean.get("conditions") and "conditions" not in errors:
        if not await runtime.timers.async_validate_conditions(clean["conditions"]):
            errors["conditions"] = "invalid_conditions"
    return clean, errors


@callback
def async_register(hass: HomeAssistant) -> None:
    for command in (ws_get, ws_save, ws_remove, ws_duplicate, ws_run, ws_settings, ws_preset):
        websocket_api.async_register_command(hass, command)


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/get",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Optional("profile"): cv.string,
    }
)
@callback
def ws_get(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    lang = norm_language(msg.get("language") or runtime.language)
    view = _view(runtime, lang)
    if msg.get("profile") in runtime.timers.store.profiles:  # preview another profile (dry run)
        view["preview"] = runtime.timers.preview(dt_util.now(), lang, msg["profile"])
    connection.send_result(msg["id"], view)


RULE_FIELDS = {
    vol.Optional("name"): cv.string,
    vol.Optional("targets"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("action"): cv.string,
    vol.Optional("anchor"): cv.string,
    vol.Optional("offset_min"): vol.Any(int, float, cv.string),
    vol.Optional("time"): vol.Any(None, cv.string),
    vol.Optional("days"): cv.string,
    vol.Optional("applies_to"): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional("profile"): cv.string,
    vol.Optional("conditions"): vol.Any(None, list),
    vol.Optional("enabled"): bool,
}


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/save",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Optional("rule_id"): cv.string,
        **RULE_FIELDS,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_save(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Add (no rule_id) or update a rule. Validation problems: {"errors": {field: code}}."""
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    store = runtime.timers.store
    data = {k: v for k, v in msg.items() if k in {str(f) for f in RULE_FIELDS}}
    existing = store.get(msg["rule_id"]) if "rule_id" in msg else None
    if "rule_id" in msg and existing is None:
        connection.send_result(msg["id"], {"errors": {"rule_id": "not_found"}})
        return
    if existing is None and len(store.rules) >= MAX_RULES:
        connection.send_result(msg["id"], {"errors": {"base": "too_many_rules"}})
        return
    clean, errors = await _validate(hass, runtime, data, existing)
    if errors:
        connection.send_result(msg["id"], {"errors": errors})
        return
    if existing is None:
        rule = {"id": store.new_id(), **clean}
        store.rules.append(rule)
    else:
        existing.update(clean)
        rule = existing
    await _changed(runtime)
    connection.send_result(msg["id"], {"errors": {}, "rule": rule})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/remove",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("rule_id"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_remove(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    store = runtime.timers.store
    if store.get(msg["rule_id"]) is None:
        connection.send_result(msg["id"], {"errors": {"rule_id": "not_found"}})
        return
    store.rules = [r for r in store.rules if r["id"] != msg["rule_id"]]
    await _changed(runtime)
    connection.send_result(msg["id"], {"errors": {}})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/duplicate",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("rule_id"): cv.string,
        vol.Optional("profile"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_duplicate(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    store = runtime.timers.store
    rule = store.get(msg["rule_id"])
    if rule is None:
        connection.send_result(msg["id"], {"errors": {"rule_id": "not_found"}})
        return
    if len(store.rules) >= MAX_RULES:
        connection.send_result(msg["id"], {"errors": {"base": "too_many_rules"}})
        return
    profile = msg.get("profile") or rule.get("profile")
    if profile not in store.profiles:
        connection.send_result(msg["id"], {"errors": {"profile": "invalid_profile"}})
        return
    suffix = " (2)" if profile == rule.get("profile") else ""
    copy = {**rule, "id": store.new_id(), "profile": profile, "name": (rule["name"] + suffix)[:MAX_NAME_LENGTH]}
    store.rules.append(copy)
    await _changed(runtime)
    connection.send_result(msg["id"], {"errors": {}, "rule": copy})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/run",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("language"): cv.string,
        vol.Required("rule_id"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_run(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Run a rule's action right now (to test it); conditions and schedule are ignored."""
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    rule = runtime.timers.store.get(msg["rule_id"])
    if rule is None:
        connection.send_result(msg["id"], {"errors": {"rule_id": "not_found"}})
        return
    try:
        await runtime.timers.async_execute(rule["action"], rule["targets"])
    except (HomeAssistantError, TimeoutError) as err:
        connection.send_result(msg["id"], {"errors": {"base": "run_failed"}, "message": str(err)})
        return
    connection.send_result(msg["id"], {"errors": {}})


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/settings",
        vol.Optional("entry_id"): cv.string,
        vol.Optional("enabled"): bool,
        vol.Optional("skip_next"): bool,
        vol.Optional("active_profile"): cv.string,
        vol.Optional("add_profile"): PROFILE_NAME,
        vol.Optional("copy_from"): cv.string,  # with add_profile: duplicate that profile's rules
        vol.Optional("rename_profile"): cv.string,
        vol.Optional("new_name"): PROFILE_NAME,
        vol.Optional("remove_profile"): cv.string,
        vol.Optional("language"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_settings(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    errors = await async_apply_settings(runtime, msg)
    lang = norm_language(msg.get("language") or runtime.language)
    connection.send_result(msg["id"], {"errors": errors, **_view(runtime, lang)})


async def async_apply_settings(runtime: GoodDaysRuntime, msg: dict[str, Any]) -> dict[str, str]:
    """Shared by the WS command and the switch / select entities."""
    store = runtime.timers.store
    errors: dict[str, str] = {}
    if "enabled" in msg:
        store.enabled = msg["enabled"]
    if "skip_next" in msg:
        periods = runtime.timers.periods(dt_util.now(), 1)
        if periods:
            uid = periods[0].uid
            store.skip = [u for u in store.skip if u != uid] + ([uid] if msg["skip_next"] else [])
    if "add_profile" in msg:
        name = msg["add_profile"]
        if name in store.profiles or len(store.profiles) >= MAX_PROFILES:
            errors["add_profile"] = "invalid_profile_name"
        elif msg.get("copy_from") and msg["copy_from"] not in store.profiles:
            errors["copy_from"] = "invalid_profile"
        else:
            store.profiles.append(name)
            if msg.get("copy_from"):
                store.rules += [
                    {**r, "id": store.new_id(), "profile": name}
                    for r in list(store.rules)
                    if r.get("profile") == msg["copy_from"]
                ]
    if "rename_profile" in msg:
        old, new = msg["rename_profile"], msg.get("new_name")
        if old not in store.profiles or not new or new in store.profiles:
            errors["rename_profile"] = "invalid_profile_name"
        else:
            store.profiles[store.profiles.index(old)] = new
            for rule in store.rules:
                if rule.get("profile") == old:
                    rule["profile"] = new
            if store.active_profile == old:
                store.active_profile = new
    if "remove_profile" in msg:
        name = msg["remove_profile"]
        if name not in store.profiles or len(store.profiles) == 1:
            errors["remove_profile"] = "invalid_profile"
        else:
            store.profiles.remove(name)
            store.rules = [r for r in store.rules if r.get("profile") != name]
            if store.active_profile == name:
                store.active_profile = store.profiles[0]
    if "active_profile" in msg:
        if msg["active_profile"] not in store.profiles:
            errors["active_profile"] = "invalid_profile"
        else:
            store.active_profile = msg["active_profile"]
    await _changed(runtime)
    return errors


@websocket_api.websocket_command(
    {
        vol.Required("type"): f"{DOMAIN}/timers/preset",
        vol.Optional("entry_id"): cv.string,
        vol.Required("preset"): vol.In(list(PRESETS)),
        vol.Required("name"): cv.string,
        vol.Required("targets"): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional("profile"): cv.string,
        vol.Optional("language"): cv.string,
    }
)
@websocket_api.require_admin
@websocket_api.async_response
async def ws_preset(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict[str, Any]) -> None:
    """Create the rules of a preset (e.g. hot plate: on before candle lighting, off after havdalah)."""
    if (runtime := _runtime(hass, connection, msg)) is None:
        return
    store = runtime.timers.store
    parts = PRESETS[msg["preset"]]
    if len(store.rules) + len(parts) > MAX_RULES:
        connection.send_result(msg["id"], {"errors": {"base": "too_many_rules"}})
        return
    hebrew = norm_language(msg.get("language") or runtime.language) == "he"
    suffixes = {"on": "הדלקה", "off": "כיבוי"} if hebrew else {"on": "on", "off": "off"}
    created = []
    for part in parts:
        data = {
            **part,
            "name": f"{msg['name']} ({suffixes[part['action']]})",
            "targets": msg["targets"],
            "profile": msg.get("profile") or store.active_profile,
        }
        clean, errors = await _validate(hass, runtime, data)
        if errors:
            connection.send_result(msg["id"], {"errors": errors})
            return
        created.append({"id": store.new_id(), **clean})
    store.rules += created
    await _changed(runtime)
    connection.send_result(msg["id"], {"errors": {}, "rules": created})
