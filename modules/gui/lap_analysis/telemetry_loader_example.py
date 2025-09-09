#!/usr/bin/env python3
"""
TelemetryDataLoader 基類使用示例
展示如何使用新的通用遙測數據載入器
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from PyQt5.QtCore import QObject, pyqtSignal
from telemetry_data_loader_base import TelemetryDataLoader, create_telemetry_loader

class ExampleUsage(QObject):
    """使用示例類"""
    
    def __init__(self):
        super().__init__()
        
        # 創建不同類型的遙測載入器
        self.speed_loader = TelemetryDataLoader('speed', self)
        self.rpm_loader = TelemetryDataLoader('rpm', self)
        self.gear_loader = TelemetryDataLoader('gear', self)
        
        # 或者使用工廠函數
        self.throttle_loader = create_telemetry_loader('throttle', self)
        
        # 連接信號
        self._connect_signals()
    
    def _connect_signals(self):
        """連接信號"""
        # 速度載入器信號
        self.speed_loader.data_loaded.connect(self.on_speed_data_loaded)
        self.speed_loader.load_error.connect(self.on_load_error)
        self.speed_loader.status_changed.connect(self.on_status_changed)
        
        # RPM載入器信號  
        self.rpm_loader.data_loaded.connect(self.on_rpm_data_loaded)
        self.rpm_loader.load_error.connect(self.on_load_error)
        
        # 檔位載入器信號
        self.gear_loader.data_loaded.connect(self.on_gear_data_loaded)
        self.gear_loader.load_error.connect(self.on_load_error)
    
    def load_speed_comparison(self):
        """載入速度比較數據示例"""
        print("開始載入速度比較數據...")
        success = self.speed_loader.load_telemetry_data(
            year=2025,
            race="Japan", 
            session="R",
            driver1="VER",
            driver2="LEC",
            lap1=1,
            lap2=1
        )
        print(f"速度載入啟動: {success}")
    
    def load_rpm_analysis(self):
        """載入RPM分析數據示例"""
        print("開始載入RPM分析數據...")
        success = self.rpm_loader.load_telemetry_data(
            year=2025,
            race="Japan",
            session="R", 
            driver1="HAM",
            lap1=1
        )
        print(f"RPM載入啟動: {success}")
    
    def load_gear_analysis(self):
        """載入檔位分析數據示例"""
        print("開始載入檔位分析數據...")
        success = self.gear_loader.load_telemetry_data(
            year=2025,
            race="Japan",
            session="R",
            driver1="NOR",
            driver2="SAI", 
            lap1=1,
            lap2=1
        )
        print(f"檔位載入啟動: {success}")
    
    def on_speed_data_loaded(self, data):
        """處理速度數據載入完成"""
        print("✅ 速度數據載入完成!")
        print(f"數據類型: {data.get('metadata', {}).get('telemetry_type')}")
        print(f"顯示名稱: {data.get('metadata', {}).get('display_name')}")
        
        speed_data = data.get('speed_data', {})
        distance_count = len(speed_data.get('distance', []))
        print(f"距離數據點數: {distance_count}")
    
    def on_rpm_data_loaded(self, data):
        """處理RPM數據載入完成"""
        print("✅ RPM數據載入完成!")
        print(f"數據類型: {data.get('metadata', {}).get('telemetry_type')}")
        
        rpm_data = data.get('rpm_data', {})
        distance_count = len(rpm_data.get('distance', []))
        print(f"距離數據點數: {distance_count}")
    
    def on_gear_data_loaded(self, data):
        """處理檔位數據載入完成"""
        print("✅ 檔位數據載入完成!")
        print(f"數據類型: {data.get('metadata', {}).get('telemetry_type')}")
        
        gear_data = data.get('gear_data', {})
        distance_count = len(gear_data.get('distance', []))
        print(f"距離數據點數: {distance_count}")
    
    def on_load_error(self, error_msg):
        """處理載入錯誤"""
        print(f"❌ 載入錯誤: {error_msg}")
    
    def on_status_changed(self, status):
        """處理狀態變更"""
        print(f"📊 狀態: {status}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    
    app = QApplication(sys.argv)
    
    # 創建使用示例
    example = ExampleUsage()
    
    # 模擬載入不同類型的遙測數據
    QTimer.singleShot(1000, example.load_speed_comparison)
    QTimer.singleShot(2000, example.load_rpm_analysis) 
    QTimer.singleShot(3000, example.load_gear_analysis)
    
    # 5秒後退出
    QTimer.singleShot(5000, app.quit)
    
    print("=== TelemetryDataLoader 基類使用示例 ===")
    print("支援的遙測類型:")
    for telemetry_type, config in TelemetryDataLoader.TELEMETRY_TYPES.items():
        print(f"  - {telemetry_type}: {config['display_name']} ({config['unit']})")
    print()
    
    sys.exit(app.exec_())
