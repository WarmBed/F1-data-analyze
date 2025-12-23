#!/usr/bin/env python3
"""測試 team_slug 映射功能"""

from modules.gui.constructor_standings.constructor_standings_data_loader import ConstructorStandingsDataLoader
from pathlib import Path
import json

# 測試 1: 載入 team_slug 映射
print("=" * 60)
print("測試 1: team_slug 映射載入")
print("=" * 60)

loader = ConstructorStandingsDataLoader('2025')
mapping = loader._load_team_slug_mapping()

print(f"\n✅ 總共載入 {len(mapping)} 個映射")
print("\n關鍵映射:")
print(f"  RB → {mapping.get('RB', 'NOT FOUND')}")
print(f"  Sauber → {mapping.get('Sauber', 'NOT FOUND')}")
print(f"  Red Bull → {mapping.get('Red Bull', 'NOT FOUND')}")
print(f"  McLaren → {mapping.get('McLaren', 'NOT FOUND')}")

# 測試 2: 讀取並轉換數據
print("\n" + "=" * 60)
print("測試 2: 數據轉換（含 team_slug）")
print("=" * 60)

# 直接載入最新的 JSON
json_dir = Path("json")
json_files = list(json_dir.glob("championship_standings_2025_*.json"))
if json_files:
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"\n✅ 找到 JSON: {latest_file.name}")
    
    with open(latest_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
    
    transformed = loader._transform_data_for_display(raw_data)
    standings = transformed.get("standings", [])
    
    print(f"\n✅ 轉換 {len(standings)} 支車隊")
    print("\n前 5 支車隊的 team_slug:")
    for i, entry in enumerate(standings[:5], 1):
        team_name = entry.get("constructor_name")
        team_slug = entry.get("team_slug")
        print(f"  {i}. {team_name:15} → {team_slug}")
    
    # 特別檢查 RB 和 Sauber
    print("\n特別檢查 RB 和 Sauber:")
    for entry in standings:
        team_name = entry.get("constructor_name")
        if team_name in ["RB", "Sauber"]:
            team_slug = entry.get("team_slug")
            print(f"  ✅ {team_name:15} → {team_slug}")
else:
    print("\n❌ 找不到 championship_standings JSON")

