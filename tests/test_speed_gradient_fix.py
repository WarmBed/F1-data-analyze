"""
測試速度梯度修復效果
啟動 Historical Track Map 並驗證 80m 附近顯示正確的藍色（高速）
"""
import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from modules.gui.track_analysis.track_map_widget import TrackMapWidget

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🧪 速度梯度修復測試 - 2024 Brazil")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主布局
        central = QWidget()
        layout = QVBoxLayout(central)
        
        # 說明標籤
        info = QLabel(
            "✅ 測試目標: 80m 附近應顯示藍色（高速 310 km/h）\n"
            "❌ 修復前: 顯示紅色（錯誤的 <100 km/h）\n"
            "🔍 查看賽道左上方區域（起跑線附近）的顏色"
        )
        info.setStyleSheet("font-size: 14px; padding: 10px; background: #f0f0f0;")
        layout.addWidget(info)
        
        # Track Map Widget
        self.track_widget = TrackMapWidget()
        self.track_widget.set_speed_gradient_enabled(True)  # 啟用速度梯度
        layout.addWidget(self.track_widget)
        
        self.setCentralWidget(central)
        
        # 載入 JSON 數據
        self.load_brazil_data()
    
    def load_brazil_data(self):
        """載入 2024 Brazil Historical Flags JSON"""
        json_path = Path("json/historical_flags_Brazil_2022-2025.json")
        
        if not json_path.exists():
            print(f"❌ 找不到檔案: {json_path}")
            return
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                root_data = json.load(f)
                data = root_data.get('data', {})
            
            print(f"✅ 成功載入 JSON")
            print(f"   - 數據點數: {len(data.get('detailed_position_records', []))}")
            
            # 載入到 Widget
            self.track_widget.load_track_data(data)
            
            # 顯示速度統計
            speeds = [r.get('speed', 0) for r in data.get('detailed_position_records', [])]
            if speeds:
                print(f"   - 速度範圍: {min(speeds):.1f} - {max(speeds):.1f} km/h")
                print(f"   - 平均速度: {sum(speeds)/len(speeds):.1f} km/h")
            
        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
