# Entities and automations

## Entities

| Entity | What |
|---|---|
| `calendar.good_days_holidays` | Shabbatot, Yom Tov, Chol HaMoed, fasts, minor and national days (categories from the options). Shabbat / Yom Tov events run from candle lighting to havdalah; adjacent Yom Tov and Shabbat are one event. Fasts run from dawn (Tisha B'Av: sunset) to nightfall. Others are all-day. |
| `sensor.good_days_next_shabbat` | Candle lighting of the current or next Shabbat (timestamp). Attributes: `havdalah`, `parasha`, `special_shabbat`, `haftarah`, `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `sensor.good_days_next_candle_lighting` | Candle lighting of the current or next Shabbat **or Yom Tov** (timestamp), regardless of all-day events around it. Attributes: `havdalah`, `title`, `category`, `days_until`, `in_effect`. Best for automations. |
| `sensor.good_days_next_holiday` | Name of the current or next holiday (not plain Shabbat or Rosh Chodesh). Attributes: `start`, `end`, `category`, `days_until`, `candle_lighting`, `havdalah`, `hebrew_date`. |
| `binary_sensor.good_days_holiday_today` | On during a holiday day. Attribute `holidays`. |
| `sensor.good_days_next_fast` | Start of the current or next fast, Yom Kippur included (timestamp). Attributes: `end`, `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `binary_sensor.good_days_fasting` | On from the start to the end of a fast (Yom Kippur too). Attributes `title`, `end`. |
| `sensor.good_days_omer` | Day of the Omer (1-49), moving on at nightfall; unknown outside the Omer. Attributes: `weeks`, `days`, `text` (the counting sentence), `next_count`, `counted`. |
| `calendar.good_days_family` | Family dates. Birthdays and anniversaries are all-day; a yahrzeit runs from sunset the evening before to sunset. |
| `sensor.good_days_next_family_date` | Title of the current or next family date. Attributes: `name`, `kind`, `years`, `start`, `days_until`, `hebrew_date`, `conflicts_shabbat`. |
| `switch.good_days_shabbat_timers` | Shabbat timers on / off (rules are kept). |
| `switch.good_days_skip_next_shabbat_or_chag` | Skip the timers of the current or next Shabbat / Chag only; resets by itself. |
| `select.good_days_timer_profile` | Active timer profile. |
| `sensor.good_days_next_timer_action` | When the next timer fires; attributes `rule`, `action`, `targets`. |

The `special_shabbat` attribute looks like `["Shekalim", "Mevarchim Chodesh Adar"]`. Special Shabbatot (Shekalim, Zachor, Parah, HaChodesh, HaGadol, Shuva, Chazon, Nachamu, Shira, Rosh Chodesh, Chanukah, Chol HaMoed) appear in the title; Mevarchim and Machar Chodesh appear in the details.

!!! note "Direction marks in names"
    Hebrew names inside English titles are wrapped in invisible direction marks. A state such as `sensor.good_days_next_family_date` therefore contains them; an automation that compares it to a plain string must strip them.

## Example: porch light before candle lighting

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

## Services

`good_days.add_date`, `good_days.update_date`, `good_days.remove_date`, `good_days.list_dates`. See [Usage](usage.md#services).

## Events { #events }

- `good_days_reminder`, fired for every reminder, even without notify targets. Data: `name, kind, day, years, title, message, date_id, entry_id`.
- `good_days_omer`, fired by the Omer reminder. Data: `night, day, message, counted`. It fires again with `counted: true` when the **Counted** button is pressed, and `sensor.good_days_omer` has the attribute `counted`, so an automation can remind again later.

## Blueprints { #blueprints }

**Lights before candle lighting.** Turns lights or switches on N minutes before candle lighting of Shabbat and Yom Tov (from `sensor.good_days_next_candle_lighting`), and optionally off, with a delay, after havdalah. If you imported it before v0.4, import it again.

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fbareli%2Fgood_days%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgood_days%2Fcandle_lighting_light.yaml)

**Yahrzeit candle.** Turns an electric memorial candle on for a yahrzeit from your family dates: at sunset the evening before (or up to an hour earlier), and off at sunset at the end of the day (or up to two hours later, or never). Pick the candle (light, switch or input_boolean) and type the name as entered in Good Days (part of it is enough; empty means every yahrzeit). Make one automation per candle. Birthdays and anniversaries never light the candle.

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fbareli%2Fgood_days%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgood_days%2Fyahrzeit_candle.yaml)

## Assist { #assist }

Copy [`en/good_days.yaml`](https://github.com/bareli/good_days/blob/main/docs/assist/en/good_days.yaml) and / or [`he/good_days.yaml`](https://github.com/bareli/good_days/blob/main/docs/assist/he/good_days.yaml) to `<config>/custom_sentences/<language>/` and restart. Answers are spoken in the language you asked in.

| Intent | English | עברית |
|---|---|---|
| `GoodDaysUpcoming` | What's coming up this week? | מה יש השבוע? |
| `GoodDaysNextHoliday` | When is the next holiday? | מתי החג הבא? |
| `GoodDaysShabbatTimes` | When is candle lighting? | מתי כניסת השבת? |
| `GoodDaysOmer` | What's the Omer count? | כמה בעומר היום? |
| `GoodDaysFastTimes` | When does the fast end? | מתי נגמר הצום? |

## WebSocket API

`good_days/upcoming` takes `{calendars, days, limit, categories?, language?, entry_id?, latitude?, longitude?, candle_lighting?, havdalah?, diaspora?}`. The last five override the entry's settings for that reply; `latitude` and `longitude` go together. It returns `{items, current, omer, errors, now, language}`, where `omer` is `{day, text, counted, next_count}` during the Omer and null otherwise. Items are sorted by start and carry `uid, source, title, start, end, all_day, category, hebrew_date, candle_lighting, havdalah, in_effect, conflicts_shabbat, description, haftarah, haftarah_label`; family items add `kind, name, years, day, date_id`.

Family dates: `good_days/dates/list`, `dates/add`, `dates/update`, `dates/remove` (validation problems return `{errors: {field: code}}`) and `dates/convert` (Gregorian to Hebrew).
