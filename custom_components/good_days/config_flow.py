"""Config and options flow for Good Days."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CATEGORIES,
    CONF_CANDLE_LIGHTING,
    CONF_CATEGORIES,
    CONF_DIASPORA,
    CONF_FAST_END,
    CONF_FAST_START,
    CONF_HAVDALAH,
    CONF_OMER_REMINDER,
    CONF_OMER_REMINDER_OFFSET,
    DEFAULT_FAST_END,
    DEFAULT_FAST_START,
    DEFAULT_OMER_REMINDER_OFFSET,
    FAST_END_OPTIONS,
    FAST_START_OPTIONS,
    MAX_OMER_REMINDER_OFFSET,
    CONF_NUSACH,
    DEFAULT_NUSACH,
    LEGACY_NUSACH,
    NUSACH_OPTIONS,
    CONF_LANGUAGE,
    CONF_LATITUDE,
    CONF_LOCATION,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_DAYS,
    CONF_NOTIFY_TARGETS,
    CONF_QUIET_ON_SHABBAT,
    CONF_REMINDER_TIME,
    DEFAULT_CANDLE_LIGHTING,
    DEFAULT_REMINDER_TIME,
    DEFAULT_CATEGORIES,
    DEFAULT_HAVDALAH,
    DEFAULT_LOOKAHEAD_DAYS,
    DOMAIN,
    LANG_AUTO,
    LANGUAGES,
    MAX_LOOKAHEAD_DAYS,
    MAX_OFFSET_MINUTES,
    MIN_LOOKAHEAD_DAYS,
)

JEWISH_CALENDAR = "jewish_calendar"
# Keys of the core Jewish Calendar entry (data / options). Read once as defaults, never live.
JC_CANDLE = "candle_lighting_minutes_before_sunset"
JC_HAVDALAH = "havdalah_minutes_after_sunset"


def jewish_calendar_defaults(hass: HomeAssistant) -> dict[str, Any]:
    """Settings of an existing Jewish Calendar entry, in our option keys ({} if none)."""
    entries = hass.config_entries.async_entries(JEWISH_CALENDAR)
    if not entries:
        return {}
    data, options = entries[0].data, entries[0].options
    out: dict[str, Any] = {}
    try:
        if CONF_LATITUDE in data and CONF_LONGITUDE in data:
            out[CONF_LATITUDE] = float(data[CONF_LATITUDE])
            out[CONF_LONGITUDE] = float(data[CONF_LONGITUDE])
        if CONF_DIASPORA in data:
            out[CONF_DIASPORA] = bool(data[CONF_DIASPORA])
        if JC_CANDLE in options:
            out[CONF_CANDLE_LIGHTING] = int(options[JC_CANDLE])
        if JC_HAVDALAH in options:
            out[CONF_HAVDALAH] = int(options[JC_HAVDALAH])
    except (TypeError, ValueError):
        return {}
    return out


def _base_defaults(hass: HomeAssistant) -> dict[str, Any]:
    return {
        CONF_LATITUDE: hass.config.latitude,
        CONF_LONGITUDE: hass.config.longitude,
        CONF_DIASPORA: bool(hass.config.country) and hass.config.country != "IL",
        CONF_CANDLE_LIGHTING: DEFAULT_CANDLE_LIGHTING,
        CONF_HAVDALAH: DEFAULT_HAVDALAH,
        CONF_NUSACH: DEFAULT_NUSACH,
        CONF_LANGUAGE: LANG_AUTO,
        CONF_CATEGORIES: DEFAULT_CATEGORIES,
        CONF_LOOKAHEAD_DAYS: DEFAULT_LOOKAHEAD_DAYS,
        CONF_NOTIFY_TARGETS: [],
        CONF_REMINDER_TIME: DEFAULT_REMINDER_TIME,
        CONF_QUIET_ON_SHABBAT: True,
        CONF_FAST_START: DEFAULT_FAST_START,
        CONF_FAST_END: DEFAULT_FAST_END,
        CONF_OMER_REMINDER: False,
        CONF_OMER_REMINDER_OFFSET: DEFAULT_OMER_REMINDER_OFFSET,
    }


class _TimeWithoutSeconds(selector.TimeSelector):
    """HH:MM input. The frontend's time selector supports `no_second`; core's config schema
    (2026.2 - 2026.9) does not list it yet, so it is accepted here."""

    CONFIG_SCHEMA = vol.Schema({vol.Optional("no_second"): bool})


def _minutes() -> selector.NumberSelector:
    # The unit is a word in the translated label; a raw "min" code is not translated.
    return selector.NumberSelector(
        selector.NumberSelectorConfig(min=0, max=MAX_OFFSET_MINUTES, step=1, mode=selector.NumberSelectorMode.BOX)
    )


def _location_fields(d: dict[str, Any]) -> dict:
    return {
        vol.Required(
            CONF_LOCATION,
            default={CONF_LATITUDE: d[CONF_LATITUDE], CONF_LONGITUDE: d[CONF_LONGITUDE]},
        ): selector.LocationSelector(selector.LocationSelectorConfig(radius=False)),
        vol.Required(CONF_DIASPORA, default=d[CONF_DIASPORA]): selector.BooleanSelector(),
        vol.Required(CONF_CANDLE_LIGHTING, default=d[CONF_CANDLE_LIGHTING]): _minutes(),
        vol.Required(CONF_HAVDALAH, default=d[CONF_HAVDALAH]): _minutes(),
        vol.Required(CONF_NUSACH, default=d.get(CONF_NUSACH, DEFAULT_NUSACH)): selector.SelectSelector(
            selector.SelectSelectorConfig(options=NUSACH_OPTIONS, translation_key="nusach")
        ),
        vol.Required(CONF_LANGUAGE, default=d[CONF_LANGUAGE]): selector.SelectSelector(
            selector.SelectSelectorConfig(options=LANGUAGES, translation_key="language")
        ),
    }


def _notify_services(hass: HomeAssistant) -> list[str]:
    return sorted(hass.services.async_services_for_domain("notify"))


def _option_fields(hass: HomeAssistant, d: dict[str, Any]) -> dict:
    return {
        vol.Required(CONF_CATEGORIES, default=list(d[CONF_CATEGORIES])): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=CATEGORIES, multiple=True, translation_key="category",
                mode=selector.SelectSelectorMode.LIST,
            )
        ),
        vol.Required(CONF_FAST_START, default=d[CONF_FAST_START]): selector.SelectSelector(
            selector.SelectSelectorConfig(options=FAST_START_OPTIONS, translation_key="fast_start")
        ),
        vol.Required(CONF_FAST_END, default=d[CONF_FAST_END]): selector.SelectSelector(
            selector.SelectSelectorConfig(options=FAST_END_OPTIONS, translation_key="fast_end")
        ),
        vol.Required(CONF_LOOKAHEAD_DAYS, default=d[CONF_LOOKAHEAD_DAYS]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=MIN_LOOKAHEAD_DAYS, max=MAX_LOOKAHEAD_DAYS, step=1, mode=selector.NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(CONF_NOTIFY_TARGETS, default=list(d[CONF_NOTIFY_TARGETS])): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=sorted({*_notify_services(hass), *d[CONF_NOTIFY_TARGETS]}),
                multiple=True,
                custom_value=True,
                mode=selector.SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(CONF_REMINDER_TIME, default=d[CONF_REMINDER_TIME]): _TimeWithoutSeconds({"no_second": True}),
        vol.Required(CONF_QUIET_ON_SHABBAT, default=d[CONF_QUIET_ON_SHABBAT]): selector.BooleanSelector(),
        vol.Required(CONF_OMER_REMINDER, default=d[CONF_OMER_REMINDER]): selector.BooleanSelector(),
        vol.Required(CONF_OMER_REMINDER_OFFSET, default=d[CONF_OMER_REMINDER_OFFSET]): selector.NumberSelector(
            selector.NumberSelectorConfig(
                min=0, max=MAX_OMER_REMINDER_OFFSET, step=1, mode=selector.NumberSelectorMode.BOX
            )
        ),
    }


def _int_in(value: Any, low: int, high: int) -> int | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != int(number) or not low <= number <= high:
        return None
    return int(number)


def _hhmm(value: Any) -> str | None:
    """'HH:MM' from 'HH:MM' or the TimeSelector's 'HH:MM:SS'."""
    parts = str(value or "").split(":")
    if len(parts) not in (2, 3) or not all(p.isdigit() for p in parts):
        return None
    hours, minutes = int(parts[0]), int(parts[1])
    if not (0 <= hours < 24 and 0 <= minutes < 60):
        return None
    return f"{hours:02d}:{minutes:02d}"


