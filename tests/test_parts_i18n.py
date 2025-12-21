#!/usr/bin/env python3
"""測試 Parts Analysis 多國語言化"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from core.gui_i18n import tr

print("=" * 60)
print("🌐 Parts Analysis 多國語言化測試")
print("=" * 60)

# 所有需要翻譯的 key
translation_keys = [
    # 篩選工具列
    ('race', 'Race'),
    ('all_races', 'All Races'),
    ('team', 'Team'),
    ('all_teams', 'All Teams'),
    ('driver', 'Driver'),
    ('all_drivers', 'All Drivers'),
    ('main_category', 'Main Cat'),
    ('all_main_categories', 'All Main Categories'),
    ('sub_category', 'Sub Cat'),
    ('all_sub_categories', 'All Sub Categories'),
    ('change_type', 'Type'),
    ('all_types', 'All Types'),
    ('search_description', 'Search description or keywords...'),
    
    # 表格標題
    ('sequence_number', 'No.'),
    ('confidence', 'Confidence'),
    ('description', 'Description'),
    ('part', 'Part'),
    ('date', 'Date'),
    
    # 統計列
    ('loading', 'Loading...'),
    ('no_data', 'No data'),
    ('total_records', 'Total Records'),
    ('avg_confidence', 'Avg Confidence'),
    ('repair', 'Repair'),
    ('major_update', 'Major'),
    ('change', 'Change'),
    ('param_adj', 'Param Adj'),
    ('other', 'Other'),
    
    # 錯誤訊息
    ('error', 'Error'),
    
    # 視窗標題
    ('fia_parts_analysis', 'FIA Parts Analysis Widget - API-ONLY Test'),
    ('fia_parts_analysis_test', 'FIA Parts Analysis Test'),
]

print("\n測試所有翻譯鍵:")
print("-" * 60)

for key, fallback in translation_keys:
    translated = tr(key, fallback)
    status = "✅" if translated else "❌"
    print(f"{status} {key:30} → {translated}")

print("\n" + "=" * 60)
print("✅ 測試完成")
print("=" * 60)
