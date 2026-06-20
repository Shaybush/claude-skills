#!/usr/bin/env python3
'''Get details for one Zoom meeting by id.'''
import argparse
from _client import api, out

p = argparse.ArgumentParser(description='Get a Zoom meeting by id.')
p.add_argument('meeting_id')
a = p.parse_args()

out(api('GET', '/meetings/' + a.meeting_id))
