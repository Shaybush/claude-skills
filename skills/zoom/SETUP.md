# Zoom skill — setup

One-time. Creates `scripts/.env`. The scripts read it themselves; the model never
reads it (`.env` is gitignored).

## 1. Create a Server-to-Server OAuth app

1. Go to <https://marketplace.zoom.us/develop/create>.
2. **Develop → Build App → Server-to-Server OAuth** (not regular OAuth).
3. Name it (e.g. "Claude Zoom").

## 2. Copy the credentials

From the app's **App Credentials** tab:

| Field | Env var |
| --- | --- |
| Account ID | `ZOOM_ACCOUNT_ID` |
| Client ID | `ZOOM_CLIENT_ID` |
| Client Secret (click to reveal) | `ZOOM_CLIENT_SECRET` |

## 3. Add scopes

**Scopes** tab → **Add Scopes**. Classic scope names (granular equivalents also work):

| Scope | Enables |
| --- | --- |
| `user:read:admin` | `verify.py` (`GET /users/me`) |
| `meeting:read:admin` | `list.py`, `get.py` |
| `meeting:write:admin` | `schedule.py`, `rename.py`, `delete.py` |
| `recording:read:admin` | `recording.py` |

## 4. Activate

Click **Activate**. The app does nothing in draft mode.

## 5. Create the .env

```bash
cd ~/.claude/skills/zoom/scripts
cp .env.example .env
```

Fill in the three values.

## 6. Verify

```bash
cd ~/.claude/skills/zoom
python3 scripts/verify.py
```

Expect your user profile JSON.

## Troubleshooting

| Error | Fix |
| --- | --- |
| `invalid_client` | App not activated, or wrong Client ID/Secret |
| `... does not contain scopes ...` | Add the exact scope named, then re-Activate |
| `Missing scripts/.env` | Step 5 not done |
| `Invalid access token` | Account ID wrong, or app deactivated |
