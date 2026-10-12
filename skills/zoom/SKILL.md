---
name: zoom
description: "Manage Zoom meetings via Server-to-Server OAuth. Schedule or create a meeting, list and get meetings, rename or reschedule one, delete/cancel, and fetch cloud recording links. Use when the user wants to set up a Zoom call, change a meeting's title or time, cancel a meeting, or grab a recording link. Triggers: 'schedule a zoom', 'rename the zoom meeting', 'send me the recording link', 'cancel the zoom'."
---

# Zoom

Run Zoom operations through the scripts in `scripts/`. Each one loads credentials
from `scripts/.env` at runtime, exchanges them for a Server-to-Server OAuth token,
calls the Zoom API, and prints the JSON response. **Never read `scripts/.env`** —
a secrets guard blocks credential files and the scripts read it themselves.

> **First time?** Follow `./SETUP.md`. A `Missing scripts/.env` error means setup
> isn't done. A `does not contain scopes` error means a scope is missing — see SETUP.

## Scripts

| Script | Use |
| --- | --- |
| `verify.py` | Confirm credentials work (`GET /users/me`). Run first. |
| `schedule.py` | Create/schedule a meeting → returns `id` + `join_url` |
| `list.py` | List meetings (`--type upcoming\|scheduled\|live\|previous_meetings`) |
| `get.py` | Get one meeting's details by id |
| `rename.py` | Rename and/or reschedule a meeting (`--topic/--start/--duration/--tz/--agenda`) |
| `delete.py` | Delete/cancel a meeting (`--notify` to email attendees) |
| `recording.py` | Get a meeting's recording links, or list a user's recordings |

## Workflow

1. Pick the script for the task.
2. Run `python3 scripts/<script>.py [flags]` (add `--help` for flags). Run from the
   skill root so the scripts find their `.env`.
3. Read the JSON; a non-zero exit means a Zoom API error (the message is printed).

## Notes

- **Meeting id** comes from `schedule.py`/`list.py` output (the numeric `id`). Most
  verbs take it as the first positional arg.
- **Start time** is ISO8601 *local* time (`2026-06-25T15:00:00`) paired with `--tz`
  (IANA, e.g. `Asia/Jerusalem`). Omit `--start` on `schedule.py` for an instant meeting.
- **Recording links**: `recording.py <meeting_id>` prints `share_url` (the one to
  hand out) plus per-file `play_url`s before the full JSON. Recordings exist only for
  meetings that were cloud-recorded.
- **"Send" the link**: this skill *fetches* the link. To actually send it, pass the
  `share_url` to the `whatsapp` or `gws-gmail` skill.
- Tokens are fetched fresh per command (S2S OAuth, no user login). Free Zoom accounts work.
