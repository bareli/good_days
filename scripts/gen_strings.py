"""Generate strings.json, translations/en.json and translations/he.json from one table.

Run from the repo root: python scripts/gen_strings.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "custom_components", "good_days")

# key -> (en, he)
FIELDS = {
    "location": ("Location (for candle lighting and havdalah times)", "מיקום (לזמני הדלקת נרות והבדלה)"),
    "elevation": ("Elevation", "גובה"),
    "diaspora": ("Diaspora (two-day Yom Tov)", "חוץ לארץ (יום טוב שני)"),
    "candle_lighting_minutes": ("Candle lighting, minutes before sunset", "הדלקת נרות, דקות לפני השקיעה"),
    "havdalah_minutes": ("Havdalah, minutes after sunset (0 = three stars)", "הבדלה, דקות אחרי השקיעה (0 = צאת הכוכבים)"),
    "language": ("Event names language", "שפת שמות האירועים"),
    "categories": ("Show on the calendar", "להציג בלוח השנה"),
    "lookahead_days": ("Days to compute ahead", "מספר ימים לחישוב מראש"),
}
DESCRIPTIONS = {
    "candle_lighting_minutes": (
        "Most of Israel: 18-30. Jerusalem: 40. Haifa: 30.",
        "ברוב הארץ: 18-30. ירושלים: 40. חיפה: 30.",
    ),
    "diaspora": (
        "Off in Israel. On outside Israel.",
        "כבוי בארץ ישראל. מופעל בחוץ לארץ.",
    ),
}
USER_FIELDS = ["location", "elevation", "diaspora", "candle_lighting_minutes", "havdalah_minutes", "language"]
OPTION_FIELDS = USER_FIELDS + ["categories", "lookahead_days"]

TEXT = {
    "user_title": ("Good Days", "ימים טובים"),
    "user_desc": (
        "Defaults were taken from {source}. You can change everything later in the options.",
        "ערכי ברירת המחדל נלקחו מ-{source}. אפשר לשנות הכול אחר כך באפשרויות.",
    ),
    "options_title": ("Good Days options", "אפשרויות ימים טובים"),
}
ERRORS = {
    "invalid_location": ("Pick a valid location.", "יש לבחור מיקום תקין."),
    "invalid_elevation": ("Elevation must be a whole number between -500 and 9000 m.", "הגובה חייב להיות מספר שלם בין ⁦-500⁩ ל-9000 מ׳."),
    "invalid_minutes": ("Minutes must be a whole number between 0 and 120.", "מספר הדקות חייב להיות מספר שלם בין 0 ל-120."),
    "invalid_language": ("Pick a language from the list.", "יש לבחור שפה מהרשימה."),
    "no_categories": ("Pick at least one category.", "יש לבחור לפחות קטגוריה אחת."),
    "invalid_lookahead": ("Days ahead must be a whole number between 30 and 730.", "מספר הימים חייב להיות מספר שלם בין 30 ל-730."),
}
SELECTORS = {
    "language": {
        "auto": ("Same as Home Assistant", "כמו Home Assistant"),
        "he": ("Hebrew", "עברית"),
        "en": ("English", "אנגלית"),
    },
    "category": {
        "shabbat": ("Shabbat", "שבת"),
        "yom_tov": ("Yom Tov", "יום טוב"),
        "chol_hamoed": ("Chol HaMoed", "חול המועד"),
        "minor": ("Minor holidays (Chanukah, Purim, Tu BiShvat...)", "חגים קטנים (חנוכה, פורים, ט״ו בשבט...)"),
        "fast": ("Fast days", "צומות"),
        "rosh_chodesh": ("Rosh Chodesh", "ראש חודש"),
        "modern": ("Israeli national days (Yom HaAtzmaut, Yom HaZikaron...)", "ימים לאומיים (יום העצמאות, יום הזיכרון...)"),
        "memorial": ("Other memorial and national days", "ימי זיכרון וימים לאומיים נוספים"),
        "erev": ("Erev Yom Tov days", "ערבי חג"),
    },
}
ENTITY = {
    "calendar": {"holidays": ("Holidays", "חגים")},
    "sensor": {
        "next_shabbat": ("Next Shabbat", "השבת הבאה"),
        "next_holiday": ("Next holiday", "החג הבא"),
    },
    "binary_sensor": {"holiday_today": ("Holiday today", "חג היום")},
}


def build(i: int) -> dict:
    def fields(keys: list[str]) -> dict:
        return {k: FIELDS[k][i] for k in keys}

    def descriptions(keys: list[str]) -> dict:
        return {k: DESCRIPTIONS[k][i] for k in keys if k in DESCRIPTIONS}

    errors = {k: v[i] for k, v in ERRORS.items()}
    return {
        "config": {
            "step": {
                "user": {
                    "title": TEXT["user_title"][i],
                    "description": TEXT["user_desc"][i],
                    "data": fields(USER_FIELDS),
                    "data_description": descriptions(USER_FIELDS),
                }
            },
            "error": errors,
        },
        "options": {
            "step": {
                "init": {
                    "title": TEXT["options_title"][i],
                    "data": fields(OPTION_FIELDS),
                    "data_description": descriptions(OPTION_FIELDS),
                }
            },
            "error": errors,
        },
        "selector": {
            name: {"options": {k: v[i] for k, v in opts.items()}} for name, opts in SELECTORS.items()
        },
        "entity": {
            platform: {key: {"name": names[i]} for key, names in items.items()}
            for platform, items in ENTITY.items()
        },
    }


def write(path: str, data: dict) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


if __name__ == "__main__":
    en, he = build(0), build(1)
    os.makedirs(os.path.join(ROOT, "translations"), exist_ok=True)
    write(os.path.join(ROOT, "strings.json"), en)
    write(os.path.join(ROOT, "translations", "en.json"), en)
    write(os.path.join(ROOT, "translations", "he.json"), he)
