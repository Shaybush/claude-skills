#!/usr/bin/env python3
'''Create a new domain (zone) on the account.

Returns name_servers in .result — the user must set those at their registrar
before the zone activates.
'''
import argparse
from _cf import api, out, account_id

p = argparse.ArgumentParser(description='Add a new domain (zone) to Cloudflare.')
p.add_argument('--name', required=True, help='domain, e.g. example.com')
p.add_argument('--type', default='full', choices=['full', 'partial'],
               help='full = Cloudflare authoritative DNS (default)')
a = p.parse_args()

body = {'account': {'id': account_id()}, 'name': a.name, 'type': a.type}
out(api('POST', '/zones', body))