def validate(
    user_input: dict[str, Any], with_options: bool, notify_services: set[str] | None = None
) -> tuple[dict[str, Any], dict[str, str]]:
    """Server-side validation; returns (clean options, errors keyed by field)."""
    errors: dict[str, str] = {}
    clean: dict[str, Any] = {}

    location = user_input.get(CONF_LOCATION) or {}
    try:
        lat, lon = float(location[CONF_LATITUDE]), float(location[CONF_LONGITUDE])
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError
        clean[CONF_LATITUDE], clean[CONF_LONGITUDE] = lat, lon
    except (KeyError, TypeError, ValueError):
        errors[CONF_LOCATION] = "invalid_location"

    for key in (CONF_CANDLE_LIGHTING, CONF_HAVDALAH):
        minutes = _int_in(user_input.get(key), 0, MAX_OFFSET_MINUTES)
        if minutes is None:
            errors[key] = "invalid_minutes"
        else:
            clean[key] = minutes

    clean[CONF_DIASPORA] = bool(user_input.get(CONF_DIASPORA, False))
    nusach = user_input.get(CONF_NUSACH, DEFAULT_NUSACH)
    if nusach not in NUSACH_OPTIONS:
        errors[CONF_NUSACH] = "invalid_nusach"
    else:
        clean[CONF_NUSACH] = nusach
    language = user_input.get(CONF_LANGUAGE, LANG_AUTO)
    if language not in LANGUAGES:
        errors[CONF_LANGUAGE] = "invalid_language"
    else:
        clean[CONF_LANGUAGE] = language

    if with_options:
        categories = user_input.get(CONF_CATEGORIES) or []
        if not categories or any(c not in CATEGORIES for c in categories):
            errors[CONF_CATEGORIES] = "no_categories"
        else:
            clean[CONF_CATEGORIES] = [c for c in CATEGORIES if c in categories]
        days = _int_in(user_input.get(CONF_LOOKAHEAD_DAYS), MIN_LOOKAHEAD_DAYS, MAX_LOOKAHEAD_DAYS)
        if days is None:
            errors[CONF_LOOKAHEAD_DAYS] = "invalid_lookahead"
        else:
            clean[CONF_LOOKAHEAD_DAYS] = days

        targets = user_input.get(CONF_NOTIFY_TARGETS) or []
        targets = [str(t).strip().removeprefix("notify.") for t in targets if str(t).strip()]
        if notify_services is not None and any(t not in notify_services for t in targets):
            errors[CONF_NOTIFY_TARGETS] = "invalid_notify"
        else:
            clean[CONF_NOTIFY_TARGETS] = list(dict.fromkeys(targets))
        reminder_time = _hhmm(user_input.get(CONF_REMINDER_TIME, DEFAULT_REMINDER_TIME))
        if reminder_time is None:
            errors[CONF_REMINDER_TIME] = "invalid_time"
        else:
            clean[CONF_REMINDER_TIME] = reminder_time
        clean[CONF_QUIET_ON_SHABBAT] = bool(user_input.get(CONF_QUIET_ON_SHABBAT, True))
        for key, allowed, default in (
            (CONF_FAST_START, FAST_START_OPTIONS, DEFAULT_FAST_START),
            (CONF_FAST_END, FAST_END_OPTIONS, DEFAULT_FAST_END),
        ):
            value = user_input.get(key, default)
            if value not in allowed:
                errors[key] = "invalid_choice"
            else:
                clean[key] = value
        clean[CONF_OMER_REMINDER] = bool(user_input.get(CONF_OMER_REMINDER, False))
        offset = _int_in(
            user_input.get(CONF_OMER_REMINDER_OFFSET, DEFAULT_OMER_REMINDER_OFFSET), 0, MAX_OMER_REMINDER_OFFSET
        )
        if offset is None:
            errors[CONF_OMER_REMINDER_OFFSET] = "invalid_omer_offset"
        else:
            clean[CONF_OMER_REMINDER_OFFSET] = offset
    return clean, errors


