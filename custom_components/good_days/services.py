"""Services for family dates: add_date, update_date, remove_date, list_dates."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.util import dt as dt_util

from .const import ADAR_RULES, DAY30_RULES, DOMAIN, HEBREW_MONTHS, KINDS
from .storage import DateValidationError
from .websocket import _date_view, resolve_runtime

SERVICE_ADD = "add_date"
SERVICE_UPDATE = "update_date"
SERVICE_REMOVE = "remove_date"
SERVICE_LIST = "list_dates"

_FIELDS = {
    vol.Optional("entry_id"): cv.string,
    vol.Optional("name"): cv.string,
    vol.Optional("kind"): vol.In(KINDS),
    vol.Optional("hebrew_day"): vol.All(vol.Coerce(int), vol.Range(min=1, max=30)),
    vol.Optional("hebrew_month"): vol.In(HEBREW_MONTHS),
    vol.Optional("original_year"): vol.All(vol.Coerce(int), vol.Range(min=3000, max=6500)),
    vol.Optional("gregorian_date"): cv.date,
    vol.Optional("after_sunset"): cv.boolean,
    vol.Optional("adar_rule"): vol.In(ADAR_RULES),
    vol.Optional("day30_rule"): vol.In(DAY30_RULES),
    vol.Optional("reminder_days"): vol.All(cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=0, max=60))]),
    vol.Optional("notes"): cv.string,
}
SCHEMA_ADD = vol.Schema(_FIELDS)
SCHEMA_UPDATE = vol.Schema({vol.Required("date_id"): cv.string, **_FIELDS})
SCHEMA_REMOVE = vol.Schema({vol.Optional("entry_id"): cv.string, vol.Required("date_id"): cv.string})
SCHEMA_LIST = vol.Schema({vol.Optional("entry_id"): cv.string})


def _data(call: ServiceCall) -> dict[str, Any]:
    data = {k: v for k, v in call.data.items() if k not in ("entry_id", "date_id")}
    if "gregorian_date" in data:
        data["gregorian_date"] = data["gregorian_date"].isoformat()
    return data


def _invalid(err: DateValidationError) -> ServiceValidationError:
    return ServiceValidationError(f"Invalid family date: {err}")


@callback
def async_register_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, SERVICE_ADD):
        return

    async def add(call: ServiceCall) -> ServiceResponse:
        runtime = resolve_runtime(hass, call.data.get("entry_id"))
        try:
            record = await runtime.store.async_add(_data(call))
        except DateValidationError as err:
            raise _invalid(err) from err
        await runtime.async_refresh_family()
        return {"date": dict(record)}

    async def update(call: ServiceCall) -> None:
        runtime = resolve_runtime(hass, call.data.get("entry_id"))
        try:
            await runtime.store.async_update(call.data["date_id"], _data(call))
        except DateValidationError as err:
            raise _invalid(err) from err
        await runtime.async_refresh_family()

    async def remove(call: ServiceCall) -> None:
        runtime = resolve_runtime(hass, call.data.get("entry_id"))
        try:
            await runtime.store.async_remove(call.data["date_id"])
        except DateValidationError as err:
            raise _invalid(err) from err
        await runtime.async_refresh_family()

    async def list_dates(call: ServiceCall) -> ServiceResponse:
        runtime = resolve_runtime(hass, call.data.get("entry_id"))
        now, lang = dt_util.now(), runtime.language
        records = list(runtime.store.dates)
        views = await hass.async_add_executor_job(
            lambda: [_date_view(runtime, r, lang, now) for r in records]
        )
        return {"dates": views}

    hass.services.async_register(DOMAIN, SERVICE_ADD, add, SCHEMA_ADD, SupportsResponse.OPTIONAL)
    hass.services.async_register(DOMAIN, SERVICE_UPDATE, update, SCHEMA_UPDATE)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE, remove, SCHEMA_REMOVE)
    hass.services.async_register(DOMAIN, SERVICE_LIST, list_dates, SCHEMA_LIST, SupportsResponse.ONLY)
