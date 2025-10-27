#!/usr/bin/env python3
"""
Demo 1: 測試數據載入器
Test Corner Performance Data Loader

測試項目：
1. 載入本地 JSON 檔案
2. 驗證數據格式
3. 檢查數據結構

執行命令：
python demo_1_test_loader.py
"""

import sys
import os

# 設定路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from modules.gui.all_drivers_corner_performance_analysis.corner_performance_loader import CornerPerformanceDataLoader


def test_loader():
    """測試數據載入器"""
    print("=" * 60)
    print("Demo 1: 測試彎道性能數據載入器")
    print("=" * 60)
    
    app = QApplication(sys.argv)
    
    # 創建載入器
    loader = CornerPerformanceDataLoader()
    
    # 連接信號
    def on_data_loaded(data):
        print("\n✅ 數據載入成功!")
        print(f"Year: {data.get('year')}")
        print(f"Race: {data.get('race')}")
        print(f"Session: {data.get('session')}")
        
        selected_corners = data.get('selected_corners', {})
        print("\n選擇的彎道：")
        for corner_type, corner_info in selected_corners.items():
            print(f"  - {corner_type}: T{corner_info['corner_number']} ({corner_info['avg_apex_speed']:.1f} km/h)")
        
        fastest_lap = data.get('fastest_lap_analysis', {})
        print(f"\n最速圈分析: {fastest_lap.get('total_drivers', 0)} 位車手")
        
        all_laps = data.get('all_laps_analysis', {})
        print(f"全圈分析: {all_laps.get('total_drivers', 0)} 位車手")
        
        # 顯示前 3 位車手的數據
        print("\n前 3 位車手數據：")
        for i, driver_data in enumerate(fastest_lap.get('drivers', [])[:3]):
            driver = driver_data.get('driver')
            lap_num = driver_data.get('fastest_lap_number')
            print(f"  {i+1}. {driver} (Lap {lap_num})")
            
            corners = driver_data.get('corners', {})
            for corner_key, speeds in corners.items():
                entry = speeds.get('entry_50m_speed', 0)
                apex = speeds.get('apex_speed', 0)
                exit_speed = speeds.get('exit_50m_speed', 0)
                print(f"     {corner_key}: Entry={entry:.1f}, Apex={apex:.1f}, Exit={exit_speed:.1f}")
        
        print("\n✅ Demo 1 測試完成!")
        QTimer.singleShot(1000, app.quit)
    
    def on_load_error(error):
        print(f"\n❌ 載入失敗: {error}")
        QTimer.singleShot(1000, app.quit)
    
    def on_status_changed(status):
        print(f"狀態: {status}")
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_load_error)
    loader.status_changed.connect(on_status_changed)
    
    # 測試載入 Japan 2024 R 的數據
    print("\n開始載入數據...")
    print("參數: year=2024, race=Japan, session=R")
    
    success = loader.load_data(
        year=2024,
        race="Japan",
        session="R"
    )
    
    if not success:
        print("❌ 載入請求失敗")
        return 1
    
    return app.exec_()


if __name__ == "__main__":
    sys.exit(test_loader())
