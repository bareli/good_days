"""Shabbat Home timers: rule validation and expansion into exact actions. No HA imports."""
from __future__ import annotations

import datetime as dt
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo

from .const import MAX_NAME_LENGTH
from .engine import HolyEvent

ANCHOR_CANDLE = "candle_lighting"
ANCHOR_HAVDALAH = "havdalah"
ANCHOR_CLOCK = "clock"
ANCHORS = [ANCHOR_CANDLE, ANCHOR_HAVDALAH, ANCHOR_CLOCK]
ACTIONS = ["on", "off"]
KIND_SHABBAT, KIND_YOM_TOV, KIND_YOM_KIPPUR = "shabbat", "yom_tov", "yom_kippur"
KINDS = [KIND_SHABBAT, KIND_YOM_TOV, KIND_YOM_KIPPUR]
# Which days of a period a clock rule runs on.
DAYS_EACH, DAYS_FIRST, DAYS_LAST, DAYS_EREV = "each", "first", "last", "erev"
DAY_CHOICES = [DAYS_EACH, DAYS_FIRST, DAYS_LAST, DAYS_EREV]
MAX_OFFSET_MIN = 12 * 60
MAX_RULES = 200
MAX_PROFILES = 10
DEFAULT_PROFILE = "default"
CONFLICT_WINDOW = dt.timedelta(minutes=1)
TARGET_DOMAINS = {
    "switch", "light", "input_boolean", "fan", "climate", "water_heater", "media_player",
    "humidifier", "cover", "scene", "script", "automation", "siren", "vacuum", "valve", "lock",
}
RE_TIME = re.compile(r"^([01]?\d|2[0-3]):([0-5]\d)(:[0-5]\d)?$")
RE_ENTITY = re.compile(r"^[a-z_]+\.[a-z0-9_]+$")

# Presets fill the editor; everything stays editable.
PRESETS: dict[str, list[dict[str, Any]]] = {
    "hot_plate": [
        {"action": "on", "anchor": ANCHOR_CANDLE, "offset_min": -20, "applies_to": [KIND_SHABBAT, KIND_YOM_TOV]},
        {"action": "off", "anchor": ANCHOR_HAVDALAH, "offset_min": 30, "applies_to": [KIND_SHABBAT, KIND_YOM_TOV]},
    ],
    "urn": [
        {"action": "on", "anchor": ANCHOR_CANDLE, "offset_min": -30, "applies_to": [KIND_SHABBAT, KIND_YOM_TOV]},
        {"action": "off", "anchor": ANCHOR_HAVDALAH, "offset_min": 15, "applies_to": [KIND_SHABBAT, KIND_YOM_TOV]},
    ],
    "evening_lights": [
        {"action": "on", "anchor": ANCHOR_CANDLE, "offset_min": -10, "applies_to": KINDS},
        {"action": "off", "anchor": ANCHOR_CLOCK, "time": "23:00", "days": DAYS_EACH, "applies_to": KINDS},
    ],
    "morning_lights": [
        {"action": "on", "anchor": ANCHOR_CLOCK, "time": "07:00", "days": DAYS_EACH, "applies_to": KINDS},
        {"action": "off", "anchor": ANCHOR_CLOCK, "time": "09:30", "days": DAYS_EACH, "applies_to": KINDS},
    ],
    "air_conditioner": [
        {"action": "on", "anchor": ANCHOR_CANDLE, "offset_min": -15, "applies_to": KINDS},
        {"action": "off", "anchor": ANCHOR_HAVDALAH, "offset_min": 5, "applies_to": KINDS},
    ],
}


def _int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return int(number) if number == int(number) else None


def validate_rule(
    data: dict[str, Any],
    existing: dict[str, Any] | None = None,
    known_entities: set[str] | None = None,
    profiles: Iterable[str] = (DEFAULT_PROFILE,),
) -> tuple[dict[str, Any], dict[str, str]]:
    """Clean a timer rule (full, or a patch over `existing`); errors keyed by field.

    Conditions are only shape-checked here; the manager validates them with Home Assistant.
    """
    merged = {**(existing or {}), **data}
    errors: dict[str, str] = {}
    clean: dict[str, Any] = {}

    name = str(merged.get("name") or "").strip()
    if not name or len(name) > MAX_NAME_LENGTH:
        errors["name"] = "invalid_name"
    clean["name"] = name

    targets = merged.get("targets") or []
    if isinstance(targets, str):
        targets = [targets]
    targets = list(dict.fromkeys(str(t).strip() for t in targets if str(t).strip()))
    if not targets or any(
        not RE_ENTITY.match(t) or t.split(".")[0] not in TARGET_DOMAINS for t in targets
    ):
        errors["targets"] = "invalid_targets"
    elif known_entities is not None and any(t not in known_entities for t in targets):
        errors["targets"] = "unknown_targets"
    clean["targets"] = targets

    action = merged.get("action")
    if action not in ACTIONS:
        errors["action"] = "invalid_action"
    clean["action"] = action

    anchor = merged.get("anchor")
    if anchor not in ANCHORS:
        errors["anchor"] = "invalid_anchor"
    clean["anchor"] = anchor

    if anchor == ANCHOR_CLOCK:
        match = RE_TIME.match(str(merged.get("time") or ""))
        if not match:
            errors["time"] = "invalid_time"
            clean["time"] = None
        else:
            clean["time"] = f"{int(match.group(1)):02d}:{match.group(2)}"
        days = merged.get("days") or DAYS_EACH
        if days not in DAY_CHOICES:
            errors["days"] = "invalid_days"
        clean["days"] = days
        clean["offset_min"] = 0
    else:
        offset = _int(merged.get("offset_min", 0))
        if offset is None or not -MAX_OFFSET_MIN <= offset <= MAX_OFFSET_MIN:
            errors["offset_min"] = "invalid_offset"
        clean["offset_min"] = offset
        clean["time"] = None
        clean["days"] = DAYS_EACH

    applies = merged.get("applies_to") or []
    if isinstance(applies, str):
        applies = [applies]
    if not applies or any(a not in KINDS for a in applies):
        errors["applies_to"] = "invalid_applies_to"
    clean["applies_to"] = [k for k in KINDS if k in applies]

    profile = merged.get("profile") or DEFAULT_PROFILE
    if profile not in set(profiles):
        errors["profile"] = "invalid_profile"
    clean["profile"] = profile

    conditions = merged.get("conditions") or []
    if not isinstance(conditions, list) or any(not isinstance(c, dict) for c in conditions):
        errors["conditions"] = "invalid_conditions"
        conditions = []
    clean["conditions"] = conditions
    clean["enabled"] = bool(merged.get("enabled", True))
    return clean, errors


