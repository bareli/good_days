"""Family dates storage (one HA Store per config entry) and input validation."""
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.util import dt as dt_util

from .const import (
    ADAR_RULES,
    DAY30_RULES,
    DOMAIN,
    HEBREW_MONTHS,
    KINDS,
    MAX_DATES,
    MAX_HEBREW_YEAR,
    MAX_NAME_LENGTH,
    MAX_NOTES_LENGTH,
    MAX_REMINDER_DAYS,
    MIN_HEBREW_YEAR,
    MONTHS_29,
)
from .family import hebrew_from_gregorian

STORAGE_VERSION = 1
FIELDS = (
    "name", "kind", "hebrew_day", "hebrew_month", "original_year",
    "adar_rule", "day30_rule", "reminder_days", "notes",
)


def _int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number == int(number) else None


def validate_date(data: dict[str, Any], existing: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, str]]:
    """Clean a family date (full record, or a patch over `existing`); errors keyed by field.

    A Gregorian `gregorian_date` (+ `after_sunset`) may replace hebrew_day / hebrew_month /
    original_year.
    """
    merged = {**(existing or {}), **{k: v for k, v in data.items() if k in FIELDS}}
    errors: dict[str, str] = {}

    if data.get("gregorian_date") not in (None, ""):
        try:
            day = dt.date.fromisoformat(str(data["gregorian_date"]))
        except ValueError:
            errors["gregorian_date"] = "invalid_date"
        else:
            converted = hebrew_from_gregorian(day, bool(data.get("after_sunset")))
            merged["hebrew_day"] = converted["hebrew_day"]
            merged["hebrew_month"] = converted["hebrew_month"]
            merged["original_year"] = converted["hebrew_year"]

    clean: dict[str, Any] = {}
    name = str(merged.get("name") or "").strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        errors["name"] = "invalid_name"
    clean["name"] = name

    kind = merged.get("kind")
    if kind not in KINDS:
        errors["kind"] = "invalid_kind"
    clean["kind"] = kind

    month = merged.get("hebrew_month")
    if month not in HEBREW_MONTHS:
        errors.setdefault("hebrew_month", "invalid_month")
    clean["hebrew_month"] = month

    day = _int(merged.get("hebrew_day"))
    if day is None or not 1 <= day <= 30 or (day == 30 and month in MONTHS_29):
        errors.setdefault("hebrew_day", "invalid_day")
    clean["hebrew_day"] = day

    year = merged.get("original_year")
    if year in (None, ""):
        clean["original_year"] = None
    else:
        year = _int(year)
        if year is None or not MIN_HEBREW_YEAR <= year <= MAX_HEBREW_YEAR:
            errors["original_year"] = "invalid_year"
        clean["original_year"] = year

    adar_rule = merged.get("adar_rule") or None
    if adar_rule is not None and adar_rule not in ADAR_RULES:
        errors["adar_rule"] = "invalid_adar_rule"
    clean["adar_rule"] = adar_rule

    day30 = merged.get("day30_rule") or None
    if day30 is not None and day30 not in DAY30_RULES:
        errors["day30_rule"] = "invalid_day30_rule"
    clean["day30_rule"] = day30

    reminders = merged.get("reminder_days")
    if reminders in (None, ""):
        reminders = [1]
    if not isinstance(reminders, list):
        reminders = [reminders]
    parsed = [_int(x) for x in reminders]
    if any(r is None or not 0 <= r <= MAX_REMINDER_DAYS for r in parsed):
        errors["reminder_days"] = "invalid_reminder_days"
    clean["reminder_days"] = sorted({r for r in parsed if r is not None})

    notes = str(merged.get("notes") or "").strip()
    if len(notes) > MAX_NOTES_LENGTH:
        errors["notes"] = "invalid_notes"
    clean["notes"] = notes
    return clean, errors


class DateValidationError(Exception):
    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__(", ".join(f"{k}: {v}" for k, v in errors.items()))
        self.errors = errors


