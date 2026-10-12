#!/usr/bin/env python3
'''Rename a Zoom meeting (and optionally reschedule / change agenda).'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='Rename / update a Zoom meeting.')
p.add_argument('meeting_id')
p.add_argument('--topic', help='new title')
p.add_argument('--start', help='new ISO8601 start, e.g. 2026-06-25T16:00:00')
p.add_argument('--duration', type=int, help='new duration (minutes)')
p.add_argument('--tz', help='new IANA timezone')
p.add_argument('--agenda')
a = p.parse_args()

body = {}
if a.topic:
    body['topic'] = a.topic
if a.start:
    body['start_time'] = a.start
if a.duration:
    body['duration'] = a.duration
if a.tz:
    body['timezone'] = a.tz
if a.agenda:
    body['agenda'] = a.agenda
if not body:
    raise SystemExit('Nothing to update — pass at least one of --topic/--start/--duration/--tz/--agenda')

out(api('PATCH', '/meetings/' + a.meeting_id, body))
