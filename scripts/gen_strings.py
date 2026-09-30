"""Generate strings.json, translations/en.json and translations/he.json from one table.

Run from the repo root: python scripts/gen_strings.py
"""
import json
import os

ROOT = os.path.join(os.path.dirname(__file__), "..", "custom_components", "good_days")

# key -> (en, he)
FIELDS = {
    "location": ("Location (for candle lighting and havdalah times)", "מיקום (לזמני הדלקת נרות והבדלה)"),
    "diaspora": ("Diaspora (two-day Yom Tov)", "חוץ לארץ (יום טוב שני)"),
    "candle_lighting_minutes": ("Candle lighting, minutes before sunset", "הדלקת נרות, דקות לפני השקיעה"),
    "havdalah_minutes": ("Havdalah, minutes after sunset (0 = three stars)", "הבדלה, דקות אחרי השקיעה (0 = צאת הכוכבים)"),
    "language": ("Event names language", "שפת שמות האירועים"),
    "categories": ("Show on the calendar", "להציג בלוח השנה"),
    "lookahead_days": ("Days to compute ahead", "מספר ימים לחישוב מראש"),
    "notify_targets": ("Send family-date reminders to", "לשלוח תזכורות לתאריכים משפחתיים אל"),
    "reminder_time": ("Reminder time", "שעת התזכורת"),
    "quiet_on_shabbat": ("No reminders during Shabbat and Yom Tov", "לא לשלוח תזכורות בשבת ובחג"),
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
    "notify_targets": (
        "Notify services, e.g. mobile_app_my_phone. Phones get Got it / Remind me tomorrow buttons. Empty: only the good_days_reminder event.",
        "שירותי התראה, למשל mobile_app_my_phone. בטלפון יופיעו כפתורי הבנתי / תזכירו לי מחר. ריק: רק האירוע good_days_reminder.",
    ),
    "quiet_on_shabbat": (
        "A reminder due on Shabbat or Yom Tov is sent an hour before candle lighting.",
        "תזכורת שחלה בשבת או בחג תישלח שעה לפני הדלקת הנרות.",
    ),
}
USER_FIELDS = ["location", "diaspora", "candle_lighting_minutes", "havdalah_minutes", "language"]
OPTION_FIELDS = USER_FIELDS + ["categories", "lookahead_days", "notify_targets", "reminder_time", "quiet_on_shabbat"]

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
    "invalid_minutes": ("Minutes must be a whole number between 0 and 120.", "מספר הדקות חייב להיות מספר שלם בין 0 ל-120."),
    "invalid_language": ("Pick a language from the list.", "יש לבחור שפה מהרשימה."),
    "no_categories": ("Pick at least one category.", "יש לבחור לפחות קטגוריה אחת."),
    "invalid_lookahead": ("Days ahead must be a whole number between 30 and 730.", "מספר הימים חייב להיות מספר שלם בין 30 ל-730."),
    "invalid_notify": ("Pick existing notify services (Developer tools → Actions → notify.*).", "יש לבחור שירותי התראה קיימים (כלי מפתחים ← פעולות ← notify.*)."),
    "invalid_time": ("Enter a time as HH:MM.", "יש להזין שעה בפורמט HH:MM."),
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
    "kind": {
        "birthday": ("Birthday", "יום הולדת"),
        "yahrzeit": ("Yahrzeit", "יום השנה (יארצייט)"),
        "anniversary": ("Anniversary", "יום נישואין"),
        "custom": ("Other", "אחר"),
    },
    "hebrew_month": {
        "tishrei": ("Tishrei", "תשרי"),
        "marcheshvan": ("Cheshvan", "חשוון"),
        "kislev": ("Kislev", "כסלו"),
        "tevet": ("Tevet", "טבת"),
        "shvat": ("Shvat", "שבט"),
        "adar": ("Adar (plain year)", "אדר (שנה פשוטה)"),
        "adar_i": ("Adar I", "אדר א׳"),
        "adar_ii": ("Adar II", "אדר ב׳"),
        "nisan": ("Nisan", "ניסן"),
        "iyyar": ("Iyar", "אייר"),
        "sivan": ("Sivan", "סיוון"),
        "tammuz": ("Tammuz", "תמוז"),
        "av": ("Av", "אב"),
        "elul": ("Elul", "אלול"),
    },
    "adar_rule": {
        "adar_i": ("Adar I", "אדר א׳"),
        "adar_ii": ("Adar II", "אדר ב׳"),
        "both": ("Both", "שניהם"),
    },
    "day30_rule": {
        "next": ("1st of the next month", "א׳ בחודש הבא"),
        "29": ("29th of the same month", "כ״ט באותו חודש"),
    },
}
ENTITY = {
    "calendar": {
        "holidays": ("Holidays", "חגים"),
        "family": ("Family", "משפחה"),
    },
    "sensor": {
        "next_shabbat": ("Next Shabbat", "השבת הבאה"),
        "next_holiday": ("Next holiday", "החג הבא"),
        "next_family": ("Next family date", "התאריך המשפחתי הבא"),
        "next_candle_lighting": ("Next candle lighting", "הדלקת הנרות הבאה"),
        "next_timer_action": ("Next timer action", "הפעולה הבאה של הטיימרים"),
    },
    "binary_sensor": {"holiday_today": ("Holiday today", "חג היום")},
    "switch": {
        "shabbat_timers": ("Shabbat timers", "טיימרים לשבת"),
        "skip_next": ("Skip next Shabbat or Chag", "דילוג על השבת או החג הבא"),
    },
    "select": {"timer_profile": ("Timer profile", "פרופיל טיימרים")},
}

