#!/usr/bin/env python3
"""
Japan 賽道整合型視覺化 Demo
==========================

展示整合 GeoJSON 賽道輪廓 + FastF1 官方彎道標註

功能：
- 🗺️ 顯示 GeoJSON 賽道輪廓（GPS 轉 X/Y 座標）
- 📍 顯示 FastF1 官方彎道標記與編號
- 🏔️ 顯示高程資訊（元數據）

使用 TrackMapWidget 進行視覺化

Author: F1T Team
Date: 2025-10-11
"""

import sys
import json
from pathlib import Path

from PyQt5.QtWidgets import (
    QApplication, 
    QMainWindow, 
    QVBoxLayout, 
    QWidget,
    QLabel,
    QHBoxLayout,
    QPushButton
)
from PyQt5.QtCore import Qt

# 導入 TrackMapWidget
sys.path.insert(0, str(Path(__file__).parent))
from modules.gui.track_analysis.track_map_widget import TrackMapWidget


class JapanCircuitDemo(QMainWindow):
    """Japan 賽道整合型視覺化 Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Japan Circuit Demo - GeoJSON + FastF1 Corners")
        self.setGeometry(100, 100, 1200, 800)
        
        # 載入整合型 JSON
        self.json_path = Path("json/japan_circuit_integrated_2025.json")
        self.integrated_data = self._load_integrated_json()
        
        # 創建 UI
        self._create_ui()
        
        # 載入數據到 TrackMapWidget
        self._load_data_to_widget()
    
    def _load_integrated_json(self) -> dict:
        """載入整合型 JSON 檔案"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 成功載入: {self.json_path}")
            print(f"📊 賽道: {data['circuit_info']['name']}")
            print(f"📊 座標點: {data['track_outline']['coordinate_count']}")
            print(f"📊 彎道數: {data['fastf1_corners']['count']}")
            return data
        except Exception as e:
            print(f"❌ 載入 JSON 失敗: {e}")
            return {}
    
    def _create_ui(self):
        """創建使用者介面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # === 頂部資訊欄 ===
        info_layout = QHBoxLayout()
        
        # 賽道資訊
        circuit_info = self.integrated_data.get('circuit_info', {})
        info_text = (
            f"賽道: {circuit_info.get('name', 'N/A')} | "
            f"年份: {circuit_info.get('year', 'N/A')} | "
            f"長度: {circuit_info.get('track_length_km', 'N/A')} km"
        )
        info_label = QLabel(info_text)
        info_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 10px;")
        info_layout.addWidget(info_label)
        
        # 高程資訊
        elevation = self.integrated_data.get('elevation_profile', {})
        elevation_text = (
            f"高程: {elevation.get('min_elevation', 'N/A')}-{elevation.get('max_elevation', 'N/A')}m "
            f"(變化 {elevation.get('elevation_change', 'N/A')}m)"
        )
        elevation_label = QLabel(elevation_text)
        elevation_label.setStyleSheet("font-size: 12px; color: #666; padding: 10px;")
        info_layout.addWidget(elevation_label)
        
        info_layout.addStretch()
        
        # 控制按鈕
        toggle_corners_btn = QPushButton("切換彎道顯示")
        toggle_corners_btn.clicked.connect(self._toggle_corners)
        info_layout.addWidget(toggle_corners_btn)
        
        fit_view_btn = QPushButton("重置視圖")
        fit_view_btn.clicked.connect(self._fit_view)
        info_layout.addWidget(fit_view_btn)
        
        layout.addLayout(info_layout)
        
        # === TrackMapWidget ===
        self.track_map = TrackMapWidget()
        self.track_map.show_official_corners = True  # 啟用彎道顯示
        layout.addWidget(self.track_map)
        
        # === 底部統計資訊 ===
        stats_layout = QHBoxLayout()
        
        track_outline = self.integrated_data.get('track_outline', {})
        fastf1_corners = self.integrated_data.get('fastf1_corners', {})
        
        stats_text = (
            f"賽道輪廓點數: {track_outline.get('coordinate_count', 0)} | "
            f"官方彎道數: {fastf1_corners.get('count', 0)} | "
            f"座標系統: {self.integrated_data.get('metadata', {}).get('coordinate_system', 'N/A')}"
        )
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("font-size: 11px; color: #888; padding: 5px;")
        stats_layout.addWidget(stats_label)
        stats_layout.addStretch()
        
        layout.addLayout(stats_layout)
    
    def _load_data_to_widget(self):
        """將整合型數據載入 TrackMapWidget"""
        if not self.integrated_data:
            print("❌ 無數據可載入", flush=True)
            return
        
        # 轉換為 TrackMapWidget 期望的格式
        track_data = self._convert_to_trackmap_format(self.integrated_data)
        
        print("=" * 70, flush=True)
        print("[DEBUG] 轉換後的數據格式:", flush=True)
        print(f"  position_records 數量: {len(track_data.get('position_records', []))}", flush=True)
        if track_data.get('position_records'):
            first = track_data['position_records'][0]
            print(f"  第一個點: {first}", flush=True)
        print(f"  track_bounds: {track_data.get('track_bounds')}", flush=True)
        print(f"  official_corners 數量: {track_data.get('official_corners', {}).get('count', 0)}", flush=True)
        print("=" * 70, flush=True)
        
        # 載入數據
        success = self.track_map.load_track_data(track_data)
        if success:
            print("✅ 數據已載入到 TrackMapWidget", flush=True)
        else:
            print("❌ TrackMapWidget 載入失敗", flush=True)
    
    def _convert_to_trackmap_format(self, integrated_data: dict) -> dict:
        """
        轉換整合型 JSON 為 TrackMapWidget 期望的格式
        
        TrackMapWidget 期望格式：
        {
            'position_records': [{'position_x': float, 'position_y': float, ...}],
            'track_bounds': {'x_min': float, 'x_max': float, 'y_min': float, 'y_max': float},
            'official_corners': {'available': bool, 'corners': [...]},
            'session_info': {'track_name': str, ...}
        }
        """
        # 1. 賽道輪廓點（position_records）- 注意欄位名稱要用 position_x/position_y
        track_outline = integrated_data.get('track_outline', {})
        position_records = []
        for coord in track_outline.get('coordinates', []):
            position_records.append({
                'position_x': coord['x'],  # ⚠️ TrackMapWidget 期望 position_x
                'position_y': coord['y'],  # ⚠️ TrackMapWidget 期望 position_y
                'x': coord['x'],  # 保留原始欄位名稱
                'y': coord['y'],
                'elevation': coord.get('elevation'),
                'distance': coord.get('distance_km', 0) * 1000  # km → m
            })
        
        # 2. 賽道邊界
        track_bounds = integrated_data.get('track_bounds', {})
        
        # 3. 官方彎道
        official_corners = integrated_data.get('fastf1_corners', {})
        
        # 4. 會話資訊
        circuit_info = integrated_data.get('circuit_info', {})
        session_info = {
            'track_name': circuit_info.get('name', 'Japan Circuit'),
            'year': circuit_info.get('year', 2025),
            'location': circuit_info.get('location', 'Suzuka')
        }
        
        return {
            'position_records': position_records,
            'track_bounds': track_bounds,
            'official_corners': official_corners,
            'session_info': session_info
        }
    
    def _toggle_corners(self):
        """切換彎道顯示"""
        self.track_map.show_official_corners = not self.track_map.show_official_corners
        print(f"{'✅' if self.track_map.show_official_corners else '❌'} 彎道顯示: {self.track_map.show_official_corners}")
        self.track_map.update()
    
    def _fit_view(self):
        """重置視圖"""
        self.track_map.fit_to_view()
        print("🔄 視圖已重置")


def main():
    """主程式進入點"""
    print("=" * 70, flush=True)
    print("Japan Circuit Demo - GeoJSON + FastF1 Corners", flush=True)
    print("=" * 70, flush=True)
    
    # 檢查檔案是否存在
    json_path = Path("json/japan_circuit_integrated_2025.json")
    if not json_path.exists():
        print(f"❌ 找不到整合型 JSON: {json_path}", flush=True)
        print("💡 請先執行: python generate_japan_circuit_integrated_json.py", flush=True)
        sys.exit(1)
    
    print(f"✅ 找到整合型 JSON: {json_path}", flush=True)
    
    try:
        app = QApplication(sys.argv)
        
        # 啟動 Demo
        print("🔨 創建 Demo 視窗...", flush=True)
        demo = JapanCircuitDemo()
        demo.show()
        
        print("✅ Demo 視窗已啟動", flush=True)
        print("💡 功能說明:", flush=True)
        print("   - 滑鼠滾輪: 縮放視圖", flush=True)
        print("   - 滑鼠拖曳: 平移視圖", flush=True)
        print("   - 切換彎道顯示: 顯示/隱藏官方彎道標記", flush=True)
        print("   - 重置視圖: 恢復到最佳視圖範圍", flush=True)
        
        sys.exit(app.exec_())
    except Exception as e:
        print(f"❌ Demo 啟動失敗: {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
