# QA overlay: Good Days

Read `~/.claude/qa-kit/RULEBOOK.md` first, then `qa/PROJECT.md`. This file adds this project's
specifics under the same § numbers. Where it contradicts the rulebook, it wins here, and says so.

## §1 Environments

| Env | Base URL | Storage | Writes |
|---|---|---|---|
| `dev` | `http://127.0.0.1:<port>` (see §4) | throwaway HA config dir in the session scratchpad | Allowed |
| `prod` | none hosted; users' own Home Assistant | their `.storage` | **Never** (there is no QA access to any user's HA) |

There is no production for QA. The owner's own Home Assistant is off limits.

How to start a dev Home Assistant on native Windows (HA refuses Windows; this QA-only launcher stubs the two
Windows gaps: `add_signal_handler` and `signal.SIGHUP`). Needs the Python 3.14 venv from §3:

```bash
S=<scratchpad>
cp -r custom_components/good_days $S/haconfig-<port>/custom_components/   # copy, never symlink
PYTHONPATH=$S $S/venv314/Scripts/python.exe $S/ha_launch.py -c $S/haconfig-<port> --ignore-os-check --skip-pip
```

`configuration.yaml` sets `http.server_port`, Israel location / time zone / language `he`, and input_booleans
used as timer targets. Seed with `ha_seed.py` (onboarding owner `qa_admin`, Good Days via the real config flow)
and add the non-admin `qa_user` over the websocket. Credentials: `qa/fixtures/dev-accounts-<port>.json`
(git-ignored). Errors about `ffmpeg`, `conversation`, `camera`, `radio_frequency`, `infrared` at startup are
missing optional packages in this venv and unrelated to Good Days; Assist (`conversation`) is therefore not
available in the dev instance - test intents through pytest.

### Database access

No database. State lives in `<config>/.storage/good_days.<entry_id>` and `good_days.timers.<entry_id>` (JSON),
read them directly. Websocket helper: `ha_ws.py <accounts.json> '<json msg>' ...` (runs as qa_admin).

## §2 Boundaries

See `PROJECT.md` -> *Paths*. Copying the integration into a dev config dir is not modifying application code.

## §3 Builds

No build. Test environments (session scratchpad, rebuild each session):

- `venv314`: Python 3.14, latest pytest-homeassistant-custom-component + matching home-assistant-frontend, hdate.
  Same as CI. Also runs the dev Home Assistant.
- `venv`: Python 3.13, HA 2026.2.3, phcc 0.13.316.
- Both need stub `fcntl.py` / `resource.py` in site-packages and `win_shim.py` (no-op pytest_socket) on
  PYTHONPATH. Full suite:
  `PYTHONPATH=$S $S/venv314/Scripts/python.exe -c "import win_shim,sys,pytest;sys.exit(pytest.main(['-q','-p','no:cacheprovider','--timeout=120','tests']))"`
- Windows' OS time zone is Asia/Jerusalem: bugs that depend on the OS zone only reproduce on Linux CI.

## §4 Instances

| Port | Config dir | Owner of the instance (run 2026-09-30) |
|---|---|---|
| 8129 | `$S/haconfig-8129` | qa-engineer |
| 8130 | `$S/haconfig-8130` | qa-ux-expert |
| 8131 | `$S/haconfig-8131` | qa-accessibility-expert |
| 8132 | `$S/haconfig-8132` | qa-security-expert |

Each: HA 2026.9, Good Days v0.5.0 copy, owner `qa_admin` and non-admin `qa_user` (passwords and an admin
token in `qa/fixtures/dev-accounts-<port>.json`), input_booleans `hot_plate`, `living_room`, `guests`.

Traps:
- **HA 2026.9 treats YAML `http:` settings as pending and reverts them with a restart after 5 minutes.**
  Right after a new instance first answers, send the websocket command `{"type":"http/config/promote"}`.
- Start every instance as its own long-running background process; an instance started from inside a script
  dies when the script ends.
- **The HA frontend hangs on "loading" because `get_services` fails (missing `hassil`).** Install `hassil`
  and `ical` into venv314 before starting (`uv pip install --python venv314/Scripts/python.exe hassil ical`),
  or patch that reply in Playwright (`routeWebSocket`), see `qa/knowledge/environment.md`.
- The dev instance's clock is real time: timers and reminders cannot be watched firing unless a Shabbat is
  near. Use "run now", the preview, and the pytest suite (frozen clock) for firing behaviour.

## §8 Specs

Frontend harness pages (fake `hass`) in `$S/ui/` served on :8765 were used during development; the dev
Home Assistant supersedes them for QA.
