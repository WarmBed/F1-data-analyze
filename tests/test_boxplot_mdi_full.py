"""
完整測試 Lap Box Plot MDI 模組
模擬 GUI 中打開 MDI 視窗並更新參數的完整流程
"""

import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

# 必須先導入 PyQt5
from PyQt5.QtWidgets import QApplication, QMainWindow, QMdiArea
from PyQt5.QtCore import QTimer
import time

print("=" * 80)
print("[完整測試] Lap Time Box Plot MDI 模組")
print("=" * 80)

# 創建 QApplication
app = QApplication(sys.argv)

# 創建主視窗和 MDI 區域 (模擬 F1T GUI)
main_window = QMainWindow()
mdi_area = QMdiArea()
main_window.setCentralWidget(mdi_area)
main_window.resize(1400, 900)
main_window.setWindowTitle("測試: Lap Box Plot MDI")

# 導入 MDI 模組
from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi import LapTimeBoxPlotAnalysis
from PyQt5.QtWidgets import QMdiSubWindow

print("\n[1] 創建 Lap Box Plot 分析模組...")
analysis_module = LapTimeBoxPlotAnalysis(parent=None)
print(f"✅ 模組創建完成")
print(f"   - 數據管理器: {type(analysis_module.data_manager).__name__ if analysis_module.data_manager else 'None'}")
print(f"   - 圖表組件: {type(analysis_module.chart_widget).__name__ if analysis_module.chart_widget else 'None'}")

# 檢查信號連接
if hasattr(analysis_module.data_manager, 'data_loaded'):
    print(f"   - data_loaded 信號存在: ✅")
else:
    print(f"   - data_loaded 信號存在: ❌")

print("\n[2] 將模組添加到 MDI 視窗...")
sub_window = QMdiSubWindow()
sub_window.setWidget(analysis_module.get_widget())
sub_window.setWindowTitle("Lap Time Box Plot - 測試")
mdi_area.addSubWindow(sub_window)
sub_window.show()
print(f"✅ MDI 視窗創建完成")

# 顯示主視窗
main_window.show()

# 設置數據接收標誌
data_received = {"success": False, "data": None}

def on_data_loaded_in_mdi(data):
    print("\n[MDI 信號] ✅ 圖表應該已更新!")
    print(f"   - 數據類型: {type(data)}")
    if isinstance(data, dict) and 'driver_laptimes' in data:
        driver_count = len(data['driver_laptimes'])
        total_laps = sum(len(laps) for laps in data['driver_laptimes'].values())
        print(f"   - 車手數: {driver_count}, 總圈數: {total_laps}")
        
        # 檢查圖表組件是否收到數據
        if hasattr(analysis_module, 'chart_widget') and analysis_module.chart_widget:
            chart = analysis_module.chart_widget
            if hasattr(chart, 'driver_laptimes'):
                chart_drivers = len(chart.driver_laptimes) if chart.driver_laptimes else 0
                print(f"   - 圖表內部 driver_laptimes: {chart_drivers} 位車手")
                if chart_drivers > 0:
                    print(f"   ✅ 圖表組件已成功接收數據!")
                else:
                    print(f"   ❌ 圖表組件未收到數據 (driver_laptimes 為空)")
    
    data_received["success"] = True
    data_received["data"] = data

# 連接信號到測試接收器
if hasattr(analysis_module.data_manager, 'data_loaded'):
    analysis_module.data_manager.data_loaded.connect(on_data_loaded_in_mdi)
    print(f"[測試] ✅ 信號已連接到測試接收器")

print("\n[3] 模擬參數更新 (切換到 2025 Japan R)...")
print("   這會觸發數據載入流程...")

# 啟用數據管理器調試
if hasattr(analysis_module.data_manager, '_debug_enabled'):
    analysis_module.data_manager._debug_enabled = True

# 調用 update_lap_parameters (這是 GUI 切換賽事時會調用的方法)
result = analysis_module.update_lap_parameters(
    year="2025",
    race="Japan",
    session="R"
)

print(f"\n   update_lap_parameters() 返回: {result}")

if result:
    print("\n[4] 等待異步數據載入...")
    
    # 設置20秒超時
    timeout_occurred = {"value": False}
    
    def on_timeout():
        timeout_occurred["value"] = True
        print("\n[超時] ⚠️ 20秒內未收到數據")
        print("\n檢查圖表組件狀態:")
        if hasattr(analysis_module, 'chart_widget') and analysis_module.chart_widget:
            chart = analysis_module.chart_widget
            has_data = hasattr(chart, 'driver_laptimes') and chart.driver_laptimes
            print(f"   - 圖表 driver_laptimes: {'有數據' if has_data else '無數據'}")
            if has_data:
                print(f"   - 車手數: {len(chart.driver_laptimes)}")
        app.quit()
    
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(on_timeout)
    timeout_timer.start(20000)
    
    # 設置成功後自動關閉
    def check_success():
        if data_received["success"]:
            timeout_timer.stop()
            print("\n✅ 數據載入成功,5秒後自動關閉...")
            QTimer.singleShot(5000, app.quit)
    
    success_timer = QTimer()
    success_timer.timeout.connect(check_success)
    success_timer.start(500)  # 每0.5秒檢查一次
    
    # 啟動事件循環
    app.exec_()
    
    print("\n" + "=" * 80)
    print("[測試結果]")
    print("=" * 80)
    
    if data_received["success"]:
        print("✅ 測試成功: MDI 模組完整數據流正常")
        
        # 最終檢查圖表狀態
        if hasattr(analysis_module, 'chart_widget') and analysis_module.chart_widget:
            chart = analysis_module.chart_widget
            if hasattr(chart, 'driver_laptimes') and chart.driver_laptimes:
                driver_count = len(chart.driver_laptimes)
                print(f"\n圖表最終狀態:")
                print(f"   - 車手數量: {driver_count}")
                print(f"   - 應該顯示箱型圖: ✅")
            else:
                print(f"\n⚠️ 圖表最終狀態: driver_laptimes 為空")
                print(f"   - 可能原因: _update_chart() 未正確調用 chart_widget.update_data()")
    elif timeout_occurred["value"]:
        print("❌ 測試超時: 20秒內未收到數據")
        print("\n可能原因:")
        print("   1. API 服務器未運行且本地 JSON 不存在")
        print("   2. 數據載入發生異常")
        print("   3. 信號未正確觸發")
    else:
        print("❌ 測試失敗: 未知原因")
        
else:
    print("\n❌ update_lap_parameters() 返回 False")
    print("   參數更新失敗,未啟動數據載入")

print("\n💡 調試建議:")
print("   - 查看控制台中的 [BOXPLOT_MDI] 和 [BOXPLOT_DATA] 調試輸出")
print("   - 確認 JSON 檔案存在: json/detailed_laptime_analysis_2025_Japan_R_all_drivers.json")
print("   - 檢查 _update_chart() 方法是否被調用")
