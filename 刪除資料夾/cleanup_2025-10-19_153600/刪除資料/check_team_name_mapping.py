#!/usr/bin/env python3
"""檢查車隊名稱映射問題"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.themes.color_palette_provider import ColorPaletteProvider

cp = ColorPaletteProvider()

# 強制載入 2024 年顏色配置
print("=" * 60)
print("強制載入 2024 年顏色配置")
print("=" * 60)
try:
    cp.ensure_loaded(year=2024)
    print("✅ 顏色配置載入成功")
except Exception as e:
    print(f"❌ 顏色配置載入失敗: {e}")

# 測試各種可能的車隊名稱
test_names = [
    'Alpine',
    'Alpine F1 Team',
    'AlpineF1Team',
    'Haas',
    'Haas F1 Team',
    'HaasF1Team',
    'RB',
    'RB F1 Team',
    'RBF1Team',
    'VCARB',
    'Visa Cash App RB',
]

print("=" * 60)
print("車隊名稱顏色映射測試")
print("=" * 60)

for name in test_names:
    color = cp.get_team_color(name)
    # 顯示 RGB 值
    rgb = (color.red(), color.green(), color.blue())
    hex_color = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
    print(f"{name:25s} → RGB{rgb} {hex_color}")

# 檢查 JSON 數據
print("\n" + "=" * 60)
print("檢查本地 JSON 車隊數據")
print("=" * 60)
if cp.teams_data:
    for team_id in list(cp.teams_data.keys())[:5]:
        team = cp.teams_data[team_id]
        print(f"{team_id:15s} → {team.get('team_name', 'N/A'):20s} {team.get('selected_hex', 'N/A')}")
else:
    print("❌ 沒有車隊數據")
