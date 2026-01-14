"""測試 F1 Team Radio API"""
import requests

url = "https://livetiming.formula1.com/static/2025/2025-12-07_Abu_Dhabi_Grand_Prix/2025-12-07_Race/TeamRadio.jsonStream"
r = requests.get(url, timeout=30)
print(f"HTTP: {r.status_code}")
print(f"Size: {len(r.content)/1024:.2f} KB")
print(f"Lines: {len(r.text.strip().splitlines())}")

# 統計車手
import json
records = []
for line in r.text.strip().splitlines():
    if len(line) > 12:
        try:
            data = json.loads(line[12:])
            if 'Captures' in data:
                caps = data['Captures']
                if isinstance(caps, list):
                    for c in caps:
                        if 'RacingNumber' in c:
                            records.append(c['RacingNumber'])
                elif isinstance(caps, dict):
                    for k, c in caps.items():
                        if isinstance(c, dict) and 'RacingNumber' in c:
                            records.append(c['RacingNumber'])
        except:
            pass

print(f"\n車手統計 ({len(records)} 筆記錄):")
from collections import Counter
for num, count in Counter(records).most_common():
    print(f"  車手 {num}: {count} 筆")
