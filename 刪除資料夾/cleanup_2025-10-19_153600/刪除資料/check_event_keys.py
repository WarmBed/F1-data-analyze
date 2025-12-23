# -*- coding: utf-8 -*-
import json
import glob

# Find latest calendar file
calendar_files = glob.glob('json/season_calendar_multi_year_*.json')
latest_calendar = max(calendar_files)

with open(latest_calendar, encoding='utf-8') as f:
    data = json.load(f)

events = data.get('data', {}).get('2025', [])

print("Event Name vs Country comparison:")
print("=" * 70)
for e in events[:10]:
    event_name = e.get('event_name', '')
    country = e.get('country', '')
    race_key = e.get('race_key', '')  # Check if race_key exists
    print(f"Event: {event_name:35s} | Country: {country:15s} | Key: {race_key}")
