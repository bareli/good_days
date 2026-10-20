# Troubleshooting

## Google Calendar does not load the calendar link

Google fetches the link from the internet, so it must use an external address: Home Assistant Cloud, or your external URL from *Settings → System → Network*.

## I want to cancel a shared calendar link

Anyone with the link can read the dates. In the panel choose **New link**: the old one stops working. Turn sharing off to disable it completely. Family notes are not included unless an admin ticks **Include family notes**.

## A reminder did not arrive at its time

With **Hold reminders during Shabbat and Yom Tov** on (the default), a reminder due on Shabbat or Yom Tov is sent an hour before candle lighting instead. Also check that **Send family-date reminders to** lists a valid notify service such as `mobile_app_my_phone`. The event `good_days_reminder` fires for every reminder even without targets, which helps to test.

## A timer did not run

- Each action runs once; a manual change afterwards is left alone.
- If Home Assistant was down when an action was due, it still runs when it is at most 10 minutes late. Older actions are skipped and marked *missed* in the history.
- Check that `switch.good_days_shabbat_timers` is on and that **Skip next Shabbat / Chag** is not.
- Check the active profile in `select.good_days_timer_profile`.
- A timer with a condition (**Only if**) does not run when the condition is false at that moment.
- A device that cannot be switched on and off is logged as failed.
- Use **Run now** and the **preview** in the Shabbat timers tab to see what would happen and when.

## I cannot change the timers

Only admins can change timers, the profile and the skip switch through the panel and the entities. Other users see the timers read-only, with an explanation.

## Candle lighting differs by a few minutes from another source

Good Days uses sea-level sunset, like printed calendars, and ignores elevation. Candle lighting and havdalah minutes are your own settings (Configure), and a card can have its own values, see [Card](card.md#own-location-and-times).

## The fasts are no longer all-day events

Since v0.11.0 fasts are timed events (dawn to nightfall; Tisha B'Av from sunset to havdalah). An automation that relied on them being all-day needs a look. You can choose when minor fasts begin and end in the options.

## The Lovelace card is missing

The resource is registered automatically on storage-mode dashboards. On YAML-mode dashboards add `/good_days_static/card.js` as a JavaScript module.

## The card shows calendars but no holidays

Without the Good Days integration the card lists the selected calendars only and shows a hint. Add the integration under *Settings → Devices & services*.

## The card shows less than I expect

The card adapts to its own width. Below 400 px it hides details and below 280 px it hides more. Set `responsive: false` to always show the full card. Tap a row to see everything it hides.

## An automation comparing the family-date sensor stopped matching

Names are wrapped in invisible direction marks (since v0.6.0). Strip them in the comparison.

## A Shabbat that is also Yom Tov shows no haftarah

A Shabbat that is itself Yom Tov or Chol HaMoed (no weekly parasha) shows no haftarah yet.

## Still stuck

Open an issue at [github.com/bareli/good_days/issues](https://github.com/bareli/good_days/issues) with your Home Assistant version and the Good Days version.
