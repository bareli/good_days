"""Constants for Good Days. No Home Assistant imports (engine.py uses them too)."""
from __future__ import annotations

DOMAIN = "good_days"

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_LOCATION = "location"
CONF_ELEVATION = "elevation"
CONF_DIASPORA = "diaspora"
CONF_CANDLE_LIGHTING = "candle_lighting_minutes"
CONF_HAVDALAH = "havdalah_minutes"
CONF_LANGUAGE = "language"
CONF_CATEGORIES = "categories"
CONF_LOOKAHEAD_DAYS = "lookahead_days"

LANG_AUTO = "auto"
LANGUAGES = [LANG_AUTO, "he", "en"]

DEFAULT_CANDLE_LIGHTING = 18
DEFAULT_HAVDALAH = 0  # 0 = tzeit hakochavim (three stars)
DEFAULT_LOOKAHEAD_DAYS = 400
MIN_LOOKAHEAD_DAYS = 30
MAX_LOOKAHEAD_DAYS = 730
MAX_OFFSET_MINUTES = 120

CAT_SHABBAT = "shabbat"
CAT_YOM_TOV = "yom_tov"
CAT_CHOL_HAMOED = "chol_hamoed"
CAT_MINOR = "minor"
CAT_FAST = "fast"
CAT_ROSH_CHODESH = "rosh_chodesh"
CAT_MODERN = "modern"
CAT_MEMORIAL = "memorial"
CAT_EREV = "erev"

CATEGORIES = [
    CAT_SHABBAT, CAT_YOM_TOV, CAT_CHOL_HAMOED, CAT_MINOR, CAT_FAST,
    CAT_ROSH_CHODESH, CAT_MODERN, CAT_MEMORIAL, CAT_EREV,
]
DEFAULT_CATEGORIES = [
    CAT_SHABBAT, CAT_YOM_TOV, CAT_CHOL_HAMOED, CAT_MINOR, CAT_FAST, CAT_MODERN,
]
# Not "holidays" for the next-holiday sensor and the holiday-today binary sensor.
NON_HOLIDAY_CATEGORIES = {CAT_SHABBAT, CAT_ROSH_CHODESH, CAT_EREV}

SOURCE_HOLIDAYS = "holidays"
SOURCE_FAMILY = "family"
CAT_FAMILY = "family"

# Family (Hebrew-date) dates, v0.2
KIND_BIRTHDAY = "birthday"
KIND_YAHRZEIT = "yahrzeit"
KIND_ANNIVERSARY = "anniversary"
KIND_CUSTOM = "custom"
KINDS = [KIND_BIRTHDAY, KIND_YAHRZEIT, KIND_ANNIVERSARY, KIND_CUSTOM]

# hdate Months keys, calendar order.
HEBREW_MONTHS = [
    "tishrei", "marcheshvan", "kislev", "tevet", "shvat", "adar", "adar_i", "adar_ii",
    "nisan", "iyyar", "sivan", "tammuz", "av", "elul",
]
# Months that never have a 30th day ("adar" = Adar of a plain year).
MONTHS_29 = {"tevet", "adar", "adar_ii", "iyyar", "tammuz", "elul"}

ADAR_I = "adar_i"
ADAR_II = "adar_ii"
ADAR_BOTH = "both"
ADAR_RULES = [ADAR_I, ADAR_II, ADAR_BOTH]
# Provisional customs (SPEC §11.5), configurable per date: birthdays of plain Adar in
# Adar II, yahrzeits of plain Adar in Adar I (Rema).
DEFAULT_ADAR_RULE = {KIND_YAHRZEIT: ADAR_I}
DEFAULT_ADAR_RULE_OTHER = ADAR_II

DAY30_NEXT = "next"  # 1st of the next month
DAY30_29 = "29"
DAY30_RULES = [DAY30_NEXT, DAY30_29]

MAX_NAME_LENGTH = 100
MAX_NOTES_LENGTH = 500
MAX_DATES = 500
MIN_HEBREW_YEAR, MAX_HEBREW_YEAR = 3000, 6500
MAX_REMINDER_DAYS = 60

SIGNAL_UPDATED = f"{DOMAIN}_updated_{{}}"

WS_UPCOMING = f"{DOMAIN}/upcoming"
WS_MAX_DAYS = 400
WS_MAX_LIMIT = 100
