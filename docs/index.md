# Good Days

Good Days is a Home Assistant integration with a Lovelace card that shows **what is coming up**: Shabbat, Jewish holidays and fasts, the Omer, and **Hebrew-date birthdays and yahrzeits**, merged with any Home Assistant calendar. Every item has a live countdown, in Hebrew or English.

[Install](install.md){ .md-button .md-button--primary }
[GitHub](https://github.com/bareli/good_days){ .md-button }

## What it does

- **Works offline.** Holidays, candle lighting and havdalah are computed locally with [hdate](https://github.com/py-libhdate/py-libhdate), the library behind Home Assistant's own Jewish Calendar.
- **Israel and diaspora**, with one or two days of Yom Tov.
- **Timed calendar events.** Shabbat and Yom Tov run from candle lighting to havdalah, so calendar triggers work in automations.
- **Family dates by Hebrew date**: birthdays, yahrzeits and anniversaries, managed in a sidebar panel, with the leap-year Adar and 30 Cheshvan / Kislev rules.
- **Reminders** for family dates on your phone, with *Got it* and *Remind me tomorrow* buttons, held during Shabbat and Yom Tov.
- **Shabbat timers**: hot plate, urn, lights, AC and anything with an on/off switch itself around candle lighting and havdalah, with profiles, conditions and a preview.
- **Haftarah** for every Shabbat with a weekly parasha, Sephardi or Ashkenazi.
- **Fasts and the Omer**: timed fasts, a fasting sensor, and the Omer count.
- **Calendar link (ICS)** to subscribe to your family dates from Google Calendar or a phone.
- **Assist** sentences in Hebrew and English, and two blueprints.
- A Hebrew-first card: RTL, Hebrew dates, countdowns, keyboard accessible.

## Requirements

- Home Assistant 2025.7 or newer.
- HACS, if you want the easy install (a manual copy also works).

!!! note "Times use sea-level sunset"
    Like printed calendars, Good Days ignores elevation.

## Where to go next

| I want to... | Go to |
|---|---|
| Install it | [Install](install.md) |
| Add birthdays, set reminders, share a calendar link | [Usage](usage.md) |
| Switch the hot plate or lights on and off for Shabbat | [Shabbat timers](timers.md) |
| Put the agenda on a dashboard | [Card](card.md) |
| Write automations | [Entities and automations](entities.md) |
