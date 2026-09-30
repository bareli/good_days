# Good Days (ימים טובים)

Home Assistant integration + Lovelace card that shows **what's coming up**: Shabbat, Jewish holidays and fasts, **Hebrew-date birthdays and yahrzeits**, merged with any HA calendar, each with a live countdown, in Hebrew or English.

- Works offline: holidays, candle lighting and havdalah are computed locally with [hdate](https://github.com/py-libhdate/py-libhdate) (the library HA's own Jewish Calendar uses).
- Israel and diaspora (one or two days of Yom Tov).
- Shabbat and Yom Tov are **timed** calendar events, candle lighting to havdalah, so calendar triggers work in automations.
- Family dates that repeat by **Hebrew date** (birthdays, yahrzeits, anniversaries), managed in a sidebar panel, with leap-year Adar and 30 Cheshvan / Kislev rules.
- Reminders for family dates on your phone (Got it / Remind me tomorrow buttons), held during Shabbat and Yom Tov.
- Special Shabbatot (Shekalim, Zachor, Parah, HaChodesh, HaGadol, Shuva, Chazon, Nachamu, Shira, Rosh Chodesh, Chanukah, Chol HaMoed) in titles; Mevarchim and Machar Chodesh in the details.
- Subscribe to your family dates from Google Calendar or your phone (private ICS link).
- Assist: "מה יש השבוע?", "When is the next holiday?", "מתי הדלקת נרות?".
- Hebrew-first card: RTL, Hebrew dates, "בעוד יומיים" countdowns, keyboard accessible.

## Install

HACS: add `https://github.com/bareli/good_days` as a custom repository (category Integration), install **Good Days**, restart Home Assistant.

Manual: copy `custom_components/good_days` into `<config>/custom_components/`, restart.

Then **Settings → Devices & services → Add integration → Good Days**. If the core Jewish Calendar integration is configured, its location, diaspora and candle lighting / havdalah minutes are offered as defaults (copied once, not linked).

Times use sea-level sunset, like printed calendars (elevation is ignored).

Requires Home Assistant 2025.7 or newer.

## Entities

| Entity | What |
|---|---|
| `calendar.good_days_holidays` | Shabbatot, Yom Tov, Chol HaMoed, fasts, minor and national days (categories from the options). Shabbat / Yom Tov events run from candle lighting to havdalah; adjacent Yom Tov and Shabbat are one event. Others are all-day. |
| `sensor.good_days_next_shabbat` | Candle lighting of the current or next Shabbat (timestamp). Attributes: `havdalah`, `parasha`, `special_shabbat` (e.g. `["Shekalim", "Mevarchim Chodesh Adar"]`), `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `sensor.good_days_next_candle_lighting` | Candle lighting of the current or next Shabbat **or Yom Tov** (timestamp), regardless of all-day events around it. Attributes: `havdalah`, `title`, `category`, `days_until`, `in_effect`. Best for automations. |
| `sensor.good_days_next_holiday` | Name of the current or next holiday (not plain Shabbat or Rosh Chodesh). Attributes: `start`, `end`, `category`, `days_until`, `candle_lighting`, `havdalah`, `hebrew_date`. |
| `binary_sensor.good_days_holiday_today` | On during a holiday day. Attribute `holidays`. |
| `calendar.good_days_family` | Family dates. Birthdays and anniversaries are all-day; a yahrzeit runs from sunset the evening before to sunset. |
| `sensor.good_days_next_family_date` | Title of the current or next family date. Attributes: `name`, `kind`, `years`, `start`, `days_until`, `hebrew_date`, `conflicts_shabbat`. |

Categories: `shabbat`, `yom_tov`, `chol_hamoed`, `minor` (Chanukah, Purim, Tu BiShvat, Lag BaOmer...), `fast`, `rosh_chodesh`, `modern` (Yom HaAtzmaut, Yom HaZikaron, Yom HaShoah, Yom Yerushalayim), `memorial` (other memorial / national days), `erev` (Erev Yom Tov days). Default: the first five plus `modern`.

### Automation example: porch light 10 minutes before candle lighting

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

## Family dates

Sidebar → **Good Days** (all users). Add a birthday, yahrzeit, anniversary or other date by its Hebrew date, or type the Gregorian date (tick *after sunset* if it was after sunset) and it is converted. With the Hebrew year the title shows the age or number of years ("Noa's birthday (7)", "יום הולדת 7 לנועה").

Rules, per date (defaults are common customs; they differ between communities, so check yours):

- **Plain Adar in a leap year**: birthdays and anniversaries in Adar II, yahrzeits in Adar I; or pick Adar I, Adar II or both.
- **Dates in Adar I / Adar II** fall in plain Adar in a regular year.
- **30 Cheshvan / 30 Kislev** in a year where the month has 29 days: the 1st of the next month (first day of Rosh Chodesh), or the 29th. **30 Adar I** in a plain year: 30 Shvat (first day of Rosh Chodesh Adar), or 29 Adar.

Services: `good_days.add_date`, `update_date`, `remove_date`, `list_dates` (returns every date with its next occurrence). Data is stored per instance in `.storage/good_days.<entry_id>`.

```yaml
action: good_days.add_date
data:
  name: Saba Moshe
  kind: yahrzeit
  hebrew_day: 3
  hebrew_month: marcheshvan   # tishrei ... elul; adar = Adar of a plain year; adar_i / adar_ii
  original_year: 5770
```

## Calendar subscription (ICS)

In the Good Days panel (admins): **Share family dates as a calendar link**, optionally **Include Shabbat and holidays**. Copy the link into Google Calendar (*Other calendars → From URL*), Outlook, or open it on a phone (*Open in calendar app*). The feed covers 30 days back to 2 years ahead and refreshes every 12 hours.

- The link works without logging in; the long random part is the key. Anyone with the link can read the dates. **New link** replaces it (the old one stops working); turning sharing off disables it.
- Google Calendar fetches from the internet, so the link must use an external address (Home Assistant Cloud or your external URL, from Settings → System → Network).

## Reminders

Options (Settings → Devices & services → Good Days → Configure):

- **Send family-date reminders to**: notify services, e.g. `mobile_app_my_phone`. Phones get **Got it** (no more reminders for this occurrence) and **Remind me tomorrow** buttons.
- **Reminder time** (default 09:00).
- **Hold reminders during Shabbat and Yom Tov** (default on): reminders due then are sent before candle lighting.

Each family date chooses when (in the panel): on the day, 1, 3 or 7 days before (any 0-60 via the services). For a yahrzeit, "on the day" means the evening it begins, an hour before sunset, with the time to light the candle. When the yahrzeit begins on Shabbat or Yom Tov, the message says to light before candle lighting; when it begins as Shabbat ends, after havdalah.

Reminders that would fall on Shabbat or Yom Tov are sent an hour before candle lighting instead (option **Hold reminders during Shabbat and Yom Tov**).

Every reminder also fires the `good_days_reminder` event (`name, kind, day, years, title, message, date_id, entry_id`), even without notify targets, for your own automations.

## Assist

Copy [`docs/assist/en/good_days.yaml`](docs/assist/en/good_days.yaml) and/or [`docs/assist/he/good_days.yaml`](docs/assist/he/good_days.yaml) to `<config>/custom_sentences/<language>/` and restart. Then ask:

| Intent | English | עברית |
|---|---|---|
| `GoodDaysUpcoming` | What's coming up this week? | מה יש השבוע? |
| `GoodDaysNextHoliday` | When is the next holiday? | מתי החג הבא? |
| `GoodDaysShabbatTimes` | When is candle lighting? | מתי כניסת השבת? |

Answers are spoken in the language you asked in.

## Blueprint: lights before candle lighting

[![Import blueprint](https://my.home-assistant.io/badges/blueprint_import.svg)](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Fbareli%2Fgood_days%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fgood_days%2Fcandle_lighting_light.yaml)

Turns lights or switches on N minutes before candle lighting of Shabbat and Yom Tov (from `sensor.good_days_next_candle_lighting`), and optionally off (with a delay) after havdalah. If you imported it before v0.4, re-import it: the old version read the holidays calendar and missed Shabbat when Chanukah or a fast was on that Friday. Source: [`blueprints/automation/good_days/candle_lighting_light.yaml`](blueprints/automation/good_days/candle_lighting_light.yaml).

## The card

The card resource is registered automatically (storage-mode dashboards). YAML-mode dashboards: add `/good_days_static/card.js` as a JavaScript module.

```yaml
type: custom:good-days-card
title: What's coming          # optional
calendars:                    # external calendars to merge
  - calendar.family
  - calendar.school
colors:                       # optional, per source ("holidays", "family", or a calendar)
  calendar.family: "#4caf50"
days: 30                      # look-ahead, 1-400
limit: 10                     # items, 1-100
categories: [shabbat, yom_tov, minor, fast, family]   # optional, default = integration options + family
show_hebrew_date: true
show_candle_lighting: true
compact: false                # one line: "Next: Shabbat · in 2 days · candles 17:52"
entry_id: <optional, for a second Good Days instance>
```

Everything is editable in the visual editor. The card follows the user's HA language (Hebrew → RTL). External and family events that fall on Shabbat or Yom Tov get a warning badge. Tap an item for details.

Without the integration the card still lists the selected calendars (no holidays) and shows a hint.

### WebSocket API

`good_days/upcoming` with `{calendars, days, limit, categories?, language?, entry_id?}` returns `{items, current, errors, now, language}`. Items are sorted by start and carry `uid, source, title, start, end, all_day, category, hebrew_date, candle_lighting, havdalah, in_effect, conflicts_shabbat, description` (family items add `kind, name, years, day, date_id`).

Family dates: `good_days/dates/list`, `dates/add`, `dates/update`, `dates/remove` (validation problems return `{errors: {field: code}}`), `dates/convert` (Gregorian → Hebrew).

## Roadmap

- Later: feed a Shabbat Home timers product, Torah reading details, ICS export of family dates.

## License

MIT. Uses `hdate` (GPL-3.0-or-later), installed by Home Assistant as a runtime requirement, not bundled.
