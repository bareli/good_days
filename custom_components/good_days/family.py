"""Family dates recurring by Hebrew date (birthdays, yahrzeits, anniversaries). No HA imports."""
from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any
from zoneinfo import ZoneInfo

from hdate import HebrewDate, Zmanim
from hdate.hebrew_date import Months, is_leap_year

from .const import (
    ADAR_BOTH,
    ADAR_I,
    ADAR_II,
    CAT_FAMILY,
    DAY30_29,
    DEFAULT_ADAR_RULE,
    DEFAULT_ADAR_RULE_OTHER,
    KIND_ANNIVERSARY,
    KIND_BIRTHDAY,
    KIND_YAHRZEIT,
)
from .engine import EngineSettings, _midnight, hebrew_date, make_location

ONE_DAY = dt.timedelta(days=1)
ADAR_KEYS = {"adar", ADAR_I, ADAR_II}

KIND_TEXT = {
    KIND_BIRTHDAY: ("Birthday", "יום הולדת"),
    KIND_YAHRZEIT: ("Yahrzeit", "יום השנה"),
    KIND_ANNIVERSARY: ("Anniversary", "יום נישואין"),
}


def adar_rule_of(record: dict[str, Any]) -> str:
    return record.get("adar_rule") or DEFAULT_ADAR_RULE.get(record.get("kind"), DEFAULT_ADAR_RULE_OTHER)


def _months_in_year(month_key: str, year: int, adar_rule: str) -> list[Months]:
    if month_key not in ADAR_KEYS:
        return [Months[month_key.upper()]]
    if not is_leap_year(year):
        return [Months.ADAR]
    if month_key == ADAR_I:
        return [Months.ADAR_I]
    if month_key == ADAR_II:
        return [Months.ADAR_II]
    return {ADAR_I: [Months.ADAR_I], ADAR_II: [Months.ADAR_II], ADAR_BOTH: [Months.ADAR_I, Months.ADAR_II]}[adar_rule]


def occurrences_in_year(record: dict[str, Any], year: int) -> list[dt.date]:
    """Gregorian dates of the record in Hebrew year `year` (two when Adar rule is 'both')."""
    day = int(record["hebrew_day"])
    result = []
    for month in _months_in_year(record["hebrew_month"], year, adar_rule_of(record)):
        this_day, this_month = day, month
        if day > month.days(year):
            # 30 Cheshvan / Kislev in a short year, or 30 Adar I in a plain year.
            if record.get("day30_rule") == DAY30_29:
                this_day = month.days(year)
            else:
                this_day, this_month = 1, month.next_month(year)
        result.append(HebrewDate(year, this_month, this_day).to_gdate())
    return result


def hebrew_from_gregorian(day: dt.date, after_sunset: bool = False) -> dict[str, Any]:
    """Hebrew date of a Gregorian day (the next day's date after sunset)."""
    hd = HebrewDate.from_gdate(day + ONE_DAY if after_sunset else day)
    return {
        "hebrew_day": hd.day,
        "hebrew_month": hd.month.name.lower(),
        "hebrew_year": hd.year,
        "leap_year": is_leap_year(hd.year),
    }


@dataclass(frozen=True)
class FamilyEvent:
    """One yearly occurrence of a family date."""

    uid: str
    date_id: str
    name: str
    kind: str
    first_day: dt.date  # the Hebrew date's Gregorian day
    start: dt.datetime
    end: dt.datetime
    all_day: bool
    years: int | None  # age / anniversary count, when the original year is known
    notes: str = ""
    category: str = CAT_FAMILY
    period: bool = False
    days: int = 1
    candle_lighting: dt.datetime | None = None
    havdalah: dt.datetime | None = None

    @property
    def last_day(self) -> dt.date:
        return self.first_day

    def overlaps(self, start: dt.datetime, end: dt.datetime) -> bool:
        return self.start < end and self.end > start

    def covers_day(self, day: dt.date) -> bool:
        return day == self.first_day

    def title(self, lang: str) -> str:
        he = lang == "he"
        n = self.years
        if self.kind == KIND_BIRTHDAY:
            if he:
                return f"יום הולדת {n} ל{self.name}" if n else f"יום הולדת ל{self.name}"
            return f"{self.name}'s birthday ({n})" if n else f"{self.name}'s birthday"
        if self.kind in KIND_TEXT:
            label = KIND_TEXT[self.kind][1 if he else 0]
            suffix = f" ({n})" if n else ""
            return f"{label}: {self.name}{suffix}"
        return self.name

    def description(self, lang: str) -> str:
        parts = [hebrew_date(self.first_day, lang)]
        if self.notes:
            parts.append(self.notes)
        return "\n".join(parts)


def compute_family(
    records: Iterable[dict[str, Any]], settings: EngineSettings, start: dt.date, end: dt.date
) -> list[FamilyEvent]:
    """Occurrences of all records overlapping the local days start..end, sorted by start."""
    tz = ZoneInfo(settings.time_zone)
    location = None
    first_year = HebrewDate.from_gdate(start - ONE_DAY).year
    last_year = HebrewDate.from_gdate(end + ONE_DAY).year
    lo, hi = _midnight(start, tz), _midnight(end + ONE_DAY, tz)
    events: list[FamilyEvent] = []
    for record in records:
        original = record.get("original_year")
        for year in range(first_year, last_year + 1):
            for day in occurrences_in_year(record, year):
                years = year - int(original) if original else None
                if years is not None and (years < 0 or (years == 0 and record["kind"] == KIND_YAHRZEIT)):
                    continue
                if record["kind"] == KIND_YAHRZEIT:
                    # Observed from the evening before: sunset to sunset.
                    location = location or make_location(settings)
                    try:
                        begin = _sunset(day - ONE_DAY, settings, location)
                        finish = _sunset(day, settings, location)
                        all_day = False
                    except (ValueError, ArithmeticError):
                        begin, finish, all_day = _midnight(day, tz), _midnight(day + ONE_DAY, tz), True
                else:
                    begin, finish, all_day = _midnight(day, tz), _midnight(day + ONE_DAY, tz), True
                event = FamilyEvent(
                    uid=f"family-{record['id']}-{day.isoformat()}",
                    date_id=record["id"],
                    name=record["name"],
                    kind=record["kind"],
                    first_day=day,
                    start=begin,
                    end=finish,
                    all_day=all_day,
                    years=years or None,
                    notes=record.get("notes") or "",
                )
                if event.overlaps(lo, hi):
                    events.append(event)
    events.sort(key=lambda e: (e.start, e.name, e.uid))
    return events


def _sunset(day: dt.date, settings: EngineSettings, location) -> dt.datetime:
    return Zmanim(date=day, location=location).shkia.local


def next_occurrence(
    record: dict[str, Any], settings: EngineSettings, now: dt.datetime
) -> FamilyEvent | None:
    """Current or next occurrence (searches about 14 months ahead)."""
    today = now.astimezone(ZoneInfo(settings.time_zone)).date()
    events = compute_family([record], settings, today - ONE_DAY, today + dt.timedelta(days=420))
    return next((e for e in events if e.end > now), None)
