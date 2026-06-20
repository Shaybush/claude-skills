#!/usr/bin/env python3
'''Delete (cancel) a Zoom meeting.'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='Delete a Zoom meeting.')
p.add_argument('meeting_id')
p.add_argument('--notify', action='store_true', help='email the host + registrants about the cancellation')
a = p.parse_args()

out(api('DELETE', '/meetings/' + a.meeting_id,
        params={'cancel_meeting_reminder': 'true' if a.notify else 'false'}))
