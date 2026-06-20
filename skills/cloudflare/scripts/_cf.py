'''Shared Cloudflare v4 API helper.

Loads credentials from .env beside this file and makes authenticated requests.
The verb scripts import api()/out() from here. Claude never reads .env — these
scripts load it at runtime, so credentials are never exposed to the model.

Self-check: python3 _cf.py  ->  prints 'ok'
'''
import json
import os
import sys
import urllib.error
import urllib.request

BASE = 'https://api.cloudflare.com/client/v4'
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


def account_id():
    return _load().get('CF_ACCOUNT_ID', '')


def api(method, path, body=None):
    '''Make an API call. {account} in path is replaced with the account id.'''
    env = _load()
    token = env.get('CF_API_TOKEN')
    if not token:
        sys.exit('CF_API_TOKEN not set in scripts/.env')
    path = path.replace('{account}', env.get('CF_ACCOUNT_ID', ''))
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header('Authorization', 'Bearer ' + token)
    if data is not None:
        req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        return json.load(e)  # Cloudflare returns JSON error bodies


def zone_id(name):
    '''Resolve a domain name to its zone ID, or exit if not found.'''
    res = api('GET', '/zones?name=' + name).get('result') or []
    if not res:
        sys.exit('Zone not found: ' + name)
    return res[0]['id']


def out(resp):
    '''Pretty-print a response; exit non-zero on API failure.'''
    print(json.dumps(resp, indent=2))
    if not resp.get('success', False):
        errs = '; '.join(m.get('message', '') for m in resp.get('errors', []))
        sys.exit('API error: ' + (errs or 'unknown'))


if __name__ == '__main__':
    sample = "# comment\nCF_API_TOKEN='abc'\nCF_ACCOUNT_ID=xyz\n\nNOEQUALS\n"
    assert _parse_env(sample) == {'CF_API_TOKEN': 'abc', 'CF_ACCOUNT_ID': 'xyz'}
    assert '/accounts/X/y' == '/accounts/{account}/y'.replace('{account}', 'X')
    print('ok')
