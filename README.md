# Good Days (ימים טובים)

Home Assistant integration + Lovelace card that shows **what's coming up**: Shabbat, Jewish holidays and fasts, merged with any HA calendar, each with a live countdown, in Hebrew or English.

- Works offline: holidays, candle lighting and havdalah are computed locally with [hdate](https://github.com/py-libhdate/py-libhdate) (the library HA's own Jewish Calendar uses).
- Israel and diaspora (one or two days of Yom Tov).
- Shabbat and Yom Tov are **timed** calendar events, candle lighting to havdalah, so calendar triggers work in automations.
- Hebrew-first card: RTL, Hebrew dates, "בעוד יומיים" countdowns, keyboard accessible.

## Install

HACS: add `https://github.com/bareli/good_days` as a custom repository (category Integration), install **Good Days**, restart Home Assistant.

Manual: copy `custom_components/good_days` into `<config>/custom_components/`, restart.

Then **Settings → Devices & services → Add integration → Good Days**. If the core Jewish Calendar integration is configured, its location, diaspora and candle lighting / havdalah minutes are offered as defaults (copied once, not linked).

Requires Home Assistant 2025.7 or newer.

## Entities

| Entity | What |
|---|---|
| `calendar.good_days_holidays` | Shabbatot, Yom Tov, Chol HaMoed, fasts, minor and national days (categories from the options). Shabbat / Yom Tov events run from candle lighting to havdalah; adjacent Yom Tov and Shabbat are one event. Others are all-day. |
| `sensor.good_days_next_shabbat` | Candle lighting of the current or next Shabbat (timestamp). Attributes: `havdalah`, `parasha`, `title`, `hebrew_date`, `days_until`, `in_effect`. |
| `sensor.good_days_next_holiday` | Name of the current or next holiday (not plain Shabbat or Rosh Chodesh). Attributes: `start`, `end`, `category`, `days_until`, `candle_lighting`, `havdalah`, `hebrew_date`. |
| `binary_sensor.good_days_holiday_today` | On during a holiday day. Attribute `holidays`. |

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

## The card

The card resource is registered automatically (storage-mode dashboards). YAML-mode dashboards: add `/good_days_static/card.js` as a JavaScript module.

```yaml
type: custom:good-days-card
title: What's coming          # optional
calendars:                    # external calendars to merge
  - calendar.family
  - calendar.school
colors:                       # optional, per source ("holidays" for ours)
  calendar.family: "#4caf50"
days: 30                      # look-ahead, 1-400
limit: 10                     # items, 1-100
categories: [shabbat, yom_tov, minor, fast]   # optional, default = integration options
show_hebrew_date: true
show_candle_lighting: true
compact: false                # one line: "Next: Shabbat · in 2 days · candles 17:52"
entry_id: <optional, for a second Good Days instance>
```

Everything is editable in the visual editor. The card follows the user's HA language (Hebrew → RTL). Events of external calendars that fall on Shabbat or Yom Tov get a warning badge. Tap an item for details.

Without the integration the card still lists the selected calendars (no holidays) and shows a hint.

### WebSocket API

`good_days/upcoming` with `{calendars, days, limit, categories?, language?, entry_id?}` returns `{items, current, errors, now, language}`. Items are sorted by start and carry `uid, source, title, start, end, all_day, category, hebrew_date, candle_lighting, havdalah, in_effect, conflicts_shabbat, description`.

## Roadmap

- v0.2: Hebrew-date birthdays and yahrzeits (`calendar.good_days_family`), family-dates panel.
- v0.3: reminders with actionable notifications, Assist ("מה יש השבוע?"), blueprints.

## License

MIT. Uses `hdate` (GPL-3.0-or-later), installed by Home Assistant as a runtime requirement, not bundled.
