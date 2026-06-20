#!/usr/bin/env python3
'''Create a DNS record (subdomain) on a zone.'''
import argparse
from _cf import api, out, zone_id

p = argparse.ArgumentParser(description='Create a DNS record on a Cloudflare zone.')
p.add_argument('--zone', required=True, help='zone name, e.g. example.com')
p.add_argument('--type', default='A', help='A, AAAA, CNAME, TXT, MX, ... (default A)')
p.add_argument('--name', required=True, help='record name, e.g. sub.example.com or @')
p.add_argument('--content', required=True, help='IP / hostname / text value')
p.add_argument('--ttl', type=int, default=1, help='1 = automatic (default)')
p.add_argument('--priority', type=int, help='MX priority')
p.add_argument('--proxied', action='store_true', help='route through Cloudflare (A/AAAA/CNAME)')
a = p.parse_args()

body = {'type': a.type, 'name': a.name, 'content': a.content,
        'ttl': a.ttl, 'proxied': a.proxied}
if a.priority is not None:
    body['priority'] = a.priority
out(api('POST', '/zones/' + zone_id(a.zone) + '/dns_records', body))
