#!/usr/bin/env python3
'''Delete a zone (domain). Irreversible — removes the domain and its records.'''
import argparse
from _cf import api, out, zone_id

p = argparse.ArgumentParser(description='Delete a Cloudflare zone (domain).')
p.add_argument('--name', required=True, help='domain to delete')
a = p.parse_args()

out(api('DELETE', '/zones/' + zone_id(a.name)))
