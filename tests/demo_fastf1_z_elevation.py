#!/usr/bin/env python3
"""
FastF1 Z 軸高程分析演示
=====================

使用 FastF1 遙測數據的 Z 軸（高度）繪製賽道高程剖面圖

特點：
1. 直接使用 FastF1 的 X, Y, Z 座標數據
2. 不依賴外部 GeoJSON 或 DEM 數據
3. 與遙測數據完美同步
4. 顯示賽道地圖 + 高程剖面

Author: F1T Team
Date: 2025-11-09
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QLinearGradient, QBrush

# 設置路徑
sys.path.insert(0, str(Path(__file__).parent))

from modules.gui.track_analysis.track_map_widget import TrackMapWidget
from modules.gui.track_elevation.elevation_chart_widget_pyqt5 import ElevationChartWidget

import fastf1
import numpy as np


class FastF1ElevationDemo(QMainWindow):
    """FastF1 Z 軸高程演示視窗"""
    
    def __init__(self):
        super().__init__()
        
        self.track_data: Dict[str, Any] = {}
        self.flags_data: Dict[str, Any] = {}  # 旗幟統計數據
        self.setWindowTitle("FastF1 Z 軸高程分析演示 + 歷年旗幟統計")
        self.setGeometry(100, 100, 1600, 900)  # 加寬視窗以容納表格
        
        self.init_ui()
        self._load_and_display()
    
    def init_ui(self):
        """初始化 UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)  # 🔒 固定間距，防止元素間距擴張
        
        # === 頂部資訊與控制 ===
        info_layout = QHBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 5)  # 🔒 設定邊距
        
        self.info_label = QLabel("載入中...")
        self.info_label.setStyleSheet(
            "font-size: 14px; padding: 10px; "
            "background: #e3f2fd; border-radius: 5px; border: 1px solid #90caf9;"
        )
        self.info_label.setMinimumWidth(400)  # 🔒 設定最小寬度
        self.info_label.setMaximumWidth(800)  # 🔒 設定最大寬度，防止無限擴張
        info_layout.addWidget(self.info_label, stretch=0)  # 🔒 移除 stretch，改為 0
        
        # 控制按鈕
        toggle_corners_btn = QPushButton("🎯 切換彎道")
        toggle_corners_btn.clicked.connect(self._toggle_corners)
        toggle_corners_btn.setFixedWidth(120)
        toggle_corners_btn.setFixedHeight(40)  # 🔒 固定高度
        info_layout.addWidget(toggle_corners_btn, stretch=0)  # 🔒 無伸縮
        
        fit_view_btn = QPushButton("🔄 重置視圖")
        fit_view_btn.clicked.connect(self._fit_view)
        fit_view_btn.setFixedWidth(120)
        fit_view_btn.setFixedHeight(40)  # 🔒 固定高度
        info_layout.addWidget(fit_view_btn, stretch=0)  # 🔒 無伸縮
        
        refresh_btn = QPushButton("📊 重新繪製")
        refresh_btn.clicked.connect(self._refresh_charts)
        refresh_btn.setFixedWidth(120)
        refresh_btn.setFixedHeight(40)  # 🔒 固定高度
        info_layout.addWidget(refresh_btn, stretch=0)  # 🔒 無伸縮
        
        # 速度漸層模式 Checkbox
        self.speed_gradient_checkbox = QCheckBox("🌈 速度漸層")
        self.speed_gradient_checkbox.setFixedHeight(40)
        self.speed_gradient_checkbox.setStyleSheet("font-size: 12px; padding: 5px;")
        self.speed_gradient_checkbox.stateChanged.connect(self._toggle_speed_gradient)
        info_layout.addWidget(self.speed_gradient_checkbox, stretch=0)  # 🔒 無伸縮
        
        # 🔒 不加 addStretch()，保持固定佈局
        
        main_layout.addLayout(info_layout)
        
        # === 使用水平 QSplitter 分割左側圖表和右側統計表 ===
        horizontal_splitter = QSplitter(Qt.Horizontal)
        
        # === 左側：垂直 QSplitter 分割 TrackMap 和 Elevation ===
        left_splitter = QSplitter(Qt.Vertical)
        
        # TrackMapWidget（賽道平面圖）
        self.track_map = TrackMapWidget()
        self.track_map.show_official_corners = True
        left_splitter.addWidget(self.track_map)
        
        # ElevationChartWidget（高程剖面圖）
        self.elevation_chart = ElevationChartWidget()
        left_splitter.addWidget(self.elevation_chart)
        
        # 設定左側比例（TrackMap 60%，Elevation 40%）
        left_splitter.setStretchFactor(0, 6)
        left_splitter.setStretchFactor(1, 4)
        
        horizontal_splitter.addWidget(left_splitter)
        
        # === 右側：旗幟統計表格 ===
        right_panel = self._create_flags_statistics_panel()
        horizontal_splitter.addWidget(right_panel)
        
        # 設定水平比例（左側圖表 65%，右側表格 35%）
        horizontal_splitter.setStretchFactor(0, 65)
        horizontal_splitter.setStretchFactor(1, 35)
        
        main_layout.addWidget(horizontal_splitter)
    
    def _create_flags_statistics_panel(self) -> QWidget:
        """創建右側旗幟統計面板"""
        panel = QWidget()
        panel.setMaximumWidth(600)  # 🔒 強制最大寬度 600px (35%)
        panel.setMinimumWidth(400)  # 🔒 最小寬度 400px
        panel.setMaximumHeight(700)  # 🔒 強制最大高度，防止隨視窗放大
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)  # 🔒 固定尺寸約束
        
        # === 標題 ===
        title_label = QLabel("歷年旗幟統計 (2022-2025)")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet(
            "background: #F5F5F5; color: #333; padding: 8px; "
            "border: 1px solid #E0E0E0; border-radius: 3px;"
        )
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # === 年度統計表格 ===
        yearly_group = QGroupBox("年度統計")
        yearly_group.setMaximumHeight(200)  # 🔒 固定 GroupBox 最大高度
        yearly_layout = QVBoxLayout(yearly_group)
        yearly_layout.setContentsMargins(5, 5, 5, 5)  # 🔧 減少邊距 (左, 上, 右, 下)
        yearly_layout.setSpacing(2)  # 🔧 減少間距
        
        self.yearly_table = QTableWidget()
        self.yearly_table.setRowCount(4)  # 4 行（年份）
        self.yearly_table.setColumnCount(5)  # 🆕 5 列（旗幟類型 + 名次變更）
        self.yearly_table.setFixedWidth(660)  # 🔧 調整寬度 (540 → 660，增加 120px)
        self.yearly_table.setMinimumHeight(130)  # 🔧 最小高度
        self.yearly_table.setMaximumHeight(160)  # 🔧 最大高度（解除固定限制）
        self.yearly_table.setVerticalHeaderLabels(['2022', '2023', '2024', '2025'])
        self.yearly_table.setHorizontalHeaderLabels(['Yellow', 'D-Yellow', 'Red', 'Safety', 'Position Δ'])  # 🆕 新增列
        
        # 設定固定列寬和行高
        # 計算：660px 總寬 - 60px 垂直標題 = 600px 可用寬度
        # 600px ÷ 5 列 = 120px 每列
        for col in range(5):  # 🆕 改為 5 列
            self.yearly_table.setColumnWidth(col, 120)
        for row in range(4):
            self.yearly_table.setRowHeight(row, 26)  # 🔧 調整行高 (24 → 26)
        
        self.yearly_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.yearly_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.yearly_table.setAlternatingRowColors(True)
        
        # 🎨 設定標題欄位顏色（淺色系）
        header_colors = [
            QColor('#FFF9C4'),  # Yellow - 淺黃色
            QColor('#FFE082'),  # D-Yellow - 淺橙色
            QColor('#FFCDD2'),  # Red - 淺紅色
            QColor('#E1BEE7'),  # Safety - 淺紫色
            QColor('#C5E1A5')   # 🆕 Position Δ - 淺綠色
        ]
        for col, color in enumerate(header_colors):
            header_item = self.yearly_table.horizontalHeaderItem(col)
            if header_item:
                header_item.setBackground(color)
        
        self.yearly_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 10px;
            }
            QHeaderView::section {
                padding: 4px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 9px;
            }
        """)
        
        yearly_layout.addWidget(self.yearly_table)
        layout.addWidget(yearly_group)
        
        # === 彎道統計表格 ===
        corner_group = QGroupBox("彎道旗幟統計 (2022-2025)")
        corner_group.setMaximumHeight(300)  # 🔒 固定 GroupBox 最大高度
        corner_layout = QVBoxLayout(corner_group)
        corner_layout.setContentsMargins(5, 5, 5, 5)  # 🔧 減少邊距
        corner_layout.setSpacing(2)  # 🔧 減少間距
        
        self.corner_table = QTableWidget()
        self.corner_table.setColumnCount(5)  # Turn, Yellow, D-Yellow, Red, Safety
        self.corner_table.setRowCount(0)  # 動態填充
        self.corner_table.setMaximumWidth(540)  # 🔧 調整寬度 (560 → 540)
        self.corner_table.setMinimumHeight(150)
        self.corner_table.setMaximumHeight(250)  # 限制高度，可滾動
        self.corner_table.setHorizontalHeaderLabels(['Turn', 'Yellow', 'D-Yellow', 'Red', 'Safety'])
        
        # 設定列寬
        self.corner_table.setColumnWidth(0, 60)  # Turn 列較窄
        for col in range(1, 5):
            self.corner_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)
        
        self.corner_table.verticalHeader().setVisible(False)
        self.corner_table.setAlternatingRowColors(True)
        self.corner_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 9px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 4px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 9px;
            }
        """)
        
        corner_layout.addWidget(self.corner_table)
        layout.addWidget(corner_group)
        
        # === 總計統計表格（水平排列）===
        total_group = QGroupBox("總計 (2022-2025)")
        total_group.setMaximumHeight(120)  # 🔒 固定 GroupBox 最大高度
        total_layout = QVBoxLayout(total_group)
        total_layout.setContentsMargins(1, 1, 1, 1)  # 🔧 邊距設為 1
        total_layout.setSpacing(1)  # 🔧 間距設為 1
        
        self.total_table = QTableWidget()
        self.total_table.setRowCount(2)  # 2 行: 類型 + 數量
        self.total_table.setColumnCount(5)  # 🆕 5 列: Yellow, D-Yellow, Red, Safety, Position Δ
        self.total_table.setFixedWidth(660)  # 🆕 調整寬度 (540 → 660，增加 120px)
        self.total_table.setFixedHeight(80)  # 固定高度 80px
        self.total_table.setVerticalHeaderLabels(['類型', '總數'])
        self.total_table.setHorizontalHeaderLabels(['Yellow', 'D-Yellow', 'Red', 'Safety', 'Position Δ'])  # 🆕 新增列
        
        # 初始化類型行（第 0 行）- 加入顏色（淺色系）
        flag_types = ['Yellow', 'D-Yellow', 'Red', 'Safety', 'Position Δ']  # 🆕 新增
        flag_colors = [
            QColor('#FFF9C4'),  # Yellow - 淺黃色
            QColor('#FFE082'),  # D-Yellow - 淺橙色
            QColor('#FFCDD2'),  # Red - 淺紅色
            QColor('#E1BEE7'),  # Safety - 淺紫色
            QColor('#C5E1A5')   # 🆕 Position Δ - 淺綠色
        ]
        
        for col, (flag_type, flag_color) in enumerate(zip(flag_types, flag_colors)):
            type_item = QTableWidgetItem(flag_type)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setBackground(flag_color)  # 設定背景色
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            type_item.setFont(font)
            self.total_table.setItem(0, col, type_item)
            
            # 初始化數量行（第 1 行）
            count_item = QTableWidgetItem("0")
            count_item.setTextAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(8)  # 固定字體大小 8
            count_item.setFont(font)
            self.total_table.setItem(1, col, count_item)
        
        # 設定固定列寬
        for col in range(5):  # 🆕 改為 5 列
            self.total_table.setColumnWidth(col, 120)  # 調整列寬為 120
        
        self.total_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.total_table.horizontalHeader().setVisible(False)  # 隱藏列標題
        self.total_table.verticalHeader().setVisible(True)
        self.total_table.setAlternatingRowColors(False)
        self.total_table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                gridline-color: #E0E0E0;
                font-size: 8px;
            }
            QHeaderView::section {
                background-color: #F5F5F5;
                padding: 4px;
                border: 1px solid #E0E0E0;
                font-weight: bold;
                font-size: 9px;
            }
        """)
        
        total_layout.addWidget(self.total_table)
        layout.addWidget(total_group)
        
        # === 數據來源說明 ===
        source_label = QLabel("數據來源: Function 100")
        source_label.setStyleSheet(
            "font-size: 9px; color: #999; padding: 3px; "
            "background: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 2px;"
        )
        source_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(source_label)
        
        # ✅ 移除 addStretch() 以防止垂直擴展
        # layout.addStretch()  # 已禁用：會導致灰色空白處隨視窗變大
        return panel
    
    def _load_and_display(self):
        """載入 FastF1 數據並顯示"""
        try:
            print("\n" + "=" * 70)
            print("🏎️  載入 FastF1 Z 軸高程數據 + Function 100 Speed 數據")
            print("=" * 70)
            
            # 載入 FastF1 數據
            track_data = self._load_fastf1_data(
                year=2024,
                race='Japan',
                session='R'
            )
            
            if not track_data:
                self.info_label.setText("❌ FastF1 數據載入失敗")
                QMessageBox.critical(self, "載入失敗", 
                                   "無法載入 FastF1 數據，請檢查網路連接或緩存。")
                return
            
            self.track_data = track_data
            
            # 🚀 載入 Function 100 的 Speed 數據
            self._load_function100_speed_data()
            
            # 設置賽道名稱
            metadata = track_data.get('metadata', {})
            circuit_name = f"{metadata.get('race', 'Circuit')} {metadata.get('year', '')}"
            self.elevation_chart.set_circuit_name(circuit_name)
            
            # 轉換為 TrackMapWidget 格式
            trackmap_data = self._convert_to_trackmap_format()
            
            # 載入到 TrackMapWidget
            success = self.track_map.load_track_data(trackmap_data)
            
            # 🚩 載入旗幟統計數據（在賽道載入後）
            self._load_flags_statistics()
            
            # 🎨 將旗幟數據傳遞給 TrackMapWidget 用於彎道標記
            if self.flags_data and hasattr(self.track_map, 'set_corner_flags'):
                corner_analysis = self.flags_data.get('corner_analysis', {})
                self.track_map.set_corner_flags(corner_analysis)
                print(f"✅ 已傳遞 {len(corner_analysis)} 個彎道的旗幟數據給 TrackMapWidget")
            
            if success:
                # 更新資訊標籤
                elev_profile = track_data.get('elevation_profile', {})
                driver = metadata.get('fastest_lap_driver', 'N/A')
                
                info_html = f"""
                <b>🏁 {circuit_name}</b> | 
                Driver: {driver} | 
                Distance: {metadata.get('total_distance_m', 0)/1000:.2f} km | 
                <b>Elevation: {elev_profile.get('min_elevation', 0):.0f}m ~ {elev_profile.get('max_elevation', 0):.0f}m</b> 
                (Δ{elev_profile.get('elevation_change', 0):.0f}m) | 
                <span style='color: #2196F3; font-weight: bold;'>數據來源: FastF1 Z 軸</span>
                """
                self.info_label.setText(info_html)
                
                # 繪製高程剖面
                self._refresh_charts()
                
                # 更新統計資訊
                outline_count = len(trackmap_data['position_records'])
                corners_count = len(trackmap_data.get('official_corners', {}).get('corners', []))
                data_points = metadata.get('data_points', 0)
                
                print("\n✅ 數據載入完成")
                print(f"   - 賽道點數: {outline_count}")
                print(f"   - 彎道數: {corners_count}")
                print(f"   - 高程範圍: {elev_profile.get('min_elevation', 0):.1f}m ~ {elev_profile.get('max_elevation', 0):.1f}m")
                
            else:
                self.info_label.setText("❌ TrackMapWidget 載入失敗")
                
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.info_label.setText(f"❌ 錯誤: {str(e)}")
    
    def _load_fastf1_data(self, year: int, race: str, session: str) -> Dict[str, Any]:
        """
        載入 FastF1 數據（包含 Z 軸高度）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 ('R', 'Q', 'FP1' 等)
            
        Returns:
            包含賽道輪廓、彎道、高程的字典
        """
        print(f"\n[載入] FastF1 {year} {race} {session}")
        
        # 啟用緩存
        cache_dir = Path(__file__).parent / 'f1_analysis_cache'
        cache_dir.mkdir(exist_ok=True)
        fastf1.Cache.enable_cache(str(cache_dir))
        
        # 載入會話
        print("   - 載入會話數據...")
        session_obj = fastf1.get_session(year, race, session)
        session_obj.load()
        print("   ✅ 會話數據載入完成")
        
        # 獲取最快圈
        print("   - 獲取最快圈...")
        fastest_lap = session_obj.laps.pick_fastest()
        driver = fastest_lap['Driver']
        lap_time = fastest_lap['LapTime']
        print(f"   ✅ 最快圈: {driver} - {lap_time}")
        
        # 獲取位置數據（包含 X, Y, Z）
        print("   - 獲取位置數據（X, Y, Z）...")
        pos_data = fastest_lap.get_pos_data()
        
        # 檢查 Z 軸數據
        if 'Z' not in pos_data.columns:
            print("   ❌ 錯誤: 無 Z 軸數據")
            return None
        
        print(f"   ✅ 位置數據: {len(pos_data)} 點（包含 Z 軸）")
        
        # 獲取遙測數據（包含 Distance 欄位）
        print("   - 獲取遙測數據...")
        telemetry = fastest_lap.get_telemetry()
        
        # 使用 FastF1 提供的 Distance 欄位（公尺）
        if 'Distance' not in telemetry.columns:
            print("   ❌ 錯誤: 遙測數據中無 Distance 欄位")
            return None
        
        # ⚠️ 重要：不使用 pos_data！改用 telemetry 的完整數據
        # telemetry 已包含 X, Y, Z 和 Distance，且數據點更完整（698 vs 350）
        if 'X' in telemetry.columns and 'Y' in telemetry.columns and 'Z' in telemetry.columns:
            # 使用 telemetry 的完整數據
            x = telemetry['X'].values
            y = telemetry['Y'].values
            z = telemetry['Z'].values
            distances = telemetry['Distance'].values
            print(f"   ✅ 使用 telemetry 完整數據（更精確）")
        else:
            # Fallback: 使用 pos_data（但會被截斷）
            x = pos_data['X'].values
            y = pos_data['Y'].values
            z = pos_data['Z'].values
            distances = telemetry['Distance'].values
            
            # 確保數據長度一致
            min_len = min(len(x), len(distances))
            x = x[:min_len]
            y = y[:min_len]
            z = z[:min_len]
            distances = distances[:min_len]
            print(f"   ⚠️ 使用 pos_data（數據點較少）")
        
        print(f"   ✅ 遙測數據: {len(distances)} 點")
        print(f"   ✅ 距離範圍: {distances[0]:.1f}m ~ {distances[-1]:.1f}m (總長 {distances[-1]:.1f}m)")
        
        # 採樣賽道輪廓（每 50 公尺取一個點）
        sample_size = 200
        sample_indices = np.linspace(0, len(distances)-1, sample_size, dtype=int)
        
        track_outline = []
        for idx in sample_indices:
            point = {
                "x": float(x[idx]),
                "y": float(y[idx]),
                "elevation": float(z[idx]),  # Z 軸原始值（會在圖表中除以 10）
                "z": float(z[idx]),  # 同時提供 z 欄位
                "distance_m": float(distances[idx])  # 使用 FastF1 的 Distance
            }
            track_outline.append(point)
        
        print(f"   ✅ 賽道輪廓: {len(track_outline)} 點")
        
        # 計算賽道邊界
        track_bounds = {
            "x_min": float(np.min(x)),
            "x_max": float(np.max(x)),
            "y_min": float(np.min(y)),
            "y_max": float(np.max(y))
        }
        
        # 高程統計（FastF1 Z 軸需除以 10）
        z_clean = z[~np.isnan(z)]
        elevation_profile = {
            "available": True,
            "min_elevation": float(np.min(z_clean) / 10.0),
            "max_elevation": float(np.max(z_clean) / 10.0),
            "elevation_change": float((np.max(z_clean) - np.min(z_clean)) / 10.0),
            "data_source": "FastF1 Z Axis (corrected /10)"
        }
        
        print(f"   ✅ 高程: {elevation_profile['min_elevation']:.1f}m ~ {elevation_profile['max_elevation']:.1f}m")
        print(f"      變化: {elevation_profile['elevation_change']:.1f}m")
        print(f"      ⚠️ FastF1 Z 軸已除以 10 修正單位")
        
        # 獲取官方彎道數據（如果有）
        official_corners = self._get_official_corners(session_obj, fastest_lap)
        
        # 構建結果
        result = {
            "metadata": {
                "source": "FastF1 Position Data (X/Y/Z)",
                "year": year,
                "race": race,
                "session": session,
                "fastest_lap_driver": str(driver),
                "fastest_lap_time": str(lap_time),
                "total_distance_m": float(distances[-1]),
                "data_points": len(pos_data)
            },
            "track_outline": track_outline,
            "track_bounds": track_bounds,
            "elevation_profile": elevation_profile,
            "official_corners": official_corners
        }
        
        return result
    
    def _get_official_corners(self, session_obj, fastest_lap) -> Dict[str, Any]:
        """獲取 FastF1 官方彎道數據"""
        try:
            # 方法 1: 使用 session.get_circuit_info()
            if hasattr(session_obj, 'get_circuit_info'):
                try:
                    circuit_info = session_obj.get_circuit_info()
                    if hasattr(circuit_info, 'corners') and len(circuit_info.corners) > 0:
                        corner_list = []
                        for _, corner in circuit_info.corners.iterrows():
                            corner_data = {
                                "number": int(corner['Number']),
                                "x": float(corner['X']),
                                "y": float(corner['Y']),
                                "distance": float(corner.get('Distance', 0)),
                                "angle": float(corner.get('Angle', 0))
                            }
                            corner_list.append(corner_data)
                        
                        print(f"   ✅ 官方彎道（circuit_info）: {len(corner_list)} 個")
                        return {
                            "available": True,
                            "count": len(corner_list),
                            "corners": corner_list
                        }
                except Exception as e:
                    print(f"   ⚠️ circuit_info 方法失敗: {e}")
            
            # 方法 2: 手動定義鈴鹿賽道彎道（Fallback）
            print(f"   ℹ️ 使用預設鈴鹿賽道彎道定義")
            
            # 獲取遙測數據以計算距離
            telemetry = fastest_lap.get_telemetry()
            pos_data = fastest_lap.get_pos_data()
            
            # 鈴鹿賽道 18 個彎道的大致位置（基於距離百分比）
            suzuka_corners = [
                {"number": 1, "distance_pct": 0.048},   # Turn 1
                {"number": 2, "distance_pct": 0.120},   # Turn 2
                {"number": 3, "distance_pct": 0.168},   # Turn 3 (Spoon Curve entry)
                {"number": 4, "distance_pct": 0.216},   # Turn 4 (Spoon Curve exit)
                {"number": 5, "distance_pct": 0.264},   # Turn 5 (Hairpin)
                {"number": 6, "distance_pct": 0.312},   # Turn 6
                {"number": 7, "distance_pct": 0.360},   # Turn 7 (Degner 1)
                {"number": 8, "distance_pct": 0.408},   # Turn 8 (Degner 2)
                {"number": 9, "distance_pct": 0.456},   # Turn 9
                {"number": 10, "distance_pct": 0.504},  # Turn 10 (Hairpin)
                {"number": 11, "distance_pct": 0.552},  # Turn 11 (Spoon entry)
                {"number": 12, "distance_pct": 0.600},  # Turn 12 (Spoon exit)
                {"number": 13, "distance_pct": 0.648},  # Turn 13 (130R entry)
                {"number": 14, "distance_pct": 0.696},  # Turn 14 (130R exit)
                {"number": 15, "distance_pct": 0.744},  # Turn 15 (Casio Triangle)
                {"number": 16, "distance_pct": 0.792},  # Turn 16
                {"number": 17, "distance_pct": 0.840},  # Turn 17
                {"number": 18, "distance_pct": 0.888},  # Turn 18 (Chicane)
            ]
            
            # 使用遙測數據的 Distance 欄位
            telemetry = fastest_lap.get_telemetry()
            if 'Distance' not in telemetry.columns:
                print(f"   ❌ 錯誤: 無 Distance 欄位")
                return {"available": False, "count": 0, "corners": []}
            
            # 獲取位置數據
            pos_data = fastest_lap.get_pos_data()
            x = pos_data['X'].values
            y = pos_data['Y'].values
            
            distances = telemetry['Distance'].values
            total_distance = distances[-1]
            
            # 確保數據長度一致
            min_len = min(len(x), len(distances))
            x = x[:min_len]
            y = y[:min_len]
            distances = distances[:min_len]
            
            print(f"   ℹ️ 賽道總長度: {total_distance:.1f}m")
            
            corner_list = []
            for corner_def in suzuka_corners:
                corner_dist = total_distance * corner_def['distance_pct']
                
                # 找到最接近的位置點
                idx = np.argmin(np.abs(distances - corner_dist))
                
                corner_data = {
                    "number": corner_def['number'],
                    "x": float(x[idx]),
                    "y": float(y[idx]),
                    "distance": float(distances[idx]),  # 使用 FastF1 的 Distance
                    "angle": 0.0
                }
                corner_list.append(corner_data)
            
            print(f"   ✅ 預設彎道定義: {len(corner_list)} 個")
            return {
                "available": True,
                "count": len(corner_list),
                "corners": corner_list
            }
            
        except Exception as e:
            print(f"   ⚠️ 無法獲取彎道數據: {e}")
            import traceback
            traceback.print_exc()
            return {"available": False, "count": 0, "corners": []}
    
    def _convert_to_trackmap_format(self) -> Dict[str, Any]:
        """轉換為 TrackMapWidget 格式（包含 Speed 數據）"""
        track_outline = self.track_data.get('track_outline', [])
        
        # 轉換為 position_records 格式
        position_records = []
        for point in track_outline:
            record = {
                "position_x": point['x'],
                "position_y": point['y'],
                "distance_m": point['distance_m'],
                "elevation": point.get('elevation', 0.0),
                "z": point.get('z', 0.0),
                "speed": point.get('speed', 0.0)  # 🚀 添加 Speed 數據
            }
            position_records.append(record)
        
        return {
            "position_records": position_records,
            "track_bounds": self.track_data.get('track_bounds'),
            "official_corners": self.track_data.get('official_corners', {}),
            "metadata": self.track_data.get('metadata', {})
        }
    
    def _toggle_corners(self):
        """切換彎道顯示"""
        self.track_map.show_official_corners = not self.track_map.show_official_corners
        self.track_map.update()
        status = "已啟用" if self.track_map.show_official_corners else "已停用"
        print(f"\n🎯 彎道顯示: {status}")
    
    def _toggle_speed_gradient(self, state):
        """切換速度漸層模式"""
        enabled = (state == Qt.Checked)
        self.track_map.set_speed_gradient_enabled(enabled)
        mode = "速度漸層模式（藍色→紅色）" if enabled else "一般藍色模式"
        print(f"\n🌈 賽道顯示: {mode}")
    
    def _fit_view(self):
        """重置視圖"""
        self.track_map.fit_to_view()
        print("\n🔄 視圖已重置")
    
    def _refresh_charts(self):
        """重新繪製高程圖"""
        if not self.track_data:
            return
        
        track_outline = self.track_data.get('track_outline', [])
        corners = self.track_data.get('official_corners', {}).get('corners', [])
        
        print(f"\n[_refresh_charts] 傳遞給 elevation_chart 的彎道數據:")
        print(f"   - 彎道數量: {len(corners)}")
        if corners:
            print(f"   - 第 1 個彎道: T{corners[0]['number']} at {corners[0]['distance']:.2f}m")
            print(f"   - 第 11 個彎道: T{corners[10]['number']} at {corners[10]['distance']:.2f}m")
            print(f"   - 第 18 個彎道: T{corners[17]['number']} at {corners[17]['distance']:.2f}m")
        
        self.elevation_chart.plot_elevation(track_outline, corners)


    def _load_flags_statistics(self):
        """載入旗幟統計數據（從 Function 100）"""
        try:
            print("\n" + "=" * 70)
            print("🚩 載入歷年旗幟統計數據 (Function 100)")
            print("=" * 70)
            
            # 查找最新的 Japan 旗幟統計 JSON
            json_dir = Path(__file__).parent / 'json'
            json_files = list(json_dir.glob('historical_flags_Japan_2022-2025_*.json'))
            
            if not json_files:
                print("⚠️ 未找到旗幟統計 JSON，嘗試生成...")
                self._generate_flags_data()
                # 重新查找
                json_files = list(json_dir.glob('historical_flags_Japan_2022-2025_*.json'))
                
                if not json_files:
                    print("❌ 無法載入旗幟統計數據")
                    return
            
            # 使用最新檔案
            latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
            print(f"📂 載入檔案: {latest_json.name}")
            
            with open(latest_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 提取數據
            self.flags_data = json_data.get('data', {})
            
            if self.flags_data:
                self._update_flags_tables()
                print("✅ 旗幟統計數據已載入並更新表格")
            else:
                print("❌ JSON 格式錯誤")
                
        except Exception as e:
            print(f"❌ 載入旗幟統計失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _load_position_changes_data(self) -> Dict[str, int]:
        """
        載入每年度的名次變更總次數（從 Function 15 的 JSON）
        
        Returns:
            Dict[str, int]: {年份: 名次變更總次數}
        """
        try:
            print("\n📊 載入名次變更數據 (Function 15)...")
            
            json_dir = Path(__file__).parent / 'json'
            years = ['2022', '2023', '2024', '2025']
            position_changes = {}
            
            # 查找所有超車統計 JSON
            json_files = list(json_dir.glob('all_drivers_annual_overtaking_statistics_*.json'))
            
            if not json_files:
                print("   ⚠️ 找不到超車統計 JSON 檔案")
                return {'2022': 0, '2023': 0, '2024': 0, '2025': 0}
            
            # 遍歷所有檔案，根據內容中的年份進行分類
            for json_file in json_files:
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_data = json.load(f)
                    
                    # 從 race_info 中提取年份（格式："2024 Japan"）
                    race_info = json_data.get('analysis_info', {}).get('race_info', '')
                    year = race_info.split()[0] if race_info else None
                    
                    if year in years:
                        # 提取 total_position_changes
                        summary = json_data.get('summary', {})
                        total_changes = summary.get('total_position_changes', 0)
                        
                        # 只保留該年份的最大值（如果有多個檔案）
                        if year not in position_changes or total_changes > position_changes[year]:
                            position_changes[year] = total_changes
                            print(f"   ✅ {year}: {total_changes} 次名次變更 (檔案: {json_file.name})")
                
                except Exception as e:
                    print(f"   ⚠️ 讀取檔案失敗 {json_file.name}: {e}")
                    continue
            
            # 填充缺失的年份
            for year in years:
                if year not in position_changes:
                    position_changes[year] = 0
                    print(f"   ⚠️ {year}: 找不到數據")
            
            return position_changes
            
        except Exception as e:
            print(f"❌ 載入名次變更數據失敗: {e}")
            import traceback
            traceback.print_exc()
            return {'2022': 0, '2023': 0, '2024': 0, '2025': 0}
    
    def _generate_flags_data(self):
        """生成旗幟統計數據（調用 Function 100）"""
        try:
            print("   🔄 執行 Function 100...")
            from CLI_modules.cli.analyzer.historical_flags_analysis import run_historical_flags_analysis_json
            
            result = run_historical_flags_analysis_json('Japan', 2022, 2025, 'R')
            
            if result.get('success'):
                print("   ✅ Function 100 執行成功")
            else:
                print(f"   ❌ Function 100 執行失敗: {result.get('message')}")
                
        except Exception as e:
            print(f"   ❌ Function 100 執行異常: {e}")
    
    def _update_flags_tables(self):
        """更新旗幟統計表格"""
        if not self.flags_data:
            return
        
        yearly_summary = self.flags_data.get('yearly_summary', {})
        
        # 🆕 載入每年度的名次變更數據（從 Function 15 的 JSON）
        position_changes_data = self._load_position_changes_data()
        
        # 更新年度表格（行列對調：行=年份，列=旗幟類型 + 名次變更）
        years = ['2022', '2023', '2024', '2025']
        flag_keys = ['yellow_flags', 'double_yellow_flags', 'red_flags', 'safety_cars']
        
        # 🎨 設定標題列顏色（淺色系）
        header_colors = [
            QColor('#FFF9C4'),  # Yellow - 淺黃色
            QColor('#FFE082'),  # D-Yellow - 淺橙色
            QColor('#FFCDD2'),  # Red - 淺紅色
            QColor('#E1BEE7'),  # Safety - 淺紫色
            QColor('#C5E1A5')   # 🆕 Position Δ - 淺綠色
        ]
        for col, color in enumerate(header_colors):
            header_item = self.yearly_table.horizontalHeaderItem(col)
            if header_item:
                header_item.setBackground(color)
        
        for row, year in enumerate(years):
            year_data = yearly_summary.get(year, {})
            
            # 填充旗幟數據（列 0-3）
            for col, key in enumerate(flag_keys):
                count = year_data.get(key, 0)
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                
                # 🔧 移除數據儲存格的背景色，只在有數值時粗體
                if count > 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                
                self.yearly_table.setItem(row, col, item)
            
            # 🆕 填充名次變更數據（列 4）
            position_changes = position_changes_data.get(year, 0)
            pos_item = QTableWidgetItem(str(position_changes))
            pos_item.setTextAlignment(Qt.AlignCenter)
            
            # 名次變更數據用粗體顯示
            if position_changes > 0:
                font = QFont()
                font.setBold(True)
                pos_item.setFont(font)
            
            self.yearly_table.setItem(row, 4, pos_item)
        
        # 更新總計表格（水平排列）
        total_yellow = sum(yearly_summary.get(y, {}).get('yellow_flags', 0) for y in years)
        total_double_yellow = sum(yearly_summary.get(y, {}).get('double_yellow_flags', 0) for y in years)
        total_red = sum(yearly_summary.get(y, {}).get('red_flags', 0) for y in years)
        total_safety_car = sum(yearly_summary.get(y, {}).get('safety_cars', 0) for y in years)
        total_all = total_yellow + total_double_yellow + total_red + total_safety_car
        
        # 🆕 計算 2022-2025 累計的名次變更總數
        total_position_changes = sum(position_changes_data.get(y, 0) for y in years)
        
        # 🆕 更新第 1 行（數量行）的 5 列（新增名次變更）
        totals = [total_yellow, total_double_yellow, total_red, total_safety_car, total_position_changes]
        
        for col, count in enumerate(totals):
            item = QTableWidgetItem(str(count))
            item.setTextAlignment(Qt.AlignCenter)
            font = QFont()
            font.setPointSize(8)  # 🔒 固定字體大小 8，不粗體
            item.setFont(font)
            self.total_table.setItem(1, col, item)
        
        print(f"\n📊 統計更新:")
        print(f"   Yellow Flags: {total_yellow}")
        print(f"   Double Yellow: {total_double_yellow}")
        print(f"   Red Flags: {total_red}")
        print(f"   Safety Cars: {total_safety_car}")
        print(f"   Position Changes: {total_position_changes}")  # 🆕
        print(f"   總計: {total_all}")
        
        # 更新彎道統計表格 (新增)
        self._update_corner_table()
    
    def _load_function100_speed_data(self):
        """載入 Function 100 的 Speed 數據並映射到賽道點"""
        try:
            print("\n🚀 載入 Function 100 Speed 數據...")
            
            # 查找最新的 Function 100 JSON（2024 年單年數據）
            json_dir = Path(__file__).parent / 'json'
            json_files = list(json_dir.glob('historical_flags_Japan_2024-2024_*.json'))
            
            if not json_files:
                print("⚠️ 未找到 Function 100 JSON (2024 單年)")
                return
            
            # 使用最新檔案
            latest_json = max(json_files, key=lambda p: p.stat().st_mtime)
            print(f"📂 載入檔案: {latest_json.name}")
            
            with open(latest_json, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 提取 detailed_position_records
            position_records = json_data.get('data', {}).get('detailed_position_records', [])
            
            if not position_records:
                print("❌ JSON 中無 detailed_position_records")
                return
            
            print(f"✅ 載入 {len(position_records)} 個 Speed 數據點")
            
            # 提取 Speed 數據（格式：distance_m → speed）
            speed_map = {}
            for record in position_records:
                distance = record.get('distance_m', 0)
                speed = record.get('speed', 0)
                speed_map[distance] = speed
            
            # 將 Speed 映射到 track_outline
            track_outline = self.track_data.get('track_outline', [])
            
            for point in track_outline:
                distance = point.get('distance_m', 0)
                
                # 找到最接近的 Speed 數據點
                closest_distance = min(speed_map.keys(), key=lambda d: abs(d - distance))
                point['speed'] = speed_map[closest_distance]
            
            print(f"✅ Speed 數據已映射到 {len(track_outline)} 個賽道點")
            
            # 檢查 Speed 範圍
            speeds = [p.get('speed', 0) for p in track_outline if 'speed' in p]
            if speeds:
                print(f"   Speed 範圍: {min(speeds):.1f} ~ {max(speeds):.1f} km/h")
            
        except Exception as e:
            print(f"❌ 載入 Function 100 Speed 數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_corner_table(self):
        """更新彎道旗幟統計表格"""
        if not self.flags_data:
            return
        
        corner_analysis = self.flags_data.get('corner_analysis', {})
        if not corner_analysis:
            return
        
        # 按彎道編號排序
        sorted_corners = sorted(
            corner_analysis.items(),
            key=lambda x: int(x[0].replace('T', ''))
        )
        
        # 設定行數
        self.corner_table.setRowCount(len(sorted_corners))
        
        print(f"\n🏁 更新彎道統計表格: {len(sorted_corners)} 個彎道")
        
        for row, (corner_key, corner_data) in enumerate(sorted_corners):
            corner_num = corner_data.get('corner_number', corner_key.replace('T', ''))
            yearly_breakdown = corner_data.get('yearly_breakdown', {})
            
            # 計算 2022-2025 年的總和
            total_yellow = 0
            total_double_yellow = 0
            total_red = 0
            total_safety_car = 0
            
            for year in ['2022', '2023', '2024', '2025']:
                year_data = yearly_breakdown.get(year, {})
                # 只要有就算 1（四捨五入並確保最小為 1）
                yellow_val = year_data.get('yellow', 0)
                double_val = year_data.get('double_yellow', 0)
                red_val = year_data.get('red_flag', 0)
                safety_val = year_data.get('safety_car', 0)
                
                # 如果 > 0，就算作 1（移除小數）
                total_yellow += 1 if yellow_val > 0 else 0
                total_double_yellow += 1 if double_val > 0 else 0
                total_red += 1 if red_val > 0 else 0
                total_safety_car += 1 if safety_val > 0 else 0
            
            # 填充表格
            # 列 0: Turn 編號（根據旗幟類型設定背景色）
            turn_item = QTableWidgetItem(f"T{corner_num}")
            turn_item.setTextAlignment(Qt.AlignCenter)
            turn_font = QFont()
            turn_font.setBold(True)
            turn_item.setFont(turn_font)
            
            # 🎨 根據旗幟類型設定 Turn 欄位顏色
            has_yellow = (total_yellow > 0) or (total_double_yellow > 0)  # 黃旗或雙黃旗
            has_safety = total_safety_car > 0  # 安全車
            
            if has_yellow and has_safety:
                # 同時有黃旗和安全車：使用漸層（左淺黃右淺紫）
                gradient = QLinearGradient(0, 0, 1, 0)
                gradient.setCoordinateMode(QLinearGradient.ObjectBoundingMode)
                gradient.setColorAt(0.0, QColor('#FFF9C4'))  # 左側淺黃色
                gradient.setColorAt(1.0, QColor('#E1BEE7'))  # 右側淺紫色
                turn_item.setBackground(QBrush(gradient))
            elif has_yellow:
                # 只有黃旗：淺黃色
                turn_item.setBackground(QColor('#FFF9C4'))
            elif has_safety:
                # 只有安全車：淺紫色
                turn_item.setBackground(QColor('#E1BEE7'))
            
            self.corner_table.setItem(row, 0, turn_item)
            
            # 列 1-4: 旗幟數量（無背景色）
            counts = [total_yellow, total_double_yellow, total_red, total_safety_car]
            
            for col, count in enumerate(counts, start=1):
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                
                # 移除背景色，只保留粗體
                if count > 0:
                    font = QFont()
                    font.setBold(True)
                    item.setFont(font)
                
                self.corner_table.setItem(row, col, item)
        
        print(f"✅ 彎道統計表格更新完成")


def main():
    """主程式入口"""
    print("=" * 70)
    print("🏎️  FastF1 Z 軸高程分析演示")
    print("=" * 70)
    print("\n功能說明:")
    print("   - 使用 FastF1 原生的 X, Y, Z 座標數據")
    print("   - 不依賴外部 GeoJSON 或 DEM 數據")
    print("   - 與遙測數據完美同步")
    print("   - 顯示賽道平面圖 + 高程剖面圖")
    print("\n載入目標: 2024 日本站正賽 (Suzuka)")
    print("   鈴鹿賽道是經典的起伏賽道，高程變化明顯")
    print("=" * 70)
    
    app = QApplication(sys.argv)
    
    demo = FastF1ElevationDemo()
    demo.show()
    
    print("\n✅ 視窗已開啟")
    print("💡 提示:")
    print("   - 上方: 賽道平面圖（彎道標註）")
    print("   - 下方: 高程剖面圖（基於 FastF1 Z 軸）")
    print("   - 可拖曳中間分隔線調整比例")
    print("   - 點擊按鈕切換彎道顯示或重置視圖")
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