def _form_values(user_input: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    """Re-show what the user typed after an error (location flattened back)."""
    values = {**fallback, **{k: v for k, v in user_input.items() if k != CONF_LOCATION}}
    location = user_input.get(CONF_LOCATION)
    if isinstance(location, dict) and CONF_LATITUDE in location and CONF_LONGITUDE in location:
        values[CONF_LATITUDE], values[CONF_LONGITUDE] = location[CONF_LATITUDE], location[CONF_LONGITUDE]
    return values


class GoodDaysConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        imported = jewish_calendar_defaults(self.hass)
        defaults = {**_base_defaults(self.hass), **imported}
        errors: dict[str, str] = {}
        if user_input is not None:
            clean, errors = validate(user_input, with_options=False)
            if not errors:
                options = {
                    CONF_CATEGORIES: DEFAULT_CATEGORIES,
                    CONF_LOOKAHEAD_DAYS: DEFAULT_LOOKAHEAD_DAYS,
                    **clean,
                }
                return self.async_create_entry(title=self._new_title(), data={}, options=options)
            defaults = _form_values(user_input, defaults)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(_location_fields(defaults)),
            errors=errors,
            description_placeholders={"source": "Jewish Calendar" if imported else "Home Assistant"},
        )

    def _new_title(self) -> str:
        """"Good Days", then "Good Days 2", "Good Days 3"... so two entries never look the same."""
        taken = {entry.title for entry in self.hass.config_entries.async_entries(DOMAIN)}
        title, number = "Good Days", 1
        while title in taken:
            number += 1
            title = f"Good Days {number}"
        return title

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return GoodDaysOptionsFlow(config_entry)


class GoodDaysOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        current = {**_base_defaults(self.hass), **self._entry.options}
        # Saved before the option existed: show the custom the entry actually uses.
        if CONF_NUSACH not in self._entry.options:
            current[CONF_NUSACH] = LEGACY_NUSACH
        errors: dict[str, str] = {}
        if user_input is not None:
            clean, errors = validate(
                user_input, with_options=True, notify_services=set(_notify_services(self.hass))
            )
            if not errors:
                # Merge: keys this form does not show must survive.
                return self.async_create_entry(data={**self._entry.options, **clean})
            current = _form_values(user_input, current)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({**_location_fields(current), **_option_fields(self.hass, current)}),
            errors=errors,
        )
