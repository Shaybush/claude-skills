'''Shared Zoom API helper (Server-to-Server OAuth).

Loads ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET from .env beside this
file, exchanges them for an access token, then calls api.zoom.us/v2. Verb scripts
import api()/out() from here. Claude never reads .env — these scripts load it at
runtime, so credentials are never exposed to the model.

Self-check: python3 _client.py  ->  prints 'ok'
'''
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

OAUTH = 'https://zoom.us/oauth/token'
BASE = 'https://api.zoom.us/v2'
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
            sys.exit('Missing scripts/.env — cp .env.example .env and fill it in (see SETUP.md).')
        with open(path) as f:
            _ENV = _parse_env(f.read())
    return _ENV


def _token():
    # ponytail: fresh token per process (one extra POST per command). Tokens last
    # ~1h; cache to a temp file with expiry only if command latency matters.
    env = _load()
    cid, sec, acct = env.get('ZOOM_CLIENT_ID'), env.get('ZOOM_CLIENT_SECRET'), env.get('ZOOM_ACCOUNT_ID')
    if not (cid and sec and acct):
        sys.exit('ZOOM_ACCOUNT_ID / ZOOM_CLIENT_ID / ZOOM_CLIENT_SECRET must all be set in scripts/.env')
    body = urllib.parse.urlencode({'grant_type': 'account_credentials', 'account_id': acct}).encode()
    basic = base64.b64encode((cid + ':' + sec).encode()).decode()
    req = urllib.request.Request(OAUTH, data=body, method='POST')
    req.add_header('Authorization', 'Basic ' + basic)
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req) as r:
            tok = json.load(r).get('access_token')
    except urllib.error.HTTPError as e:
        sys.exit('Zoom OAuth failed (' + str(e.code) + '): ' + e.read().decode(errors='replace'))
    if not tok:
        sys.exit('Zoom OAuth returned no access_token — check credentials and that the app is Activated.')
    return tok


def api(method, path, body=None, params=None):
    if params:
        clean = {k: v for k, v in params.items() if v is not None}
        if clean:
            path += ('&' if '?' in path else '?') + urllib.parse.urlencode(clean)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + _token())
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return json.loads(raw) if raw else {'status': 'ok', 'code': r.status}
    except urllib.error.HTTPError as e:
        raw = e.read()
        try:
            return json.loads(raw)
        except ValueError:
            return {'code': e.code, 'message': raw.decode(errors='replace')}


def out(resp):
    '''Pretty-print a response; exit non-zero on a Zoom API error.'''
    print(json.dumps(resp, indent=2, ensure_ascii=False))
    # Zoom error bodies carry numeric "code" + "message"; success payloads don't.
    if isinstance(resp, dict) and 'code' in resp and 'message' in resp and resp.get('status') != 'ok':
        sys.exit('Zoom API error ' + str(resp['code']) + ': ' + str(resp['message']))


if __name__ == '__main__':
    sample = "# c\nZOOM_CLIENT_ID='abc'\nZOOM_ACCOUNT_ID=xyz\n\nNOEQ\n"
    assert _parse_env(sample) == {'ZOOM_CLIENT_ID': 'abc', 'ZOOM_ACCOUNT_ID': 'xyz'}
    print('ok')
