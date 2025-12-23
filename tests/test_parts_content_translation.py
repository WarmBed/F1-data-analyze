#!/usr/bin/env python3
"""測試 Parts Analysis 內容翻譯功能"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from modules.gui.partupdated_analysis.parts_analysis_widget import (
    CHANGE_TYPE_TRANSLATION_MAP,
    MAIN_CATEGORY_TRANSLATION_MAP,
    SUB_CATEGORY_TRANSLATION_MAP
)
from core.gui_i18n import tr

print("=" * 80)
print("🌐 Parts Analysis 內容翻譯測試")
print("=" * 80)

# 測試 1: 變更類型翻譯
print("\n📋 測試 1: 變更類型翻譯（JSON 中文 → 多國語言）")
print("-" * 80)
test_change_types = [
    "維修 (Repair)",
    "重大更新 (Major Update)",
    "變更 (Change)",
    "參數調整 (Parameter Adjustment)",
]

for change_type in test_change_types:
    trans_key = CHANGE_TYPE_TRANSLATION_MAP.get(change_type)
    if trans_key:
        translated = tr(trans_key, change_type)
        print(f"  {change_type:35} → {trans_key:20} → {translated}")
    else:
        print(f"  {change_type:35} → ❌ 無映射")

# 測試 2: 主分類翻譯
print("\n📋 測試 2: 主分類翻譯（英文 → 多國語言）")
print("-" * 80)
test_main_categories = [
    "Aerodynamics",
    "Cooling",
    "Powertrain",
    "Brakes",
    "Suspension",
]

for category in test_main_categories:
    trans_key = MAIN_CATEGORY_TRANSLATION_MAP.get(category)
    if trans_key:
        translated = tr(trans_key, category)
        print(f"  {category:25} → {trans_key:20} → {translated}")
    else:
        print(f"  {category:25} → ❌ 無映射")

# 測試 3: 子分類翻譯
print("\n📋 測試 3: 子分類翻譯（英文 → 多國語言）")
print("-" * 80)
test_sub_categories = [
    "Front Wing",
    "Rear Wing",
    "ICE",
    "Radiators",
    "Brake Discs",
    "Gearbox",
]

for category in test_sub_categories:
    trans_key = SUB_CATEGORY_TRANSLATION_MAP.get(category)
    if trans_key:
        translated = tr(trans_key, category)
        print(f"  {category:25} → {trans_key:20} → {translated}")
    else:
        print(f"  {category:25} → ❌ 無映射")

# 統計資訊
print("\n" + "=" * 80)
print("📊 統計資訊")
print("-" * 80)
print(f"  變更類型映射: {len(CHANGE_TYPE_TRANSLATION_MAP)} 個")
print(f"  主分類映射:   {len(MAIN_CATEGORY_TRANSLATION_MAP)} 個")
print(f"  子分類映射:   {len(SUB_CATEGORY_TRANSLATION_MAP)} 個")
print(f"  總計:         {len(CHANGE_TYPE_TRANSLATION_MAP) + len(MAIN_CATEGORY_TRANSLATION_MAP) + len(SUB_CATEGORY_TRANSLATION_MAP)} 個映射")

print("\n" + "=" * 80)
print("✅ 測試完成")
print("=" * 80)
