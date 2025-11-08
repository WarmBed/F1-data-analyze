#!/usr/bin/env python3
"""
Track Map Widget 獨立測試腳本
=============================

不啟動主 GUI，單獨測試 Track Map 模組的數據載入和顯示功能

使用方式：
    python test_track_map_standalone.py
    python test_track_map_standalone.py --year 2024 --race Japan
    python test_track_map_standalone.py --json json/track_position_analysis_2024_Japan_R.json

Author: F1T Team
Date: 2025-10-26
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QLabel, QPushButton, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 確保能找到模組
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.track_analysis.track_map_widget import TrackMapWidget


class TrackMapTestWindow(QMainWindow):
    """Track Map 獨立測試視窗"""
    
    def __init__(self, json_path: Optional[str] = None):
        super().__init__()
        self.json_path = json_path
        self.track_data = None
        
        self.setWindowTitle("Track Map Widget 獨立測試")
        self.resize(1200, 800)
        
        # 創建主 Widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        
        # 標題
        title = QLabel("🏎️ Track Map Widget 獨立測試")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        # 資訊欄
        self.info_label = QLabel("等待載入數據...")
        self.info_label.setStyleSheet("padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        main_layout.addWidget(self.info_label)
        
        # 控制面板
        control_group = QGroupBox("顯示選項")
        control_layout = QHBoxLayout()
        
        self.cb_start = QCheckBox("起點")
        self.cb_finish = QCheckBox("終點")
        self.cb_markers = QCheckBox("距離標記")
        self.cb_labels = QCheckBox("標籤")
        self.cb_grid = QCheckBox("網格")
        self.cb_corners = QCheckBox("官方彎道")  # 新增
        
        # 預設啟用
        self.cb_start.setChecked(True)
        self.cb_finish.setChecked(True)
        self.cb_markers.setChecked(True)
        self.cb_grid.setChecked(True)
        self.cb_corners.setChecked(True)  # 預設啟用彎道標記
        
        # 連接信號
        self.cb_start.toggled.connect(self.update_display_options)
        self.cb_finish.toggled.connect(self.update_display_options)
        self.cb_markers.toggled.connect(self.update_display_options)
        self.cb_labels.toggled.connect(self.update_display_options)
        self.cb_grid.toggled.connect(self.update_display_options)
        self.cb_corners.toggled.connect(self.update_display_options)  # 新增
        
        control_layout.addWidget(self.cb_start)
        control_layout.addWidget(self.cb_finish)
        control_layout.addWidget(self.cb_markers)
        control_layout.addWidget(self.cb_labels)
        control_layout.addWidget(self.cb_grid)
        control_layout.addWidget(self.cb_corners)  # 新增
        control_layout.addStretch()
        
        btn_reload = QPushButton("重新載入")
        btn_reload.clicked.connect(self.reload_data)
        control_layout.addWidget(btn_reload)
        
        btn_fit = QPushButton("自動縮放")
        btn_fit.clicked.connect(self.fit_to_view)
        control_layout.addWidget(btn_fit)
        
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # Track Map Widget
        self.track_map = TrackMapWidget()
        self.track_map.setMinimumHeight(500)
        main_layout.addWidget(self.track_map, stretch=1)
        
        # 狀態列
        self.status_label = QLabel("就緒")
        self.status_label.setStyleSheet("padding: 5px; background-color: #e0e0e0;")
        main_layout.addWidget(self.status_label)
        
        # 自動載入數據
        if self.json_path:
            self.load_data_from_json(self.json_path)
    
    def load_data_from_json(self, json_path: str):
        """從 JSON 檔案載入數據"""
        try:
            self.status_label.setText(f"載入中: {json_path}")
            
            if not os.path.exists(json_path):
                self.info_label.setText(f"❌ 檔案不存在: {json_path}")
                self.status_label.setText("載入失敗")
                return
            
            # 讀取 JSON
            with open(json_path, 'r', encoding='utf-8') as f:
                self.track_data = json.load(f)
            
            # 驗證數據結構
            if not self.track_data.get('success'):
                self.info_label.setText(f"❌ JSON 標記為失敗")
                self.status_label.setText("數據無效")
                return
            
            data = self.track_data.get('data', {})
            
            if not data.get('has_position_data'):
                self.info_label.setText(f"❌ 沒有位置數據")
                self.status_label.setText("數據不完整")
                return
            
            position_records = data.get('position_records', [])
            track_bounds = data.get('track_bounds')
            official_corners = data.get('official_corners', {})
            
            # 顯示資訊
            info_lines = [
                f"📁 檔案: {Path(json_path).name}",
                f"📊 位置點數量: {len(position_records)}",
                f"🏁 賽道邊界: X[{track_bounds.get('x_min', 0):.1f}, {track_bounds.get('x_max', 0):.1f}] "
                f"Y[{track_bounds.get('y_min', 0):.1f}, {track_bounds.get('y_max', 0):.1f}]",
                f"📏 總距離: {data.get('distance_covered', 0):.1f} m",
                f"🔄 FastF1 官方彎道: {official_corners.get('count', 0)} 個 "
                f"({'可用' if official_corners.get('available') else '不可用'})"
            ]
            
            if official_corners.get('available'):
                mapping_quality = official_corners.get('mapping_quality', {})
                info_lines.append(
                    f"   └─ 映射品質: 平均誤差 {mapping_quality.get('average_error_m', 0):.1f}m, "
                    f"最大誤差 {mapping_quality.get('max_error_m', 0):.1f}m"
                )
            
            self.info_label.setText("\n".join(info_lines))
            
            # 設置 Track Map 數據 (使用 load_track_data 以支持官方彎道)
            self.track_map.load_track_data(data)
            self.update_display_options()
            
            self.status_label.setText(f"✅ 成功載入 {len(position_records)} 個位置點")
            
        except json.JSONDecodeError as e:
            self.info_label.setText(f"❌ JSON 解析錯誤: {e}")
            self.status_label.setText("解析失敗")
        except Exception as e:
            self.info_label.setText(f"❌ 載入錯誤: {e}")
            self.status_label.setText("載入失敗")
            import traceback
            traceback.print_exc()
    
    def update_display_options(self):
        """更新顯示選項"""
        if self.track_map:
            self.track_map.set_display_options(
                show_start=self.cb_start.isChecked(),
                show_finish=self.cb_finish.isChecked(),
                show_markers=self.cb_markers.isChecked(),
                show_labels=self.cb_labels.isChecked(),
                show_grid=self.cb_grid.isChecked(),
                show_corners=self.cb_corners.isChecked()  # 新增
            )
    
    def reload_data(self):
        """重新載入數據"""
        if self.json_path:
            self.load_data_from_json(self.json_path)
    
    def fit_to_view(self):
        """自動縮放"""
        if self.track_map:
            self.track_map.fit_to_view()


def find_json_file(year: int, race: str) -> Optional[str]:
    """尋找對應的 JSON 檔案"""
    json_dir = Path("json")
    
    # 嘗試多種命名模式
    patterns = [
        f"track_position_analysis_{year}_{race}_R.json",
        f"track_position_analysis_{year}*{race}*.json",
    ]
    
    for pattern in patterns:
        matches = list(json_dir.glob(pattern))
        if matches:
            return str(matches[0])
    
    return None


def main():
    parser = argparse.ArgumentParser(description="Track Map Widget 獨立測試")
    parser.add_argument("--json", help="直接指定 JSON 檔案路徑")
    parser.add_argument("--year", type=int, default=2024, help="年份 (預設: 2024)")
    parser.add_argument("--race", default="Japan", help="賽事名稱 (預設: Japan)")
    
    args = parser.parse_args()
    
    # 確定 JSON 路徑
    json_path = args.json
    
    if not json_path:
        # 自動尋找
        json_path = find_json_file(args.year, args.race)
        if not json_path:
            print(f"❌ 找不到 {args.year} {args.race} 的 JSON 檔案")
            print(f"   提示: 先執行 'python f1_analysis_modular_main.py -f 2 -y {args.year} -r {args.race} -s R'")
            return 1
    
    print(f"🏎️  Track Map Widget 獨立測試")
    print(f"📁 JSON: {json_path}")
    print(f"")
    
    # 創建 Qt 應用
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    window = TrackMapTestWindow(json_path)
    window.show()
    
    # 執行
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