class FamilyStore:
    """`.storage/good_days.<entry_id>`.

    {"dates": [record], "reminders": {"since": iso, "sent": {key: day}, "acked": {key: day},
    "snoozes": [{"date_id", "day", "due"}]}}. Reminder keys carry their occurrence day so old
    ones can be pruned.
    """

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}")
        self.dates: list[dict[str, Any]] = []
        self.reminders: dict[str, Any] = {}
        self.ics: dict[str, Any] = {}  # {"token": str | None, "holidays": bool}

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.dates = [d for d in data.get("dates", []) if isinstance(d, dict) and d.get("id")]
        reminders = data.get("reminders") if isinstance(data.get("reminders"), dict) else {}
        self.reminders = {
            # First run: only reminders due from now on (no burst of old ones).
            "since": reminders.get("since") or dt_util.utcnow().isoformat(),
            "sent": dict(reminders.get("sent") or {}),
            "acked": dict(reminders.get("acked") or {}),
            "snoozes": list(reminders.get("snoozes") or []),
        }
        ics = data.get("ics") if isinstance(data.get("ics"), dict) else {}
        self.ics = {"token": ics.get("token") or None, "holidays": bool(ics.get("holidays"))}

    async def _async_save(self) -> None:
        await self._store.async_save({"dates": self.dates, "reminders": self.reminders, "ics": self.ics})

    async def async_save_reminders(self) -> None:
        await self._async_save()

    async def async_set_ics(self, token: str | None, holidays: bool) -> None:
        self.ics = {"token": token, "holidays": holidays}
        await self._async_save()

    def get(self, date_id: str) -> dict[str, Any] | None:
        return next((d for d in self.dates if d["id"] == date_id), None)

    async def async_add(self, data: dict[str, Any]) -> dict[str, Any]:
        if len(self.dates) >= MAX_DATES:
            raise DateValidationError({"base": "too_many_dates"})
        clean, errors = validate_date(data)
        if errors:
            raise DateValidationError(errors)
        record = {"id": uuid.uuid4().hex, **clean, "created_at": dt_util.utcnow().isoformat()}
        self.dates.append(record)
        await self._async_save()
        return record

    async def async_update(self, date_id: str, data: dict[str, Any]) -> dict[str, Any]:
        record = self.get(date_id)
        if record is None:
            raise DateValidationError({"id": "not_found"})
        clean, errors = validate_date(data, record)
        if errors:
            raise DateValidationError(errors)
        record.update(clean)
        await self._async_save()
        return record

    async def async_remove(self, date_id: str) -> None:
        if self.get(date_id) is None:
            raise DateValidationError({"id": "not_found"})
        self.dates = [d for d in self.dates if d["id"] != date_id]
        await self._async_save()


class TimerStore:
    """`.storage/good_days.timers.<entry_id>`: Shabbat timer rules and their run state."""

    HISTORY_MAX = 100

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store[dict[str, Any]] = Store(hass, STORAGE_VERSION, f"{DOMAIN}.timers.{entry_id}")
        self.rules: list[dict[str, Any]] = []
        self.profiles: list[str] = ["default"]
        self.active_profile = "default"
        self.enabled = True
        self.skip: list[str] = []  # period uids to skip
        self.done: dict[str, str] = {}  # planned action key -> period end iso (for pruning)
        self.history: list[dict[str, Any]] = []

    async def async_load(self) -> None:
        data = await self._store.async_load() or {}
        self.rules = [r for r in data.get("rules", []) if isinstance(r, dict) and r.get("id")]
        self.profiles = [p for p in data.get("profiles", []) if isinstance(p, str)] or ["default"]
        self.active_profile = data.get("active_profile") if data.get("active_profile") in self.profiles else self.profiles[0]
        self.enabled = bool(data.get("enabled", True))
        self.skip = list(data.get("skip") or [])
        self.done = dict(data.get("done") or {})
        self.history = list(data.get("history") or [])[-self.HISTORY_MAX :]

    async def async_save(self) -> None:
        await self._store.async_save(
            {
                "rules": self.rules,
                "profiles": self.profiles,
                "active_profile": self.active_profile,
                "enabled": self.enabled,
                "skip": self.skip,
                "done": self.done,
                "history": self.history[-self.HISTORY_MAX :],
            }
        )

    def get(self, rule_id: str) -> dict[str, Any] | None:
        return next((r for r in self.rules if r["id"] == rule_id), None)

    @staticmethod
    def new_id() -> str:
        return uuid.uuid4().hex

    def add_history(self, entry: dict[str, Any]) -> None:
        self.history.append(entry)
        del self.history[: -self.HISTORY_MAX]
