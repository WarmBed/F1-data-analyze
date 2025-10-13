#!/usr/bin/env python3
"""檢查 TSU, RIC, LAW 車手和 Sauber 車隊的顏色問題"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.themes.color_palette_provider import ColorPaletteProvider

cp = ColorPaletteProvider()

# 強制載入 2024 年顏色配置
print("=" * 60)
print("載入 2024 年顏色配置")
print("=" * 60)
cp.ensure_loaded(year=2024)

# 檢查問題車手
print("\n" + "=" * 60)
print("問題車手顏色檢查")
print("=" * 60)

problem_drivers = ["TSU", "RIC", "LAW"]
for code in problem_drivers:
    color = cp.get_driver_color(code, format="qcolor", fallback=True)
    rgb = (color.red(), color.green(), color.blue())
    hex_color = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
    print(f"{code}: RGB{rgb} {hex_color}")

# 檢查 Sauber 車隊
print("\n" + "=" * 60)
print("Sauber 車隊顏色檢查")
print("=" * 60)

sauber_variants = [
    "Sauber",
    "Kick Sauber",
    "Alfa Romeo",
    "Stake F1 Team Kick Sauber",
]

for name in sauber_variants:
    color = cp.get_team_color(name, format="qcolor", fallback=True)
    rgb = (color.red(), color.green(), color.blue())
    hex_color = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
    print(f"{name:30s}: RGB{rgb} {hex_color}")

# 檢查 JSON 中的實際數據
print("\n" + "=" * 60)
print("檢查 team_colors JSON 內容")
print("=" * 60)

import json
import glob

json_files = glob.glob("json/team_colors_2024_*.json")
if json_files:
    latest = max(json_files, key=os.path.getmtime)
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查車隊 slugs
    teams = data.get("data", {}).get("teams", {})
    print(f"\n所有車隊 slugs ({len(teams)} 個):")
    for slug in teams.keys():
        team_name = teams[slug].get("team_name", "")
        print(f"  - '{slug}' → {team_name}")
    
    # 檢查車手
    drivers = data.get("data", {}).get("drivers", {})
    print(f"\n檢查問題車手:")
    for code in ["TSU", "RIC", "LAW"]:
        if code in drivers:
            driver_data = drivers[code]
            print(f"  {code}: team_slug='{driver_data.get('team_slug')}', hex={driver_data.get('hex', 'N/A')}")
        else:
            print(f"  {code}: ❌ 不存在於 JSON 中")
else:
    print("❌ 找不到 team_colors JSON 檔案")
