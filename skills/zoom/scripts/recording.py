#!/usr/bin/env python3
'''Get cloud-recording links for a meeting, or list a user's recent recordings.

With a meeting id: prints that meeting's share_url + per-file play_urls, then the
full JSON. Without one: lists the user's recordings in a date range.
'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='Get Zoom cloud recording links.')
p.add_argument('meeting_id', nargs='?', help='meeting id or uuid (omit to list user recordings)')
p.add_argument('--user', default='me')
p.add_argument('--from', dest='frm', help='list mode: start date YYYY-MM-DD')
p.add_argument('--to', dest='to', help='list mode: end date YYYY-MM-DD')
a = p.parse_args()

if a.meeting_id:
    resp = api('GET', '/meetings/' + a.meeting_id + '/recordings')
    if isinstance(resp, dict) and resp.get('share_url'):
        print('share_url: ' + resp['share_url'])
        for f in resp.get('recording_files', []):
            if f.get('play_url'):
                print(f.get('recording_type', 'file') + ': ' + f['play_url'])
        print('---')
    out(resp)
else:
    out(api('GET', '/users/' + a.user + '/recordings', params={'from': a.frm, 'to': a.to}))
