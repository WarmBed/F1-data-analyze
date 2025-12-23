"""
Parts Analysis 離線測試（使用本地 JSON）
測試所有功能：匯入、數據載入、篩選器、顏色標記、統計
"""

import sys
import json
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow, QMessageBox
from PyQt5.QtCore import QTimer

# 匯入測試
print("=" * 80)
print("📋 測試 1: 模組匯入")
print("=" * 80)

try:
    from modules.gui.partupdated_analysis import PartsAnalysisMDI, PartsAnalysisWidget
    print("✅ PartsAnalysisMDI 匯入成功")
    print("✅ PartsAnalysisWidget 匯入成功")
except Exception as e:
    print(f"❌ 匯入失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("📋 測試 2: 載入本地 JSON 數據")
print("=" * 80)

# 讀取本地 JSON
json_file = "2025_f1_parts_changes_v2_classified_with_categories.json"
try:
    with open(json_file, 'r', encoding='utf-8') as f:
        local_data = json.load(f)
    print(f"✅ 本地 JSON 載入成功: {json_file}")
    print(f"   - 記錄數: {len(local_data)}")
except Exception as e:
    print(f"❌ 本地 JSON 載入失敗: {e}")
    sys.exit(1)

# 構建 API 格式的數據
api_data = {
    "success": True,
    "message": "本地測試數據",
    "function_id": 29,
    "year": 2025,
    "records": local_data,
    "metadata": {
        "total_records": len(local_data),
        "data_source": "local_json"
    },
    "statistics": {
        "total": len(local_data)
    }
}

print("\n" + "=" * 80)
print("📋 測試 3: 創建 GUI 視窗")
print("=" * 80)

app = QApplication(sys.argv)

# 創建主視窗
main_window = QMainWindow()
main_window.setWindowTitle("Parts Analysis 離線測試 (本地 JSON)")
main_window.resize(1400, 800)

# 創建 MDI 區域
mdi_area = QMdiArea()
main_window.setCentralWidget(mdi_area)

# 創建 Parts Analysis Widget（直接創建 Widget，不經過 MDI）
try:
    print("🚀 創建 PartsAnalysisWidget...")
    parts_widget = PartsAnalysisWidget(
        api_base_url="https://localhost:8000",
        year="2025"
    )
    print("✅ PartsAnalysisWidget 創建成功")
    
    # 創建子視窗
    parts_sub = QMdiSubWindow()
    parts_sub.setWidget(parts_widget)
    parts_sub.setWindowTitle("FIA Parts Analysis 2025 (離線測試)")
    parts_sub.resize(1200, 700)
    
    # 添加到 MDI 區域
    mdi_area.addSubWindow(parts_sub)
    parts_sub.show()
    print("✅ MDI 子視窗創建成功")
    
except Exception as e:
    print(f"❌ 創建失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 80)
print("📋 測試 4: 手動載入數據")
print("=" * 80)

try:
    print("📦 手動調用 on_data_loaded()...")
    parts_widget.on_data_loaded(api_data)
    print("✅ 數據載入成功")
except Exception as e:
    print(f"❌ 數據載入失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("📋 測試 5-8: 篩選器、顏色標記、統計功能")
print("=" * 80)
print("💡 GUI 視窗已啟動，請手動測試以下功能：")
print("")
print("✅ 測試清單:")
print("   1. ✓ 檢查表格是否載入記錄")
print("   2. ✓ 測試賽事篩選器 (Race)")
print("   3. ✓ 測試車隊篩選器 (Team)")
print("   4. ✓ 測試車手篩選器 (Driver)")
print("   5. ✓ 測試主分類篩選器 (Main Category)")
print("   6. ✓ 測試子分類篩選器 (Sub Category)")
print("      ⚠️  重點測試：子分類應根據主分類動態更新")
print("   7. ✓ 測試變更類型篩選器 (Change Type)")
print("   8. ✓ 測試關鍵字搜尋")
print("   9. ✓ 檢查顏色標記:")
print("      - Major Update: 淺紅色 (#f5c6cb)")
print("      - Change: 淺綠色 (#d4edda)")
print("      - Repair: 淺黃色 (#fff3cd)")
print("      - Parameter Adjustment: 淺青色 (#d1ecf1)")
print("  10. ✓ 檢查信心度顏色:")
print("      - ≥0.95: 深綠色")
print("      - ≥0.80: 淺青色")
print("      - ≥0.70: 淺黃色")
print("      - ≥0.60: 淺橙色")
print("      - <0.60: 淺紅色")
print("  11. ✓ 檢查統計摘要列:")
print("      - 總記錄數")
print("      - 平均信心度")
print("      - 各類型統計")
print("")
print("⌨️  按 Ctrl+C 結束測試")
print("=" * 80)

# 顯示主視窗
main_window.show()

# 設定 2 秒後輸出狀態
def check_status():
    print("\n" + "=" * 80)
    print("📊 2 秒後狀態檢查")
    print("=" * 80)
    
    # 檢查 Widget 狀態
    if hasattr(parts_widget, 'all_records'):
        record_count = len(parts_widget.all_records)
        filtered_count = parts_widget.table.rowCount()
        print(f"✅ 數據狀態:")
        print(f"   - 總記錄數: {record_count}")
        print(f"   - 表格顯示: {filtered_count} 行")
        
        # 檢查篩選器
        if hasattr(parts_widget, 'race_filter'):
            race_count = parts_widget.race_filter.count()
            team_count = parts_widget.team_filter.count()
            driver_count = parts_widget.driver_filter.count()
            main_cat_count = parts_widget.main_category_filter.count()
            sub_cat_count = parts_widget.sub_category_filter.count()
            type_count = parts_widget.type_filter.count()
            
            print(f"\n✅ 篩選器選項:")
            print(f"   - 賽事: {race_count} 個選項")
            print(f"   - 車隊: {team_count} 個選項")
            print(f"   - 車手: {driver_count} 個選項")
            print(f"   - 主分類: {main_cat_count} 個選項")
            print(f"   - 子分類: {sub_cat_count} 個選項")
            print(f"   - 變更類型: {type_count} 個選項")
        
        # 檢查統計
        if hasattr(parts_widget, 'stats_label'):
            stats_text = parts_widget.stats_label.text()
            print(f"\n✅ 統計摘要:")
            print(f"   {stats_text}")
        
        print("\n💡 所有功能已就緒，請在 GUI 中手動測試篩選和顏色標記")
    else:
        print("⚠️  Widget 狀態異常")
    
    print("=" * 80)

QTimer.singleShot(2000, check_status)

# 執行應用程式
sys.exit(app.exec_())
