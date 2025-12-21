#!/usr/bin/env python3
"""
全車手煞車性能圖表元件
All Drivers Brake Performance Chart Widget

提供水平長條圖（煞車時間）和垂直長條圖（最大減速度）的視覺化

作者: F1T Team
日期: 2025-10-18
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
from modules.gui.themes.color_palette_provider import color_palette_provider

from core.logger import get_logger
logger = get_logger(__name__)

# 導入 logger


class AllDriversBrakePerformanceWidget(QWidget):
    """
    全車手煞車性能圖表元件
    
    功能：
    - 水平長條圖：顯示煞車時間（Y 軸車手，X 軸時間）
    - 垂直長條圖：顯示最大減速度（X 軸車手，Y 軸減速度 G-force）
    - 圖表切換功能
    - 資料高亮顯示
    """
    
    # 信號定義
    driver_clicked = pyqtSignal(str)  # 點擊車手時發射
    chart_switched = pyqtSignal(str)  # 圖表切換時發射 ("brake_time" or "deceleration")
    
    def __init__(self, parent=None):
        """初始化圖表元件"""
        super().__init__(parent)
        
        # 數據屬性
        self.current_data: Optional[Dict] = None
        self.current_chart_type = "brake_time"  # "brake_time" or "deceleration"
        
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
        self.chart_combo.addItem(tr("brake_time_chart", "煞車時間圖表"), "brake_time")
        self.chart_combo.addItem(tr("deceleration_chart", "最大減速度圖表"), "deceleration")
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
            data: 包含 driver_brakes 的數據字典
        """
        try:
            if not data or not isinstance(data, dict):
                logger.warning("[BRAKE_WIDGET] 無效的數據格式")
                return
            
            self.current_data = data
            
            # 根據當前圖表類型繪製
            if self.current_chart_type == "brake_time":
                self.draw_brake_time_chart()
            else:
                self.draw_deceleration_chart()
                
            logger.info(f"[BRAKE_WIDGET] 數據更新完成，圖表類型: {self.current_chart_type}")
            
        except Exception as e:
            logger.error(f"[BRAKE_WIDGET] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_brake_time_chart(self):
        """
        繪製水平長條圖（煞車時間）
        
        顯示每位車手的煞車時間（秒）
        """
        try:
            if not self.current_data:
                logger.warning("[BRAKE_WIDGET] 無數據可繪製")
                return
            
            # 提取原始車手數據（從 driver_brakes）
            driver_brakes = self.current_data.get("driver_brakes", [])
            if not driver_brakes:
                logger.warning("[BRAKE_WIDGET] 缺少 driver_brakes 數據")
                return
            
            # 提取煞車時間數據
            drivers = []
            brake_times = []
            
            for driver_data in driver_brakes:
                driver = driver_data.get("driver", "")
                brake_time = driver_data.get("brake_time_s", 0)
                
                if not driver or brake_time <= 0:
                    continue
                
                drivers.append(driver)
                brake_times.append(brake_time)
            
            if not drivers:
                logger.warning("[BRAKE_WIDGET] 計算後無有效數據")
                return
            
            # 清除舊圖
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 準備數據
            y_pos = np.arange(len(drivers))
            
            # 為每個車手分配顏色
            colors = []
            for driver in drivers:
                colors.append(self._get_driver_color(driver))
            
            # 繪製水平長條圖
            bars = self.ax.barh(y_pos, brake_times, color=colors, alpha=0.8, 
                               edgecolor='black', linewidth=0.5)
            
            # 設定 Y 軸
            self.ax.set_yticks(y_pos)
            self.ax.set_yticklabels(drivers, fontsize=10)
            self.ax.invert_yaxis()  # 最快的在頂端
            
            # 設定 X 軸
            self.ax.set_xlabel(
                tr("brake_time_seconds", "煞車時間 (秒)"), 
                fontsize=12, fontweight='bold'
            )
            self.ax.set_title(
                tr("brake_time_chart_title", "全車手煞車時間排名"),
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # 在長條右側顯示數值
            for i, time_val in enumerate(brake_times):
                self.ax.text(
                    time_val + 0.02,
                    i,
                    f"{time_val:.3f}s",
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
            
            logger.info(f"[BRAKE_WIDGET] 煤車時間圖表繪製完成：{len(drivers)} 位車手")
            
        except Exception as e:
            logger.error(f"[BRAKE_WIDGET] 繪製煤車時間圖表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def draw_deceleration_chart(self):
        """繪製垂直長條圖（最大減速度）"""
        try:
            if not self.current_data:
                logger.warning("[BRAKE_WIDGET] 無數據可繪製")
                return
            
            # 提取車手煤車數據
            driver_brakes = self.current_data.get("driver_brakes", [])
            if not driver_brakes:
                logger.warning("[BRAKE_WIDGET] 缺少 driver_brakes 數據")
                return
            
            drivers = []
            decelerations = []
            
            for driver_data in driver_brakes:
                driver = driver_data.get("driver", "")
                decel_g = driver_data.get("max_deceleration_g", 0)
                
                if not driver or decel_g <= 0:
                    continue
                
                drivers.append(driver)
                decelerations.append(decel_g)
            
            if not drivers:
                logger.warning("[BRAKE_WIDGET] 減速度數據為空")
                return
            
            # 清除舊圖
            self.figure.clear()
            self.ax = self.figure.add_subplot(111)
            
            # 準備數據
            x_pos = np.arange(len(drivers))
            
            # 為每個車手分配顏色
            colors = []
            for driver in drivers:
                colors.append(self._get_driver_color(driver))
            
            # 繪製垂直長條圖
            bars = self.ax.bar(x_pos, decelerations, color=colors, alpha=0.8, edgecolor='black', linewidth=0.5)
            
            # 設定 X 軸
            self.ax.set_xticks(x_pos)
            self.ax.set_xticklabels(drivers, rotation=45, ha='right', fontsize=10)
            
            # 設定 Y 軸
            self.ax.set_ylabel(tr("max_deceleration_g", "最大減速度 (G)"), fontsize=12, fontweight='bold')
            self.ax.set_title(
                tr("max_deceleration_chart", "全車手最大減速度排名"),
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
            # 在長條頂部顯示數值
            for i, (bar, decel_val) in enumerate(zip(bars, decelerations)):
                height = bar.get_height()
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2.,
                    height + 0.05,
                    f"{decel_val:.2f}G",
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    fontweight='bold'
                )
            
            # 添加網格
            self.ax.grid(True, axis='y', alpha=0.3, linestyle='--')
            self.ax.set_axisbelow(True)
            
            # 調整佈局
            self.figure.tight_layout()
            
            # 刷新畫布
            self.canvas.draw()
            
            logger.info(f"[BRAKE_WIDGET] 減速度圖表繪製完成：{len(drivers)} 位車手")
            
        except Exception as e:
            logger.error(f"[BRAKE_WIDGET] 繪製減速度圖表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_driver_color(self, driver_code: str) -> str:
        """
        獲取車手顏色（基於車隊配色）
        
        使用 shared_colors 模組獲取統一的車隊顏色
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            str: 顏色 Hex 代碼
        """
        try:
            # ✅ 使用 color_palette_provider.get_driver_color() 與 driver_standings 一致
            qcolor = color_palette_provider.get_driver_color(driver_code, fallback=True)
            return qcolor.name()
            
        except Exception:
            return '#1E90FF'
    
    def _on_chart_switch(self, index: int):
        """圖表切換事件處理"""
        chart_type = self.chart_combo.itemData(index)
        if chart_type != self.current_chart_type:
            self.current_chart_type = chart_type
            self.chart_switched.emit(chart_type)
            
            # 重繪圖表
            if self.current_data:
                if chart_type == "brake_time":
                    self.draw_brake_time_chart()
                else:
                    self.draw_deceleration_chart()
    
    def _refresh_chart(self):
        """刷新當前圖表"""
        if self.current_data:
            if self.current_chart_type == "brake_time":
                self.draw_brake_time_chart()
            else:
                self.draw_deceleration_chart()
    
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
            
            default_name = f"brake_performance_{year}_{race}_{session}_{self.current_chart_type}.png"
            
            # 開啟儲存對話框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                tr("export_chart", "匯出圖表"),
                default_name,
                "PNG Files (*.png);;PDF Files (*.pdf);;All Files (*)"
            )
            
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                logger.info(f"[BRAKE_WIDGET] 圖表已匯出: {file_path}")
                
        except Exception as e:
            logger.error(f"[BRAKE_WIDGET] 匯出圖表失敗: {e}")


__all__ = ["AllDriversBrakePerformanceWidget"]
