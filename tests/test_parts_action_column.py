ㄋ"""
測試 Parts Analysis Widget 的 Action 欄位顯示

驗證：
1. 表格有 7 個欄位（新增 Action）
2. Action 欄位顯示 "N/A"
3. Action 欄位為灰色文字
"""

import sys
import json
from PyQt5.QtWidgets import QApplication
from modules.gui.partupdated_analysis.parts_analysis_widget import PartsAnalysisWidget

def test_action_column():
    """測試 Action 欄位"""
    app = QApplication(sys.argv)
    
    # 讀取測試數據
    json_path = "json/fia_parts_analysis_2025_20251110T223130Z.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    print("=" * 80)
    print("Testing Parts Analysis Widget - Action Column")
    print("=" * 80)
    
    # 創建 Widget（提供必要的 api_base_url 參數）
    api_base_url = "https://api.f1telemetrystationpro.org"
    widget = PartsAnalysisWidget(api_base_url=api_base_url)
    
    # 載入數據
    widget.on_data_loaded(data)
    
    # 驗證表格結構
    column_count = widget.table_widget.columnCount()
    print(f"\n✅ Table Structure:")
    print(f"   - Column count: {column_count} (Expected: 7)")
    
    # 檢查欄位標題
    headers = []
    for col in range(column_count):
        header = widget.table_widget.horizontalHeaderItem(col)
        header_text = header.text() if header else "N/A"
        headers.append(header_text)
        print(f"   - Column {col}: {header_text}")
    
    # 驗證 Action 欄位存在
    has_action = "Action" in headers or "action" in [h.lower() for h in headers]
    print(f"\n✅ Action Column: {'FOUND' if has_action else 'NOT FOUND'}")
    
    # 檢查第一行的 Action 值
    if widget.table_widget.rowCount() > 0:
        action_col = column_count - 1  # Action 是最後一欄
        action_item = widget.table_widget.item(0, action_col)
        if action_item:
            action_value = action_item.text()
            action_color = action_item.foreground().color().name()
            print(f"\n✅ First Row Action Value:")
            print(f"   - Text: '{action_value}' (Expected: 'N/A')")
            print(f"   - Color: {action_color} (Expected: #888888 or similar gray)")
            print(f"   - Tooltip: {action_item.toolTip()}")
        else:
            print("\n❌ Action column item is None!")
    
    # 驗證數據行數
    row_count = widget.table_widget.rowCount()
    expected_count = len(data.get('records', []))
    print(f"\n✅ Data Verification:")
    print(f"   - Table rows: {row_count}")
    print(f"   - JSON records: {expected_count}")
    print(f"   - Match: {row_count == expected_count}")
    
    print("\n" + "=" * 80)
    print("Test Completed! Check the results above.")
    print("=" * 80)
    
    # 不顯示 Widget，僅測試結構
    # widget.show()
    
    # 結束應用程式
    app.quit()

if __name__ == "__main__":
    test_action_column()
