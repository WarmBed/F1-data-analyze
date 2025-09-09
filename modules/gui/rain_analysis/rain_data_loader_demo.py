#!/usr/bin/env python3
"""
RainDataLoader 使用範例
展示如何使用降雨數據載入器進行實際數據載入和處理
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject
from modules.gui.rain_analysis import RainDataLoader, create_rain_data_loader

class RainDataLoaderDemo(QObject):
    """降雨數據載入器演示類"""
    
    def __init__(self):
        super().__init__()
        
        # 創建降雨數據載入器
        self.rain_loader = create_rain_data_loader(self)
        
        # 連接信號
        self._connect_signals()
        
        print("=== RainDataLoader 使用範例 ===")
        print(f"載入器類型: {type(self.rain_loader)}")
        print(f"可用分析類型: {self.rain_loader.get_available_analyses()}")
        print(f"必需數據類型: {self.rain_loader.get_required_data()}")
        print()
    
    def _connect_signals(self):
        """連接信號處理函數"""
        self.rain_loader.data_loaded.connect(self.on_data_loaded)
        self.rain_loader.load_error.connect(self.on_load_error)
        self.rain_loader.status_changed.connect(self.on_status_changed)
    
    def on_data_loaded(self, data):
        """數據載入完成處理"""
        print("✓ 數據載入完成!")
        print(f"  - 元數據鍵: {list(data.get('metadata', {}).keys())}")
        print(f"  - 會話信息: {data.get('session_info', {}).get('SessionName', 'Unknown')}")
        
        # 降雨分析特定數據
        rain_analysis = data.get('rain_analysis', {})
        if rain_analysis:
            print(f"  - 降雨分析數據: {list(rain_analysis.keys())}")
        
        # 天氣數據
        weather_data = data.get('weather_data', {})
        if weather_data:
            print(f"  - 天氣數據點數: {len(weather_data) if isinstance(weather_data, (list, dict)) else 'Unknown'}")
        
        # 檢查數據完整性
        is_complete = self.rain_loader.is_data_complete(data)
        print(f"  - 數據完整性: {'✓ 完整' if is_complete else '⚠ 不完整'}")
        print()
    
    def on_load_error(self, error_message):
        """載入錯誤處理"""
        print(f"✗ 載入錯誤: {error_message}")
        print()
    
    def on_status_changed(self, status):
        """狀態變化處理"""
        print(f"📊 狀態: {status}")
    
    def demo_json_loading(self):
        """演示 JSON 文件載入"""
        print("--- 演示 JSON 文件載入 ---")
        
        # 測試載入範例 JSON 文件
        json_files = [
            "json/enhanced_rain_analysis_2025_Belgium_R.json",
            "json/enhanced_rain_analysis_2025_Japan_R.json",
            "json/enhanced_rain_analysis_2025_11_R.json"
        ]
        
        for json_file in json_files:
            if os.path.exists(json_file):
                print(f"嘗試載入: {json_file}")
                success = self.rain_loader.load_from_json(json_file)
                if success:
                    print(f"✓ 開始載入 {json_file}")
                else:
                    print(f"✗ 載入失敗 {json_file}")
                break
        else:
            print("找不到可用的測試 JSON 文件")
        
        print()
    
    def demo_race_data_loading(self):
        """演示比賽數據載入"""
        print("--- 演示比賽數據載入 ---")
        
        # 嘗試載入 2025 年比利時站降雨數據
        print("嘗試載入 2025 年比利時站正賽降雨數據...")
        success = self.rain_loader.load_rain_analysis_data(
            year=2025,
            race="Belgium", 
            session="R"
        )
        
        if success:
            print("✓ 開始載入比賽數據")
        else:
            print("✗ 載入比賽數據失敗")
        
        print()
    
    def demo_analysis_info(self):
        """演示分析信息獲取"""
        print("--- 分析配置信息 ---")
        
        analyses = self.rain_loader.get_available_analyses()
        print(f"可用分析類型 ({len(analyses)} 種):")
        for i, analysis in enumerate(analyses, 1):
            print(f"  {i}. {analysis}")
        
        required_data = self.rain_loader.get_required_data()
        print(f"\n必需數據類型 ({len(required_data)} 種):")
        for i, data_type in enumerate(required_data, 1):
            print(f"  {i}. {data_type}")
        
        print()

def main():
    """主函數"""
    app = QApplication(sys.argv)
    
    try:
        # 創建演示實例
        demo = RainDataLoaderDemo()
        
        # 顯示分析信息
        demo.demo_analysis_info()
        
        # 演示 JSON 載入
        demo.demo_json_loading()
        
        # 演示比賽數據載入
        demo.demo_race_data_loading()
        
        print("=== 演示完成 ===")
        
        # 不啟動 Qt 事件循環，因為這只是演示
        # app.exec_()
        
    except Exception as e:
        print(f"演示過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