def period_kinds(period: HolyEvent) -> set[str]:
    kinds = set()
    if "shabbat" in period.keys:
        kinds.add(KIND_SHABBAT)
    if "yom_kippur" in period.keys:
        kinds.add(KIND_YOM_KIPPUR)
    if any(k not in ("shabbat", "yom_kippur") for k in period.keys):
        kinds.add(KIND_YOM_TOV)
    return kinds


@dataclass(frozen=True)
class PlannedAction:
    key: str  # "<rule_id>:<period uid>:<iso time>", stable for dedupe
    rule_id: str
    rule_name: str
    period_uid: str
    when: dt.datetime
    action: str
    targets: tuple[str, ...]
    outside: bool  # before candle lighting or after havdalah (allowed, shown in the preview)


def _clock_days(period: HolyEvent, days: str) -> list[dt.date]:
    holy = [period.first_day + dt.timedelta(days=i) for i in range(period.days)]
    if days == DAYS_FIRST:
        return holy[:1]
    if days == DAYS_LAST:
        return holy[-1:]
    if days == DAYS_EREV:
        return [period.first_day - dt.timedelta(days=1)]
    return holy


def expand(
    rules: Iterable[dict[str, Any]], periods: Iterable[HolyEvent], time_zone: str, profile: str
) -> list[PlannedAction]:
    """Exact actions of the enabled rules of `profile` for the given Shabbat / Yom Tov periods."""
    tz = ZoneInfo(time_zone)
    planned: list[PlannedAction] = []
    for period in periods:
        if not period.period or period.all_day:  # no times (polar fallback)
            continue
        kinds = period_kinds(period)
        for rule in rules:
            if not rule.get("enabled", True) or rule.get("profile", DEFAULT_PROFILE) != profile:
                continue
            if not kinds & set(rule.get("applies_to") or []):
                continue
            times: list[dt.datetime] = []
            if rule["anchor"] == ANCHOR_CANDLE:
                times.append(period.start + dt.timedelta(minutes=rule.get("offset_min") or 0))
            elif rule["anchor"] == ANCHOR_HAVDALAH:
                times.append(period.end + dt.timedelta(minutes=rule.get("offset_min") or 0))
            else:
                at = dt.time(*(int(x) for x in rule["time"].split(":")))
                # Holy day D begins the evening before: a time later than candle lighting
                # (23:00) is that evening, D - 1; earlier times (07:00, 13:00, 00:30) are on D.
                evening_from = period.start.astimezone(tz).time()
                for day in _clock_days(period, rule.get("days") or DAYS_EACH):
                    if rule.get("days") != DAYS_EREV and at >= evening_from:
                        day -= dt.timedelta(days=1)
                    times.append(dt.datetime.combine(day, at, tz))
            for when in times:
                planned.append(
                    PlannedAction(
                        key=f"{rule['id']}:{period.uid}:{when.isoformat()}",
                        rule_id=rule["id"],
                        rule_name=rule.get("name", ""),
                        period_uid=period.uid,
                        when=when,
                        action=rule["action"],
                        targets=tuple(rule["targets"]),
                        outside=not period.start <= when < period.end,
                    )
                )
    planned.sort(key=lambda p: (p.when, p.rule_name, p.key))
    return planned


def conflicts(planned: list[PlannedAction]) -> list[dict[str, Any]]:
    """Same target, opposite actions within a minute: reported, never resolved."""
    found = []
    for i, first in enumerate(planned):
        for second in planned[i + 1 :]:
            if second.when - first.when > CONFLICT_WINDOW:
                break
            if first.action == second.action:
                continue
            for target in set(first.targets) & set(second.targets):
                found.append(
                    {
                        "target": target,
                        "when": first.when.isoformat(),
                        "rules": [first.rule_id, second.rule_id],
                    }
                )
    return found
