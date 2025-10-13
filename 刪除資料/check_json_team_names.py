#!/usr/bin/env python3
"""檢查 JSON 中的車隊名稱"""

import json

with open("json/championship_standings_2024_R24_20251012T155237Z.json", encoding="utf-8") as f:
    data = json.load(f)

constructors = data["data"]["constructors"]

print("=" * 60)
print("JSON 中的所有車隊名稱")
print("=" * 60)
for c in constructors:
    name = c["constructor"]["name"]
    pos = c["position"]
    print(f"{pos:2d}. {name}")
