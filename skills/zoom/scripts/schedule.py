#!/usr/bin/env python3
'''Schedule (create) a Zoom meeting. Prints the meeting, incl. join_url + id.'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='Schedule a Zoom meeting.')
p.add_argument('--topic', required=True)
p.add_argument('--start', help='ISO8601 local start, e.g. 2026-06-25T15:00:00 (omit for an instant meeting)')
p.add_argument('--duration', type=int, default=30, help='minutes (default 30)')
p.add_argument('--tz', default='UTC', help='IANA timezone, e.g. Asia/Jerusalem (default UTC)')
p.add_argument('--agenda', default=None)
p.add_argument('--password', default=None)
p.add_argument('--user', default='me', help="host user id or email (default 'me')")
a = p.parse_args()

body = {
    'topic': a.topic,
    'type': 2 if a.start else 1,  # 2 = scheduled, 1 = instant
    'duration': a.duration,
    'timezone': a.tz,
}
if a.start:
    body['start_time'] = a.start
if a.agenda:
    body['agenda'] = a.agenda
if a.password:
    body['password'] = a.password

out(api('POST', '/users/' + a.user + '/meetings', body))
