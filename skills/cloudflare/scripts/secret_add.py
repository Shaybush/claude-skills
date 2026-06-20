#!/usr/bin/env python3
'''Add a secret to the account Secrets Store.

Uses --store if given, else the first existing store, else creates 'default_store'.
'''
import argparse
from _cf import api, out

p = argparse.ArgumentParser(description='Add a secret to the Cloudflare Secrets Store.')
p.add_argument('--name', required=True, help='secret name')
p.add_argument('--value', required=True, help='secret value')
p.add_argument('--store', help='store ID (default: first store, created if none)')
p.add_argument('--scope', default='workers', help='comma-separated scopes')
a = p.parse_args()

store = a.store
if not store:
    stores = api('GET', '/accounts/{account}/secrets_store/stores').get('result') or []
    if stores:
        store = stores[0]['id']
    else:
        store = api('POST', '/accounts/{account}/secrets_store/stores',
                    {'name': 'default_store'})['result']['id']

body = [{'name': a.name, 'value': a.value, 'scopes': a.scope.split(',')}]
out(api('POST', '/accounts/{account}/secrets_store/stores/' + store + '/secrets', body))
