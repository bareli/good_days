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

SIGNAL_UPDATED = f"{DOMAIN}_updated_{{}}"

WS_UPCOMING = f"{DOMAIN}/upcoming"
WS_MAX_DAYS = 400
WS_MAX_LIMIT = 100
