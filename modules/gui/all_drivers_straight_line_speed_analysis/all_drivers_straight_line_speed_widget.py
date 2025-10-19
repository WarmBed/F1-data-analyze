#!/usr/bin/env python3
"""
全車手直線速度與加速性能圖表元件
All Drivers Straight Line Speed Chart Widget

提供水平長條圖（加速性能）和垂直長條圖（最高速度）的視覺化

作者: F1T Team
日期: 2025-10-14
版本: 1.0.0
"""

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal, Qt
from typing import Dict, List, Any, Optional

# 導入國際化和車隊配色
from core.gui_i18n import tr
from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
    TEAM_COLORS,
)


class AllDriversStraightLineSpeedWidget(QWidget):
    """
    全車手直線速度與加速性能圖表元件
    
    功能：
    - 水平長條圖：顯示 100-300km/h 加速時間（Y 軸車手，X 軸時間）
    - 垂直長條圖：顯示最高速度（X 軸車手，Y 軸速度）
    - 圖表切換功能
    - 資料高亮顯示
    """
    
    # 信號定義
    driver_clicked = pyqtSignal(str)  # 點擊車手時發射
    chart_switched = pyqtSignal(str)  # 圖表切換時發射 ("acceleration" or "speed")
    
    def __init__(self, parent=None):
        """初始化圖表元件"""
        super().__init__(parent)
        
        # 數據屬性
        self.current_data: Optional[Dict] = None
        self.current_chart_type = "acceleration"  # "acceleration" or "speed"
        
        # 設定中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 創建 Matplotlib 圖形
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.ax = None
        
        # 初始化 UI
        self._init_ui()
        
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 圖表切換按鈕
        self.chart_combo = QComboBox()
        self.chart_combo.addItem(tr("acceleration_chart", "加速性能圖表"), "acceleration")
        self.chart_combo.addItem(tr("speed_chart", "最高速度圖表"), "speed")
        self.chart_combo.currentIndexChanged.connect(self._on_chart_switch)
        
        # 匯出按鈕
        self.export_btn = QPushButton(tr("export_chart", "匯出圖表"))
        self.export_btn.clicked.connect(self._export_chart)
        
        # 刷新按鈕
        self.refresh_btn = QPushButton(tr("refresh_chart", "刷新圖表"))
        self.refresh_btn.clicked.connect(self._refresh_chart)
        
        control_layout.addWidget(QLabel(tr("chart_type", "圖表類型：")))
        control_layout.addWidget(self.chart_combo)
        control_layout.addStretch()
        control_layout.addWidget(self.refresh_btn)
        control_layout.addWidget(self.export_btn)
        
        # 添加到主佈局
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
        
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並重繪圖表
        
        Args:
            data: 包含 chart_data 的數據字典
        """
        try:
            if not data or not isinstance(data, dict):
                print("[WARNING] [SPEED_WIDGET] 無效的數據格式")
                return
            
            self.current_data = data
            
            # 確保配色匹配賽季
            self._ensure_palette_for_data(data)
            
            # 根據當前圖表類型繪製
            if self.current_chart_type == "acceleration":
                self.draw_acceleration_chart()
            else:
                self.draw_speed_chart()
                
            print(f"[SPEED_WIDGET] 數據更新完成，圖表類型: {self.current_chart_type}")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_WIDGET] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_acceleration_chart(self):
        """
        繪製水平長條圖（加速性能）
        
        ✅ 新邏輯: 顯示從 100 km/h 加速到該車手最高速度所需時間
        ✅ 棒狀圖後加虛線延伸至最長時間
        """
        try:
            if not self.current_data:
                print("[WARNING] [SPEED_WIDGET] 無數據可繪製")
                return
            
            # 提取原始車手數據（從 driver_speeds）
            driver_speeds = self.current_data.get("driver_speeds", [])
            if not driver_speeds:
                print("[WARNING] [SPEED_WIDGET] 缺少 driver_speeds 數據")
                return
            
            # ✅ 計算從 100 km/h 到最高速度的時間
            drivers = []
            times_to_max = []
            max_speeds = []
            
            for driver_data in driver_speeds:
                driver = driver_data.get("driver", "")
                max_speed = driver_data.get("max_speed_kmh", 0)
                accel_data = driver_data.get("acceleration_100_300", {})
                accel_100_300_time = accel_data.get("time", 0)
                
                if not driver or max_speed <= 100 or accel_100_300_time <= 0:
                    continue
                
                # 計算: 100 → max_speed 所需時間
                # 假設線性加速: time_to_max = (max_speed - 100) / (300 - 100) × accel_100_300_time
                time_to_max = self._calculate_time_to_max_speed(max_speed, accel_100_300_time)
                
                drivers.append(driver)
                times_to_max.append(time_to_max)
                max_speeds.append(max_speed)
            
            if not drivers:
                print("[WARNING] [SPEED_WIDGET] 計算後無有效數據")
                return
            
            # 清除舊圖
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 準備數據
            y_pos = np.arange(len(drivers))
            max_time = max(times_to_max)  # 用於虛線延伸
            
            # 為每個車手分配顏色
            colors = []
            for driver in drivers:
                colors.append(self._get_driver_color(driver))
            
            # ✅ 繪製水平長條圖（實心部分）
            bars = self.ax.barh(y_pos, times_to_max, color=colors, alpha=0.8, 
                               edgecolor='black', linewidth=0.5)
            
            # ✅ 繪製虛線延伸（從實心棒狀圖終點到最長時間）
            for i, time_val in enumerate(times_to_max):
                if time_val < max_time:
                    # 虛線從 time_val 延伸到 max_time
                    self.ax.plot([time_val, max_time], [i, i], 
                                linestyle='--', color='gray', alpha=0.4, linewidth=1.5)
            
            # 設定 Y 軸
            self.ax.set_yticks(y_pos)
            self.ax.set_yticklabels(drivers, fontsize=10)
            self.ax.invert_yaxis()  # 最快的在頂端
            
            # 設定 X 軸
            self.ax.set_xlabel(
                tr("time_to_max_speed_seconds", "加速時間 (100 km/h → 最高速度，秒)"), 
                fontsize=12, fontweight='bold'
            )
            self.ax.set_title(
                tr("acceleration_to_max_speed_chart", "全車手加速至最高速度性能排名"),
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # ✅ 在長條右側顯示新格式標註: "7.12s → 328.5 km/h"
            for i, (time_val, speed_val) in enumerate(zip(times_to_max, max_speeds)):
                self.ax.text(
                    time_val + 0.1,
                    i,
                    f"{time_val:.2f}s → {speed_val:.1f} km/h",
                    va='center',
                    ha='left',
                    fontsize=9,
                    fontweight='bold',
                    color='#000000'
                )
            
            # 添加網格
            self.ax.grid(True, axis='x', alpha=0.3, linestyle='--')
            self.ax.set_axisbelow(True)
            
            # 調整佈局
            self.figure.tight_layout()
            
            # 刷新畫布
            self.canvas.draw()
            
            print(f"[SPEED_WIDGET] 加速圖表繪製完成：{len(drivers)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_WIDGET] 繪製加速圖表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_speed_chart(self):
        """繪製垂直長條圖（最高速度）"""
        try:
            if not self.current_data:
                print("[WARNING] [SPEED_WIDGET] 無數據可繪製")
                return
            
            # 提取圖表數據
            chart_data = self.current_data.get("chart_data", {}).get("speed_chart", {})
            if not chart_data:
                print("[WARNING] [SPEED_WIDGET] 缺少速度圖表數據")
                return
            
            drivers = chart_data.get("x", [])
            speeds = chart_data.get("values", [])
            highlight = chart_data.get("highlight", "")
            
            if not drivers or not speeds:
                print("[WARNING] [SPEED_WIDGET] 速度數據為空")
                return
            
            # 清除舊圖
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 準備數據
            x_pos = np.arange(len(drivers))
            
            # 為每個車手分配顏色
            colors = []
            for driver in drivers:
                if driver == highlight:
                    colors.append('#00FF00')  # 綠色高亮
                else:
                    colors.append(self._get_driver_color(driver))
            
            # 繪製垂直長條圖
            bars = self.ax.bar(x_pos, speeds, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
            
            # 設定 X 軸
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(drivers, rotation=45, ha='right', fontsize=10)
            
            # 設定 Y 軸
            self.ax.set_ylabel(tr("max_speed_kmh", "最高速度 (km/h)"), fontsize=12, fontweight='bold')
            self.ax.set_title(
                tr("max_speed_chart", "全車手最高速度排名"),
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # 在長條頂部顯示數值
            for i, (bar, speed_val) in enumerate(zip(bars, speeds)):
                height = bar.get_height()
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + 1,
                    f"{speed_val:.0f}",
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold' if drivers[i] == highlight else 'normal'
                )
            
            # 添加網格
            self.ax.grid(True, axis='y', alpha=0.3, linestyle='--')
            self.ax.set_axisbelow(True)
            
            # 調整佈局
            self.figure.tight_layout()
            
            # 刷新畫布
            self.canvas.draw()
            
            print(f"[SPEED_WIDGET] 速度圖表繪製完成：{len(drivers)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_WIDGET] 繪製速度圖表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_time_to_max_speed(self, max_speed: float, accel_100_300_time: float) -> float:
        """
        計算從 100 km/h 加速到最高速度所需時間
        
        假設線性加速:
        time_to_max = (max_speed - 100) / (300 - 100) × accel_100_300_time
        
        Args:
            max_speed: 車手最高速度 (km/h)
            accel_100_300_time: 100→300 km/h 加速時間 (秒)
            
        Returns:
            float: 100 km/h → max_speed 所需時間 (秒)
        """
        if max_speed <= 100:
            return 0.0
        
        speed_range_100_300 = 300 - 100  # 200 km/h
        speed_range_100_max = max_speed - 100
        
        # 線性加速假設
        time_to_max = (speed_range_100_max / speed_range_100_300) * accel_100_300_time
        
        return time_to_max
    
    def _get_driver_color(self, driver_code: str) -> str:
        """
        獲取車手顏色（基於車隊配色）
        
        使用 shared_colors 模組獲取統一的車隊顏色（與 Ideal Ranking Table 一致）
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            str: 顏色 Hex 代碼（例如："#3671C6"）
        """
        try:
            # 從 current_data 中查找車手的車隊
            driver_speeds = self.current_data.get("driver_speeds", [])
            for driver_data in driver_speeds:
                if driver_data.get("driver") == driver_code:
                    team = driver_data.get("team", "")
                    # ✅ 使用 shared_colors 獲取 QColor 並轉換為 Hex
                    qcolor = get_team_color(team)
                    return qcolor.name()  # 轉換為 Hex 格式（例如："#0050b4"）
            
            # 預設藍色
            return '#1E90FF'
            
        except Exception:
            return '#1E90FF'
    
    def _ensure_palette_for_data(self, data: Dict[str, Any]):
        """
        確保車隊配色匹配數據的賽季
        
        ✅ 使用 shared_colors 模組，顏色已在模組中定義，無需動態載入
        """
        # shared_colors 模組的顏色是靜態定義的，不需要動態載入
        pass
    
    def _on_chart_switch(self, index: int):
        """圖表切換事件處理"""
        chart_type = self.chart_combo.itemData(index)
        if chart_type != self.current_chart_type:
            self.current_chart_type = chart_type
            self.chart_switched.emit(chart_type)
            
            # 重繪圖表
            if self.current_data:
                if chart_type == "acceleration":
                    self.draw_acceleration_chart()
                else:
                    self.draw_speed_chart()
    
    def _refresh_chart(self):
        """刷新當前圖表"""
        if self.current_data:
            if self.current_chart_type == "acceleration":
                self.draw_acceleration_chart()
            else:
                self.draw_speed_chart()
    
    def _export_chart(self):
        """匯出圖表為圖片"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            # 生成預設檔名
            metadata = self.current_data.get("metadata", {}) if self.current_data else {}
            year = metadata.get("year", "unknown")
            race = metadata.get("race", "unknown")
            session = metadata.get("session", "unknown")
            
            default_name = f"speed_analysis_{year}_{race}_{session}_{self.current_chart_type}.png"
            
            # 開啟儲存對話框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr("export_chart", "匯出圖表"),
                default_name,
                "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                print(f"[SPEED_WIDGET] 圖表已匯出: {file_path}")
                
        except Exception as e:
            print(f"[ERROR] [SPEED_WIDGET] 匯出圖表失敗: {e}")


__all__ = ["AllDriversStraightLineSpeedWidget"]
