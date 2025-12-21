#!/usr/bin/env python3
"""最終顏色系統驗證測試"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.gui.themes.color_palette_provider import ColorPaletteProvider

cp = ColorPaletteProvider()
cp.ensure_loaded(year=2024)

print("=" * 70)
print("🎨 F1T 顏色系統最終驗證測試")
print("=" * 70)

# 測試 1: 車隊名稱後綴處理
print("\n✅ 測試 1: 車隊名稱 'F1 Team' 後綴處理")
print("-" * 70)
test_teams = [
    ("Alpine F1 Team", "#FF87BC", "粉色"),
    ("Haas F1 Team", "#B6BABD", "銀灰色"),
    ("RB F1 Team", "#364AA9", "藍色"),
    ("Kick Sauber", "#00E700", "綠色"),
]

for team_name, expected_hex, color_desc in test_teams:
    color = cp.get_team_color(team_name, format="qcolor")
    actual_hex = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
    status = "✅" if actual_hex == expected_hex else "❌"
    print(f"{status} {team_name:25s} → {actual_hex} ({color_desc})")

# 測試 2: 缺失車手的 Fallback
print("\n✅ 測試 2: JSON 中缺失車手的 Fallback 機制")
print("-" * 70)
missing_drivers = [
    ("TSU", "rb", "#364AA9", "RB 藍色"),
    ("RIC", "rb", "#364AA9", "RB 藍色"),
    ("LAW", "red bull", "#0600EF", "Red Bull 深藍"),
]

for code, team, expected_hex, color_desc in missing_drivers:
    color = cp.get_driver_color(code, format="qcolor")
    actual_hex = f"#{color.red():02X}{color.green():02X}{color.blue():02X}"
    status = "✅" if actual_hex == expected_hex else "❌"
    print(f"{status} {code} ({team:10s}) → {actual_hex} ({color_desc})")

# 測試 3: 文字顏色選擇邏輯
print("\n✅ 測試 3: 背景色亮度與文字顏色自動選擇")
print("-" * 70)

def get_text_color(bg_hex: str) -> str:
    """根據背景色計算應該使用的文字顏色"""
    # 移除 # 號
    hex_color = bg_hex.lstrip('#')
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b)
    return "白色" if luminance < 128 else "黑色"

text_color_tests = [
    ("Ferrari", "#E80020", "白色"),
    ("Red Bull", "#0600EF", "白色"),
    ("Mercedes", "#27F4D2", "黑色"),
    ("McLaren", "#FF8000", "黑色"),
    ("RB", "#364AA9", "白色"),
]

for team, bg_hex, expected_text in text_color_tests:
    actual_text = get_text_color(bg_hex)
    status = "✅" if actual_text == expected_text else "❌"
    print(f"{status} {team:12s} (背景 {bg_hex}) → 文字 {actual_text}")

# 測試 4: 所有 2024 正式車隊顏色
print("\n✅ 測試 4: 2024 年所有正式車隊顏色配置")
print("-" * 70)

all_teams = [
    ("Red Bull", "#0600EF"),
    ("Ferrari", "#E80020"),
    ("Mercedes", "#27F4D2"),
    ("McLaren", "#FF8000"),
    ("Aston Martin", "#00665F"),
    ("Alpine", "#FF87BC"),
    ("Haas", "#B6BABD"),
    ("RB", "#364AA9"),
    ("Kick Sauber", "#00E700"),
    ("Williams", "#00A0DD"),
]

for team_name, expected_hex in all_teams:
    color = cp.get_team_color(team_name, format="hex")
    status = "✅" if color == expected_hex else "❌"
    print(f"{status} {team_name:15s} → {color}")

print("\n" + "=" * 70)
print("🎉 顏色系統驗證測試完成")
print("=" * 70)
