"""
測試 Parts Analysis 整合到主 GUI
測試項目：
1. 模組匯入
2. MDI 視窗創建
3. API 調用
4. 數據載入
5. 篩選器功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea, QMdiSubWindow
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
print("📋 測試 2: MDI 視窗創建")
print("=" * 80)

app = QApplication(sys.argv)

# 創建主視窗
main_window = QMainWindow()
main_window.setWindowTitle("Parts Analysis 整合測試")
main_window.resize(1400, 800)

# 創建 MDI 區域
mdi_area = QMdiArea()
main_window.setCentralWidget(mdi_area)

# 創建 Parts Analysis MDI
try:
    print("🚀 創建 PartsAnalysisMDI (year=2025)...")
    parts_mdi = PartsAnalysisMDI(year="2025")
    print("✅ PartsAnalysisMDI 創建成功")
    
    # 創建子視窗
    parts_sub = QMdiSubWindow()
    parts_sub.setWidget(parts_mdi)
    parts_sub.setWindowTitle("FIA Parts Analysis 2025")
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
print("📋 測試 3-5: API 調用、數據載入、篩選器功能")
print("=" * 80)
print("⏳ 等待 API 回應...")
print("💡 提示：GUI 視窗將自動顯示，請在視窗中測試以下功能：")
print("   1. 檢查表格是否載入 475 筆記錄")
print("   2. 測試賽事篩選器（Race）")
print("   3. 測試車隊篩選器（Team）")
print("   4. 測試主分類篩選器（Main Category）")
print("   5. 測試子分類篩選器（Sub Category，應根據主分類動態更新）")
print("   6. 測試變更類型篩選器（Change Type）")
print("   7. 檢查顏色標記（Major=紅、Change=綠、Repair=黃、Param=青）")
print("   8. 檢查統計摘要列（總數、平均信心度、類型統計）")
print("\n⌨️  按 Ctrl+C 結束測試")
print("=" * 80)

# 顯示主視窗
main_window.show()

# 設定 5 秒後輸出狀態
def check_status():
    print("\n" + "=" * 80)
    print("📊 5 秒後狀態檢查")
    print("=" * 80)
    
    # 檢查 Widget 是否有數據
    if hasattr(parts_mdi, 'chart_widget'):
        widget = parts_mdi.chart_widget
        if hasattr(widget, 'all_records'):
            record_count = len(widget.all_records)
            filtered_count = widget.table.rowCount()
            print(f"✅ 數據載入成功")
            print(f"   - 總記錄數: {record_count}")
            print(f"   - 篩選後記錄數: {filtered_count}")
            
            # 檢查篩選器
            if hasattr(widget, 'race_filter'):
                race_count = widget.race_filter.count()
                team_count = widget.team_filter.count()
                main_cat_count = widget.main_category_filter.count()
                sub_cat_count = widget.sub_category_filter.count()
                print(f"   - 賽事選項: {race_count}")
                print(f"   - 車隊選項: {team_count}")
                print(f"   - 主分類選項: {main_cat_count}")
                print(f"   - 子分類選項: {sub_cat_count}")
            
            print("\n💡 請在 GUI 視窗中手動測試篩選器功能")
        else:
            print("⏳ 數據尚未載入，請稍候...")
    else:
        print("⚠️  Widget 尚未初始化")
    
    print("=" * 80)

QTimer.singleShot(5000, check_status)

# 執行應用程式
sys.exit(app.exec_())
