"""
完整診斷 Speed Analysis 的 API 調用流程
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader import SpeedAnalysisDataLoader

def main():
    """完整測試 Speed Analysis 數據載入"""
    app = QApplication(sys.argv)
    
    print("=" * 80)
    print("🔍 完整診斷: Speed Analysis API 調用流程")
    print("=" * 80)
    print()
    
    # 創建 Speed Data Loader
    print("📦 步驟 1: 創建 SpeedAnalysisDataLoader...")
    loader = SpeedAnalysisDataLoader()
    print(f"   ✅ Loader 類型: {type(loader).__name__}")
    print(f"   ✅ Telemetry 類型: {loader.get_telemetry_type()}")
    print(f"   ✅ 顯示名稱: {loader.get_display_name()}")
    print()
    
    # 連接信號
    print("📡 步驟 2: 連接信號...")
    
    def on_data_loaded(data):
        print(f"\n✅ 信號觸發: data_loaded")
        print(f"   數據類型: {type(data)}")
        if isinstance(data, dict):
            print(f"   數據鍵: {list(data.keys())[:10]}")
        app.quit()
    
    def on_error(error_msg):
        print(f"\n❌ 信號觸發: load_error")
        print(f"   錯誤: {error_msg}")
        app.quit()
    
    def on_progress(value):
        print(f"📊 進度: {value}%")
    
    loader.data_loaded.connect(on_data_loaded, Qt.QueuedConnection)
    loader.load_error.connect(on_error, Qt.QueuedConnection)
    loader.load_progress.connect(on_progress, Qt.QueuedConnection)
    print("   ✅ 信號已連接 (使用 Qt.QueuedConnection)")
    print()
    
    # 設置測試參數
    test_params = {
        'year': 2025,
        'race': 'Australia',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 1,
        'lap2': 1
    }
    
    print("📋 步驟 3: 設置測試參數")
    for key, value in test_params.items():
        print(f"   {key}: {value}")
    print()
    
    # 調用 load_speed_data
    print("🚀 步驟 4: 調用 load_speed_data()...")
    print("-" * 80)
    
    # 添加額外調試
    import threading
    print(f"   當前線程: {threading.current_thread().name}")
    print(f"   是否在載入: {loader.is_loading()}")
    
    result = loader.load_speed_data(**test_params)
    print("-" * 80)
    print(f"   返回值: {result}")
    print(f"   載入後狀態: {loader.is_loading()}")
    print()
    
    if not result:
        print("❌ load_speed_data() 返回 False，載入未啟動")
        print("   這表示在載入前就失敗了")
        return
    
    print("⏳ 步驟 5: 等待 API 響應...")
    print("   (最多等待 10 秒)")
    print()
    
    # 設置超時
    start_time = time.time()
    timeout = 10
    
    def check_timeout():
        if time.time() - start_time > timeout:
            print(f"\n⏰ 超時！已等待 {timeout} 秒但沒有響應")
            print("   可能的原因:")
            print("   1. API 服務未啟動")
            print("   2. API 請求被阻塞")
            print("   3. 信號未正確觸發")
            app.quit()
    
    from PyQt5.QtCore import QTimer
    timer = QTimer()
    timer.timeout.connect(check_timeout)
    timer.start(1000)  # 每秒檢查一次
    
    # 運行事件循環
    app.exec_()
    
    print("\n" + "=" * 80)
    print("✅ 診斷完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
