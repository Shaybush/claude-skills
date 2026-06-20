#!/usr/bin/env python3
'''Delete an R2 bucket (must be empty). Irreversible.'''
import argparse
from _cf import api, out

p = argparse.ArgumentParser(description='Delete a Cloudflare R2 bucket.')
p.add_argument('--name', required=True, help='bucket name')
a = p.parse_args()

out(api('DELETE', '/accounts/{account}/r2/buckets/' + a.name))
