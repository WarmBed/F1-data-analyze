#!/usr/bin/env python3
"""
簡單測試 Sector Comparison 表格 Import
"""

print("🧪 測試 1: Import 模組...")
try:
    from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget import (
        IdealLapSectorComparisonTableWidget
    )
    print("✅ Import 成功")
except Exception as e:
    print(f"❌ Import 失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🧪 測試 2: 創建 Widget...")
try:
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = IdealLapSectorComparisonTableWidget()
    print("✅ Widget 創建成功")
    print(f"   表格欄位數: {widget.table.columnCount()}")
    print(f"   表格行數: {widget.table.rowCount()}")
except Exception as e:
    print(f"❌ Widget 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🧪 測試 3: 載入數據...")
try:
    import json
    with open('json/ideal_lap_ranking_2025_Australia_R.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ 數據載入成功")
    print(f"   車手數量: {len(data['analysis_result']['ranking'])}")
    
    # 測試數據結構
    first_driver = data['analysis_result']['ranking'][0]
    print(f"   第一名: {first_driver['driver']}")
    print(f"   S1 delta: {first_driver['sector_breakdown']['sector_1'].get('delta')}")
    print(f"   S2 delta: {first_driver['sector_breakdown']['sector_2'].get('delta')}")
    print(f"   S3 delta: {first_driver['sector_breakdown']['sector_3'].get('delta')}")
    
except Exception as e:
    print(f"❌ 數據載入失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n🧪 測試 4: 更新表格...")
try:
    widget.update_data(data)
    print(f"✅ 表格更新成功")
    print(f"   表格行數: {widget.table.rowCount()}")
    print(f"   max_cumulative: {widget.max_cumulative:.3f}s")
except Exception as e:
    print(f"❌ 表格更新失敗: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n✅ 所有測試通過！")
print("💡 提示: 如果所有測試都通過，表格版本應該可以正常運行")
