#!/usr/bin/env python3
'''List zones (domains); with --name, resolve one domain to its zone ID.'''
import argparse
from _cf import api, out

p = argparse.ArgumentParser(description='List Cloudflare zones.')
p.add_argument('--name', help='filter to this domain (returns its zone ID)')
a = p.parse_args()

path = '/zones?name=' + a.name if a.name else '/zones?per_page=50'
out(api('GET', path))
