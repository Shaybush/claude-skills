# Secrets / env pattern for skills

Use this layout for any skill that calls an authenticated API or needs a token,
password, or other credential (Cloudflare, Stripe, OpenAI, a private DB, etc.).

**Core invariant: the model never reads the secret.** Scripts load `.env`
themselves at runtime, so credential values never enter the context window. A
secrets guard hook blocks the model from reading `.env`/key files, and `**/.env`
is gitignored so secrets are never committed.

## Layout

```
skill-name/
├── SKILL.md                # workflow + "Never read scripts/.env" + script table
├── SETUP.md                # one-time: how to create scripts/.env
└── scripts/
    ├── _client.py          # shared helper: loads .env, makes auth'd requests
    ├── .env.example        # committed: blank keys + where to get them
    ├── .env                # gitignored, created by user — NEVER read by the model
    ├── verify.py           # cheap auth check (run first to confirm setup)
    └── <verb>.py           # one thin script per operation
```

Rules:
1. `.env` lives in `scripts/`, beside the helper. Gitignored via `**/.env`.
2. Commit `.env.example` only — blank values, comments on where each comes from.
3. One shared helper (`_client.py`) loads `.env` with a stdlib parser — **no
   `python-dotenv` dependency**. It exposes `api()`/`out()` to the verb scripts.
4. Verb scripts are thin: import the helper, parse args, call one endpoint.
5. `SETUP.md` documents the one-time `cp .env.example .env` + fill-in.
6. SKILL.md states **Never read `scripts/.env`** and lists scripts in a table.
7. Never echo a secret, pass it where it lands in shell history/process list
   unnecessarily, or print it back. Secret values are write-only.

## Templates

### `scripts/.env.example`

```
# <Service> credentials — copy to .env (same folder) and fill in. .env is gitignored.
# API key: <where to get it, e.g. dashboard → Settings → API Keys>.
SERVICE_API_KEY=''
# Optional account/org id if the API needs one.
SERVICE_ACCOUNT_ID=''
```

### `scripts/_client.py` (shared helper — stdlib only, no deps)

```python
'''Shared <Service> API helper.

Loads credentials from .env beside this file and makes authenticated requests.
Verb scripts import api()/out() from here. Claude never reads .env — these
scripts load it at runtime, so credentials are never exposed to the model.

Self-check: python3 _client.py  ->  prints 'ok'
'''
import json
import os
import sys
import urllib.error
import urllib.request

BASE = 'https://api.example.com/v1'
_DIR = os.path.dirname(os.path.abspath(__file__))
_ENV = None


def _parse_env(text):
    env = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        env[k.strip()] = v.strip().strip('\'"')
    return env


def _load():
    global _ENV
    if _ENV is None:
        path = os.path.join(_DIR, '.env')
        if not os.path.isfile(path):
            sys.exit('Missing scripts/.env — cp .env.example .env and fill it in.')
        with open(path) as f:
            _ENV = _parse_env(f.read())
    return _ENV


def api(method, path, body=None):
    env = _load()
    token = env.get('SERVICE_API_KEY')
    if not token:
        sys.exit('SERVICE_API_KEY not set in scripts/.env')
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)  # most APIs return JSON error bodies


def out(resp):
    '''Pretty-print a response; exit non-zero on API failure.'''
    print(json.dumps(resp, indent=2))
    if isinstance(resp, dict) and resp.get('success') is False:
        errs = '; '.join(m.get('message', '') for m in resp.get('errors', []))
        sys.exit('API error: ' + (errs or 'unknown'))


if __name__ == '__main__':
    sample = "# c\nSERVICE_API_KEY='abc'\nSERVICE_ACCOUNT_ID=xyz\n\nNOEQ\n"
    assert _parse_env(sample) == {'SERVICE_API_KEY': 'abc', 'SERVICE_ACCOUNT_ID': 'xyz'}
    print('ok')
```

### `scripts/verify.py` (cheapest auth check — run first)

```python
#!/usr/bin/env python3
'''Verify the API key is active.'''
from _client import api, out

out(api('GET', '/whoami'))  # swap for the service's cheapest auth'd endpoint
```

### `scripts/<verb>.py` (one thin script per operation)

```python
#!/usr/bin/env python3
'''List widgets.'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='List widgets.')
p.add_argument('--limit', type=int, default=20)
a = p.parse_args()

out(api('GET', '/widgets?limit=' + str(a.limit)))
```

### `SETUP.md`

```markdown
# <Service> skill — setup

One-time. Creates `scripts/.env`. Scripts read it themselves; the model never
reads it (`**/.env` is gitignored).

## 1. Get credentials
- API key — <where>.
- Account ID — <where, if needed>.

## 2. Create the .env
\`\`\`bash
cd ~/.claude/skills/<skill-name>/scripts
cp .env.example .env
\`\`\`
Fill in the values.

## 3. Verify
\`\`\`bash
cd ~/.claude/skills/<skill-name>
python3 scripts/verify.py
\`\`\`
Expect a success response.
```

### SKILL.md skeleton

```markdown
---
name: <skill-name>
description: <what + when to use it>
---

# <Service>

Run operations through the scripts in `scripts/`. Each loads credentials from
`scripts/.env` at runtime and prints the JSON response. **Never read
`scripts/.env`** — a secrets guard blocks credential files and the scripts read
it themselves.

> **First time?** Follow `./SETUP.md`. `Missing scripts/.env` means setup isn't done.

## Scripts

| Script | Use |
| --- | --- |
| `verify.py` | Check the API key works |
| `<verb>.py` | <one line> |

## Workflow
1. Pick the script for the task.
2. Run `python3 scripts/<script>.py [flags]` (`--help` for flags).
3. Read the JSON; check `success`/exit code.
```

## Adapting per service

- Change `BASE`, the auth header, and the env var names in `_client.py`.
- Add path helpers (e.g. resolve a name → id) to `_client.py` if multiple verbs
  reuse them — keep verb scripts thin.
- If a value must be passed as a CLI arg (e.g. setting a secret), note in SKILL.md
  that it's briefly visible in the process list; never log it.
- Keep the helper dependency-free (stdlib `urllib`) so the skill runs anywhere
  without `pip install`. Reach for `requests`/an SDK only if the API genuinely
  needs it (multipart, OAuth refresh, signing).
