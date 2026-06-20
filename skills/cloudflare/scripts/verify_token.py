#!/usr/bin/env python3
'''Verify the API token is active.'''
from _cf import api, out

out(api('GET', '/accounts/{account}/tokens/verify'))
