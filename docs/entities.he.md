# ישויות ואוטומציות

## ישויות

| ישות | מה היא |
|---|---|
| `calendar.good_days_holidays` | שבתות, ימים טובים, חול המועד, צומות, ימים קלים ולאומיים (הקטגוריות לפי האפשרויות). אירועי שבת ויום טוב נמשכים מהדלקת נרות עד הבדלה; יום טוב ושבת צמודים הם אירוע אחד. צומות נמשכים מעלות השחר (תשעה באב: משקיעה) עד צאת הכוכבים. השאר הם אירועי יום שלם. |
| `sensor.good_days_next_shabbat` | הדלקת הנרות של השבת הנוכחית או הבאה (חותמת זמן). מאפיינים: `havdalah`, `parasha`, `special_shabbat`, `haftarah`, `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `sensor.good_days_next_candle_lighting` | הדלקת הנרות של השבת **או היום טוב** הנוכחי או הבא (חותמת זמן), בלי קשר לאירועי יום שלם סביבו. מאפיינים: `havdalah`, `title`, `category`, `days_until`, `in_effect`. הכי מתאים לאוטומציות. |
| `sensor.good_days_next_holiday` | שם החג הנוכחי או הבא (לא שבת רגילה ולא ראש חודש). מאפיינים: `start`, `end`, `category`, `days_until`, `candle_lighting`, `havdalah`, `hebrew_date`. |
| `binary_sensor.good_days_holiday_today` | דלוק ביום חג. מאפיין `holidays`. |
| `sensor.good_days_next_fast` | תחילת הצום הנוכחי או הבא, כולל יום כיפור (חותמת זמן). מאפיינים: `end`, `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `binary_sensor.good_days_fasting` | דלוק מתחילת הצום עד סופו (גם ביום כיפור). מאפיינים `title`, `end`. |
| `sensor.good_days_omer` | היום בעומר (1 עד 49), מתחלף בצאת הכוכבים; לא ידוע מחוץ לעומר. מאפיינים: `weeks`, `days`, `text` (נוסח הספירה), `next_count`, `counted`. |
| `calendar.good_days_family` | תאריכים משפחתיים. ימי הולדת וימי נישואין הם אירועי יום שלם; יארצייט נמשך משקיעה בערב שלפניו עד השקיעה. |
| `sensor.good_days_next_family_date` | כותרת התאריך המשפחתי הנוכחי או הבא. מאפיינים: `name`, `kind`, `years`, `start`, `days_until`, `hebrew_date`, `conflicts_shabbat`. |
| `switch.good_days_shabbat_timers` | טיימרים לשבת פועלים או כבויים (הכללים נשמרים). |
| `switch.good_days_skip_next_shabbat_or_chag` | מדלג על הטיימרים של השבת או החג הנוכחי או הבא בלבד; מתאפס מעצמו. |
| `select.good_days_timer_profile` | פרופיל הטיימרים הפעיל. |
| `sensor.good_days_next_timer_action` | מתי הטיימר הבא יפעל; מאפיינים `rule`, `action`, `targets`. |

המאפיין `special_shabbat` נראה כך: `["Shekalim", "Mevarchim Chodesh Adar"]`. שבתות מיוחדות (שקלים, זכור, פרה, החודש, הגדול, שובה, חזון, נחמו, שירה, ראש חודש, חנוכה, חול המועד) מופיעות בכותרת; מברכים החודש ושבת מחר חודש מופיעים בפרטים.

!!! note "סימני כיווניות בשמות"
    שמות בעברית בתוך כותרות באנגלית עטופים בסימני כיווניות בלתי נראים. לכן גם מצב כמו `sensor.good_days_next_family_date` מכיל אותם; אוטומציה שמשווה אותו למחרוזת רגילה צריכה להסיר אותם.

## דוגמה: תאורת כניסה לפני הדלקת נרות

```yaml
triggers:
  - trigger: calendar
    event: start
    entity_id: calendar.good_days_holidays
    offset: "-0:10:0"
conditions:
  - condition: template
    value_template: "{{ not trigger.calendar_event.all_day }}"
actions:
  - action: light.turn_on
    target:
      entity_id: light.porch
```

