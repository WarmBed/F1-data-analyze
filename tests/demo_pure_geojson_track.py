"""
純 GeoJSON 賽道視覺化 - 無座標映射版本
只使用 GeoJSON 數據：賽道輪廓 + 高程剖面，不包含 FastF1 彎道

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
import numpy as np

# 導入 TrackMapWidget
sys.path.insert(0, str(Path(__file__).parent))
from modules.gui.track_analysis.track_map_widget import TrackMapWidget


class PureGeoTrackMap(QMainWindow):
    """純 GeoJSON 賽道視覺化"""
    
    def __init__(self):
        super().__init__()
        self.geo_data = None
        self.init_ui()
        self._load_and_display()
    
    def init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("🌍 Pure GeoJSON Track Visualizer")
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
        self.track_map.show_official_corners = False  # 關閉彎道顯示
        splitter.addWidget(self.track_map)
        
        # ElevationProfileWidget
        self.elevation_widget = ElevationProfileWidget()
        splitter.addWidget(self.elevation_widget)
        
        # 設定比例（TrackMap 70%，Elevation 30%）
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
        """載入並顯示數據"""
        # 從命令列參數讀取檔案
        if len(sys.argv) > 1:
            json_file = sys.argv[1]
        else:
            json_file = "mc_1929_elevation_data.json"
        
        if not self._load_geojson_data(json_file):
            self.info_label.setText("❌ 數據載入失敗")
            return
        
        # 轉換為 TrackMapWidget 格式
        trackmap_data = self._convert_geojson_to_trackmap()
        
        # 載入到 TrackMapWidget
        success = self.track_map.load_track_data(trackmap_data)
        
        if success:
            # 更新資訊標籤
            info = self.geo_data.get('basic_info', {})
            coords = self.geo_data.get('coordinates', [])
            elevations = [c['elevation'] for c in coords]
            
            info_html = f"""
            <b>🌍 {info.get('name', 'Circuit')}</b> | 
            {info.get('country', 'N/A')} | 
            Length: {info.get('length_meters', 0)/1000:.3f} km | 
            Elevation: {min(elevations):.0f}m ~ {max(elevations):.0f}m 
            (Δ{max(elevations) - min(elevations):.0f}m)
            """
            
            # 顯示校正資訊（如果有）
            correction = self.geo_data.get('elevation_correction', {})
            if correction.get('applied', False):
                info_html += f"<br><small>📊 高程校正: {correction.get('source', 'Applied')}</small>"
            
            self.info_label.setText(info_html)
            
            # 設置賽道名稱
            circuit_name = info.get('name', 'Circuit')
            self.elevation_widget.set_circuit_name(circuit_name)
            
            # 繪製高程剖面
            self._refresh_elevation()
            
            # 更新統計
            self.stats_label.setText(
                f"資料來源: 純 GeoJSON | 座標點: {len(coords)} | "
                f"座標系統: GPS (經緯度) | 無 FastF1 映射"
            )
            
            print("\n✅ 純 GeoJSON 數據已載入")
        else:
            self.info_label.setText("❌ TrackMapWidget 載入失敗")
    
    def _load_geojson_data(self, json_file: str):
        """載入 GeoJSON 數據"""
        print(f"\n🔄 載入 GeoJSON: {json_file}")
        
        try:
            # 嘗試多個路徑
            possible_paths = [
                Path(json_file),
                Path(f"json/f1-circuits-master/circuit_data/{json_file}"),
                Path(__file__).parent / "json" / "f1-circuits-master" / "circuit_data" / json_file
            ]
            
            json_path = None
            for path in possible_paths:
                if path.exists():
                    json_path = path
                    break
            
            if json_path is None:
                print(f"❌ 找不到檔案: {json_file}")
                return False
            
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'coordinates' not in data:
                print(f"❌ JSON 缺少 'coordinates' 欄位")
                return False
            
            # F1 官方高程校正（針對特定賽道）
            self._apply_f1_official_elevation_correction(data)
            
            self.geo_data = data
            
            coords = data['coordinates']
            elevations = [c['elevation'] for c in coords]
            info = data.get('basic_info', {})
            
            print(f"✅ 載入成功:")
            print(f"   - 賽道: {info.get('name', 'N/A')}")
            print(f"   - 點數: {len(coords)}")
            print(f"   - 長度: {info.get('length_meters', 0)}m")
            print(f"   - 高程: {min(elevations):.1f}m ~ {max(elevations):.1f}m")
            
            return True
            
        except Exception as e:
            print(f"❌ 載入失敗: {e}")
            return False
    
    def _apply_f1_official_elevation_correction(self, data):
        """根據 F1 官方數據校正高程"""
        circuit_name = data.get('basic_info', {}).get('name', '').lower()
        coordinates = data['coordinates']
        elevations = [c['elevation'] for c in coordinates]
        
        # F1 官方高程數據
        f1_official_data = {
            'monaco': {
                'min_elevation': 47.5,  # 港口區域
                'max_elevation': 89.5,  # Casino Square
                'description': 'F1 Official (above sea level)'
            },
            'suzuka': {
                'min_elevation': 45,
                'max_elevation': 95,
                'description': 'F1 Official estimate'
            }
        }
        
        # 檢查是否需要校正
        for key, official in f1_official_data.items():
            if key in circuit_name:
                current_min = min(elevations)
                current_max = max(elevations)
                current_range = current_max - current_min
                official_range = official['max_elevation'] - official['min_elevation']
                
                print(f"\n🔧 應用 F1 官方高程校正:")
                print(f"   原始: {current_min:.1f}m ~ {current_max:.1f}m (Δ{current_range:.1f}m)")
                print(f"   官方: {official['min_elevation']:.1f}m ~ {official['max_elevation']:.1f}m (Δ{official_range:.1f}m)")
                
                # 線性縮放到官方範圍
                for coord in coordinates:
                    # 正規化到 [0, 1]
                    normalized = (coord['elevation'] - current_min) / current_range if current_range > 0 else 0
                    # 縮放到官方範圍
                    coord['elevation'] = official['min_elevation'] + normalized * official_range
                
                # 更新 metadata
                data['elevation_correction'] = {
                    'applied': True,
                    'source': official['description'],
                    'original_range': f"{current_min:.1f}m ~ {current_max:.1f}m",
                    'corrected_range': f"{official['min_elevation']:.1f}m ~ {official['max_elevation']:.1f}m"
                }
                
                print(f"   ✅ 校正完成: 縮放到官方範圍")
                break
        else:
            # 沒有官方數據，只移除負值
            min_elev = min(elevations)
            if min_elev < 0:
                offset = abs(min_elev)
                for coord in coordinates:
                    coord['elevation'] += offset
                print(f"\n⚠️  移除負值高程: +{offset:.1f}m 偏移")
                data['elevation_correction'] = {
                    'applied': True,
                    'source': 'Negative value removal',
                    'offset': offset
                }
    
    def _convert_geojson_to_trackmap(self):
        """將 GeoJSON 轉換為 TrackMapWidget 格式"""
        if not self.geo_data:
            return {}
        
        coordinates = self.geo_data['coordinates']
        
        # 轉換 GPS 坐標為 X/Y 平面坐標（簡單投影）
        lons = [c['lon'] for c in coordinates]
        lats = [c['lat'] for c in coordinates]
        
        # 計算中心點
        center_lon = (max(lons) + min(lons)) / 2
        center_lat = (max(lats) + min(lats)) / 2
        
        print(f"\n🔄 GPS → X/Y 座標轉換")
        print(f"   中心點: {center_lat:.6f}, {center_lon:.6f}")
        
        # 轉換為 X/Y 米座標
        position_records = []
        for i, coord in enumerate(coordinates):
            # 簡單墨卡托投影
            x = (coord['lon'] - center_lon) * 111320 * np.cos(np.radians(center_lat))
            y = (coord['lat'] - center_lat) * 111320
            
            record = {
                "point_index": i + 1,
                "distance_m": coord['distance_km'] * 1000,
                "position_x": x,
                "position_y": y,
                "elevation": coord['elevation'],
                "time_seconds": 0.0
            }
            position_records.append(record)
        
        # 計算邊界
        x_coords = [r['position_x'] for r in position_records]
        y_coords = [r['position_y'] for r in position_records]
        
        track_bounds = {
            "x_min": min(x_coords),
            "x_max": max(x_coords),
            "y_min": min(y_coords),
            "y_max": max(y_coords),
            "width": max(x_coords) - min(x_coords),
            "height": max(y_coords) - min(y_coords)
        }
        
        print(f"   轉換完成: {len(position_records)} 個點")
        print(f"   範圍: {track_bounds['width']:.1f}m × {track_bounds['height']:.1f}m")
        
        return {
            "has_position_data": True,
            "position_records": position_records,
            "track_bounds": track_bounds,
            "official_corners": {
                "available": False,  # 不使用彎道數據
                "count": 0,
                "corners": []
            }
        }
    
    def _fit_view(self):
        """重置視圖"""
        self.track_map.fit_to_view()
        print("\n🔄 視圖已重置")
    
    def _refresh_elevation(self):
        """重新繪製高程剖面"""
        if not self.geo_data:
            return
        
        coordinates = self.geo_data['coordinates']
        self.elevation_widget.plot_pure_geojson_elevation(coordinates)


class ElevationProfileWidget(QWidget):
    """高程剖面圖 Widget（純 GeoJSON 版）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.circuit_name = "Circuit"
        self.init_ui()
    
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建 Matplotlib Figure
        self.figure = Figure(figsize=(12, 4), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 設置中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
    
    def set_circuit_name(self, name: str):
        """設置賽道名稱"""
        self.circuit_name = name
    
    def plot_pure_geojson_elevation(self, coordinates: list):
        """
        繪製純 GeoJSON 高程剖面（無彎道標註）
        
        Args:
            coordinates: GeoJSON 座標列表 [{'distance_km', 'elevation', ...}]
        """
        if not coordinates:
            return
        
        # 提取數據
        distances = [c['distance_km'] for c in coordinates]
        elevations = [c['elevation'] for c in coordinates]
        
        # 清除舊圖
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 繪製高程剖面
        ax.plot(distances, elevations, 'b-', linewidth=2.5, label='Track Elevation')
        ax.fill_between(distances, elevations, alpha=0.2, color='lightblue')
        
        # 標註最高點和最低點
        max_idx = elevations.index(max(elevations))
        min_idx = elevations.index(min(elevations))
        
        ax.plot(distances[max_idx], elevations[max_idx], 'ro', markersize=8)
        ax.text(distances[max_idx], elevations[max_idx] + 2, 
               f'最高點\n{elevations[max_idx]:.0f}m',
               ha='center', va='bottom', fontsize=9, color='red', fontweight='bold')
        
        ax.plot(distances[min_idx], elevations[min_idx], 'go', markersize=8)
        ax.text(distances[min_idx], elevations[min_idx] - 5, 
               f'最低點\n{elevations[min_idx]:.0f}m',
               ha='center', va='top', fontsize=9, color='green', fontweight='bold')
        
        # 設置圖表樣式
        ax.set_xlabel('Distance (km)', fontsize=11)
        ax.set_ylabel('Elevation (m)', fontsize=11)
        ax.set_title(f'{self.circuit_name} - Elevation Profile (GeoJSON)', 
                    fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right')
        
        # Y 軸範圍
        y_range = max(elevations) - min(elevations)
        margin = y_range * 0.1
        ax.set_ylim(min(elevations) - margin, max(elevations) + margin)
        
        # 緊湊佈局
        self.figure.tight_layout()
        self.canvas.draw()
        
        print(f"✅ 純 GeoJSON 高程剖面已繪製: {len(distances)} 個點")
        print(f"   範圍: {min(elevations):.1f}m ~ {max(elevations):.1f}m (Δ{max(elevations) - min(elevations):.1f}m)")


def main():
    """主程式入口"""
    print("=" * 70)
    print("🌍  Pure GeoJSON Track Visualizer")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    demo = PureGeoTrackMap()
    demo.show()
    
    print("\n✅ 視窗已開啟")
    print("💡 特點:")
    print("   - 純 GeoJSON 數據，無 FastF1 映射")
    print("   - 無彎道編號標註")
    print("   - 完整高程剖面顯示")
    print("   - 避免座標系統衝突")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()