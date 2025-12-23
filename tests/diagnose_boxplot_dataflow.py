"""
診斷 Lap Box Plot 數據流問題
追蹤從 API 到圖表的完整數據傳遞路徑
"""

import sys
import json
import io
from pathlib import Path

# 設置 stdout 編碼為 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加項目路徑
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("[診斷] Lap Time Box Plot 數據流診斷工具")
print("=" * 80)

# 測試 1: 檢查本地 JSON 檔案
print("\n📁 [測試 1] 檢查本地 JSON 檔案...")
json_dir = Path("json")
if not json_dir.exists():
    print(f"❌ JSON 目錄不存在: {json_dir}")
else:
    # 搜尋圈速箱型圖相關檔案 (實際檔名格式)
    pattern = "detailed_laptime_analysis_2025_Japan_R_all_drivers.json"
    json_files = list(json_dir.glob(pattern))
    
    if not json_files:
        print(f"⚠️  找不到符合條件的 JSON 檔案: {pattern}")
        print(f"   提示: 請先執行 CLI 命令生成數據:")
        print(f"   python f1_analysis_modular_main.py -f 52 -y 2025 -r Japan -s R")
    else:
        print(f"✅ 找到 {len(json_files)} 個檔案:")
        for f in json_files:
            print(f"   - {f.name} ({f.stat().st_size} bytes)")
            
            # 讀取並檢查數據結構
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    
                print(f"\n   📊 檔案結構:")
                if isinstance(data, dict):
                    print(f"      - 頂層鍵: {list(data.keys())}")
                    
                    # 檢查是否有所有車手圈速數據
                    if 'all_drivers_detailed_laptime' in data:
                        detailed = data['all_drivers_detailed_laptime']
                        print(f"      - all_drivers_detailed_laptime: {type(detailed)}")
                        
                        if isinstance(detailed, dict):
                            drivers = list(detailed.keys())
                            print(f"      - 車手數量: {len(drivers)}")
                            print(f"      - 車手列表: {drivers[:5]}{'...' if len(drivers) > 5 else ''}")
                            
                            # 檢查第一個車手的數據格式
                            if drivers:
                                first_driver = drivers[0]
                                driver_data = detailed[first_driver]
                                print(f"\n      🚗 車手 '{first_driver}' 數據:")
                                print(f"         - 數據類型: {type(driver_data)}")
                                
                                if isinstance(driver_data, list):
                                    print(f"         - 圈數數量: {len(driver_data)}")
                                    if driver_data:
                                        first_lap = driver_data[0]
                                        print(f"         - 第一圈數據: {first_lap}")
                                elif isinstance(driver_data, dict):
                                    print(f"         - 數據鍵: {list(driver_data.keys())}")
                    else:
                        print(f"      ❌ 缺少 'all_drivers_detailed_laptime' 鍵")
                        
                    # 檢查其他可能的數據鍵
                    for key in ['statistics', 'metadata', 'lap_times', 'driver_laptimes']:
                        if key in data:
                            print(f"      - {key}: {type(data[key])}")
                else:
                    print(f"      ⚠️  數據不是字典: {type(data)}")
                    
            except Exception as e:
                print(f"      ❌ 讀取失敗: {e}")

