# -*- coding: utf-8 -*-
import json
import glob

# Find latest calendar file
calendar_files = glob.glob('json/season_calendar_multi_year_*.json')
if not calendar_files:
    print("No calendar files found!")
    exit(1)

latest_calendar = max(calendar_files)
print(f"Using: {latest_calendar}\n")

with open(latest_calendar, encoding='utf-8') as f:
    data = json.load(f)

events = data.get('data', {}).get('2025', [])

print("2025 Season Events with 'Singapore':")
for e in events:
    event_name = e.get('event_name', '')
    if 'singapore' in event_name.lower():
        print(f"  Event Name: {event_name}")
        print(f"  Round: {e.get('round')}")
        print(f"  Race Date: {e.get('race_date_local')}")
        print(f"  Country: {e.get('country')}")
        print()

print("\nAll events (first 5 for reference):")
for i, e in enumerate(events[:5]):
    print(f"{i+1}. {e.get('event_name')} (Round {e.get('round')})")
