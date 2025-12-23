"""
日本電路 TrackMap 演示 - FastF1 原生坐標版
使用統一的 FastF1 坐標系統確保賽道輪廓和彎道標註完美對齊

Author: GitHub Copilot
Date: 2025-10-XX
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel)
from PyQt5.QtCore import Qt

# 導入 TrackMapWidget
sys.path.insert(0, str(Path(__file__).parent))
from modules.gui.track_analysis.track_map_widget import TrackMapWidget


class JapanCircuitDemoFastF1(QMainWindow):
    """日本電路 TrackMap 演示視窗 - FastF1 版"""
    
    def __init__(self):
        super().__init__()
        self.circuit_data = None
        self.init_ui()
        self._load_and_display()
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("🏎️ Japan Circuit - FastF1 TrackMap Demo")
        self.setGeometry(100, 100, 1200, 800)
        
        # 主視窗容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # === 頂部資訊面板 ===
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("正在載入...")
        self.info_label.setStyleSheet(
            "font-size: 14px; padding: 10px; background: #f0f0f0; border-radius: 5px;"
        )
        info_layout.addWidget(self.info_label)
        
        # 控制按鈕
        toggle_corners_btn = QPushButton("🎯 切換彎道顯示")
        toggle_corners_btn.clicked.connect(self._toggle_corners)
        info_layout.addWidget(toggle_corners_btn)
        
        fit_view_btn = QPushButton("🔄 重置視圖")
        fit_view_btn.clicked.connect(self._fit_view)
        info_layout.addWidget(fit_view_btn)
        
        layout.addLayout(info_layout)
        
        # === TrackMapWidget ===
        self.track_map = TrackMapWidget()
        self.track_map.show_official_corners = True
        layout.addWidget(self.track_map)
        
        # === 底部統計資訊 ===
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(
            "font-size: 11px; color: #666; padding: 5px;"
        )
        layout.addWidget(self.stats_label)
    
    def _load_and_display(self):
        """載入數據並顯示"""
        if not self._load_circuit_data():
            self.info_label.setText("❌ 數據載入失敗")
            return
        
        # 轉換數據格式
        trackmap_data = self._convert_to_trackmap_format()
        
        # 載入到 TrackMapWidget
        success = self.track_map.load_track_data(trackmap_data)
        
        if success:
            self.info_label.setText("✅ 賽道數據已載入")
            print("\n✅ TrackMapWidget 載入成功")
            
            # 更新統計資訊
            outline_count = len(trackmap_data['position_records'])
            corners_count = len(trackmap_data['official_corners']['corners'])
            self.stats_label.setText(
                f"賽道輪廓: {outline_count} 點 | 官方彎道: {corners_count} 個 | "
                f"座標系統: FastF1 原生坐標 (X/Y meters)"
            )
        else:
            self.info_label.setText("❌ TrackMapWidget 載入失敗")
            print("\n❌ TrackMapWidget 載入失敗")
    
    def _load_circuit_data(self, json_file: str = "japan_circuit_fastf1_2025.json"):
        """
        載入 FastF1 原生座標 JSON 檔案
        
        Args:
            json_file: JSON 檔案路徑
        
        Returns:
            bool: 是否載入成功
        """
        print(f"\n🔄 載入電路數據: {json_file}")
        
        try:
            json_path = Path(json_file)
            if not json_path.exists():
                print(f"❌ 找不到檔案: {json_file}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證數據結構
            if 'track_outline' not in data:
                print(f"❌ JSON 缺少 'track_outline' 欄位")
                return False
            
            if 'official_corners' not in data:
                print(f"❌ JSON 缺少 'official_corners' 欄位")
                return False
            
            self.circuit_data = data
            
            # 顯示數據資訊
            outline_points = len(data['track_outline']['coordinates'])
            corners_count = data['official_corners']['count']
            
            print(f"✅ 載入成功:")
            print(f"   - 賽道輪廓: {outline_points} 點")
            print(f"   - 官方彎道: {corners_count} 個")
            print(f"   - 座標系統: FastF1 原生坐標 (統一)")
            
            return True
            
        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _convert_to_trackmap_format(self):
        """
        將 FastF1 JSON 轉換為 TrackMapWidget 期望的格式
        
        Returns:
            dict: TrackMapWidget 數據格式
        """
        if not self.circuit_data:
            return {}
        
        print("\n🔄 轉換數據格式...")
        
        # 轉換 track_outline → position_records
        track_outline = self.circuit_data['track_outline']['coordinates']
        position_records = []
        
        for i, point in enumerate(track_outline):
            record = {
                "point_index": i + 1,
                "distance_m": point['distance_m'],
                "position_x": point['x'],  # FastF1 X 座標
                "position_y": point['y'],  # FastF1 Y 座標
                "time_seconds": 0.0
            }
            position_records.append(record)
        
        print(f"   ✅ position_records: {len(position_records)} 點")
        
        # 轉換 official_corners
        official_corners_data = self.circuit_data['official_corners']
        
        # 直接使用 FastF1 的 corners 數據（格式已經正確）
        corners_list = official_corners_data['corners']
        
        print(f"   ✅ official_corners: {len(corners_list)} 個彎道")
        
        # 檢查彎道座標範圍
        if corners_list:
            corner_x_values = [c['x'] for c in corners_list]
            corner_y_values = [c['y'] for c in corners_list]
            print(f"   🔍 彎道座標範圍:")
            print(f"      X: {min(corner_x_values):.1f} ~ {max(corner_x_values):.1f}")
            print(f"      Y: {min(corner_y_values):.1f} ~ {max(corner_y_values):.1f}")
        
        # 構建最終數據
        trackmap_data = {
            "has_position_data": True,
            "position_records": position_records,
            "track_bounds": self.circuit_data['track_bounds'],
            "official_corners": {
                "available": official_corners_data['available'],
                "count": official_corners_data['count'],
                "corners": corners_list
            },
            "fastest_lap_info": {
                "driver": self.circuit_data.get('metadata', {}).get('fastest_lap_driver', 'N/A'),
                "time": self.circuit_data.get('metadata', {}).get('fastest_lap_time', 'N/A')
            }
        }
        
        print(f"\n✅ 數據轉換完成")
        print(f"   - position_records: {len(position_records)}")
        print(f"   - official_corners: {len(corners_list)}")
        print(f"   - 座標系統: FastF1 原生 (統一)")
        
        return trackmap_data
    
    def _toggle_corners(self):
        """切換彎道顯示"""
        self.track_map.show_official_corners = not self.track_map.show_official_corners
        self.track_map.update()
        status = "已啟用" if self.track_map.show_official_corners else "已停用"
        print(f"\n🎯 彎道顯示: {status}")
    
    def _fit_view(self):
        """重置視圖"""
        self.track_map.fit_to_view()
        print("\n🔄 視圖已重置")


def main():
    """主程式入口"""
    print("=" * 70)
    print("🏎️  Japan Circuit - FastF1 TrackMap Demo")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    # 創建演示視窗
    demo = JapanCircuitDemoFastF1()
    demo.show()
    
    print("\n✅ 視窗已開啟")
    print("💡 提示:")
    print("   - 所有數據使用 FastF1 原生坐標系統")
    print("   - 賽道輪廓和彎道標註座標統一")
    print("   - 彎道標註應該正確對齊賽道位置")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