# 測試 2: 檢查數據管理器處理邏輯
print("\n\n🔧 [測試 2] 檢查數據管理器處理邏輯...")
try:
    from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import LapTimeBoxPlotDataManager
    
    # 創建數據管理器實例
    manager = LapTimeBoxPlotDataManager(parent=None)
    print(f"✅ 數據管理器創建成功: {type(manager)}")
    
    # 檢查方法
    print(f"\n   📋 可用方法:")
    methods = ['_validate_data_format', '_process_data', 'load_data', 'get_current_data']
    for method in methods:
        has_method = hasattr(manager, method)
        print(f"      - {method}: {'✅' if has_method else '❌'}")
    
    # 如果有本地 JSON 檔案，嘗試載入
    if json_files:
        print(f"\n   🔄 測試載入本地 JSON...")
        test_file = json_files[0]
        
        try:
            with open(test_file, 'r', encoding='utf-8') as fp:
                raw_data = json.load(fp)
            
            print(f"   📥 原始數據載入成功")
            
            # 測試驗證方法
            is_valid = manager._validate_data_format(raw_data)
            print(f"   驗證結果: {'✅ 通過' if is_valid else '❌ 失敗'}")
            
            if is_valid:
                # 測試處理方法
                processed = manager._process_data(raw_data)
                print(f"   處理結果: {type(processed)}")
                
                if isinstance(processed, dict):
                    print(f"   處理後鍵: {list(processed.keys())}")
                    
                    # 檢查圖表需要的數據格式
                    if 'driver_laptimes' in processed:
                        driver_laptimes = processed['driver_laptimes']
                        print(f"\n   ✅ 包含 driver_laptimes:")
                        print(f"      - 類型: {type(driver_laptimes)}")
                        if isinstance(driver_laptimes, dict):
                            print(f"      - 車手數: {len(driver_laptimes)}")
                            for driver, laps in list(driver_laptimes.items())[:3]:
                                print(f"      - {driver}: {len(laps)} 圈")
                    else:
                        print(f"   ❌ 缺少 driver_laptimes 鍵")
                        
        except Exception as e:
            print(f"   ❌ 測試失敗: {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"❌ 數據管理器測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 3: 檢查圖表組件
print("\n\n🎨 [測試 3] 檢查圖表組件...")
try:
    from PyQt5.QtWidgets import QApplication
    from modules.gui.lap_box_plot_analysis.lap_box_plot_chart_widget import LapTimeBoxPlotChartWidget
    
    # 創建 QApplication (圖表組件需要)
    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()
    
    # 創建圖表組件
    chart = LapTimeBoxPlotChartWidget(parent=None)
    print(f"✅ 圖表組件創建成功: {type(chart)}")
    
    # 檢查方法
    print(f"\n   📋 可用方法:")
    methods = ['update_data', 'paintEvent', '_draw_box_plots', '_draw_no_data_message']
    for method in methods:
        has_method = hasattr(chart, method)
        print(f"      - {method}: {'✅' if has_method else '❌'}")
    
    # 測試更新數據
    if json_files and 'processed' in locals():
        print(f"\n   🔄 測試更新圖表數據...")
        try:
            chart.update_data(processed)
            print(f"   ✅ update_data() 調用成功")
            
            # 檢查內部狀態
            print(f"\n   📊 圖表內部狀態:")
            print(f"      - driver_laptimes: {len(chart.driver_laptimes) if hasattr(chart, 'driver_laptimes') else 'N/A'}")
            print(f"      - statistics: {len(chart.statistics) if hasattr(chart, 'statistics') else 'N/A'}")
            
            if hasattr(chart, 'driver_laptimes') and chart.driver_laptimes:
                print(f"\n      ✅ driver_laptimes 已設置:")
                for driver, laps in list(chart.driver_laptimes.items())[:3]:
                    print(f"         - {driver}: {len(laps)} 圈")
            else:
                print(f"\n      ❌ driver_laptimes 為空或未設置")
                
        except Exception as e:
            print(f"   ❌ 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
except Exception as e:
    print(f"❌ 圖表組件測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 4: 信號連接測試
print("\n\n🔌 [測試 4] 信號連接測試...")
try:
    from PyQt5.QtCore import QObject, pyqtSignal
    
    class TestReceiver(QObject):
        def __init__(self):
            super().__init__()
            self.received_data = None
            self.signal_triggered = False
        
        def on_data_loaded(self, data):
            print(f"   📨 信號接收成功!")
            print(f"      - 數據類型: {type(data)}")
            self.received_data = data
            self.signal_triggered = True
            if isinstance(data, dict):
                print(f"      - 數據鍵: {list(data.keys())[:5]}")
    
    # 創建測試接收器
    receiver = TestReceiver()
    
    # 連接數據管理器信號
    if 'manager' in locals():
        print(f"   🔗 連接 data_loaded 信號...")
        manager.data_loaded.connect(receiver.on_data_loaded)
        
        # 嘗試載入數據
        print(f"   🔄 測試載入數據...")
        result = manager.load_data(year=2025, race="Japan", session="R")
        print(f"   載入結果: {result}")
        
        # 檢查信號是否觸發
        import time
        time.sleep(0.5)  # 等待異步處理
        
        if receiver.signal_triggered:
            print(f"\n   ✅ 信號成功觸發並接收")
            if receiver.received_data:
                if isinstance(receiver.received_data, dict):
                    print(f"      - 接收到的數據鍵: {list(receiver.received_data.keys())}")
                    if 'driver_laptimes' in receiver.received_data:
                        print(f"      ✅ 包含 driver_laptimes")
                    else:
                        print(f"      ❌ 缺少 driver_laptimes")
        else:
            print(f"\n   ⚠️  信號未觸發")
            print(f"      可能原因:")
            print(f"      1. API 請求失敗")
            print(f"      2. 本地 JSON 檔案未找到")
            print(f"      3. 數據驗證失敗")
    
except Exception as e:
    print(f"❌ 信號測試失敗: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 診斷完成")
print("=" * 80)
print("\n📋 診斷總結:")
print("   1. 檢查本地 JSON 檔案是否存在且格式正確")
print("   2. 驗證數據管理器的處理邏輯")
print("   3. 測試圖表組件的數據接收")
print("   4. 確認信號連接和傳遞")
print("\n💡 下一步建議:")
print("   - 如果 JSON 檔案不存在: 執行 CLI 命令生成數據")
print("   - 如果數據格式錯誤: 檢查 _process_data 方法")
print("   - 如果信號未觸發: 檢查 _connect_data_manager_signals")
print("   - 如果圖表未更新: 檢查 update_data 方法")
