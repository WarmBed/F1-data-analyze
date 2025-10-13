#!/usr/bin/env python3
"""列出 JSON 中的所有車手"""

import json

with open("json/team_colors_2024_fastf1_20251012T172153Z.json", encoding="utf-8") as f:
    data = json.load(f)

drivers = data["data"]["drivers"]

print(f"所有車手 ({len(drivers)} 個):")
print("=" * 60)
for code, d in sorted(drivers.items()):
    team_slug = d.get("team_slug", "N/A")
    full_name = d.get("full_name", "N/A")
    hex_color = d.get("hex", "N/A")
    print(f"{code:4s}: {full_name:25s} {team_slug:15s} {hex_color}")
