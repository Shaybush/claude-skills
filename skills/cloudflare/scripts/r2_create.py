#!/usr/bin/env python3
'''Create an R2 bucket.'''
import argparse
from _cf import api, out

p = argparse.ArgumentParser(description='Create a Cloudflare R2 bucket.')
p.add_argument('--name', required=True, help='bucket name (lowercase, hyphens)')
p.add_argument('--location', help='wnam|enam|weur|eeur|apac|oc')
p.add_argument('--storage-class', default='Standard',
               choices=['Standard', 'InfrequentAccess'])
a = p.parse_args()

body = {'name': a.name, 'storageClass': a.storage_class}
if a.location:
    body['locationHint'] = a.location
out(api('POST', '/accounts/{account}/r2/buckets', body))
