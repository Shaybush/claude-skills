#!/usr/bin/env python3
'''Delete a DNS record by ID (find the ID with dns_list.py).'''
import argparse
from _cf import api, out, zone_id

p = argparse.ArgumentParser(description='Delete a DNS record from a Cloudflare zone.')
p.add_argument('--zone', required=True, help='zone name, e.g. example.com')
p.add_argument('--id', required=True, help='record ID from dns_list.py')
a = p.parse_args()

out(api('DELETE', '/zones/' + zone_id(a.zone) + '/dns_records/' + a.id))
