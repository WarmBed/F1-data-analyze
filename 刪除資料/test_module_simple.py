#!/usr/bin/env python3
"""簡單的模組測試"""

import sys
sys.path.insert(0, 'd:\\OneDrive\\Code\\F1-data-analyze')

print("開始測試...")

from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
print("✅ 導入成功")

module = IdealLapRankingTableModule(parent=None, year=2024, race='Japan', session='R')
print("✅ 創建成功")

print(f"標題: {module.get_title()}")
print(f"尺寸: {module.get_default_size()}")
print(f"名稱: {module.module_name}")

print("✅ 所有測試通過")