## שירותים

`good_days.add_date`, `good_days.update_date`, `good_days.remove_date`, `good_days.list_dates`. ראו [שימוש](usage.md#services).

## אירועים { #events }

- `good_days_reminder`, נשלח עם כל תזכורת, גם בלי יעדי notify. נתונים: `name, kind, day, years, title, message, date_id, entry_id`.
- `good_days_omer`, נשלח מתזכורת העומר. נתונים: `night, day, message, counted`. הוא נשלח שוב עם `counted: true` כשלוחצים על **Counted**, ולחיישן `sensor.good_days_omer` יש מאפיין `counted`, כך שאוטומציה יכולה להזכיר שוב מאוחר יותר.

## בלופרינטים { #blueprints }

**תאורה לפני הדלקת נרות.** מדליק תאורה או מתגים N דקות לפני הדלקת הנרות של שבת ויום טוב (לפי `sensor.good_days_next_candle_lighting`), ואפשר גם לכבות, בהשהיה, אחרי ההבדלה. אם ייבאתם אותו לפני גרסה 0.4, ייבאו אותו מחדש.

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fbareli%2Fgood_days%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgood_days%2Fcandle_lighting_light.yaml)

**נר יארצייט.** מדליק נר זיכרון חשמלי ליארצייט מתוך התאריכים המשפחתיים: בשקיעה בערב שלפניו (או עד שעה קודם), ומכבה בשקיעה בסוף היום (או עד שעתיים אחר כך, או אף פעם). בוחרים את הנר (light, switch או input_boolean) ומקלידים את השם כפי שהוזן ב-Good Days (מספיק חלק ממנו; ריק פירושו כל היארצייטים). יוצרים אוטומציה אחת לכל נר. ימי הולדת וימי נישואין אף פעם לא מדליקים את הנר.

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fbareli%2Fgood_days%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgood_days%2Fyahrzeit_candle.yaml)

## Assist { #assist }

מעתיקים את [`en/good_days.yaml`](https://github.com/bareli/good_days/blob/main/docs/assist/en/good_days.yaml) ו/או את [`he/good_days.yaml`](https://github.com/bareli/good_days/blob/main/docs/assist/he/good_days.yaml) אל `<config>/custom_sentences/<language>/` ומפעילים מחדש. התשובות נאמרות בשפה שבה שאלתם.

| Intent | English | עברית |
|---|---|---|
| `GoodDaysUpcoming` | What's coming up this week? | מה יש השבוע? |
| `GoodDaysNextHoliday` | When is the next holiday? | מתי החג הבא? |
| `GoodDaysShabbatTimes` | When is candle lighting? | מתי כניסת השבת? |
| `GoodDaysOmer` | What's the Omer count? | כמה בעומר היום? |
| `GoodDaysFastTimes` | When does the fast end? | מתי נגמר הצום? |

## WebSocket API

`good_days/upcoming` מקבל `{calendars, days, limit, categories?, language?, entry_id?, latitude?, longitude?, candle_lighting?, havdalah?, diaspora?}`. חמשת האחרונים דורסים את הגדרות המופע עבור אותה תשובה; `latitude` ו-`longitude` באים יחד. התשובה היא `{items, current, omer, errors, now, language}`, כש-`omer` הוא `{day, text, counted, next_count}` בתקופת העומר, ו-null מחוצה לה. הפריטים ממוינים לפי התחלה ומכילים `uid, source, title, start, end, all_day, category, hebrew_date, candle_lighting, havdalah, in_effect, conflicts_shabbat, description, haftarah, haftarah_label`; פריטים משפחתיים מוסיפים `kind, name, years, day, date_id`.

תאריכים משפחתיים: `good_days/dates/list`, ‏`dates/add`, ‏`dates/update`, ‏`dates/remove` (בעיות אימות מחזירות `{errors: {field: code}}`) ו-`dates/convert` (המרה מלועזי לעברי).