# service -> (name, description), fields -> (name, description)
SERVICE_FIELDS = {
    "date_id": (("Date ID", "מזהה תאריך"), ("ID from list_dates.", "המזהה מ-list_dates.")),
    "name": (("Name", "שם"), ("Who the date is for.", "של מי התאריך.")),
    "kind": (("Kind", "סוג"), ("Birthday, yahrzeit, anniversary or other.", "יום הולדת, יום השנה, יום נישואין או אחר.")),
    "hebrew_day": (("Hebrew day", "יום בחודש העברי"), ("1-30.", "1-30.")),
    "hebrew_month": (("Hebrew month", "חודש עברי"), ("Adar = Adar of a plain year.", "אדר = אדר של שנה פשוטה.")),
    "original_year": (("Hebrew year", "שנה עברית"), ("Year of birth / passing / wedding, e.g. 5745. Shows age or count.", "שנת הלידה / הפטירה / החתונה, למשל 5745. מציג גיל או מספר שנים.")),
    "gregorian_date": (("Gregorian date", "תאריך לועזי"), ("Instead of the Hebrew date: converted for you.", "במקום התאריך העברי: יומר אוטומטית.")),
    "after_sunset": (("After sunset", "אחרי השקיעה"), ("The Gregorian date was after sunset (next Hebrew day).", "התאריך הלועזי היה אחרי השקיעה (היום העברי הבא).")),
    "adar_rule": (("Adar in a leap year", "אדר בשנה מעוברת"), ("For a date in plain Adar. Default: birthdays Adar II, yahrzeits Adar I.", "לתאריך באדר של שנה פשוטה. ברירת מחדל: יום הולדת באדר ב׳, יום השנה באדר א׳.")),
    "day30_rule": (("Missing 30th day", "כשאין יום ל׳"), ("For 30 Cheshvan / Kislev in a short year. Default: 1st of the next month.", "ל׳ חשוון / כסלו בשנה חסרה. ברירת מחדל: א׳ בחודש הבא.")),
    "reminder_days": (("Reminder days", "ימי תזכורת"), ("Days before to remind (used from v0.3).", "כמה ימים לפני להזכיר (מגרסה 0.3).")),
    "notes": (("Notes", "הערות"), ("Free text.", "טקסט חופשי.")),
    "entry_id": (("Good Days instance", "מופע ימים טובים"), ("Default: the first one.", "ברירת מחדל: הראשון.")),
}
DATE_FIELDS = ["name", "kind", "hebrew_day", "hebrew_month", "original_year", "gregorian_date",
               "after_sunset", "adar_rule", "day30_rule", "reminder_days", "notes", "entry_id"]
SERVICES = {
    "add_date": (("Add family date", "הוספת תאריך משפחתי"),
                 ("Add a birthday, yahrzeit or anniversary that repeats by Hebrew date.",
                  "הוספת יום הולדת, יום השנה או יום נישואין שחוזר לפי התאריך העברי."),
                 DATE_FIELDS),
    "update_date": (("Update family date", "עדכון תאריך משפחתי"),
                    ("Change fields of a family date.", "שינוי שדות של תאריך משפחתי."),
                    ["date_id", *DATE_FIELDS]),
    "remove_date": (("Remove family date", "מחיקת תאריך משפחתי"),
                    ("Delete a family date.", "מחיקת תאריך משפחתי."),
                    ["date_id", "entry_id"]),
    "list_dates": (("List family dates", "רשימת תאריכים משפחתיים"),
                   ("Return all family dates with their next occurrence.", "החזרת כל התאריכים המשפחתיים עם המועד הבא."),
                   ["entry_id"]),
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
        "services": {
            service: {
                "name": name[i],
                "description": description[i],
                "fields": {
                    f: {"name": SERVICE_FIELDS[f][0][i], "description": SERVICE_FIELDS[f][1][i]}
                    for f in fields_
                },
            }
            for service, (name, description, fields_) in SERVICES.items()
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
