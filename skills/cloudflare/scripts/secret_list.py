#!/usr/bin/env python3
'''List secrets in the Secrets Store (metadata only; values are never returned).'''
import argparse
from _cf import api, out

p = argparse.ArgumentParser(description='List Cloudflare Secrets Store secrets.')
p.add_argument('--store', help='store ID (default: first store)')
a = p.parse_args()

store = a.store
if not store:
    stores = api('GET', '/accounts/{account}/secrets_store/stores').get('result') or []
    if not stores:
        out({'success': True, 'errors': [], 'result': []})
        raise SystemExit
    store = stores[0]['id']
out(api('GET', '/accounts/{account}/secrets_store/stores/' + store + '/secrets'))
