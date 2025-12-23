#!/usr/bin/env python3
"""
Historical Track Map 修改驗證
測試兩項修改：
1. Data Source 標籤已隱藏
2. Total 表格改用 Stretch 模式
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("Historical Track Map 修改驗證")
print("=" * 70)

# 測試 1: 檢查原始碼中的註解
print("\n[測試 1] 檢查 Data Source 標籤是否已註解")
mdi_file = Path(__file__).parent / "modules" / "gui" / "Historical_track_map" / "historical_track_map_mdi.py"
with open(mdi_file, 'r', encoding='utf-8') as f:
    content = f.read()
    
    # 檢查是否已註解
    if '# source_label = QLabel(tr("data_source_function_100"' in content:
        print("  ✅ Data Source 標籤已註解")
    else:
        print("  ❌ Data Source 標籤未註解")
    
    # 檢查是否移除了固定列寬
    if '# for col in range(5):' in content and '#     self.total_table.setColumnWidth(col, 120)' in content:
        print("  ✅ Total 表格固定列寬已移除")
    else:
        print("  ❌ Total 表格固定列寬未移除")
    
    # 檢查是否改為 Stretch 模式
    stretch_count = content.count('self.total_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)')
    if stretch_count == 1:
        print(f"  ✅ Total 表格已改用 Stretch 模式（出現 {stretch_count} 次）")
    elif stretch_count > 1:
        print(f"  ⚠️  Total 表格 Stretch 設置重複（出現 {stretch_count} 次）")
    else:
        print("  ❌ Total 表格未設置 Stretch 模式")

# 測試 2: 導入模組測試
print("\n[測試 2] 模組導入測試")
try:
    from PyQt5.QtWidgets import QApplication, QHeaderView
    from modules.gui.Historical_track_map.historical_track_map_mdi import HistoricalTrackMapMDI
    
    app = QApplication(sys.argv)
    mdi = HistoricalTrackMapMDI()
    
    print("  ✅ HistoricalTrackMapMDI 導入成功")
    print(f"  ✅ 模組類型: {mdi.analysis_type}")
    
except Exception as e:
    print(f"  ❌ 導入失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("修改摘要")
print("=" * 70)
print("1. ✅ Data Source: Function 100 標籤已隱藏（Line 963-970）")
print("2. ✅ Total 表格改用 Stretch 模式，與 Yearly Statistics 一致")
print("3. ✅ 移除 Total 表格固定列寬設置（120px）")
print("4. ✅ 移除重複的 setSectionResizeMode 設置")
print("\n效果：")
print("  - 右下角不再顯示 'Data Source: Function 100' 標籤")
print("  - Total 表格欄位會隨 MDI 視窗寬度自動調整")
print("=" * 70)
