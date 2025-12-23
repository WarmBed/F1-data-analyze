"""
日本電路 TrackMap + 高程剖面 演示
展示賽道輪廓、彎道標註和高程變化

Author: GitHub Copilot
Date: 2025-11-09
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QSplitter)
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 導入 TrackMapWidget
sys.path.insert(0, str(Path(__file__).parent))
from modules.gui.track_analysis.track_map_widget import TrackMapWidget


class ElevationProfileWidget(QWidget):
    """高程剖面圖 Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.elevation_data = None
        self.circuit_name = "Circuit"  # 預設名稱
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建 Matplotlib Figure
        self.figure = Figure(figsize=(10, 3), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def set_circuit_name(self, name: str):
        """設置賽道名稱"""
        self.circuit_name = name
    
    def plot_elevation(self, track_outline: list, official_corners: list = None):
        """
        繪製高程剖面
        
        Args:
            track_outline: 賽道輪廓點列表 [{'distance_m', 'elevation', ...}]
            official_corners: 官方彎道列表 [{'number', 'mapped_distance', ...}]
        """
        if not track_outline:
            return
        
        # 提取數據
        distances = [p['distance_m'] / 1000 for p in track_outline]  # 轉換為 km
        elevations = [p.get('elevation', 0) for p in track_outline]
        
        # 清除舊圖
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 繪製高程剖面
        ax.plot(distances, elevations, 'b-', linewidth=2, label='Track Elevation')
        ax.fill_between(distances, elevations, alpha=0.3, color='lightblue')
        
        # 標註彎道位置
        if official_corners:
            for corner in official_corners:
                corner_dist = corner.get('mapped_distance', 0) / 1000  # km
                corner_num = corner.get('number', 0)
                
                # 找到最接近的高程值
                closest_idx = min(range(len(distances)), 
                                 key=lambda i: abs(distances[i] - corner_dist))
                corner_elev = elevations[closest_idx]
                
                # 繪製彎道標記
                ax.plot(corner_dist, corner_elev, 'ro', markersize=6)
                ax.text(corner_dist, corner_elev + 2, f'T{corner_num}',
                       ha='center', va='bottom', fontsize=8, color='red')
        
        # 設置圖表樣式
        ax.set_xlabel('Distance (km)', fontsize=10)
        ax.set_ylabel('Elevation (m)', fontsize=10)
        ax.set_title(f'{self.circuit_name} - Elevation Profile', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # 設置 Y 軸範圍（留出一些空間）
        if elevations:
            y_min = min(elevations) - 5
            y_max = max(elevations) + 10
            ax.set_ylim(y_min, y_max)
        
        # 緊湊佈局
        self.figure.tight_layout()
        self.canvas.draw()
        
        print(f"✅ 高程剖面已繪製: {len(distances)} 個點, 高程範圍 {min(elevations):.1f}m ~ {max(elevations):.1f}m")


class JapanCircuitWithElevation(QMainWindow):
    """日本電路 + 高程剖面演示視窗"""
    
    def __init__(self):
        super().__init__()
        self.circuit_data = None
        self.init_ui()
        self._load_and_display()
    
    def init_ui(self):
        """初始化 UI"""
        # 從檔案名稱取得賽道名稱
        circuit_name = "Circuit"
        if len(sys.argv) > 1:
            json_file = sys.argv[1]
            circuit_name = Path(json_file).stem.replace('_circuit_', ' ').replace('_', ' ').title()
        
        self.setWindowTitle(f"🏎️ {circuit_name} - Track Map + Elevation Profile")
        self.setGeometry(100, 100, 1400, 900)
        
        # 主視窗容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # === 頂部資訊面板 ===
        info_layout = QHBoxLayout()
        
        self.info_label = QLabel("正在載入...")
        self.info_label.setStyleSheet(
            "font-size: 14px; padding: 10px; background: #f0f0f0; border-radius: 5px;"
        )
        info_layout.addWidget(self.info_label)
        
        # 控制按鈕
        toggle_corners_btn = QPushButton("🎯 切換彎道")
        toggle_corners_btn.clicked.connect(self._toggle_corners)
        info_layout.addWidget(toggle_corners_btn)
        
        fit_view_btn = QPushButton("🔄 重置視圖")
        fit_view_btn.clicked.connect(self._fit_view)
        info_layout.addWidget(fit_view_btn)
        
        refresh_elev_btn = QPushButton("📊 重繪高程")
        refresh_elev_btn.clicked.connect(self._refresh_elevation)
        info_layout.addWidget(refresh_elev_btn)
        
        main_layout.addLayout(info_layout)
        
        # === 使用 QSplitter 分割 TrackMap 和 Elevation ===
        splitter = QSplitter(Qt.Vertical)
        
        # TrackMapWidget
        self.track_map = TrackMapWidget()
        self.track_map.show_official_corners = True
        splitter.addWidget(self.track_map)
        
        # ElevationProfileWidget
        self.elevation_widget = ElevationProfileWidget()
        splitter.addWidget(self.elevation_widget)
        
        # 設定初始比例（TrackMap 佔 70%，Elevation 佔 30%）
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        main_layout.addWidget(splitter)
        
        # === 底部統計資訊 ===
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet(
            "font-size: 11px; color: #666; padding: 5px;"
        )
        main_layout.addWidget(self.stats_label)
    
    def _load_and_display(self):
        """載入數據並顯示"""
        if not self._load_circuit_data():
            self.info_label.setText("❌ 數據載入失敗")
            return
        
        # 從 metadata 取得賽道名稱
        metadata = self.circuit_data.get('metadata', {})
        race_name = metadata.get('race', 'Circuit')
        year = metadata.get('year', '')
        
        # 設置高程圖的賽道名稱
        self.elevation_widget.set_circuit_name(f"{race_name} {year}")
        
        # 轉換數據格式
        trackmap_data = self._convert_to_trackmap_format()
        
        # 載入到 TrackMapWidget
        success = self.track_map.load_track_data(trackmap_data)
        
        if success:
            # 更新資訊標籤
            metadata = self.circuit_data.get('metadata', {})
            elev_profile = self.circuit_data.get('elevation_profile', {})
            
            info_html = f"""
            <b>🏁 {metadata.get('race', 'N/A')}</b> | 
            {metadata.get('year', 'N/A')} | 
            Distance: {metadata.get('total_distance_m', 0)/1000:.2f} km | 
            Elevation: {elev_profile.get('min_elevation', 0):.0f}m ~ {elev_profile.get('max_elevation', 0):.0f}m 
            (Δ{elev_profile.get('elevation_change', 0):.0f}m)
            """
            self.info_label.setText(info_html)
            
            # 繪製高程剖面
            self._refresh_elevation()
            
            # 更新統計資訊
            outline_count = len(trackmap_data['position_records'])
            corners_count = len(trackmap_data['official_corners']['corners'])
            self.stats_label.setText(
                f"賽道輪廓: {outline_count} 點 | 官方彎道: {corners_count} 個 | "
                f"座標系統: FastF1 (X/Y) + GeoJSON (Elevation)"
            )
            
            print("\n✅ 所有數據已載入並顯示")
        else:
            self.info_label.setText("❌ TrackMapWidget 載入失敗")
    
    def _load_circuit_data(self, json_file: str = None):
        """載入 JSON 數據"""
        # 如果沒有指定檔案，從命令列參數讀取
        if json_file is None:
            if len(sys.argv) > 1:
                json_file = sys.argv[1]
            else:
                json_file = "japan_circuit_fastf1_2025.json"
        
        print(f"\n🔄 載入電路數據: {json_file}")
        
        try:
            json_path = Path(json_file)
            if not json_path.exists():
                print(f"❌ 找不到檔案: {json_file}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'track_outline' not in data or 'official_corners' not in data:
                print(f"❌ JSON 格式錯誤")
                return False
            
            self.circuit_data = data
            print(f"✅ 數據載入成功")
            return True
            
        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            return False
    
    def _convert_to_trackmap_format(self):
        """轉換為 TrackMapWidget 格式"""
        if not self.circuit_data:
            return {}
        
        track_outline = self.circuit_data['track_outline']['coordinates']
        position_records = []
        
        for i, point in enumerate(track_outline):
            record = {
                "point_index": i + 1,
                "distance_m": point['distance_m'],
                "position_x": point['x'],
                "position_y": point['y'],
                "elevation": point.get('elevation', 0),  # 保留高程數據
                "time_seconds": 0.0
            }
            position_records.append(record)
        
        official_corners_data = self.circuit_data['official_corners']
        
        return {
            "has_position_data": True,
            "position_records": position_records,
            "track_bounds": self.circuit_data['track_bounds'],
            "official_corners": {
                "available": official_corners_data['available'],
                "count": official_corners_data['count'],
                "corners": official_corners_data['corners']
            }
        }
    
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
    
    def _refresh_elevation(self):
        """重新繪製高程剖面"""
        if not self.circuit_data:
            return
        
        track_outline = self.circuit_data['track_outline']['coordinates']
        official_corners = self.circuit_data['official_corners']['corners']
        
        self.elevation_widget.plot_elevation(track_outline, official_corners)


def main():
    """主程式入口"""
    print("=" * 70)
    print("🏎️  Japan Circuit - Track Map + Elevation Profile Demo")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    demo = JapanCircuitWithElevation()
    demo.show()
    
    print("\n✅ 視窗已開啟")
    print("💡 提示:")
    print("   - 上方: 賽道平面圖 + 彎道標註")
    print("   - 下方: 高程剖面圖")
    print("   - 可拖曳中間分隔線調整比例")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
