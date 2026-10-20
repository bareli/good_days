# Shabbat timers

Open **Good Days** in the sidebar and choose the **Shabbat timers** tab. Each timer turns devices **on or off**: switches, lights, plugs, fans, AC, water heaters, scenes and the like. Scripts, automations, locks, covers and valves are not offered.

## When a timer fires

- **Around candle lighting** or **around havdalah**: N minutes before or after. For example, a hot plate on 20 minutes before candle lighting and off 30 minutes after havdalah.
- **At a time on each holy day**: for example lights off at 23:00 and on at 07:00. A time later than candle lighting means the evening before (23:00 is Friday night); an earlier time is on the day itself. Choose every day, the first or last day, or Erev (the day before).

## Applies to

Shabbat, Yom Tov, Yom Kippur and / or fast days. A hot plate, for example, usually should not apply to Yom Kippur. A two- or three-day Chag together with Shabbat is handled as one stretch.

On a fast day, "candle lighting" means when the fast begins and "havdalah" means when it ends. A clock time on a minor fast is on that day.

## Conditions

An optional **Only if** takes Home Assistant conditions, checked when the timer fires, for example only when guests are staying.

## Presets

Presets create the on and off timers for you:

- hot plate, urn
- evening lights, morning lights
- AC
- electric water heater (on at noon on Erev Shabbat / Chag, off before candle lighting; it heats only on the Erev of a multi-day Chag)
- porch light (on before candle lighting, off at 01:00)
- bedroom AC at night (22:00 to 06:30)
- breaking the fast (urn or kettle on 30 minutes before the fast ends, off an hour after)

The preset dialog summarises what it will create before you confirm.

## Profiles

Profiles (for example Regular, Guests, Summer) hold separate sets of timers. One profile is active, shown by `select.good_days_timer_profile`. A new profile can start as a copy of another, profiles can be renamed, and you can view and edit another profile without making it active. **Duplicate** copies a single timer.

## Preview, conflicts and testing

The tab shows a **preview** of the next Shabbat / Chag: every action with its exact time (a dry run), marked when it falls before candle lighting or after havdalah. It reports **conflicts** when the same device is turned on and off at the same minute; nothing is resolved for you. **Run now** tests a timer immediately. The history keeps the last 100 runs.

## Behaviour rules

- Each action runs **once**. A manual change afterwards is left alone.
- If Home Assistant was down when an action was due, it still runs when it is at most **10 minutes** late. Older ones are skipped and shown as *missed*.
- **Skip next Shabbat / Chag** (`switch.good_days_skip_next_shabbat_or_chag`) turns off the timers of that one Shabbat / Chag only, then resets by itself.
- `switch.good_days_shabbat_timers` turns all timers on or off and keeps the rules.
- `sensor.good_days_next_timer_action` shows when the next action fires, with the attributes `rule`, `action` and `targets`.
