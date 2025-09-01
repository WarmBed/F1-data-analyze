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
    QLabel, QSplitter, QFrame, QHeaderView, QGroupBox, QGridLayout, QPushButton,
    QSizePolicy, QSpinBox
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
        
        # 固定線條和數值顯示
        self.fixed_line_x = -1  # 固定垂直線的X位置（螢幕像素）
        self.fixed_distance_value = None  # 固定線對應的實際距離值
        self.show_fixed_line = False  # 是否顯示固定線
        
        # 縮放和拖拉
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # 拖拉狀態
        self.middle_dragging = False  # 中鍵拖拉狀態
        self.last_drag_pos = QPoint()
        
        # 視圖範圍（用於縮放和拖拉）
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_speed = None
        self.view_max_speed = None
        
        self.setMinimumSize(600, 300)  # 減少最小高度，提高適應性
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 設置擴展策略
        
    def set_speed_data(self, distance: List[float], driver1_speed: List[float], 
                      driver2_speed: List[float], driver1_name: str = "Driver 1", 
                      driver2_name: str = "Driver 2", sectors: List[Dict] = None):
        """設置速度數據"""
        print(f"[SPEED CHART] 設置新的速度數據")
        print(f"[SPEED CHART] 車手1: {driver1_name}, 數據點: {len(driver1_speed)}")
        print(f"[SPEED CHART] 車手2: {driver2_name}, 數據點: {len(driver2_speed)}")
        print(f"[SPEED CHART] 距離數據點: {len(distance)}")
        
        # 強制重置視圖狀態
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_speed = None
        self.view_max_speed = None
        self.show_fixed_line = False
        self.fixed_line_x = -1
        self.fixed_distance_value = None
        
        # 設置新數據
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
            print(f"[SPEED CHART] 距離範圍: {self.min_distance:.1f} - {self.max_distance:.1f}")
        
        all_speeds = []
        if driver1_speed:
            all_speeds.extend(driver1_speed)
        if driver2_speed:
            all_speeds.extend(driver2_speed)
            
        if all_speeds:
            self.min_speed = max(0, min(all_speeds) - 20)
            self.max_speed = max(all_speeds) + 20
            print(f"[SPEED CHART] 速度範圍: {self.min_speed:.1f} - {self.max_speed:.1f}")
        
        # 強制重繪
        self.repaint()
        print(f"[SPEED CHART] ✅ 數據設置完成，已重繪圖表")
        
    def reset_view(self):
        """重置視圖到原始範圍"""
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_speed = None
        self.view_max_speed = None
        self.show_fixed_line = False
        self.fixed_line_x = -1
        self.fixed_distance_value = None
        self.update()
    
    def reset_data(self):
        """重置所有數據和視圖"""
        print(f"[SPEED CHART] 重置數據和視圖")
        self.speed_data = None
        self.driver1_name = ""
        self.driver2_name = ""
        self.distance = []
        self.driver1_speed = []
        self.driver2_speed = []
        
        # 重置範圍
        self.min_distance = 0
        self.max_distance = 5000
        self.min_speed = 0
        self.max_speed = 320
        
        # 重置視圖
        self.reset_view()
        
        # 重繪
        self.repaint()
        print(f"[SPEED CHART] ✅ 數據重置完成")
        
    def clear_fixed_line(self):
        """清除固定線條"""
        self.show_fixed_line = False
        self.fixed_line_x = -1
        self.fixed_distance_value = None
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
        
        # 繪製順序很重要 - 後繪製的會覆蓋先繪製的
        self._draw_grid(painter, chart_rect)
        self._draw_axes(painter, chart_rect)
        self._draw_speed_curves(painter, chart_rect)
        self._draw_sectors(painter, chart_rect)
        
        # 繪製滑鼠追蹤線和固定線條
        if self.show_fixed_line or (self.mouse_x > 0 and self.mouse_y > 0):
            self._draw_mouse_tracker(painter, chart_rect)
            
        # 繪製圖例
        self._draw_legend(painter)
        
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        painter.setPen(QPen(self.grid_color, 1))
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_speed = self.view_min_speed if self.view_min_speed is not None else self.min_speed
        current_max_speed = self.view_max_speed if self.view_max_speed is not None else self.max_speed
        
        # 垂直網格線 (距離)
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            grid_step = distance_range / 10
            for i in range(11):
                distance_value = current_min_distance + i * grid_step
                x = chart_rect.left() + (distance_value - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (速度)
        speed_range = current_max_speed - current_min_speed
        if speed_range > 0:
            grid_step = speed_range / 10
            for i in range(11):
                speed_value = current_min_speed + i * grid_step
                y = chart_rect.bottom() - (speed_value - current_min_speed) / speed_range * chart_rect.height()
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
            
        # 使用更明顯的分段線設定
        sector_pen_color = QColor(120, 120, 120, 200)  # 更不透明的灰色
        painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))  # 增加線條寬度到2
        
        distance_range = self.max_distance - self.min_distance
        if distance_range <= 0:
            return
            
        for i, sector in enumerate(self.sectors):
            if 'end_distance' in sector:
                end_distance = sector['end_distance']
                x = chart_rect.left() + (end_distance - self.min_distance) / distance_range * chart_rect.width()
                
                # 繪製分段垂直線
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
                
                # 繪製S1, S2, S3標籤
                if 'sector' in sector:
                    # 使用實線來繪製標籤
                    painter.setPen(QPen(self.sector_color, 1))
                    painter.setFont(QFont("Arial", 8))
                    label_y = chart_rect.bottom() + 50
                    painter.drawText(int(x - 10), label_y, 20, 15,
                                   Qt.AlignCenter, f"S{sector['sector']}")
                    
                    # 恢復虛線樣式給下一條線
                    painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))
    def _draw_speed_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製速度曲線"""
        # print(f"[SPEED CHART] ========== 開始繪製速度曲線 ==========")
        # print(f"[SPEED CHART] 距離數據點數: {len(self.distance_data) if self.distance_data else 0}")
        # print(f"[SPEED CHART] 車手1速度數據點數: {len(self.driver1_speed) if self.driver1_speed else 0}")
        # print(f"[SPEED CHART] 車手2速度數據點數: {len(self.driver2_speed) if self.driver2_speed else 0}")
        
        if not self.distance_data:
            # print(f"[SPEED CHART] ❌ 沒有距離數據，跳過繪製")
            return
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_speed = self.view_min_speed if self.view_min_speed is not None else self.min_speed
        current_max_speed = self.view_max_speed if self.view_max_speed is not None else self.max_speed
        
        # print(f"[SPEED CHART] 當前距離範圍: {current_min_distance:.1f} - {current_max_distance:.1f}")
        # print(f"[SPEED CHART] 當前速度範圍: {current_min_speed:.1f} - {current_max_speed:.1f}")
            
        distance_range = current_max_distance - current_min_distance
        speed_range = current_max_speed - current_min_speed
        
        # print(f"[SPEED CHART] 距離範圍: {distance_range:.1f}, 速度範圍: {speed_range:.1f}")
        
        if distance_range <= 0 or speed_range <= 0:
            # print(f"[SPEED CHART] ❌ 範圍無效，跳過繪製")
            return
        
        # 顯示一些樣本數據
        # if self.distance_data:
        #     print(f"[SPEED CHART] 距離數據樣本: {self.distance_data[:5]} ... {self.distance_data[-5:]}")
        # if self.driver1_speed:
        #     print(f"[SPEED CHART] 車手1速度樣本: {self.driver1_speed[:5]} ... {self.driver1_speed[-5:]}")
        # if self.driver2_speed:
        #     print(f"[SPEED CHART] 車手2速度樣本: {self.driver2_speed[:5]} ... {self.driver2_speed[-5:]}")
        
        # 繪製車手1速度曲線
        if self.driver1_speed and len(self.driver1_speed) == len(self.distance_data):
            # print(f"[SPEED CHART] 🔵 開始繪製車手1 ({self.driver1_name}) 曲線")
            painter.setPen(QPen(self.driver1_color, 2))
            points = []
            for i, (distance, speed) in enumerate(zip(self.distance_data, self.driver1_speed)):
                # 只繪製在當前視圖範圍內的點
                if current_min_distance <= distance <= current_max_distance:
                    x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (speed - current_min_speed) / speed_range * chart_rect.height()
                    points.append(QPoint(int(x), int(y)))
            
            # print(f"[SPEED CHART] 車手1 可見點數: {len(points)}")
            
            # 繪製線段
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
            # print(f"[SPEED CHART] ✅ 車手1 曲線繪製完成")
        else:
            # print(f"[SPEED CHART] ⚠️ 車手1 數據長度不匹配或為空")
            pass
        
        # 繪製車手2速度曲線
        if self.driver2_speed and len(self.driver2_speed) == len(self.distance_data):
            # print(f"[SPEED CHART] 🔴 開始繪製車手2 ({self.driver2_name}) 曲線")
            painter.setPen(QPen(self.driver2_color, 2))
            points = []
            for i, (distance, speed) in enumerate(zip(self.distance_data, self.driver2_speed)):
                # 只繪製在當前視圖範圍內的點
                if current_min_distance <= distance <= current_max_distance:
                    x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (speed - current_min_speed) / speed_range * chart_rect.height()
                    points.append(QPoint(int(x), int(y)))
            
            # print(f"[SPEED CHART] 車手2 可見點數: {len(points)}")
            
            # 繪製線段
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
            # print(f"[SPEED CHART] ✅ 車手2 曲線繪製完成")
        else:
            # print(f"[SPEED CHART] ⚠️ 車手2 數據長度不匹配或為空")
            pass
            
        # print(f"[SPEED CHART] ========== 速度曲線繪製完成 ==========")
                
    def _draw_mouse_tracker(self, painter: QPainter, chart_rect: QRect):
        """繪製滑鼠追蹤線和固定線"""
        # 繪製固定垂直線（左鍵點擊固定）
        if self.show_fixed_line and self.fixed_distance_value is not None:
            # 根據固定的距離值計算當前螢幕位置
            current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
            current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
            distance_range = current_max_distance - current_min_distance
            
            if distance_range > 0 and current_min_distance <= self.fixed_distance_value <= current_max_distance:
                # 計算固定距離值對應的X位置
                relative_pos = (self.fixed_distance_value - current_min_distance) / distance_range
                fixed_x = chart_rect.left() + relative_pos * chart_rect.width()
                self._draw_tracking_line(painter, chart_rect, int(fixed_x), is_fixed=True)
        
        # 繪製滑鼠跟隨線
        if chart_rect.contains(self.mouse_x, self.mouse_y):
            self._draw_tracking_line(painter, chart_rect, self.mouse_x, is_fixed=False)
    
    def _draw_tracking_line(self, painter: QPainter, chart_rect: QRect, x_pos: int, is_fixed: bool):
        """繪製追蹤線和數值顯示"""
        if not chart_rect.contains(x_pos, chart_rect.center().y()):
            return
            
        # 設置線條樣式
        if is_fixed:
            # 固定線：實線，更明顯
            painter.setPen(QPen(QColor(200, 0, 0), 2, Qt.SolidLine))
        else:
            # 跟隨線：虛線，較淡
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
            
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 計算當前位置對應的距離和曲線速度值
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        distance_range = current_max_distance - current_min_distance
        
        if distance_range > 0 and self.distance_data:
            # 計算距離值
            relative_x = x_pos - chart_rect.left()
            distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
            
            # 找到最接近的數據點來獲取真實的曲線速度值
            driver1_speed_at_position = None
            driver2_speed_at_position = None
            
            # 在距離數據中找到最接近的點
            if self.distance_data and len(self.distance_data) > 0:
                closest_index = 0
                min_distance_diff = abs(self.distance_data[0] - distance_value)
                
                for i, dist in enumerate(self.distance_data):
                    distance_diff = abs(dist - distance_value)
                    if distance_diff < min_distance_diff:
                        min_distance_diff = distance_diff
                        closest_index = i
                
                # 獲取對應的速度值
                if closest_index < len(self.driver1_speed):
                    driver1_speed_at_position = self.driver1_speed[closest_index]
                if closest_index < len(self.driver2_speed):
                    driver2_speed_at_position = self.driver2_speed[closest_index]
            
            # 計算需要顯示的車手數量來調整標籤大小
            drivers_to_show = []
            
            # 檢查是否為單車手模式（兩個車手名稱相同）
            is_single_driver = (self.driver1_name == self.driver2_name)
            
            # 只添加有效且不重複的車手資訊
            if driver1_speed_at_position is not None and self.driver1_name:
                drivers_to_show.append((self.driver1_name, driver1_speed_at_position, self.driver1_color))
            
            # 只有在非單車手模式且第二個車手數據不同時才添加第二個車手
            if (not is_single_driver and 
                driver2_speed_at_position is not None and 
                self.driver2_name and 
                self.driver2_name != self.driver1_name):
                drivers_to_show.append((self.driver2_name, driver2_speed_at_position, self.driver2_color))
            
            # 根據車手數量動態調整標籤高度
            base_height = 30  # 距離資訊的基本高度
            driver_height = 15 * len(drivers_to_show)  # 每個車手15像素高度
            label_height = base_height + driver_height
            
            # 繪製數值標籤背景
            label_width = 150
            label_x = min(x_pos + 10, self.width() - label_width - 10)
            # 對於固定線，使用固定的Y位置；對於跟隨線，跟隨滑鼠
            if is_fixed:
                label_y = max(chart_rect.top() + 10, 10)
            else:
                label_y = max(self.mouse_y - label_height - 10, 10)
            
            # 設置標籤背景顏色
            bg_color = QColor(255, 240, 240, 230) if is_fixed else QColor(255, 255, 255, 230)
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.setBrush(QBrush(bg_color))
            painter.drawRect(label_x, label_y, label_width, label_height)
            
            # 繪製數值文字
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.setFont(QFont("Arial", 9))
            
            text_y = label_y + 15
            painter.drawText(label_x + 5, text_y, f"距離: {distance_value:.0f} m")
            
            # 顯示車手速度資訊
            for i, (driver_name, speed, color) in enumerate(drivers_to_show):
                painter.setPen(QPen(color, 1))
                painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{driver_name}: {speed:.1f} km/h")
            
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
        
        # 中鍵拖拉處理
        if self.middle_dragging and not self.last_drag_pos.isNull():
            # 計算移動距離
            dx = event.x() - self.last_drag_pos.x()
            dy = event.y() - self.last_drag_pos.y()
            
            # 轉換為數據範圍的移動
            chart_rect = QRect(
                self.margin_left, self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            if chart_rect.width() > 0 and chart_rect.height() > 0:
                # X軸移動（距離）
                distance_range = (self.view_max_distance or self.max_distance) - (self.view_min_distance or self.min_distance)
                distance_move = -dx * distance_range / chart_rect.width()
                
                # Y軸移動（速度）
                speed_range = (self.view_max_speed or self.max_speed) - (self.view_min_speed or self.min_speed)
                speed_move = dy * speed_range / chart_rect.height()  # Y軸是倒置的
                
                # 更新視圖範圍
                if self.view_min_distance is None:
                    self.view_min_distance = self.min_distance
                    self.view_max_distance = self.max_distance
                if self.view_min_speed is None:
                    self.view_min_speed = self.min_speed
                    self.view_max_speed = self.max_speed
                
                self.view_min_distance += distance_move
                self.view_max_distance += distance_move
                self.view_min_speed += speed_move
                self.view_max_speed += speed_move
            
            self.last_drag_pos = event.pos()
        
        self.update()
        
    def mousePressEvent(self, event: QMouseEvent):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            # 左鍵點擊：固定垂直線
            chart_rect = QRect(
                self.margin_left, self.margin_top,
                self.width() - self.margin_left - self.margin_right,
                self.height() - self.margin_top - self.margin_bottom
            )
            
            if chart_rect.contains(event.pos()):
                # 計算並保存實際的距離值
                current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
                current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
                distance_range = current_max_distance - current_min_distance
                
                if distance_range > 0:
                    relative_x = event.x() - chart_rect.left()
                    self.fixed_distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
                    self.show_fixed_line = True
                    self.update()
            
        elif event.button() == Qt.MiddleButton:
            # 中鍵按下：開始拖拉
            self.middle_dragging = True
            self.last_drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
    def mouseReleaseEvent(self, event: QMouseEvent):
        """滑鼠釋放事件"""
        if event.button() == Qt.MiddleButton:
            # 中鍵釋放：結束拖拉
            self.middle_dragging = False
            self.setCursor(Qt.ArrowCursor)
            
    def wheelEvent(self, event: QWheelEvent):
        """滑鼠滾輪事件"""
        # 獲取滾輪方向
        delta = event.angleDelta().y()
        zoom_factor = 1.1 if delta > 0 else 1.0 / 1.1
        
        # 獲取滑鼠在圖表中的相對位置
        chart_rect = QRect(
            self.margin_left, self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        if chart_rect.contains(event.pos()):
            # 計算滑鼠位置對應的數據值
            mouse_rel_x = (event.x() - chart_rect.left()) / chart_rect.width()
            mouse_rel_y = (chart_rect.bottom() - event.y()) / chart_rect.height()
            
            # 初始化視圖範圍
            if self.view_min_distance is None:
                self.view_min_distance = self.min_distance
                self.view_max_distance = self.max_distance
            if self.view_min_speed is None:
                self.view_min_speed = self.min_speed
                self.view_max_speed = self.max_speed
            
            # 計算當前滑鼠對應的數據值
            distance_range = self.view_max_distance - self.view_min_distance
            speed_range = self.view_max_speed - self.view_min_speed
            
            mouse_distance = self.view_min_distance + mouse_rel_x * distance_range
            mouse_speed = self.view_min_speed + mouse_rel_y * speed_range
            
            # 計算新的範圍
            new_distance_range = distance_range / zoom_factor
            new_speed_range = speed_range / zoom_factor
            
            # 以滑鼠位置為中心進行縮放
            self.view_min_distance = mouse_distance - mouse_rel_x * new_distance_range
            self.view_max_distance = mouse_distance + (1 - mouse_rel_x) * new_distance_range
            self.view_min_speed = mouse_speed - mouse_rel_y * new_speed_range
            self.view_max_speed = mouse_speed + (1 - mouse_rel_y) * new_speed_range
            
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
    lap_numbers_changed = pyqtSignal(int, int)  # 圈數變更信號 (lap1, lap2)
    
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
        main_splitter.setStretchFactor(0, 1)  # 圖表區域可伸縮
        main_splitter.setStretchFactor(1, 0)  # 統計區域固定大小
        
        # 設置初始分割比例，讓圖表佔據大部分空間
        main_splitter.setSizes([800, 50])  # 圖表:統計 = 800:50
        
    def _create_chart_container(self) -> QWidget:
        """創建圖表容器"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 添加擴展策略
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
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setMaximumHeight(80)  # 增加高度以容納狀態資訊欄
        container.setMinimumHeight(80)  # 設置最小高度
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #f8f9fa;
            }
        """)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(3)
        
        # 標題欄（包含標題和箭頭按鈕）
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 標題標籤
        title_label = QLabel("詳細統計信息")
        title_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 11px;
                color: #2c3e50;
                background: transparent;
                border: none;
            }
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 箭頭按鈕
        self.toggle_button = QPushButton("▼")  # 向下箭頭表示可以展開
        self.toggle_button.setFixedSize(20, 20)  # 小型方形按鈕
        self.toggle_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ecf0f1;
                font-size: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
            QPushButton:pressed {
                background-color: #bdc3c7;
            }
        """)
        self.toggle_button.clicked.connect(self.toggle_statistics_panel)
        title_layout.addWidget(self.toggle_button)
        
        main_layout.addLayout(title_layout)
        
        # 車手狀態資訊欄（總是顯示）
        self.status_info_widget = self._create_status_info_widget()
        main_layout.addWidget(self.status_info_widget)
        
        # 統計表格
        self.stats_table = QTableWidget()
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        self.stats_table.setVisible(False)  # 預設隱藏統計表格
        main_layout.addWidget(self.stats_table)
        
        # 初始化表格
        self._setup_stats_table()
        
        return container
    
    def _create_status_info_widget(self) -> QWidget:
        """創建車手狀態資訊顯示小部件"""
        status_widget = QFrame()
        status_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 3px;
                margin: 2px;
            }
        """)
        
        layout = QHBoxLayout(status_widget)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        
        # 圈時間資訊
        self.lap_time_label = QLabel("⏱️ 圈時間: N/A")
        self.lap_time_label.setStyleSheet("font-size: 11px; color: #2c3e50;")
        layout.addWidget(self.lap_time_label)
        
        # 分隔線
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator1)
        
        # 輪胎配方資訊  
        self.tyre_compound_label = QLabel("🛞 輪胎配方: N/A")
        self.tyre_compound_label.setStyleSheet("font-size: 11px; color: #2c3e50;")
        layout.addWidget(self.tyre_compound_label)
        
        # 分隔線
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator2)
        
        # 輪胎圈數資訊 - 改為可編輯的輸入框
        tyre_life_container = QWidget()
        tyre_life_layout = QHBoxLayout(tyre_life_container)
        tyre_life_layout.setContentsMargins(0, 0, 0, 0)
        tyre_life_layout.setSpacing(5)
        
        # 標籤
        tyre_life_title = QLabel("🔄 圈數:")
        tyre_life_title.setStyleSheet("font-size: 11px; color: #2c3e50;")
        tyre_life_layout.addWidget(tyre_life_title)
        
        # 車手1圈數輸入
        self.lap1_spinbox = QSpinBox()
        self.lap1_spinbox.setRange(1, 99)
        self.lap1_spinbox.setValue(1)
        self.lap1_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 10px; 
                border: 1px solid #bdc3c7; 
                border-radius: 2px;
                padding: 2px;
                max-width: 40px;
            }
        """)
        self.lap1_spinbox.valueChanged.connect(self._on_lap_changed)
        tyre_life_layout.addWidget(self.lap1_spinbox)
        
        # vs 標籤
        vs_label = QLabel("vs")
        vs_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        tyre_life_layout.addWidget(vs_label)
        
        # 車手2圈數輸入
        self.lap2_spinbox = QSpinBox()
        self.lap2_spinbox.setRange(1, 99)
        self.lap2_spinbox.setValue(1)
        self.lap2_spinbox.setStyleSheet("""
            QSpinBox {
                font-size: 10px; 
                border: 1px solid #bdc3c7; 
                border-radius: 2px;
                padding: 2px;
                max-width: 40px;
            }
        """)
        self.lap2_spinbox.valueChanged.connect(self._on_lap_changed)
        tyre_life_layout.addWidget(self.lap2_spinbox)
        
        layout.addWidget(tyre_life_container)
        
        layout.addStretch()  # 推到左側
        
        return status_widget
    
    def _update_status_info(self, data: Dict[str, Any]):
        """更新狀態資訊顯示"""
        try:
            metadata = data.get('metadata', {})
            drivers = metadata.get('drivers', [])
            
            if drivers:
                # 雙車手模式：顯示對比信息
                if len(drivers) >= 2:
                    driver1 = drivers[0]
                    driver2 = drivers[1]
                    
                    # 圈時間
                    lap_time1 = driver1.get('lap_time', 'N/A')
                    lap_time2 = driver2.get('lap_time', 'N/A')
                    self.lap_time_label.setText(f"⏱️ 圈時間: {lap_time1} | {lap_time2}")
                    
                    # 輪胎配方
                    compound1 = driver1.get('compound', 'N/A')
                    compound2 = driver2.get('compound', 'N/A')
                    self.tyre_compound_label.setText(f"🛞 輪胎配方: {compound1} | {compound2}")
                    
                    # 更新圈數輸入框（如果數據中有圈數信息）
                    if 'lap_number' in driver1 and 'lap_number' in driver2:
                        lap1 = driver1.get('lap_number', 1)
                        lap2 = driver2.get('lap_number', 1)
                        self.set_lap_numbers(lap1, lap2)
                
                # 單車手模式：顯示單一車手信息
                else:
                    driver = drivers[0]
                    lap_time = driver.get('lap_time', 'N/A')
                    compound = driver.get('compound', 'N/A')
                    
                    # 更新圈數輸入框（單車手模式）
                    if 'lap_number' in driver:
                        lap_number = driver.get('lap_number', 1)
                        self.set_lap_numbers(lap_number, lap_number)
                    
                    self.lap_time_label.setText(f"⏱️ 圈時間: {lap_time}")
                    self.tyre_compound_label.setText(f"🛞 輪胎配方: {compound}")
            else:
                # 沒有車手數據時的預設顯示
                self.lap_time_label.setText("⏱️ 圈時間: N/A")
                self.tyre_compound_label.setText("🛞 輪胎配方: N/A")
                
        except Exception as e:
            print(f"[ERROR] 更新狀態資訊失敗: {e}")
            # 發生錯誤時顯示預設值
            self.lap_time_label.setText("⏱️ 圈時間: 錯誤")
            self.tyre_compound_label.setText("🛞 輪胎配方: 錯誤")
        
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
        
        # 更新箭頭方向和容器高度
        if is_visible:
            # 隱藏統計表格，但保留狀態資訊欄
            self.toggle_button.setText("▼")  # 向下箭頭表示可以展開
            self.stats_container.setMaximumHeight(80)  # 保持足夠高度顯示狀態欄
            self.stats_container.setMinimumHeight(80)
        else:
            # 顯示統計表格
            self.toggle_button.setText("▲")  # 向上箭頭表示可以收縮
            # 調用自適應高度函數
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
        row_height = self.stats_table.rowHeight(0) if row_count > 0 else 25
        
        # 總高度 = 標題欄高度 + 狀態欄高度 + 表格標題高度 + 所有行高度 + 邊距
        title_bar_height = 30  # 標題欄高度
        status_bar_height = 35  # 狀態資訊欄高度
        margins = 15  # 上下邊距
        table_height = header_height + (row_height * row_count)
        total_height = title_bar_height + status_bar_height + table_height + margins
        
        # 設置容器高度（最小120，最大400）
        container_height = max(120, min(total_height, 400))
        
        self.stats_container.setMaximumHeight(container_height)
        self.stats_container.setMinimumHeight(container_height)
        
        # 設置表格的最佳高度
        optimal_table_height = container_height - title_bar_height - status_bar_height - margins
        self.stats_table.setMaximumHeight(optimal_table_height)
        self.stats_table.setMinimumHeight(optimal_table_height)
        
    def update_speed_data(self, data: Dict[str, Any]):
        """更新速度數據"""
        print(f"[SPEED CHART WIDGET] ========== 收到數據更新請求 ==========")
        self.current_data = data
        
        try:
            # 提取元數據
            metadata = data.get('metadata', {})
            speed_data = data.get('speed_data', {})
            statistics = data.get('statistics', {})
            
            print(f"[SPEED CHART WIDGET] 元數據鍵值: {list(metadata.keys())}")
            print(f"[SPEED CHART WIDGET] 速度數據鍵值: {list(speed_data.keys())}")
            print(f"[SPEED CHART WIDGET] 統計數據鍵值: {list(statistics.keys())}")
            
            # 提取車手信息
            drivers = metadata.get('drivers', [])
            sectors = metadata.get('sectors', [])
            
            print(f"[SPEED CHART WIDGET] 車手數量: {len(drivers)}")
            print(f"[SPEED CHART WIDGET] 分段數量: {len(sectors)}")
            
            # 提取速度數據
            distance = speed_data.get('distance', [])
            driver1_speed = speed_data.get('driver1_speed', [])
            driver2_speed = speed_data.get('driver2_speed', [])
            driver1_name = speed_data.get('driver1_name', 'Driver 1')
            driver2_name = speed_data.get('driver2_name', 'Driver 2')
            
            print(f"[SPEED CHART WIDGET] 距離數據: {len(distance)} 點")
            print(f"[SPEED CHART WIDGET] 車手1 ({driver1_name}) 速度: {len(driver1_speed)} 點")
            print(f"[SPEED CHART WIDGET] 車手2 ({driver2_name}) 速度: {len(driver2_speed)} 點")
            
            # 如果有車手信息，使用車手代碼作為名稱
            if len(drivers) >= 2:
                driver1_name = drivers[0].get('code', driver1_name)
                driver2_name = drivers[1].get('code', driver2_name)
                print(f"[SPEED CHART WIDGET] 更新車手名稱: {driver1_name} vs {driver2_name}")
            
            # 更新圖表
            print(f"[SPEED CHART WIDGET] 開始更新圖表...")
            self.chart_widget.set_speed_data(
                distance=distance,
                driver1_speed=driver1_speed,
                driver2_speed=driver2_speed,
                driver1_name=driver1_name,
                driver2_name=driver2_name,
                sectors=sectors
            )
            
            # 更新統計表格
            print(f"[SPEED CHART WIDGET] 更新統計表格...")
            self._update_statistics_table(statistics, driver1_name, driver2_name)
            
            # 更新狀態資訊顯示
            print(f"[SPEED CHART WIDGET] 更新狀態資訊...")
            self._update_status_info(data)
            
            print(f"[SPEED CHART WIDGET] ✅ 數據更新完成")
            self.chart_updated.emit()
            
        except Exception as e:
            print(f"[ERROR] [SPEED CHART WIDGET] 更新數據失敗: {e}")
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
            
            # 暫時移除分段速度統計顯示
            # sector_stats = statistics.get('sector_stats', {})
            # if sector_stats:
            #     # 添加分隔行
            #     rows.append(("─────", "─────", "─────", "─────"))
            #     
            #     # 添加各分段最高速度
            #     for sector in [1, 2, 3]:
            #         sector_key = f'sector_{sector}'
            #         if sector_key in sector_stats:
            #             s1_data = sector_stats[sector_key]
            #             driver1_max = s1_data.get('driver1_max_speed', 0)
            #             driver2_max = s1_data.get('driver2_max_speed', 0)
            #             diff = driver1_max - driver2_max
            #             
            #             rows.append((
            #                 f"S{sector} 最高速度 (km/h)",
            #                 f"{driver1_max:.1f}",
            #                 f"{driver2_max:.1f}",
            #                 f"{diff:.1f}"
            #             ))
            
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
            
    def reset_chart_view(self):
        """重置圖表視圖"""
        if hasattr(self, 'chart_widget'):
            self.chart_widget.reset_view()
            
    def clear_fixed_line(self):
        """清除固定線條"""
        if hasattr(self, 'chart_widget'):
            self.chart_widget.clear_fixed_line()
    
    def _on_lap_changed(self):
        """處理圈數變更"""
        try:
            print(f"[LAP_CHANGE] ========== 圈數變更觸發 ==========")
            lap1 = self.lap1_spinbox.value()
            lap2 = self.lap2_spinbox.value()
            print(f"[LAP_CHANGE] 用戶變更圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 發送圈數變更信號
            print(f"[LAP_CHANGE] 🚀 準備發射圈數變更信號...")
            self.lap_numbers_changed.emit(lap1, lap2)
            print(f"[LAP_CHANGE] ✅ 圈數變更信號已發射")
            
        except Exception as e:
            print(f"[ERROR] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def set_lap_numbers(self, lap1: int, lap2: int):
        """設置圈數（不觸發信號）"""
        try:
            # 暫時斷開信號連接
            self.lap1_spinbox.valueChanged.disconnect()
            self.lap2_spinbox.valueChanged.disconnect()
            
            # 設置值
            self.lap1_spinbox.setValue(lap1)
            self.lap2_spinbox.setValue(lap2)
            
            # 重新連接信號
            self.lap1_spinbox.valueChanged.connect(self._on_lap_changed)
            self.lap2_spinbox.valueChanged.connect(self._on_lap_changed)
            
            print(f"[LAP_SET] 圈數已設置: 第{lap1}圈 vs 第{lap2}圈")
            
        except Exception as e:
            print(f"[ERROR] 設置圈數失敗: {e}")
