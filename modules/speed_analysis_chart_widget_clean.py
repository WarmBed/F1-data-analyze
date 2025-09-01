#!/usr/bin/env python3
"""
速度分析圖表組件
使用 PyQt5 原生繪圖實現距離-速度曲線圖表
支援雙車手對比和單車手分析，與系統其他組件保持一致的視覺風格
"""

import sys
import os
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QSplitter, QFrame, QHeaderView, QGroupBox, QGridLayout, QPushButton
)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QPen, QColor, QPainter, QBrush, QMouseEvent, QWheelEvent

class SpeedChartWidget(QWidget):
    """速度圖表繪製組件 - 使用 PyQt5 原生繪圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據
        self.distance_data = []
        self.driver1_speed = []
        self.driver2_speed = []
        self.driver1_name = "Driver 1"
        self.driver2_name = "Driver 2"
        self.sectors = []
        
        # 顏色設定
        self.driver1_color = QColor(255, 0, 0)  # 紅色
        self.driver2_color = QColor(0, 0, 255)  # 藍色
        self.grid_color = QColor(200, 200, 200)
        self.axis_color = QColor(50, 50, 50)
        self.sector_color = QColor(100, 100, 100, 100)  # 半透明灰色
        
        # 繪圖參數
        self.margin_left = 80
        self.margin_right = 20
        self.margin_top = 20
        self.margin_bottom = 80
        
        # 數據範圍
        self.min_distance = 0
        self.max_distance = 6000
        self.min_speed = 0
        self.max_speed = 350
        
        # 滑鼠交互
        self.setMouseTracking(True)
        self.mouse_x = -1
        self.mouse_y = -1
        
        # 縮放和拖拉
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        self.setMinimumSize(600, 400)
        
    def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                      driver2_speed: List[float], driver1_name: str = "Driver 1", 
                      driver2_name: str = "Driver 2", sectors: List[Dict] = None):
        """設置速度數據"""
        self.distance_data = distance
        self.driver1_speed = driver1_speed
        self.driver2_speed = driver2_speed
        self.driver1_name = driver1_name
        self.driver2_name = driver2_name
        self.sectors = sectors or []
        
        # 計算數據範圍
        if distance:
            self.min_distance = min(distance)
            self.max_distance = max(distance)
        
        all_speeds = []
        if driver1_speed:
            all_speeds.extend(driver1_speed)
        if driver2_speed:
            all_speeds.extend(driver2_speed)
            
        if all_speeds:
            self.min_speed = max(0, min(all_speeds) - 20)
            self.max_speed = max(all_speeds) + 20
        
        self.update()
        
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 清空背景
        painter.fillRect(self.rect(), QColor(255, 255, 255))
        
        # 計算圖表區域
        chart_rect = QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        # 繪製背景
        painter.fillRect(chart_rect, QColor(248, 249, 250))
        
        # 繪製網格
        self._draw_grid(painter, chart_rect)
        
        # 繪製軸
        self._draw_axes(painter, chart_rect)
        
        # 繪製分段標記
        self._draw_sectors(painter, chart_rect)
        
        # 繪製速度曲線
        self._draw_speed_curves(painter, chart_rect)
        
        # 繪製滑鼠追蹤線
        if self.mouse_x > 0 and self.mouse_y > 0:
            self._draw_mouse_tracker(painter, chart_rect)
            
        # 繪製圖例
        self._draw_legend(painter)
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        painter.setPen(QPen(self.grid_color, 1))
        
        # 垂直網格線 (距離)
        distance_range = self.max_distance - self.min_distance
        if distance_range > 0:
            grid_step = distance_range / 10
            for i in range(11):
                distance_value = self.min_distance + i * grid_step
                x = chart_rect.left() + (distance_value - self.min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (速度)
        speed_range = self.max_speed - self.min_speed
        if speed_range > 0:
            grid_step = speed_range / 10
            for i in range(11):
                speed_value = self.min_speed + i * grid_step
                y = chart_rect.bottom() - (speed_value - self.min_speed) / speed_range * chart_rect.height()
                painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
                
    def _draw_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製坐標軸和標籤"""
        painter.setPen(QPen(self.axis_color, 2))
        
        # 繪製軸線
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())  # X軸
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())      # Y軸
        
        # 設置字體
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(self.axis_color, 1))
        
        # X軸標籤 (距離)
        distance_range = self.max_distance - self.min_distance
        if distance_range > 0:
            for i in range(0, 11, 2):  # 只顯示偶數刻度
                distance_value = self.min_distance + i * distance_range / 10
                x = chart_rect.left() + i * chart_rect.width() / 10
                painter.drawText(int(x - 20), chart_rect.bottom() + 20, 40, 20, 
                               Qt.AlignCenter, f"{int(distance_value)}")
        
        # Y軸標籤 (速度)
        speed_range = self.max_speed - self.min_speed
        if speed_range > 0:
            for i in range(0, 11, 2):  # 只顯示偶數刻度
                speed_value = self.min_speed + i * speed_range / 10
                y = chart_rect.bottom() - i * chart_rect.height() / 10
                painter.drawText(10, int(y - 10), self.margin_left - 20, 20, 
                               Qt.AlignRight | Qt.AlignVCenter, f"{int(speed_value)}")
        
        # 軸標題
        title_font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(title_font)
        
        # X軸標題
        painter.drawText(chart_rect.left(), self.height() - 30, chart_rect.width(), 20,
                        Qt.AlignCenter, "距離 (米)")
        
        # Y軸標題
        painter.save()
        painter.translate(20, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(-50, -10, 100, 20, Qt.AlignCenter, "速度 (km/h)")
        painter.restore()
        
    def _draw_sectors(self, painter: QPainter, chart_rect: QRect):
        """繪製分段標記"""
        if not self.sectors:
            return
            
        painter.setPen(QPen(self.sector_color, 1, Qt.DashLine))
        
        distance_range = self.max_distance - self.min_distance
        if distance_range <= 0:
            return
            
        for sector in self.sectors:
            if 'end_distance' in sector:
                end_distance = sector['end_distance']
                x = chart_rect.left() + (end_distance - self.min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
                
                # 繪製S1, S2, S3標籤
                if 'sector' in sector:
                    painter.setPen(QPen(self.sector_color, 1))
                    painter.setFont(QFont("Arial", 8))
                    painter.drawText(int(x - 10), chart_rect.bottom() + 50, 20, 15,
                                   Qt.AlignCenter, f"S{sector['sector']}")
                                   
    def _draw_speed_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製速度曲線"""
        if not self.distance_data:
            return
            
        distance_range = self.max_distance - self.min_distance
        speed_range = self.max_speed - self.min_speed
        
        if distance_range <= 0 or speed_range <= 0:
            return
        
        # 繪製車手1速度曲線
        if self.driver1_speed and len(self.driver1_speed) == len(self.distance_data):
            painter.setPen(QPen(self.driver1_color, 2))
            points = []
            for i, (distance, speed) in enumerate(zip(self.distance_data, self.driver1_speed)):
                x = chart_rect.left() + (distance - self.min_distance) / distance_range * chart_rect.width()
                y = chart_rect.bottom() - (speed - self.min_speed) / speed_range * chart_rect.height()
                points.append(QPoint(int(x), int(y)))
            
            # 繪製線段
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # 繪製車手2速度曲線
        if self.driver2_speed and len(self.driver2_speed) == len(self.distance_data):
            painter.setPen(QPen(self.driver2_color, 2))
            points = []
            for i, (distance, speed) in enumerate(zip(self.distance_data, self.driver2_speed)):
                x = chart_rect.left() + (distance - self.min_distance) / distance_range * chart_rect.width()
                y = chart_rect.bottom() - (speed - self.min_speed) / speed_range * chart_rect.height()
                points.append(QPoint(int(x), int(y)))
            
            # 繪製線段
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
                
    def _draw_mouse_tracker(self, painter: QPainter, chart_rect: QRect):
        """繪製滑鼠追蹤線"""
        if chart_rect.contains(self.mouse_x, self.mouse_y):
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
            painter.drawLine(self.mouse_x, chart_rect.top(), self.mouse_x, chart_rect.bottom())
            painter.drawLine(chart_rect.left(), self.mouse_y, chart_rect.right(), self.mouse_y)
            
    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        legend_x = self.width() - 200
        legend_y = 30
        
        painter.setFont(QFont("Arial", 9))
        
        # 車手1圖例
        painter.setPen(QPen(self.driver1_color, 2))
        painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y - 5, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, self.driver1_name)
        
        # 車手2圖例
        painter.setPen(QPen(self.driver2_color, 2))
        painter.drawLine(legend_x, legend_y + 20, legend_x + 20, legend_y + 20)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y + 15, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, self.driver2_name)
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """滑鼠移動事件"""
        self.mouse_x = event.x()
        self.mouse_y = event.y()
        self.update()
        
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.mouse_y = -1
        self.update()


class SpeedAnalysisChartWidget(QWidget):
    """速度分析圖表組件主容器"""
    
    # 信號定義
    chart_updated = pyqtSignal()
    data_point_selected = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 主要分割器
        main_splitter = QSplitter(Qt.Vertical)
        layout.addWidget(main_splitter)
        
        # 圖表區域
        self.chart_container = self._create_chart_container()
        main_splitter.addWidget(self.chart_container)
        
        # 統計信息區域
        self.stats_container = self._create_stats_container()
        main_splitter.addWidget(self.stats_container)
        
        # 設置分割器比例
        main_splitter.setStretchFactor(0, 1)  # 圖表可伸縮
        main_splitter.setStretchFactor(1, 0)  # 統計區域固定大小
        
    def _create_chart_container(self) -> QWidget:
        """創建圖表容器"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #bdc3c7;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 創建圖表組件
        self.chart_widget = SpeedChartWidget()
        layout.addWidget(self.chart_widget)
        
        return container
        
    def _create_stats_container(self) -> QWidget:
        """創建統計信息容器"""
        container = QGroupBox("詳細統計信息")
        container.setMaximumHeight(200)  # 限制最大高度
        
        layout = QVBoxLayout(container)
        
        # 控制按鈕
        controls_layout = QHBoxLayout()
        self.toggle_button = QPushButton("隱藏詳細信息")
        self.toggle_button.setMaximumWidth(120)
        self.toggle_button.clicked.connect(self.toggle_statistics_panel)
        controls_layout.addWidget(self.toggle_button)
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # 統計表格
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)
        
        # 初始化表格
        self._setup_stats_table()
        
        return container
        
    def _setup_stats_table(self):
        """設置統計表格"""
        headers = ["項目", "車手1", "車手2", "差值"]
        self.stats_table.setColumnCount(len(headers))
        self.stats_table.setHorizontalHeaderLabels(headers)
        self.stats_table.setRowCount(0)
        
        # 設置字體大小
        font = QFont()
        font.setPointSize(9)
        self.stats_table.setFont(font)
        
    def toggle_statistics_panel(self):
        """切換統計面板顯示/隱藏"""
        is_visible = self.stats_table.isVisible()
        self.stats_table.setVisible(not is_visible)
        
        # 更新按鈕文字
        if is_visible:
            self.toggle_button.setText("顯示詳細信息")
            self.stats_container.setMaximumHeight(50)
        else:
            self.toggle_button.setText("隱藏詳細信息")
            self.stats_container.setMaximumHeight(200)
            self._adjust_table_height()
            
    def _adjust_table_height(self):
        """自動調整表格高度"""
        if not self.stats_table.isVisible():
            return
            
        row_count = self.stats_table.rowCount()
        if row_count == 0:
            return
            
        # 計算所需高度
        header_height = self.stats_table.horizontalHeader().height()
        row_height = self.stats_table.rowHeight(0)
        total_height = header_height + (row_height * row_count) + 10
        
        # 設置表格高度
        max_height = min(total_height, 150)
        self.stats_table.setMaximumHeight(max_height)
        self.stats_table.setMinimumHeight(max_height)
        
    def update_speed_data(self, data: Dict[str, Any]):
        """更新速度數據"""
        print(f"[SPEED CHART DEBUG] ========== 圖表數據更新 ==========")
        print(f"[SPEED CHART DEBUG] 收到數據: {type(data)}")
        print(f"[SPEED CHART DEBUG] 數據鍵值: {list(data.keys())}")
        
        self.current_data = data
        
        try:
            # 提取元數據
            metadata = data.get('metadata', {})
            speed_data = data.get('speed_data', {})
            statistics = data.get('statistics', {})
            
            print(f"[SPEED CHART DEBUG] 元數據: {metadata}")
            print(f"[SPEED CHART DEBUG] 速度數據鍵值: {list(speed_data.keys())}")
            
            # 提取車手信息
            drivers = metadata.get('drivers', [])
            sectors = metadata.get('sectors', [])
            
            print(f"[SPEED CHART DEBUG] 車手資訊: {drivers}")
            
            # 提取速度數據
            distance = speed_data.get('distance', [])
            driver1_speed = speed_data.get('driver1_speed', [])
            driver2_speed = speed_data.get('driver2_speed', [])
            driver1_name = speed_data.get('driver1_name', 'Driver 1')
            driver2_name = speed_data.get('driver2_name', 'Driver 2')
            
            print(f"[SPEED CHART DEBUG] 車手資料: {drivers}")
            
            # 如果有車手信息，使用車手代碼作為名稱
            if len(drivers) >= 2:
                driver1_name = drivers[0].get('code', driver1_name)
                driver2_name = drivers[1].get('code', driver2_name)
            
            print(f"[SPEED CHART DEBUG] 已移除標題顯示")
            
            # 更新圖表
            print(f"[SPEED CHART DEBUG] 使用 PyQt5 原生繪圖")
            self.chart_widget.set_speed_data(
                distance=distance,
                driver1_speed=driver1_speed,
                driver2_speed=driver2_speed,
                driver1_name=driver1_name,
                driver2_name=driver2_name,
                sectors=sectors
            )
            
            # 更新統計表格
            print(f"[SPEED CHART DEBUG] 更新統計表格")
            self._update_statistics_table(statistics, driver1_name, driver2_name)
            
            print(f"[SPEED CHART DEBUG] ✅ 圖表更新完成，發送信號")
            self.chart_updated.emit()
            
        except Exception as e:
            print(f"[ERROR] [SPEED CHART] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_statistics_table(self, statistics: Dict, driver1_name: str, driver2_name: str):
        """更新統計表格"""
        if not statistics:
            return
            
        try:
            driver1_stats = statistics.get('driver1_stats', {})
            driver2_stats = statistics.get('driver2_stats', {})
            comparison = statistics.get('comparison', {})
            
            # 準備表格數據
            rows = [
                ("最高速度 (km/h)", 
                 f"{driver1_stats.get('max_speed', 0):.1f}",
                 f"{driver2_stats.get('max_speed', 0):.1f}",
                 f"{comparison.get('max_speed_diff', 0):.1f}"),
                ("平均速度 (km/h)",
                 f"{driver1_stats.get('avg_speed', 0):.1f}",
                 f"{driver2_stats.get('avg_speed', 0):.1f}",
                 f"{comparison.get('avg_speed_diff', 0):.1f}"),
                ("最低速度 (km/h)",
                 f"{driver1_stats.get('min_speed', 0):.1f}",
                 f"{driver2_stats.get('min_speed', 0):.1f}",
                 f"{driver1_stats.get('min_speed', 0) - driver2_stats.get('min_speed', 0):.1f}")
            ]
            
            # 更新表格
            self.stats_table.setRowCount(len(rows))
            
            for row_idx, (item, driver1_val, driver2_val, diff_val) in enumerate(rows):
                self.stats_table.setItem(row_idx, 0, QTableWidgetItem(item))
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem(driver1_val))
                self.stats_table.setItem(row_idx, 2, QTableWidgetItem(driver2_val))
                self.stats_table.setItem(row_idx, 3, QTableWidgetItem(diff_val))
            
            # 調整表格高度
            self._adjust_table_height()
            
        except Exception as e:
            print(f"[ERROR] 更新統計表格失敗: {e}")
