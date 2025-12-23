"""
診斷 Speed Analysis 為何沒有調用 API
"""

import sys
from pathlib import Path

# 添加模組路徑
sys.path.insert(0, str(Path(__file__).parent))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, Qt
from modules.gui.lap_analysis.telemetry_data_loader_base import TelemetryDataLoader

class TestLoader(TelemetryDataLoader):
    """測試用載入器"""
    
    def __init__(self):
        super().__init__(
            telemetry_type='speed',
            api_base_url='https://api.f1telemetrystationpro.org',
            parent=None
        )
        
        # 連接信號
        self.data_loaded.connect(self._on_test_data_loaded, Qt.QueuedConnection)
        self.load_error.connect(self._on_test_error, Qt.QueuedConnection)
        self.load_progress.connect(self._on_test_progress, Qt.QueuedConnection)
        
        print("✅ TestLoader 初始化完成")
    
    @pyqtSlot(dict)
    def _on_test_data_loaded(self, data):
        print(f"✅ 數據載入成功！")
        print(f"   數據鍵: {list(data.keys()) if isinstance(data, dict) else type(data)}")
        QApplication.quit()
    
    @pyqtSlot(str)
    def _on_test_error(self, error):
        print(f"❌ 載入失敗: {error}")
        QApplication.quit()
    
    @pyqtSlot(int)
    def _on_test_progress(self, progress):
        print(f"📊 進度: {progress}%")

def main():
    """測試主函數"""
    app = QApplication(sys.argv)
    
    print("=" * 80)
    print("🔍 測試 Speed Analysis API 調用")
    print("=" * 80)
    print()
    
    loader = TestLoader()
    
    # 測試參數
    params = {
        'year': 2025,
        'race': 'Australia',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',
        'lap1': 1,
        'lap2': 1
    }
    
    print(f"📋 測試參數:")
    for key, value in params.items():
        print(f"   {key}: {value}")
    print()
    
    print("🚀 開始載入數據...")
    loader.load_data(**params)
    
    # 運行事件循環
    app.exec_()
    
    print("\n" + "=" * 80)
    print("✅ 測試完成")
    print("=" * 80)

if __name__ == "__main__":
    main()
