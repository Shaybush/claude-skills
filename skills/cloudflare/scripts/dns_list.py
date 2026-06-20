#!/usr/bin/env python3
'''List DNS records on a zone (optionally filter by name).'''
import argparse
from _cf import api, out, zone_id

p = argparse.ArgumentParser(description='List DNS records on a Cloudflare zone.')
p.add_argument('--zone', required=True, help='zone name, e.g. example.com')
p.add_argument('--name', help='filter to this record name')
a = p.parse_args()

path = '/zones/' + zone_id(a.zone) + '/dns_records'
if a.name:
    path += '?name=' + a.name
out(api('GET', path))
