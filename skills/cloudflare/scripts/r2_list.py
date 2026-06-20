#!/usr/bin/env python3
'''List R2 buckets.'''
from _cf import api, out

out(api('GET', '/accounts/{account}/r2/buckets'))
