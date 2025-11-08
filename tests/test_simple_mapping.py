#!/usr/bin/env python3
"""簡化測試：只測試映射載入"""

import sys
sys.path.insert(0, 'C:\\Users\\mike2\\OneDrive\\Code\\F1-data-analyze')

from pathlib import Path
import json

print("=" * 60)
print("測試: team_slug 映射載入")
print("=" * 60)

json_dir = Path("json")
team_color_files = list(json_dir.glob("team_colors_2025_*.json"))

if not team_color_files:
    print("❌ 找不到 team_colors JSON")
    sys.exit(1)

latest_file = max(team_color_files, key=lambda p: p.stat().st_mtime)
print(f"\n✅ 載入: {latest_file.name}")

with open(latest_file, "r", encoding="utf-8") as f:
    color_data = json.load(f)

# 正確的路徑是 data.teams (不是 team_palette)
teams_data = color_data.get("data", {}).get("teams", {})
team_slug_map = {}

for team_slug, info in teams_data.items():
    team_name = info.get("team_name")
    if team_name:
        team_slug_map[team_name] = team_slug

print(f"\n✅ 總共載入 {len(team_slug_map)} 個映射")
print("\n關鍵映射:")
print(f"  RB → {team_slug_map.get('RB', 'NOT FOUND')}")
print(f"  Sauber → {team_slug_map.get('Sauber', 'NOT FOUND')}")
print(f"  Red Bull → {team_slug_map.get('Red Bull', 'NOT FOUND')}")
print(f"  McLaren → {team_slug_map.get('McLaren', 'NOT FOUND')}")

# 測試數據轉換
print("\n" + "=" * 60)
print("測試: 數據轉換（含 team_slug）")
print("=" * 60)

standings_files = list(json_dir.glob("championship_standings_2025_*.json"))
if not standings_files:
    print("❌ 找不到 championship_standings JSON")
    sys.exit(1)

latest_standings = max(standings_files, key=lambda p: p.stat().st_mtime)
print(f"\n✅ 載入: {latest_standings.name}")

with open(latest_standings, "r", encoding="utf-8") as f:
    standings_data = json.load(f)

constructors = standings_data.get("data", {}).get("constructors", [])
print(f"\n✅ 找到 {len(constructors)} 支車隊")

print("\n前 5 支車隊的映射:")
for i, entry in enumerate(constructors[:5], 1):
    constructor_info = entry.get("constructor", {})
    team_name = constructor_info.get("name", "Unknown").replace(" F1 Team", "").strip()
    team_slug = team_slug_map.get(team_name, team_name.lower())
    print(f"  {i}. {team_name:15} → {team_slug}")

print("\n特別檢查 RB 和 Sauber:")
for entry in constructors:
    constructor_info = entry.get("constructor", {})
    team_name = constructor_info.get("name", "Unknown").replace(" F1 Team", "").strip()
    if team_name in ["RB", "Sauber"]:
        team_slug = team_slug_map.get(team_name, team_name.lower())
        print(f"  ✅ {team_name:15} → {team_slug}")
