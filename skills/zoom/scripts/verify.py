#!/usr/bin/env python3
'''Verify the Zoom credentials work (cheapest authed call).'''
from _client import api, out

out(api('GET', '/users/me'))
