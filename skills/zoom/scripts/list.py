#!/usr/bin/env python3
'''List a user's Zoom meetings.'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='List Zoom meetings.')
p.add_argument('--type', default='upcoming',
               help='scheduled | live | upcoming | previous_meetings (default upcoming)')
p.add_argument('--user', default='me')
p.add_argument('--limit', type=int, default=30, help='page size (default 30, max 300)')
a = p.parse_args()

out(api('GET', '/users/' + a.user + '/meetings', params={'type': a.type, 'page_size': a.limit}))
