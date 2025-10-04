"""
測試 Lap Box Plot 數據管理器的完整載入流程
模擬 GUI 環境下的數據載入
"""

import sys
from pathlib import Path

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

# 必須先導入 PyQt5
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import time

print("=" * 80)
print("[測試] Lap Time Box Plot 數據管理器載入流程")
print("=" * 80)

# 創建 QApplication (Qt 組件需要)
app = QApplication(sys.argv)

# 導入數據管理器
from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi import LapTimeBoxPlotDataManager

# 創建數據管理器實例
print("\n[1] 創建數據管理器...")
manager = LapTimeBoxPlotDataManager(parent=None)
manager._debug_enabled = True  # 啟用調試輸出
print(f"✅ 數據管理器創建完成")
print(f"   - 允許本地回退: {manager._allow_local_fallback}")
print(f"   - 回退策略: {manager._fallback_policy_reason}")

# 設置信號接收器
data_received = {"success": False, "data": None}

def on_data_loaded(data):
    print("\n[信號] ✅ data_loaded 信號接收成功!")
    print(f"   - 數據類型: {type(data)}")
    if isinstance(data, dict):
        print(f"   - 數據鍵: {list(data.keys())}")
        if 'driver_laptimes' in data:
            driver_count = len(data['driver_laptimes'])
            print(f"   - 車手數量: {driver_count}")
            # 顯示前3位車手的圈數
            for driver, laps in list(data['driver_laptimes'].items())[:3]:
                print(f"      • {driver}: {len(laps)} 圈")
    data_received["success"] = True
    data_received["data"] = data
    app.quit()

def on_load_error(error_message):
    print(f"\n[信號] ❌ load_error 信號接收: {error_message}")
    data_received["success"] = False
    app.quit()

def on_status_changed(status):
    print(f"[狀態] {status}")

# 連接信號
manager.data_loaded.connect(on_data_loaded)
manager.load_error.connect(on_load_error)
manager.status_changed.connect(on_status_changed)

print("\n[2] 開始載入數據 (API 優先模式)...")
print("   測試參數: year=2025, race=Japan, session=R")

result = manager.load_data(year=2025, race="Japan", session="R")
print(f"\n   load_data() 返回值: {result}")

if result:
    print("\n[3] 等待異步處理...")
    print("   (API 請求或本地 JSON 載入需要時間)")
    
    # 設置15秒超時
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.timeout.connect(lambda: (
        print("\n[超時] ⚠️ 15秒內未收到信號"),
        app.quit()
    ))
    timeout_timer.start(15000)
    
    # 啟動事件循環
    app.exec_()
    
    print("\n" + "=" * 80)
    print("[測試結果]")
    print("=" * 80)
    
    if data_received["success"]:
        print("✅ 測試成功: 數據已成功載入")
        data = data_received["data"]
        if isinstance(data, dict) and 'driver_laptimes' in data:
            driver_count = len(data['driver_laptimes'])
            total_laps = sum(len(laps) for laps in data['driver_laptimes'].values())
            print(f"\n統計資訊:")
            print(f"   - 總車手數: {driver_count}")
            print(f"   - 總圈數: {total_laps}")
            print(f"   - 數據來源: {data.get('metadata', {}).get('data_source', 'unknown')}")
    else:
        print("❌ 測試失敗: 未收到數據或發生錯誤")
        
else:
    print("\n❌ load_data() 返回 False,載入請求未成功提交")

print("\n💡 調試提示:")
print("   - 如果 API 請求失敗,檢查 refactored_api.py 是否運行")
print("   - 如果本地 JSON 回退失敗,檢查 json/ 目錄中是否存在檔案:")
print("     • detailed_laptime_analysis_2025_Japan_R_all_drivers.json")
print("   - 查看上方的調試輸出了解詳細流程")
