# Dev environment knowledge

- A real Home Assistant (2026.9) runs natively on Windows for QA with `ha_launch.py` (stubs `add_signal_handler`, `signal.SIGHUP`) and `--ignore-os-check --skip-pip`; see `qa/CLAUDE.md` §1, §4.
- HA 2026.9 reverts YAML `http:` settings with a restart after 5 minutes unless `http/config/promote` is sent.
- **The frontend never finishes loading ("טוען...")** in that venv: `get_services` fails server-side because `hassil` (conversation) is not installed. Browser agents patched the one reply with Playwright `routeWebSocket` (`scratchpad/ux/lib.mjs`). Fix for next time: install `hassil` (and `ical` for `local_calendar`) into the venv before starting instances.
- `local_calendar` needs `ical`; `demo` needs conversation. Without them there is no external calendar to merge (CARD-002 blocked).
- Timers / reminders fire on the real clock; outside a Shabbat, use preview, run-now, a reminder time a few minutes ahead (REM-001 was verified live that way) and the frozen-clock pytest suite.
- Windows OS time zone is Israel: OS-zone bugs only show on Linux CI.
