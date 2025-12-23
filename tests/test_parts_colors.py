#!/usr/bin/env python3
"""測試 Parts Analysis Widget 的顏色映射"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from modules.gui.partupdated_analysis.parts_analysis_widget import DRIVER_NAME_TO_CODE
from modules.gui.themes.color_palette_provider import color_palette_provider

print("=" * 60)
print("🎨 Parts Analysis 顏色映射測試")
print("=" * 60)

# 測試 1: 車手名稱映射
print("\n📋 測試 1: 車手名稱到代碼映射")
print("-" * 60)
print(f"總共映射: {len(DRIVER_NAME_TO_CODE)} 位車手")

test_drivers = [
    "Lando Norris",
    "Max Verstappen",
    "Charles Leclerc",
    "Lewis Hamilton",
    "George Russell"
]

for driver_name in test_drivers:
    code = DRIVER_NAME_TO_CODE.get(driver_name, "未找到")
    print(f"  {driver_name:20} → {code}")

# 測試 2: 顏色獲取
print("\n🎨 測試 2: 通過代碼獲取顏色")
print("-" * 60)

# 確保顏色配置已載入
try:
    color_palette_provider.ensure_loaded(year=2025)
    print("✅ 顏色配置已載入 (2025 賽季)")
except Exception as e:
    print(f"⚠️  顏色配置載入失敗: {e}")

for driver_name in test_drivers:
    code = DRIVER_NAME_TO_CODE.get(driver_name, "???")
    try:
        color = color_palette_provider.get_driver_color(code, fallback=True)
        rgb = f"({color.red()}, {color.green()}, {color.blue()})"
        print(f"  {code:4} → {rgb:20} | {driver_name}")
    except Exception as e:
        print(f"  {code:4} → ERROR: {e}")

print("\n" + "=" * 60)
print("✅ 測試完成")
print("=" * 60)
