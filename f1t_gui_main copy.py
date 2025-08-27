#!/usr/bin/env python3
"""
F1T GUI 主程式 - 專業賽車分析工作站
F1T GUI Main - Professional Racing Analysis Workstation
集成的F1分析GUI系統，提供完整的賽車數據分析功能
"""

import sys
import os
import math
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea, QHeaderView, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QPoint, QObject, QRect
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QPen, QBrush, QMouseEvent
import json
import datetime
import traceback

# 自定義QMdiArea類 - 強制執行子視窗最小尺寸
class CustomMdiArea(QMdiArea):
    """自定義MDI區域，強制執行子視窗最小尺寸限制並啟用內建功能"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 啟用MDI的內建功能
        self.setActivationOrder(QMdiArea.CreationOrder)  # 設置視窗激活順序
        self.setViewMode(QMdiArea.SubWindowView)  # 確保使用子視窗模式
        
        # 啟用右鍵選單和視窗管理功能
        self.setContextMenuPolicy(Qt.DefaultContextMenu)  # 啟用預設右鍵選單
        
        # 允許拖拉視窗
        self.setOption(QMdiArea.DontMaximizeSubWindowOnActivation, True)  # 不自動最大化
        
        #print(f"🔒 CustomMdiArea: 初始化完成，已啟用內建右鍵選單和視窗管理功能")
        
    def contextMenuEvent(self, event):
        """處理右鍵選單事件"""
        # 獲取滑鼠位置下的子視窗
        widget_at_pos = self.childAt(event.pos())
        subwindow = None
        
        # 向上查找，尋找 QMdiSubWindow
        current_widget = widget_at_pos
        while current_widget and subwindow is None:
            if isinstance(current_widget, QMdiSubWindow):
                subwindow = current_widget
                break
            # 檢查父元件是否為 QMdiSubWindow
            parent = current_widget.parent()
            if isinstance(parent, QMdiSubWindow):
                subwindow = parent
                break
            current_widget = parent
        
        if subwindow:
            # 如果在子視窗上右鍵，顯示視窗管理選單
            menu = QMenu(self)
            
            # 添加視窗管理選項
            cascade_action = menu.addAction("層疊視窗 (&C)")
            cascade_action.triggered.connect(self.cascadeSubWindows)
            
            tile_action = menu.addAction("平舖視窗 (&T)")
            tile_action.triggered.connect(self.tileSubWindows)
            
            menu.addSeparator()
            
            close_action = menu.addAction("關閉視窗 (&X)")
            close_action.triggered.connect(subwindow.close)
            
            close_all_action = menu.addAction("關閉所有視窗 (&A)")
            close_all_action.triggered.connect(self.closeAllSubWindows)
            
            menu.addSeparator()
            
            # 視窗狀態選項
            if subwindow.isMaximized():
                restore_action = menu.addAction("還原視窗 (&R)")
                restore_action.triggered.connect(subwindow.showNormal)
            else:
                maximize_action = menu.addAction("最大化視窗 (&M)")
                maximize_action.triggered.connect(subwindow.showMaximized)
            
            minimize_action = menu.addAction("最小化視窗 (&N)")
            minimize_action.triggered.connect(subwindow.showMinimized)
            
            # 顯示選單
            menu.exec_(event.globalPos())
        else:
            # 如果在空白區域右鍵，顯示區域管理選單
            menu = QMenu(self)
            
            cascade_action = menu.addAction("層疊所有視窗 (&C)")
            cascade_action.triggered.connect(self.cascadeSubWindows)
            
            tile_action = menu.addAction("平舖所有視窗 (&T)")
            tile_action.triggered.connect(self.tileSubWindows)
            
            menu.addSeparator()
            
            close_all_action = menu.addAction("關閉所有視窗 (&A)")
            close_all_action.triggered.connect(self.closeAllSubWindows)
            
            # 顯示選單
            menu.exec_(event.globalPos())
        
    def addSubWindow(self, widget, flags=None):
        """添加子視窗並強制執行最小尺寸"""
        #print(f"🔒 CustomMdiArea: addSubWindow 被調用，widget 類型: {type(widget)}")
        
        if flags is not None:
            subwindow = super().addSubWindow(widget, flags)
        else:
            subwindow = super().addSubWindow(widget)
            
        #print(f"🔒 CustomMdiArea: 創建的子視窗類型: {type(subwindow)}")
        
        # 強制設置最小尺寸
        if isinstance(subwindow, PopoutSubWindow):
            # 確保PopoutSubWindow的最小尺寸被執行
            subwindow.setMinimumSize(250, 150)
            #print(f"🔒 CustomMdiArea: 強制設置子視窗最小尺寸 250x150")
            
            # 連接調整大小事件監聽
            subwindow.resized.connect(lambda: self.enforce_minimum_size(subwindow))
            
            # 添加額外的調整大小監聽 - 確保圖表即時更新
            if hasattr(subwindow, 'resizeEvent'):
                original_resize_event = subwindow.resizeEvent
                def enhanced_resize_event(event):
                    result = original_resize_event(event)
                    self.refresh_charts_in_subwindow(subwindow)
                    return result
                subwindow.resizeEvent = enhanced_resize_event
                
            #print(f"🔒 CustomMdiArea: 已連接 resized 信號")
        
        return subwindow
    
    def enforce_minimum_size(self, subwindow):
        """強制執行子視窗最小尺寸 - 改進版圖表刷新支援"""
        if not isinstance(subwindow, PopoutSubWindow):
            return
            
        min_size = subwindow.minimumSize()
        current_size = subwindow.size()
        
        needs_resize = False
        new_width = current_size.width()
        new_height = current_size.height()
        
        if current_size.width() < min_size.width():
            new_width = min_size.width()
            needs_resize = True
            
        if current_size.height() < min_size.height():
            new_height = min_size.height()
            needs_resize = True
        
        if needs_resize:
            subwindow.resize(new_width, new_height)
            #print(f"🔒 CustomMdiArea: 強制調整子視窗尺寸至 {new_width}x{new_height}")
        
        # 通知子視窗內的圖表元件刷新
        self.refresh_charts_in_subwindow(subwindow)
    
    def refresh_charts_in_subwindow(self, subwindow):
        """刷新子視窗內的所有圖表元件 - 改進版"""
        try:
            # 查找所有 UniversalChartWidget 並刷新
            from modules.gui.universal_chart_widget import UniversalChartWidget
            
            widget = subwindow.widget()
            if widget:
                # 查找所有圖表組件並強制刷新
                chart_widgets = widget.findChildren(UniversalChartWidget)
                for chart_widget in chart_widgets:
                    if hasattr(chart_widget, 'force_refresh'):
                        chart_widget.force_refresh()
                    elif hasattr(chart_widget, 'reset_view'):
                        chart_widget.reset_view()
                    
                # 查找降雨分析模組並強制刷新
                rain_modules = widget.findChildren(QWidget)
                for module in rain_modules:
                    # 檢查是否為降雨分析模組
                    if hasattr(module, 'force_chart_refresh'):
                        module.force_chart_refresh()
                    elif hasattr(module, 'chart_widget') and hasattr(module.chart_widget, 'force_refresh'):
                        module.chart_widget.force_refresh()
                        
                print(f"[DEBUG] 已刷新 {len(chart_widgets)} 個圖表組件")
                        
        except Exception as e:
            print(f"[DEBUG] 刷新圖表時出錯: {e}")

# 全域信號管理器
class GlobalSignalManager(QObject):
    """全域信號管理器 - 用於跨視窗同步"""
    sync_x_position = pyqtSignal(int)  # X軸位置同步信號 (滑鼠位置)
    sync_x_range = pyqtSignal(float, float)  # X軸範圍同步信號 (偏移, 縮放)
    
    def __init__(self):
        super().__init__()
        
# 創建全域信號管理器實例
global_signals = GlobalSignalManager()

class TelemetryChartWidget(QWidget):
    """遙測曲線圖表小部件 - 支援縮放、拖拉、X軸同步"""
    
    def __init__(self, chart_type="speed"):
        super().__init__()
        self.chart_type = chart_type
        self.setMinimumSize(400, 200)
        self.setObjectName("TelemetryChart")
        
        # 滑鼠追蹤和虛線控制
        self.setMouseTracking(True)
        self.mouse_x = -1  # 滑鼠X位置
        self.mouse_y = -1  # 滑鼠Y位置
        self.sync_enabled = True  # 同步啟用狀態
        
        # 固定虛線控制
        self.fixed_line_x = -1  # 固定虛線X位置 (-1表示未設定)
        self.show_fixed_line = False  # 是否顯示固定虛線
        
        # 縮放和拖拉參數
        self.y_scale = 1.0  # Y軸縮放倍率
        self.y_offset = 0   # Y軸偏移
        self.x_offset = 0   # X軸偏移
        self.x_scale = 1.0  # X軸縮放倍率
        
        # 拖拉狀態
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 圖表邊距 (為坐標軸預留空間)
        self.margin_left = 50   # 左邊距 (Y軸標籤)
        self.margin_bottom = 30 # 下邊距 (X軸標籤)
        self.margin_top = 10    # 上邊距
        self.margin_right = 10  # 右邊距
        
        # 連接全域同步信號
        global_signals.sync_x_position.connect(self.on_sync_x_position)
        global_signals.sync_x_range.connect(self.on_sync_x_range)
        
    def on_sync_x_position(self, x):
        """接收來自其他圖表的X軸位置同步信號"""
        if self.sync_enabled and x != self.mouse_x:
            self.mouse_x = x
            # 計算對應的 Y 位置 (圖表中心，用於 Y 值計算)
            chart_area = self.get_chart_area()
            if chart_area:
                self.mouse_y = chart_area.center().y()
            self.update()
        
    def on_sync_x_range(self, x_offset, x_scale):
        """接收來自其他圖表的X軸範圍同步信號"""
        if self.sync_enabled:
            self.x_offset = x_offset
            self.x_scale = x_scale
            self.update()
        
    def set_sync_enabled(self, enabled):
        """設定是否啟用同步"""
        self.sync_enabled = enabled
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 更新垂直虛線位置、拖拉X軸"""
        # 更新滑鼠X和Y位置（用於虛線和數值顯示）
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            self.mouse_x = event.x()
            self.mouse_y = event.y()
            self.update()
            
            # 發送同步信號到其他圖表 (只在有勾選連動時)
            if self.sync_enabled:
                global_signals.sync_x_position.emit(self.mouse_x)
        
        # 處理X軸拖拉
        if self.dragging and event.buttons() == Qt.LeftButton:
            delta_x = event.x() - self.last_drag_pos.x()
            # 調整X軸偏移 (拖拉方向相反)
            self.x_offset -= delta_x / self.x_scale
            self.last_drag_pos = event.pos()
            self.update()
            
            # 如果啟用X軸同步，同步拖拉位置
            if self.sync_enabled:
                global_signals.sync_x_range.emit(self.x_offset, self.x_scale)
        
        super().mouseMoveEvent(event)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理固定虛線和拖拉"""
        if event.button() == Qt.LeftButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()):
                # 檢查是否按下 Ctrl 鍵來固定虛線
                if event.modifiers() & Qt.ControlModifier:
                    # Ctrl + 左鍵：固定虛線位置
                    self.fixed_line_x = event.x()
                    self.show_fixed_line = True
                    
                    # 計算並保存固定位置的真實數據值
                    self._calculate_and_save_fixed_value()
                    
                    #print(f"🔒 固定虛線位置：X = {self.fixed_line_x}")
                    self.update()
                else:
                    # 普通左鍵：開始拖拉
                    self.dragging = True
                    self.last_drag_pos = event.pos()
                    self.setCursor(Qt.ClosedHandCursor)
        
        # 右鍵：清除固定虛線
        elif event.button() == Qt.RightButton:
            chart_area = self.get_chart_area()
            if chart_area.contains(event.pos()):
                self.show_fixed_line = False
                self.fixed_line_x = -1
                #print("🔓 清除固定虛線")
                self.update()
        
        super().mousePressEvent(event)
        
    def _calculate_and_save_fixed_value(self):
        """計算並保存固定虛線位置的真實數據值"""
        if not hasattr(self, 'fixed_line_x') or self.fixed_line_x < 0:
            return
            
        chart_area = self.get_chart_area()
        if not chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            return
            
        # 計算實際的X軸數值
        if abs(self.x_scale) > 0.001:
            i = self.fixed_line_x - chart_area.left()
            x_start = int(self.x_offset)
            actual_x = x_start + i / self.x_scale
        else:
            return
            
        # 使用數據插值計算真實Y值
        if hasattr(self, 'x_data') and hasattr(self, 'y_data') and self.x_data and self.y_data:
            import numpy as np
            try:
                # 使用線性插值獲取精確的真實Y值
                fixed_y_value = np.interp(actual_x, self.x_data, self.y_data)
                
                # 保存固定值和單位
                self.fixed_y_value = fixed_y_value
                self.fixed_actual_x = actual_x
                
                # 根據圖表類型設置單位
                if self.chart_type == "speed":
                    self.fixed_unit = "km/h"
                elif self.chart_type == "brake":
                    self.fixed_unit = "%"
                elif self.chart_type == "throttle":
                    self.fixed_unit = "%"
                elif self.chart_type == "steering":
                    self.fixed_unit = "°"
                
                #print(f"🔒 保存固定值: X={actual_x:.1f}, Y={fixed_y_value:.1f}{self.fixed_unit}")
                return
            except Exception as e:
                #print(f"[WARNING] 固定值計算失敗: {e}")
                pass
        
        # 如果插值失敗，設置為未知狀態
        self.fixed_y_value = None
        self.fixed_unit = ""
        #print(f"[WARNING] 無法計算固定值 - 沒有可用數據")
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拉"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.setCursor(Qt.ArrowCursor)
        
        super().mouseReleaseEvent(event)
        
    def wheelEvent(self, event):
        """滑鼠滾輪事件 - 智能縮放"""
        chart_area = self.get_chart_area()
        if chart_area.contains(event.pos()):
            # 獲取滾輪滾動量
            delta = event.angleDelta().y()
            
            # 檢查修飾鍵
            modifiers = event.modifiers()
            
            if modifiers & Qt.ControlModifier:
                # Ctrl + 滾輪: X軸縮放
                zoom_factor = 1.2 if delta > 0 else 0.8
                self.x_scale *= zoom_factor
                self.x_scale = max(0.1, min(10.0, self.x_scale))
                #print(f"[SEARCH] X軸縮放: {self.x_scale:.2f}")
                
            elif modifiers & Qt.ShiftModifier:
                # Shift + 滾輪: 同步X+Y軸縮放
                zoom_factor = 1.2 if delta > 0 else 0.8
                self.x_scale *= zoom_factor
                self.y_scale *= zoom_factor
                self.x_scale = max(0.1, min(10.0, self.x_scale))
                # Y軸可以是負數，允許更大範圍
                self.y_scale = max(-10.0, min(10.0, self.y_scale))
                #print(f"[SEARCH] 同步縮放: X={self.x_scale:.2f}, Y={self.y_scale:.2f}")
                
            else:
                # 純滾輪: Y軸縮放 (允許負數縮放以顯示負數數據)
                zoom_factor = 1.3 if delta > 0 else 0.7
                self.y_scale *= zoom_factor
                # Y軸縮放範圍: -10.0 到 +10.0 (負數可以顯示負數數據)
                self.y_scale = max(-10.0, min(10.0, self.y_scale))
                # 避免過小的正數或負數
                if abs(self.y_scale) < 0.1:
                    self.y_scale = 0.1 if self.y_scale >= 0 else -0.1
                #print(f"[SEARCH] Y軸縮放: {self.y_scale:.2f}")
            
            self.update()
            event.accept()
            return
        
        super().wheelEvent(event)
        
    def leaveEvent(self, event):
        """滑鼠離開事件 - 隱藏動態虛線"""
        self.mouse_x = -1
        self.update()
        
        # 發送隱藏信號到其他圖表
        if self.sync_enabled:
            global_signals.sync_x_position.emit(-1)
        
        super().leaveEvent(event)
        
    def get_chart_area(self):
        """獲取圖表繪製區域 (排除坐標軸邊距)"""
        return QRect(
            self.margin_left,
            self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 黑色背景
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # 獲取圖表繪製區域
        chart_area = self.get_chart_area()
        
        # 繪製坐標軸
        self.draw_axes(painter, chart_area)
        
        # 設定裁切區域為圖表區域
        painter.setClipRect(chart_area)
        
        # 繪製網格 (在圖表區域內)
        self.draw_grid(painter, chart_area)
        
        # 繪製滑鼠位置的動態垂直線 
        if self.mouse_x >= 0 and chart_area.contains(QPoint(self.mouse_x, chart_area.center().y())):
            if self.sync_enabled:
                # 連動模式：白色虛線
                painter.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
            else:
                # 非連動模式：黃色虛線
                painter.setPen(QPen(QColor(255, 255, 0), 2, Qt.DashLine))
            
            painter.drawLine(self.mouse_x, chart_area.top(), self.mouse_x, chart_area.bottom())
            
            # 在虛線上方顯示Y軸數值
            self.draw_y_value_at_mouse(painter, chart_area)
        
        # 繪製固定位置的垂直線（如果已設定）
        if self.show_fixed_line and self.fixed_line_x >= 0 and chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            # 固定虛線：紅色實線
            painter.setPen(QPen(QColor(255, 0, 0), 3, Qt.SolidLine))
            painter.drawLine(self.fixed_line_x, chart_area.top(), self.fixed_line_x, chart_area.bottom())
            
            # 在固定虛線上方顯示Y軸數值
            self.draw_y_value_at_fixed_line(painter, chart_area)
        
        # 繪製曲線數據
        if self.chart_type == "speed":
            self.draw_speed_curve(painter, chart_area)
        elif self.chart_type == "brake":
            self.draw_brake_curve(painter, chart_area)
        elif self.chart_type == "throttle":
            self.draw_throttle_curve(painter, chart_area)
        elif self.chart_type == "steering":
            self.draw_steering_curve(painter, chart_area)
            
        # 取消裁切
        painter.setClipping(False)
        
    def draw_axes(self, painter, chart_area):
        """繪製X和Y軸"""
        painter.setPen(QPen(QColor(200, 200, 200), 2))
        
        # Y軸 (左邊)
        painter.drawLine(chart_area.left(), chart_area.top(), chart_area.left(), chart_area.bottom())
        
        # X軸 (底部)
        painter.drawLine(chart_area.left(), chart_area.bottom(), chart_area.right(), chart_area.bottom())
        
        # Y軸標籤
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 8))
        
        # 根據圖表類型設定Y軸範圍和標籤
        if self.chart_type == "speed":
            y_min, y_max = 0, 350  # 速度範圍 (km/h)
            unit = "km/h"
        elif self.chart_type == "brake":
            y_min, y_max = 0, 100  # 煞車壓力 (%)
            unit = "%"
        elif self.chart_type == "throttle":
            y_min, y_max = 0, 100  # 節流閥開度 (%)
            unit = "%"
        elif self.chart_type == "steering":
            y_min, y_max = -100, 100  # 轉向角度 (度)
            unit = "°"
        else:
            y_min, y_max = 0, 100
            unit = ""
        
        # 繪製Y軸刻度
        steps = 5
        for i in range(steps + 1):
            value = y_min + (y_max - y_min) * i / steps
            # 應用縮放和偏移
            y_pos = int(chart_area.bottom() - (i / steps) * chart_area.height())
            
            # 刻度線
            painter.drawLine(chart_area.left() - 5, y_pos, chart_area.left(), y_pos)
            
            # 標籤
            label = f"{value:.0f}"
            if i == 0:  # 在底部標籤添加單位
                label += f" {unit}"
            painter.drawText(5, y_pos + 4, label)
        
        # X軸標籤 (時間)
        x_steps = 5
        for i in range(x_steps + 1):
            x_pos = int(chart_area.left() + (i / x_steps) * chart_area.width())
            
            # 刻度線
            painter.drawLine(x_pos, chart_area.bottom(), x_pos, chart_area.bottom() + 5)
            
            # 時間標籤 (假設每個單位是1秒)
            time_value = i * (chart_area.width() / x_steps) / 50  # 每50像素 = 1秒
            painter.drawText(x_pos - 10, chart_area.bottom() + 20, f"{time_value:.1f}s")
    
    def draw_grid(self, painter, chart_area):
        """繪製網格線"""
        painter.setPen(QPen(QColor(40, 40, 40), 1))
        
        # 垂直網格線
        grid_spacing_x = 50
        for i in range(chart_area.left(), chart_area.right(), grid_spacing_x):
            painter.drawLine(i, chart_area.top(), i, chart_area.bottom())
            
        # 水平網格線
        grid_spacing_y = 30
        for i in range(chart_area.top(), chart_area.bottom(), grid_spacing_y):
            painter.drawLine(chart_area.left(), i, chart_area.right(), i)
            
    def draw_speed_curve(self, painter, chart_area):
        """繪製速度曲線"""
        painter.setPen(QPen(QColor(0, 255, 0), 2))  # 綠色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.speed_data = []  # 專門為Y值計算存儲速度數據
        
        # 計算X軸範圍 (考慮偏移和縮放)
        x_start = int(self.x_offset)
        x_range = int(chart_area.width() / self.x_scale)
        
        for i in range(0, chart_area.width(), 2):
            # 計算實際的X位置 (考慮偏移和縮放)
            real_x = x_start + i / self.x_scale
            
            # 等待真實速度資料載入
            speed = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(speed)
            self.speed_data.append(speed)  # 為Y值計算存儲速度數據
            
            # 轉換為圖表座標 (支援負數Y軸縮放)
            x_pos = chart_area.left() + i
            normalized_speed = speed / 350  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_speed * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_speed * chart_area.height() * abs(self.y_scale)) + self.y_offset
            
            points.append(QPointF(x_pos, y_pos))
        
        # 繪製曲線
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_brake_curve(self, painter, chart_area):
        """繪製煞車曲線"""
        painter.setPen(QPen(QColor(255, 0, 0), 2))  # 紅色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.brake_data = []  # 專門為Y值計算存儲煞車數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實煞車壓力資料載入
            brake = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(brake)
            self.brake_data.append(brake)  # 為Y值計算存儲煞車數據
            
            x_pos = chart_area.left() + i
            normalized_brake = brake / 100 if brake > 0 else 0  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_brake * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_brake * chart_area.height() * abs(self.y_scale)) + self.y_offset
            
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_throttle_curve(self, painter, chart_area):
        """繪製節流閥曲線"""
        painter.setPen(QPen(QColor(255, 255, 0), 2))  # 黃色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.throttle_data = []  # 專門為Y值計算存儲節流閥數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實節流閥位置資料載入
            throttle = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(throttle)
            self.throttle_data.append(throttle)  # 為Y值計算存儲節流閥數據
            
            x_pos = chart_area.left() + i
            normalized_throttle = throttle / 100 if throttle > 0 else 0  # 0-1 範圍
            
            if self.y_scale >= 0:
                # 正常縮放：底部為0，向上增長
                y_pos = chart_area.bottom() - (normalized_throttle * chart_area.height() * self.y_scale) + self.y_offset
            else:
                # 負數縮放：翻轉Y軸，頂部為0，向下增長
                y_pos = chart_area.top() + (normalized_throttle * chart_area.height() * abs(self.y_scale)) + self.y_offset
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_steering_curve(self, painter, chart_area):
        """繪製方向盤曲線"""
        painter.setPen(QPen(QColor(0, 255, 255), 2))  # 青色
        points = []
        
        # 存儲數據點以供重置功能和Y值計算使用
        self.x_data = []
        self.y_data = []
        self.steering_data = []  # 專門為Y值計算存儲方向盤數據
        
        x_start = int(self.x_offset)
        
        for i in range(0, chart_area.width(), 2):
            real_x = x_start + i / self.x_scale
            
            # 等待真實方向盤轉角資料載入
            steering = 0  # 預設值，等待真實數據
            
            # 存儲原始數據
            self.x_data.append(real_x)
            self.y_data.append(steering)
            self.steering_data.append(steering)  # 為Y值計算存儲方向盤數據
            
            x_pos = chart_area.left() + i
            # 改進的轉向角度處理 - 支援負數Y軸縮放
            # 將 -100~+100 映射到圖表高度，中心線在圖表中央
            normalized_steering = steering / 100.0  # -1.0 到 +1.0
            y_pos = chart_area.center().y() - (normalized_steering * chart_area.height() * 0.4 * abs(self.y_scale))
            
            # 如果Y軸縮放是負數，翻轉Y軸
            if self.y_scale < 0:
                y_pos = chart_area.center().y() + (normalized_steering * chart_area.height() * 0.4 * abs(self.y_scale))
            
            y_pos += self.y_offset
            points.append(QPointF(x_pos, y_pos))
        
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])
            
    def draw_y_value_at_mouse(self, painter, chart_area):
        """在滑鼠位置的虛線上方顯示Y軸數值 - 基於滑鼠位置反向計算Y值"""
        # 確保滑鼠X位置有效且在圖表區域內
        if not hasattr(self, 'mouse_x') or self.mouse_x < 0:
            return
        if not chart_area.contains(QPoint(self.mouse_x, chart_area.center().y())):
            return
            
        # 計算實際的X軸數值 - 匹配繪圖邏輯
        if abs(self.x_scale) > 0.001:
            i = self.mouse_x - chart_area.left()
            x_start = int(self.x_offset)
            actual_x = x_start + i / self.x_scale
        else:
            return
            
        # 方法1：如果有存儲的數據，使用插值計算Y值
        y_value = None
        unit = ""
        
        if hasattr(self, 'x_data') and hasattr(self, 'y_data') and self.x_data and self.y_data:
            import numpy as np
            try:
                # 使用線性插值獲取精確的Y值
                y_value = np.interp(actual_x, self.x_data, self.y_data)
                
                # 根據圖表類型設置單位
                if self.chart_type == "speed":
                    unit = "km/h"
                elif self.chart_type == "brake":
                    unit = "%"
                elif self.chart_type == "throttle":
                    unit = "%"
                elif self.chart_type == "steering":
                    unit = "°"
                else:
                    return
            except Exception:
                y_value = None
        
        # 方法2：如果插值失敗或沒有數據，使用滑鼠Y位置反向計算
        if y_value is None:
            # 從滑鼠Y位置反向計算對應的數值
            mouse_y_in_chart = self.mouse_y
            
            # 反向計算Y值 - 匹配繪圖邏輯
            if self.chart_type == "speed":
                # 速度範圍 0-350 km/h
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        # 正常縮放：底部為0，向上增長
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        # 負數縮放：頂部為0，向下增長
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(350, normalized_y * 350))
                else:
                    y_value = 175  # 中間值
                unit = "km/h"
            elif self.chart_type == "brake":
                # 煞車範圍 0-100%
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(100, normalized_y * 100))
                else:
                    y_value = 50
                unit = "%"
            elif self.chart_type == "throttle":
                # 油門範圍 0-100%
                if abs(self.y_scale) > 0.001:
                    if self.y_scale >= 0:
                        normalized_y = (chart_area.bottom() - mouse_y_in_chart + self.y_offset) / (chart_area.height() * self.y_scale)
                    else:
                        normalized_y = (mouse_y_in_chart - chart_area.top() - self.y_offset) / (chart_area.height() * abs(self.y_scale))
                    y_value = max(0, min(100, normalized_y * 100))
                else:
                    y_value = 50
                unit = "%"
            elif self.chart_type == "steering":
                # 轉向範圍 -100° to +100°，使用圖表中心為基準
                if abs(self.y_scale) > 0.001:
                    # 計算相對於圖表中心的偏移
                    center_offset = mouse_y_in_chart - chart_area.center().y() - self.y_offset
                    
                    if self.y_scale >= 0:
                        # 正常縮放：負值向上，正值向下
                        normalized_steering = -center_offset / (chart_area.height() * 0.4 * abs(self.y_scale))
                    else:
                        # 負數縮放：翻轉Y軸
                        normalized_steering = center_offset / (chart_area.height() * 0.4 * abs(self.y_scale))
                    
                    y_value = max(-100, min(100, normalized_steering * 100))
                else:
                    y_value = 0
                unit = "°"
            else:
                return
        
        # 繪製數值標籤
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        
        # 格式化數值顯示
        if self.chart_type == "steering":
            value_text = f"{y_value:+.1f}{unit}"
        else:
            value_text = f"{y_value:.1f}{unit}"
        
        # 計算標籤位置（虛線上方，在滑鼠Y位置上方）
        label_x = self.mouse_x + 5
        label_y = max(chart_area.top() + 20, self.mouse_y - 15)  # 在滑鼠位置上方顯示
        
        # 確保標籤不超出左右邊界
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(value_text)
        if label_x + text_width > chart_area.right():
            label_x = self.mouse_x - text_width - 5
        if label_x < chart_area.left():
            label_x = chart_area.left() + 5
        
        # 繪製背景框
        text_rect = text_metrics.boundingRect(value_text)
        bg_rect = text_rect.adjusted(-4, -2, 4, 2)
        bg_rect.moveTopLeft(QPoint(label_x - 4, label_y - text_rect.height() - 2))
        
        # 根據同步狀態選擇顏色
        if self.sync_enabled:
            painter.fillRect(bg_rect, QColor(0, 0, 0, 200))  # 黑色半透明背景
            text_color = QColor(255, 255, 255)  # 白色文字
            border_color = QColor(255, 255, 255)  # 白色邊框
        else:
            painter.fillRect(bg_rect, QColor(80, 80, 0, 200))  # 深黃色半透明背景
            text_color = QColor(255, 255, 0)  # 黃色文字
            border_color = QColor(255, 255, 0)  # 黃色邊框
        
        painter.setPen(QPen(border_color, 1))
        painter.drawRect(bg_rect)
        
        # 繪製文字
        painter.setPen(QPen(text_color, 1))
        painter.drawText(label_x, label_y, value_text)
        
    def draw_y_value_at_fixed_line(self, painter, chart_area):
        """在固定虛線位置顯示固定Y值 - 使用已保存的值，不會變動"""
        # 確保固定線有效
        if not hasattr(self, 'show_fixed_line') or not self.show_fixed_line:
            return
        if not hasattr(self, 'fixed_line_x') or self.fixed_line_x < 0:
            return
        if not chart_area.contains(QPoint(self.fixed_line_x, chart_area.center().y())):
            return
            
        # 使用已保存的固定值（在點擊時保存，之後不會變動）
        if hasattr(self, 'fixed_y_value') and self.fixed_y_value is not None:
            y_value = self.fixed_y_value
            unit = getattr(self, 'fixed_unit', '')
            #print(f"🔒 使用已保存的固定值: {y_value:.1f}{unit}")
        else:
            #print(f"[WARNING] 沒有已保存的固定值")
            return
        
        # 繪製數值標籤
        painter.setPen(QPen(QColor(255, 0, 0), 1))  # 紅色文字
        painter.setFont(QFont("Arial", 12, QFont.Bold))  # 稍大字體
        
        # 格式化數值顯示 (包含鎖孔圖標)
        if self.chart_type == "steering":
            value_text = f"🔒{y_value:+.1f}{unit}"
        else:
            value_text = f"🔒{y_value:.1f}{unit}"
        
        # 計算標籤位置（固定線右側，頂部）
        label_x = self.fixed_line_x + 8
        label_y = chart_area.top() + 20
        
        # 確保標籤不超出右邊界
        text_metrics = painter.fontMetrics()
        text_width = text_metrics.horizontalAdvance(value_text)
        if label_x + text_width > chart_area.right():
            label_x = self.fixed_line_x - text_width - 8
        if label_x < chart_area.left():
            label_x = chart_area.left() + 5
        
        # 繪製背景框
        text_rect = text_metrics.boundingRect(value_text)
        bg_rect = text_rect.adjusted(-4, -2, 4, 2)
        bg_rect.moveTopLeft(QPoint(label_x - 4, label_y - text_rect.height() - 2))
        
        # 紅色背景和邊框（固定線樣式）
        painter.fillRect(bg_rect, QColor(100, 0, 0, 200))  # 深紅色半透明背景
        painter.setPen(QPen(QColor(255, 0, 0), 2))
        painter.drawRect(bg_rect)
        
        # 繪製文字
        painter.setPen(QPen(QColor(255, 255, 255), 1))  # 白色文字
        painter.drawText(label_x, label_y, value_text)
        
        #print(f"[STATS] 顯示固定值標籤: {value_text} at ({label_x}, {label_y})")  # Debug

class TrackMapWidget(QWidget):
    """賽道地圖小部件"""
    
    def __init__(self):
        super().__init__()
        self.setMinimumSize(300, 200)
        self.setObjectName("TrackMap")
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 黑色背景
        painter.fillRect(self.rect(), QColor(0, 0, 0))
        
        # 繪製賽道輪廓 (基於真實賽道數據)
        painter.setPen(QPen(QColor(0, 255, 0), 3))  # 綠色賽道線
        
        # 賽道主線
        center_x, center_y = self.width() // 2, self.height() // 2
        
        # 繪製基本賽道輪廓 (待整合真實賽道數據)
        points = []
        for i in range(360):
            angle = math.radians(i)
            if i < 180:
                # 上半部分
                x = center_x + 80 * math.cos(angle)
                y = center_y - 60 + 30 * math.sin(angle)
            else:
                # 下半部分
                x = center_x + 60 * math.cos(angle)
                y = center_y + 20 + 40 * math.sin(angle)
            points.append(QPointF(x, y))
        
        # 繪製賽道
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            painter.drawLine(points[i], points[next_i])
        
        # 繪製起跑線
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        start_x = center_x + 80
        painter.drawLine(start_x, center_y - 10, start_x, center_y + 10)
        
        # 繪製車輛位置點
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(QPen(QColor(255, 0, 0), 1))
        painter.drawEllipse(start_x - 3, center_y - 3, 6, 6)
        
        # 繪製扇區標記
        painter.setPen(QPen(QColor(255, 255, 0), 1))
        painter.drawText(10, 20, "Sector 1")
        painter.drawText(10, 40, "Sector 2") 
        painter.drawText(10, 60, "Sector 3")

class SystemLogWidget(QTextEdit):
    """系統日誌小部件"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("SystemLog")
        self.setMaximumHeight(100)  # 合理的最大高度
        self.setMinimumHeight(80)   # 合理的最小高度  
        self.setReadOnly(True)
        
        # 添加一些示例日誌
        logs = [
            "[13:28:45] INFO: 系統啟動完成",
            "[13:28:46] INFO: 載入F1數據中...",
            "[13:28:47] INFO: 連接到FastF1 API",
            "[13:28:48] INFO: 載入Japan 2025 Race數據",
            "[13:28:49] INFO: 數據驗證完成 - 12,540筆記錄",
            "[13:28:50] INFO: 準備分析VER vs LEC",
            "[13:28:51] INFO: 遙測分析模組就緒"
        ]
        
        for log in logs:
            self.append(log)
        
        # 滾動到底部
        self.moveCursor(self.textCursor().End)

class DraggableTitleBar(QWidget):
    """可拖拽的自定義標題欄"""
    
    def __init__(self, parent_window, title=""):
        super().__init__()
        self.parent_window = parent_window
        self.setObjectName("CustomTitleBar")
        self.setFixedHeight(20)
        self.dragging = False
        self.drag_position = QPoint()
        
        # 調試資訊：確認 CustomTitleBar 創建
        #print(f"[DESIGN] DEBUG: Creating CustomTitleBar with title: '{title}'")
        #print(f"[INFO] ObjectName set to: {self.objectName()}")
        #print(f"📏 Fixed height set to: {self.height()}")
        
        # 創建標題欄布局
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        
        # 標題標籤
        self.title_label = QLabel(title)
        self.title_label.setObjectName("SubWindowTitle")
        layout.addWidget(self.title_label)
        
        # 🔗 X軸連動控制按鈕
        self.sync_btn = QPushButton("🔗")
        self.sync_btn.setObjectName("SyncButton")
        self.sync_btn.setFixedSize(16, 16)
        self.sync_btn.setToolTip("X軸連動：開啟")
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)  # 預設啟用
        self.sync_btn.clicked.connect(self.toggle_x_sync)
        layout.addWidget(self.sync_btn)
        
        layout.addStretch()
        
        # [HOT] 恢復按鈕（針對極小視窗）
        restore_btn = QPushButton("⟲")
        restore_btn.setObjectName("RestoreButton")
        restore_btn.setFixedSize(16, 16)
        restore_btn.setToolTip("恢復正常大小")
        restore_btn.clicked.connect(self.restore_normal_size)
        layout.addWidget(restore_btn)
        
        # 設定按鈕（放在最小化按鈕左邊）
        settings_btn = QPushButton("⚙")
        settings_btn.setObjectName("SettingsButton")
        settings_btn.setFixedSize(16, 16)
        settings_btn.setToolTip("視窗設定")
        settings_btn.clicked.connect(self.parent_window.show_settings_dialog)
        layout.addWidget(settings_btn)
        
        # 標準視窗控制按鈕
        minimize_btn = QPushButton("─")
        minimize_btn.setObjectName("WindowControlButton")
        minimize_btn.setFixedSize(16, 16)
        minimize_btn.setToolTip("最小化")
        minimize_btn.clicked.connect(self.parent_window.custom_minimize)
        layout.addWidget(minimize_btn)
        
        maximize_btn = QPushButton("□")
        maximize_btn.setObjectName("WindowControlButton")
        maximize_btn.setFixedSize(16, 16)
        maximize_btn.setToolTip("最大化/還原")
        maximize_btn.clicked.connect(self.parent_window.toggle_maximize)
        layout.addWidget(maximize_btn)
        
        # 彈出按鈕
        self.popout_btn = QPushButton("⧉")
        self.popout_btn.setObjectName("PopoutButton")
        self.popout_btn.setFixedSize(16, 16)
        self.popout_btn.setToolTip("彈出為獨立視窗")
        self.popout_btn.clicked.connect(self.parent_window.toggle_popout)
        layout.addWidget(self.popout_btn)
        
        # 關閉按鈕
        close_btn = QPushButton("✕")
        close_btn.setObjectName("WindowControlButton")
        close_btn.setFixedSize(16, 16)
        close_btn.setToolTip("關閉")
        close_btn.clicked.connect(self.parent_window.close)
        layout.addWidget(close_btn)
        
    def restore_normal_size(self):
        """恢復視窗到正常大小"""
        #print(f"[REFRESH] 恢復視窗 '{self.parent_window.windowTitle()}' 到正常大小")
        if hasattr(self.parent_window, 'content_widget') and self.parent_window.content_widget:
            # 根據內容類型設置合適的大小
            if hasattr(self.parent_window.content_widget, 'chart_type'):
                # 圖表視窗
                self.parent_window.resize(500, 350)
            else:
                # 其他視窗
                self.parent_window.resize(400, 300)
        else:
            # 默認大小
            self.parent_window.resize(400, 300)
        
        # 確保視窗在可見區域內
        if self.parent_window.parent():
            parent_rect = self.parent_window.parent().rect()
            current_pos = self.parent_window.pos()
            new_x = max(10, min(current_pos.x(), parent_rect.width() - 420))
            new_y = max(10, min(current_pos.y(), parent_rect.height() - 320))
            self.parent_window.move(new_x, new_y)
        
    def mouseDoubleClickEvent(self, event):
        """雙擊恢復視窗大小"""
        if event.button() == Qt.LeftButton:
            #print(f"🖱️ 雙擊標題欄恢復視窗大小")
            self.restore_normal_size()
            event.accept()
        else:
            super().mouseDoubleClickEvent(event)
        
    def contextMenuEvent(self, event):
        """右鍵選單"""
        menu = QMenu(self)
        restore_action = menu.addAction("[REFRESH] 恢復正常大小")
        restore_action.triggered.connect(self.restore_normal_size)
        
        maximize_action = menu.addAction("🔳 最大化")
        maximize_action.triggered.connect(self.parent_window.toggle_maximize)
        
        menu.exec_(event.globalPos())
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 開始拖拽，但不干擾調整大小"""
        if event.button() == Qt.LeftButton:
            # 檢查是否在父視窗的調整邊緣區域
            parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
            if self.parent_window.get_resize_direction(parent_pos):
                # 如果在調整區域，讓父視窗處理
                event.ignore()
                return
                
            self.dragging = True
            self.drag_position = event.globalPos() - self.parent_window.frameGeometry().topLeft()
            event.accept()
            
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 執行拖拽，但不干擾調整大小"""
        # 檢查是否在調整模式
        if hasattr(self.parent_window, 'resizing') and self.parent_window.resizing:
            event.ignore()
            return
            
        # 檢查是否在調整區域，如果是就讓父視窗處理游標
        parent_pos = self.parent_window.mapFromGlobal(event.globalPos())
        if hasattr(self.parent_window, 'get_resize_direction') and self.parent_window.get_resize_direction(parent_pos):
            event.ignore()
            return
            
        if event.buttons() == Qt.LeftButton and self.dragging:
            new_pos = event.globalPos() - self.drag_position
            self.parent_window.move(new_pos)
            event.accept()
        else:
            # 沒有拖拽時，讓父視窗處理事件
            event.ignore()
            
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束拖拽"""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            event.accept()
    
    def paintEvent(self, event):
        """繪製事件 - 手動繪製背景色以確保顯示"""
        #print(f"[DESIGN] DEBUG: CustomTitleBar paintEvent called")
        #print(f"[INFO] ObjectName: {self.objectName()}")
        #print(f"📐 Widget size: {self.width()}x{self.height()}")
        #print(f"[DESIGN] Current QSS length: {len(self.styleSheet())}")
        if self.styleSheet():
            #print(f"[DESIGN] QSS content (first 100 chars): {self.styleSheet()[:100]}...")
            pass
        else:
            #print("[WARNING] No QSS applied to CustomTitleBar")
            pass
        
        # 手動繪製 #F0F0F0 背景色以確保顯示
        painter = QPainter(self)
        # 繪製稍微大一點的矩形，確保填滿所有可能的間隙
        extended_rect = self.rect()
        extended_rect.setTop(extended_rect.top() - 5)  # 向上延伸5像素
        extended_rect.setLeft(extended_rect.left() - 5)  # 向左延伸5像素 
        extended_rect.setRight(extended_rect.right() + 5)  # 向右延伸5像素
        painter.fillRect(extended_rect, QColor("#F0F0F0"))
        #print(f"[DESIGN] Manually painted background with #F0F0F0 (extended rect)")
        
        super().paintEvent(event)
    
    def update_title(self, title):
        """更新標題"""
        self.title_label.setText(title)
    
    def toggle_x_sync(self):
        """切換X軸連動狀態"""
        is_enabled = self.sync_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.sync_btn.setText("🔗")
            self.sync_btn.setToolTip("X軸連動：開啟")
        else:
            self.sync_btn.setText("🔗̸")  # 帶斜線的連結圖示
            self.sync_btn.setToolTip("X軸連動：關閉")
        
        # 找到對應的圖表小部件並設置同步狀態
        content_widget = self.parent_window.content_widget
        if content_widget:
            # 如果內容是圖表小部件
            if hasattr(content_widget, 'set_sync_enabled'):
                content_widget.set_sync_enabled(is_enabled)
                #print(f"🔗 {'啟用' if is_enabled else '停用'} X軸連動 - {self.parent_window.windowTitle()}")
            # 如果內容是容器，查找其中的圖表小部件
            elif hasattr(content_widget, 'findChildren'):
                charts = content_widget.findChildren(TelemetryChartWidget)
                for chart in charts:
                    if hasattr(chart, 'set_sync_enabled'):
                        chart.set_sync_enabled(is_enabled)
                        #print(f"🔗 {'啟用' if is_enabled else '停用'} 圖表X軸連動 - {self.parent_window.windowTitle()}")
    
    def get_sync_status(self):
        """取得當前X軸連動狀態"""
        return self.sync_btn.isChecked()

class PopoutSubWindow(QMdiSubWindow):
    """支援彈出功能和調整大小的MDI子視窗"""
    
    # 添加自定義信號
    resized = pyqtSignal()  # 尺寸調整信號
    
    def __init__(self, title="", parent_mdi=None):
        super().__init__()
        #print(f"[START] DEBUG: Creating PopoutSubWindow '{title}'")
        self.parent_mdi = parent_mdi
        self.is_popped_out = False
        self.original_widget = None
        self.content_widget = None
        self.setWindowTitle(title)
        self.setObjectName("ProfessionalSubWindow")
        
        # � 初始化最小化狀態
        self.is_minimized = False
        self.original_geometry = None
        
        # �[HOT] 設置最小尺寸防止縮小到無法使用
        self.setMinimumSize(250, 150)
        #print(f"🔒 設置最小尺寸: 250x150")
        
        # [HOT] 測試：暫時移除 FramelessWindowHint 看看邊框是否顯示
        # self.setWindowFlags(Qt.SubWindow | Qt.FramelessWindowHint)
        self.setWindowFlags(Qt.SubWindow)
        #print(f"[LABEL] Window flags set (WITHOUT FramelessWindowHint): {self.windowFlags()}")
        
        # 移除標題欄邊距
        self.setContentsMargins(0, 0, 0, 0)
        
        # [HOT] 直接設置白色邊框樣式到這個子視窗
        subwindow_qss = """
            PopoutSubWindow {
                background-color: #000000;
                border-top: none;  /* 取消上方邊框 */
                border-left: 0.5px solid #FFFFFF;
                border-right: 0.5px solid #FFFFFF;
                border-bottom: 0.5px solid #FFFFFF;
            }
            QMdiSubWindow {
                background-color: #000000;
                border-top: none;  /* 取消上方邊框 */
                border-left: 0.5px solid #FFFFFF;
                border-right: 0.5px solid #FFFFFF;
                border-bottom: 0.5px solid #FFFFFF;
                margin: 0px;  /* 消除外邊距 */
                padding: 0px;  /* 消除內邊距 */
            }
            QMdiSubWindow::title {
                background: transparent;
                color: transparent;
                height: 0px;  /* 隱藏標題 */
                padding: 0px;
                margin: 0px;
                border: none;
                font-size: 1pt;
                font-weight: normal;
                min-height: 0px;  /* 強制最小高度為0 */
                max-height: 0px;  /* 強制最大高度為0 */
                subcontrol-position: top left;
                subcontrol-origin: margin;
                position: absolute;
                top: -1000px;  /* 移到螢幕外 */
                left: -1000px;  /* 移到螢幕外 */
            }
            QMdiSubWindow[objectName="ProfessionalSubWindow"] {
                background-color: #000000;
                border-top: none;  /* 取消上方邊框 */
                border-left: 0.5px solid #FFFFFF;
                border-right: 0.5px solid #FFFFFF;
                border-bottom: 0.5px solid #FFFFFF;
            }
            
            /* CustomTitleBar 樣式 - 與主視窗保持一致 */
            #CustomTitleBar {
                background-color: #F0F0F0;
                border-bottom: 1px solid #444444;
                border-top: none;
                border-left: none;
                border-right: none;
                color: #000000;
            }
            
            /* 視窗控制按鈕 - 與主視窗保持一致 */
            #WindowControlButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #D0D0D0;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #WindowControlButton:hover {
                background-color: #E0E0E0;
            }
            #WindowControlButton:pressed {
                background-color: #D0D0D0;
            }
            
            /* 恢復按鈕 */
            #RestoreButton {
                background-color: #2E8B57;
                color: #FFFFFF;
                border: 1px solid #3CB371;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #RestoreButton:hover {
                background-color: #3CB371;
            }
            #RestoreButton:pressed {
                background-color: #228B22;
            }
            
            /* X軸連動按鈕 */
            #SyncButton {
                background-color: #1E90FF;
                color: #FFFFFF;
                border: 1px solid #4169E1;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SyncButton:hover {
                background-color: #4169E1;
            }
            #SyncButton:pressed {
                background-color: #0000CD;
            }
            #SyncButton:checked {
                background-color: #32CD32;
                border: 1px solid #00FF00;
            }
            #SyncButton:checked:hover {
                background-color: #00FF00;
            }
            
            /* 設定按鈕 */
            #SettingsButton {
                background-color: #555555;
                color: #FFFFFF;
                border: 1px solid #777777;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SettingsButton:hover {
                background-color: #666666;
            }
            #SettingsButton:pressed {
                background-color: #444444;
            }
        """
        self.setStyleSheet(subwindow_qss)
        #print(f"[OK] Direct QSS applied to subwindow: {len(subwindow_qss)} characters")
        #print(f"[DESIGN] QSS content: {subwindow_qss[:100]}...")
        
        # 調整大小相關屬性
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        #print(f"📏 Resize margins - Visual: {self.resize_margin}px, Detection: {self.resize_detection_margin}px")
        
        # 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理調整大小"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理調整大小和游標"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
            
        # 更新游標 - 即使沒有在調整也要檢查
        direction = self.get_resize_direction(event.pos())
        
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:  # 移除 top-left
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:  # 移除 top-right
                self.setCursor(Qt.SizeBDiagCursor)
            event.accept()  # 接受事件，防止被覆蓋
        else:
            self.setCursor(Qt.ArrowCursor)
            
        # [HOT] 重要：讓事件傳遞給父類以保持拖動功能
        super().mouseMoveEvent(event)
        
    def enterEvent(self, event):
        """滑鼠進入事件"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """滑鼠離開事件 - 恢復箭頭游標"""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束調整大小"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 - 使用10像素檢測區域（取消上方調整大小）"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        detection_margin = self.resize_detection_margin  # 10像素檢測區域
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= detection_margin and y <= detection_margin:
        #     return 'top-left'
        # elif x >= w - detection_margin and y <= detection_margin:
        #     return 'top-right'
        if x <= detection_margin and y >= h - detection_margin:
            return 'bottom-left'
        elif x >= w - detection_margin and y >= h - detection_margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= detection_margin:
        #     return 'top'
        elif y >= h - detection_margin:
            return 'bottom'
        elif x <= detection_margin:
            return 'left'
        elif x >= w - detection_margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_width, min_height = 200, 150
        if new_width < min_width:
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_width
            new_width = min_width
            
        if new_height < min_height:
            # 取消 top 調整功能
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_height
            new_height = min_height
            
        # 限制在MDI區域內
        if self.parent_mdi:
            mdi_rect = self.parent_mdi.rect()
            if new_x < 0:
                new_x = 0
            if new_y < 0:
                new_y = 0
            if new_x + new_width > mdi_rect.width():
                if 'right' in self.resize_direction:
                    new_width = mdi_rect.width() - new_x
                else:
                    new_x = mdi_rect.width() - new_width
            if new_y + new_height > mdi_rect.height():
                if 'bottom' in self.resize_direction:
                    new_height = mdi_rect.height() - new_y
                else:
                    new_y = mdi_rect.height() - new_height
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 使用QSS邊框，只繪製右下角提示"""
        #print(f"[DESIGN] DEBUG: PopoutSubWindow paintEvent called for {self.windowTitle()}")
        #print(f"📐 Window size: {self.width()}x{self.height()}")
        #print(f"[PIN] Window position: ({self.x()}, {self.y()})")
        #print(f"🔲 Window rect: {self.rect()}")
        #print(f"[THEATER] Window frameless: {self.windowFlags() & Qt.FramelessWindowHint}")
        #print(f"[DESIGN] Self QSS length: {len(self.styleSheet())}")
        #print(f"🏠 Parent QSS length: {len(self.parent().styleSheet()) if self.parent() else 'No parent'}")
        
        # 調用父類方法繪製基本內容
        super().paintEvent(event)
        
        # 只繪製右下角調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 右下角調整提示 (白色)
        corner_size = 8
        corner_color = QColor(255, 255, 255, 120)
        painter.fillRect(
            w - corner_size, 
            h - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製右下角調整線條 (白色)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i in range(3):
            offset = 2 + i * 2
            painter.drawLine(
                w - offset, h - 2,
                w - 2, h - offset
            )
            
        # 在四個角落添加小的調整提示 (2像素白色方塊)
        corner_indicator_size = 2
        corner_indicator_color = QColor(255, 255, 255, 150)
        
        # 左上角
        painter.fillRect(0, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右上角  
        painter.fillRect(w - corner_indicator_size, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 左下角
        painter.fillRect(0, h - corner_indicator_size, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右下角已經有了更明顯的提示
        
    def setWidget(self, widget):
        """設置內容小部件並添加彈出按鈕"""
        #print(f"[TOOL] DEBUG: PopoutSubWindow.setWidget called for {self.windowTitle()}")
        
        # 創建包裝容器
        wrapper = QWidget()
        wrapper.setObjectName("SubWindowWrapper")
        wrapper_layout = QVBoxLayout(wrapper)
        
        # 標題欄不需要邊距，應該延伸到邊緣
        wrapper_layout.setContentsMargins(0, 0, 0, 0)  # 移除所有邊距
        wrapper_layout.setSpacing(0)
        
        # 確保wrapper本身也沒有邊距
        wrapper.setStyleSheet("""
            #SubWindowWrapper {
                margin: 0px;
                padding: 0px;
                border: none;
                background-color: transparent;
            }
        """)
        
        #print(f"[PACKAGE] Wrapper margins set to: 0px (標題欄延伸到邊緣)")
        #print(f"[DESIGN] Wrapper ObjectName: {wrapper.objectName()}")
        
        # 創建可拖拽的自定義標題欄
        self.title_bar = DraggableTitleBar(self, self.windowTitle())
        wrapper_layout.addWidget(self.title_bar)
        
        # 確保標題欄使用正確的 QSS
        self.title_bar.setStyleSheet(self.styleSheet())
        #print(f"[DESIGN] DEBUG: Applied QSS to CustomTitleBar: {len(self.styleSheet())} characters")
        
        # 創建內容容器，為內容添加邊距
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        margin = self.resize_margin  # 3像素
        content_layout.setContentsMargins(margin, margin, margin, margin)
        content_layout.setSpacing(0)
        content_layout.addWidget(widget)
        
        # 添加內容容器到主layout
        wrapper_layout.addWidget(content_container)
        
        # 保存內容widget引用
        self.content_widget = widget
        
        # 確保包裝器不攔截滑鼠事件
        wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        wrapper.setMouseTracking(True)
        
        # 設置包裝器為主widget
        super().setWidget(wrapper)
        
        # [HOT] 重新強制設置最小尺寸（在setWidget之後）
        self.setMinimumSize(250, 150)
        #print(f"🔒 強制重新設置最小尺寸: 250x150 (after setWidget)")
        
        # [HOT] 確保標題欄高度被計算在內
        title_height = self.title_bar.height() if hasattr(self, 'title_bar') else 20
        min_height = max(150, title_height + 100)  # 至少標題欄高度 + 100px內容
        self.setMinimumSize(250, min_height)
        #print(f"🔒 最終最小尺寸: 250x{min_height} (含標題欄高度)")
        
    def setMinimumSize(self, *args):
        """覆寫 setMinimumSize 來追蹤誰在修改最小尺寸"""
        if len(args) == 1:  # QSize 參數
            size = args[0]
            #print(f"[ALERT] setMinimumSize 被調用: {size.width()}x{size.height()}")
        elif len(args) == 2:  # width, height 參數
            width, height = args
            #print(f"[ALERT] setMinimumSize 被調用: {width}x{height}")
            
        # 強制確保最小尺寸不小於我們的限制
        if len(args) == 2:
            width, height = args
            width = max(width, 250)
            height = max(height, 150)
            args = (width, height)
            #print(f"🔒 強制調整最小尺寸至: {width}x{height}")
        elif len(args) == 1:
            size = args[0]
            width = max(size.width(), 250)
            height = max(size.height(), 150)
            from PyQt5.QtCore import QSize
            args = (QSize(width, height),)
            #print(f"🔒 強制調整最小尺寸至: {width}x{height}")
            
        super().setMinimumSize(*args)
        
    def minimumSize(self):
        """覆寫 minimumSize 強制返回我們的最小尺寸"""
        from PyQt5.QtCore import QSize
        forced_size = QSize(250, 150)
        # #print(f"[SEARCH] minimumSize 被查詢，強制返回: {forced_size.width()}x{forced_size.height()}")
        return forced_size
        
    def minimumSizeHint(self):
        """覆寫 minimumSizeHint 強制返回我們的最小尺寸"""
        from PyQt5.QtCore import QSize
        forced_size = QSize(250, 150)
        # #print(f"[SEARCH] minimumSizeHint 被查詢，強制返回: {forced_size.width()}x{forced_size.height()}")
        return forced_size
        
    def resizeEvent(self, event):
        """處理窗口縮放事件，確保不會小於最小尺寸"""
        #print(f"[TOOL] PopoutSubWindow: resizeEvent 被調用，新尺寸: {event.size().width()}x{event.size().height()}")
        super().resizeEvent(event)
        
        # [HOT] 強制檢查最小尺寸限制（不依賴 minimumSize()）
        MIN_WIDTH = 250
        MIN_HEIGHT = 150
        
        current_size = self.size()
        
        #print(f"🔒 PopoutSubWindow: 強制最小尺寸: {MIN_WIDTH}x{MIN_HEIGHT}")
        #print(f"🔒 PopoutSubWindow: 當前尺寸: {current_size.width()}x{current_size.height()}")
        
        needs_resize = False
        new_width = current_size.width()
        new_height = current_size.height()
        
        if current_size.width() < MIN_WIDTH:
            new_width = MIN_WIDTH
            needs_resize = True
            #print(f"[WARNING] 寬度低於最小值，調整: {current_size.width()} -> {new_width}")
            
        if current_size.height() < MIN_HEIGHT:
            new_height = MIN_HEIGHT
            needs_resize = True
            #print(f"[WARNING] 高度低於最小值，調整: {current_size.height()} -> {new_height}")
        
        if needs_resize:
            #print(f"🔒 即將強制調整至最小尺寸: {new_width}x{new_height}")
            # 使用 QTimer 延遲調整，避免與Qt內部的調整衝突
            QTimer.singleShot(0, lambda: self._force_resize(new_width, new_height))
        
        # 發射調整大小信號
        self.resized.emit()
        #print(f"📡 PopoutSubWindow: 發射 resized 信號")
        
    def _force_resize(self, width, height):
        """強制調整尺寸"""
        #print(f"💥 強制調整視窗尺寸至: {width}x{height}")
        self.resize(width, height)
        # 也嘗試更新幾何形狀
        current_pos = self.pos()
        self.setGeometry(current_pos.x(), current_pos.y(), width, height)
    
    def showEvent(self, event):
        """窗口顯示時確保最小尺寸"""
        super().showEvent(event)
        min_size = self.minimumSize()
        if self.size().width() < min_size.width() or self.size().height() < min_size.height():
            self.resize(min_size)
            #print(f"🔒 showEvent 強制調整至最小尺寸: {min_size.width()}x{min_size.height()}")

    def create_window_control_panel(self):
        """創建視窗控制面板"""
        control_panel = QWidget()
        control_panel.setObjectName("WindowControlPanel")
        control_panel.setFixedHeight(35)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 3, 5, 3)
        control_layout.setSpacing(10)
        
        # 連動控制勾選框
        self.sync_windows_checkbox = QCheckBox("🔗 連動")
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        self.sync_windows_checkbox.setChecked(True)
        self.sync_windows_checkbox.setToolTip("連動其他視窗 (賽事/賽段/年份同步)")
        self.sync_windows_checkbox.toggled.connect(self.on_sync_windows_toggled)
        control_layout.addWidget(self.sync_windows_checkbox)
        
        control_layout.addStretch()
        
        # 年份選擇器
        year_label = QLabel("年:")
        year_label.setObjectName("ControlLabel")
        control_layout.addWidget(year_label)
        
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems(["2023", "2024", "2025"])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(60)
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        control_layout.addWidget(self.year_combo)
        
        # 賽事選擇器
        race_label = QLabel("賽事:")
        race_label.setObjectName("ControlLabel")
        control_layout.addWidget(race_label)
        
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        self.race_combo.addItems([
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", 
            "Miami", "Emilia Romagna", "Monaco", "Canada", "Spain",
            "Austria", "United Kingdom", "Hungary", "Belgium", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "Qatar", "United States",
            "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"
        ])
        self.race_combo.setCurrentText("Japan")
        self.race_combo.setFixedWidth(80)
        self.race_combo.currentTextChanged.connect(self.on_race_changed)
        control_layout.addWidget(self.race_combo)
        
        # 賽段選擇器
        session_label = QLabel("賽段:")
        session_label.setObjectName("ControlLabel")
        control_layout.addWidget(session_label)
        
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "SQ", "R"])
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        control_layout.addWidget(self.session_combo)
        
        # 重新分析按鈕
        reanalyze_btn = QPushButton("[REFRESH]")
        reanalyze_btn.setObjectName("ReanalyzeButton")
        reanalyze_btn.setFixedSize(25, 25)
        reanalyze_btn.setToolTip("重新分析")
        reanalyze_btn.clicked.connect(self.perform_reanalysis)
        control_layout.addWidget(reanalyze_btn)
        
        return control_panel
        
    def on_sync_windows_toggled(self, checked):
        """處理視窗連動開關"""
        window_title = self.windowTitle()
        status = "啟用" if checked else "停用"
        #print(f"🔗 [{window_title}] 視窗連動已{status}")
        
        # 如果啟用連動，同步當前參數到其他視窗
        if checked:
            self.sync_to_other_windows()
        
    def on_year_changed(self, year):
        """處理年份變更"""
        window_title = self.windowTitle()
        #print(f"[CALENDAR] [{window_title}] 年份變更為: {year}")
        
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def on_race_changed(self, race):
        """處理賽事變更"""
        window_title = self.windowTitle()
        #print(f"[FINISH] [{window_title}] 賽事變更為: {race}")
        
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def on_session_changed(self, session):
        """處理賽段變更"""
        window_title = self.windowTitle()
        #print(f"[F1] [{window_title}] 賽段變更為: {session}")
        
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
            
    def perform_reanalysis(self):
        """執行重新分析"""
        window_title = self.windowTitle()
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        #print(f"[REFRESH] [{window_title}] 開始重新分析")
        #print(f"   參數: {year} {race} {session}")
        #print(f"   視窗連動: {'是' if self.sync_windows_checkbox.isChecked() else '否'}")
        
        # 重新分析當前視窗
        self.update_current_window()
        
        # 如果啟用連動，也更新其他視窗
        if self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
            
    def sync_to_other_windows(self):
        """同步參數到其他視窗"""
        window_title = self.windowTitle()
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        #print(f"[REFRESH] [{window_title}] 同步參數到其他視窗: {year} {race} {session}")
        
        # 在這裡可以實現實際的同步邏輯
        # 遍歷MDI區域中的所有其他子視窗
        if self.parent_mdi:
            for subwindow in self.parent_mdi.subWindowList():
                if subwindow != self and hasattr(subwindow, 'set_analysis_parameters'):
                    params = {
                        'year': year,
                        'race': race,
                        'session': session
                    }
                    subwindow.set_analysis_parameters(params)
            
    def update_current_window(self):
        """更新當前視窗的分析數據"""
        window_title = self.windowTitle()
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        #print(f"[REFRESH] [{window_title}] 更新視窗數據: {year} {race} {session}")
        # 在這裡實現實際的數據更新邏輯
        
    def get_analysis_parameters(self):
        """獲取當前分析參數"""
        if hasattr(self, 'year_combo'):
            return {
                'year': self.year_combo.currentText(),
                'race': self.race_combo.currentText(),
                'session': self.session_combo.currentText(),
                'sync_windows': self.sync_windows_checkbox.isChecked()
            }
        return None
        
    def set_analysis_parameters(self, params):
        """設置分析參數"""
        if hasattr(self, 'year_combo') and params:
            self.year_combo.setCurrentText(params.get('year', '2025'))
            self.race_combo.setCurrentText(params.get('race', 'Japan'))
            self.session_combo.setCurrentText(params.get('session', 'R'))
            # 注意：不同步連動和遙測設定，保持各視窗獨立
        
    def toggle_maximize(self):
        """切換最大化狀態"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
    
    def custom_minimize(self):
        """自定義最小化：隱藏內容，只保留標題欄，移動到底部"""
        if hasattr(self, 'is_minimized') and self.is_minimized:
            # 如果已經最小化，則恢復
            self.restore_from_minimize()
        else:
            # 執行最小化
            self.minimize_to_bottom()
    
    def minimize_to_bottom(self):
        """最小化到底部，只顯示標題欄"""
        #print(f"🔽 最小化視窗 '{self.windowTitle()}' 到底部")
        
        # 保存當前狀態
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # 隱藏內容區域
        if self.content_widget:
            self.content_widget.hide()
            #print(f"[PACKAGE] 隱藏內容區域")
        
        # 設置最小化狀態
        self.is_minimized = True
        
        # 調整視窗大小為只有標題欄高度
        title_height = 25  # 標題欄高度
        current_width = self.width()
        
        # 獲取MDI區域大小
        if self.parent():
            mdi_area = self.parent()
            mdi_height = mdi_area.height()
            mdi_width = mdi_area.width()
            
            # 移動到底部
            bottom_y = mdi_height - title_height - 5
            new_x = max(0, min(self.x(), mdi_width - current_width))
            
            # 設置新的幾何形狀
            self.setGeometry(new_x, bottom_y, current_width, title_height)
            #print(f"[PIN] 移動到底部位置: ({new_x}, {bottom_y}, {current_width}, {title_height})")
        else:
            # 如果沒有父視窗，只調整高度
            self.resize(current_width, title_height)
            #print(f"📏 調整大小為: {current_width}x{title_height}")
    
    def restore_from_minimize(self):
        """從最小化狀態恢復"""
        #print(f"🔼 恢復視窗 '{self.windowTitle()}' 從最小化狀態")
        
        # 恢復幾何形狀
        if self.original_geometry is not None:
            self.setGeometry(self.original_geometry)
            #print(f"[PIN] 恢復到原始位置: {self.original_geometry}")
        else:
            #print(f"[WARNING] 無法恢復：原始幾何形狀未保存")
            pass
        
        # 顯示內容區域
        if self.content_widget:
            self.content_widget.show()
            #print(f"[PACKAGE] 顯示內容區域")
        
        # 清除最小化狀態
        self.is_minimized = False
        
    def toggle_popout(self):
        """切換彈出狀態"""
        if not self.is_popped_out:
            self.pop_out()
        else:
            self.pop_back_in()
            
    def pop_out(self):
        """彈出為獨立視窗"""
        if self.parent_mdi and not self.is_popped_out and self.content_widget:
            # 保存原始widget
            self.original_widget = self.content_widget
            
            # 創建可調整大小的獨立視窗
            self.standalone_window = ResizableStandaloneWindow()
            self.standalone_window.setWindowTitle(f"[獨立] {self.windowTitle()}")
            self.standalone_window.setObjectName("StandaloneWindow")
            self.standalone_window.setCentralWidget(self.original_widget)
            self.standalone_window.resize(800, 600)  # 調整預設大小更大
            
            # 設置視窗最小大小
            self.standalone_window.setMinimumSize(400, 300)
            
            # 添加返回按鈕
            toolbar = self.standalone_window.addToolBar("控制")
            toolbar.setObjectName("StandaloneToolbar")
            return_action = toolbar.addAction("⌂ 返回主畫面")
            return_action.triggered.connect(self.pop_back_in)
            
            self.standalone_window.show()
            
            # 在MDI中隱藏
            self.hide()
            self.is_popped_out = True
            self.title_bar.popout_btn.setText("⌂")
            self.title_bar.popout_btn.setToolTip("返回主畫面")
            
    def pop_back_in(self):
        """返回主畫面"""
        if self.is_popped_out and self.content_widget:
            # 重新包裝widget
            wrapper = QWidget()
            wrapper.setObjectName("SubWindowWrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(0)
            
            # 重新創建可拖拽標題欄
            self.title_bar = DraggableTitleBar(self, self.windowTitle())
            wrapper_layout.addWidget(self.title_bar)
            wrapper_layout.addWidget(self.content_widget)
            
            # 恢復到MDI
            super().setWidget(wrapper)
            
            if hasattr(self, 'standalone_window'):
                self.standalone_window.close()
                delattr(self, 'standalone_window')
            
            # 在MDI中顯示
            self.show()
            self.is_popped_out = False
            self.title_bar.popout_btn.setText("⧉")
            self.title_bar.popout_btn.setToolTip("彈出為獨立視窗")
            
    def show_settings_dialog(self):
        """顯示設定對話框"""
        dialog = WindowSettingsDialog(self)
        dialog.exec_()

class ContextMenuTreeWidget(QTreeWidget):
    """支援右鍵選單的功能樹"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        
    def show_context_menu(self, position):
        """顯示右鍵選單"""
        item = self.itemAt(position)
        if item is None:
            return
            
        # 檢查是否為葉節點（可分析的項目）
        if item.childCount() == 0:
            menu = QMenu(self)
            menu.setObjectName("ContextMenu")
            
            analyze_action = menu.addAction("[ANALYSIS] 分析")
            analyze_action.triggered.connect(lambda: self.analyze_function(item.text(0)))
            
            export_action = menu.addAction("[STATS] 匯出數據")
            export_action.triggered.connect(lambda: self.export_function(item.text(0)))
            
            menu.addSeparator()
            
            help_action = menu.addAction("❓ 說明")
            help_action.triggered.connect(lambda: self.show_help(item.text(0)))
            
            menu.exec_(self.mapToGlobal(position))
    
    def analyze_function(self, function_name):
        #print(f"[分析] 執行功能: {function_name}")
        
        if self.main_window:
            # 創建新的分析視窗並添加到當前活動的分頁中
            self.main_window.create_analysis_window(function_name)
        
    def export_function(self, function_name):
        #print(f"[匯出] 匯出功能數據: {function_name}")
        pass
        
    def show_help(self, function_name):
        #print(f"[說明] 顯示功能說明: {function_name}")
        pass

class ResizableStandaloneWindow(QMainWindow):
    """可調整大小的獨立視窗"""
    
    def __init__(self):
        super().__init__()
        self.setMouseTracking(True)
        self.resize_margin = 10  # 調整邊框的寬度
        self.resizing = False
        self.resize_direction = None
        
        # 創建可視的調整邊框
        self.setStyleSheet("""
            QMainWindow {
                border: 2px solid #555555;
                background-color: #000000;
            }
            QMainWindow:hover {
                border: 2px solid #777777;
            }
        """)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
            
        # 更新游標
        direction = self.get_resize_direction(event.pos())
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                self.setCursor(Qt.SizeVerCursor)
            elif direction in ['left', 'right']:
                self.setCursor(Qt.SizeHorCursor)
            elif direction in ['bottom-right']:  # 移除 top-left
                self.setCursor(Qt.SizeFDiagCursor)
            elif direction in ['bottom-left']:  # 移除 top-right
                self.setCursor(Qt.SizeBDiagCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 (取消上方調整) - ResizableStandaloneWindow"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        margin = self.resize_margin
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= margin and y <= margin:
        #     return 'top-left'
        # elif x >= w - margin and y <= margin:
        #     return 'top-right'
        if x <= margin and y >= h - margin:
            return 'bottom-left'
        elif x >= w - margin and y >= h - margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= margin:
        #     return 'top'
        elif y >= h - margin:
            return 'bottom'
        elif x <= margin:
            return 'left'
        elif x >= w - margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom (ResizableStandaloneWindow)
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_size = self.minimumSize()
        if new_width < min_size.width():
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_size.width()
            new_width = min_size.width()
            
        if new_height < min_size.height():
            # 取消 top 調整功能 (ResizableStandaloneWindow)
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_size.height()
            new_height = min_size.height()
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 添加可視邊框提示"""
        super().paintEvent(event)
        
        # 在視窗邊緣繪製調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 右下角調整提示
        corner_size = 15
        corner_color = QColor(100, 100, 100, 150)
        painter.fillRect(
            self.width() - corner_size, 
            self.height() - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製調整線條
        painter.setPen(QPen(QColor(150, 150, 150), 1))
        for i in range(3):
            offset = 3 + i * 3
            painter.drawLine(
                self.width() - offset, self.height() - 3,
                self.width() - 3, self.height() - offset
            )

class WindowSettingsDialog(QDialog):
    """視窗設定對話框"""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.setWindowTitle("視窗設定")
        self.setObjectName("SettingsDialog")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # 設置對話框佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 標題
        title_label = QLabel("[TOOL] 視窗分析設定")
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        # 連動控制區域
        sync_group = QGroupBox("視窗連動控制")
        sync_group.setObjectName("SettingsGroup")
        sync_layout = QVBoxLayout(sync_group)
        
        # 連動控制勾選框
        self.sync_windows_checkbox = QCheckBox("🔗 連動其他視窗 (賽事/賽段/年份同步)")
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        self.sync_windows_checkbox.setChecked(True)
        sync_layout.addWidget(self.sync_windows_checkbox)
        
        layout.addWidget(sync_group)
        
        # 分析參數區域
        params_group = QGroupBox("分析參數")
        params_group.setObjectName("SettingsGroup")
        params_layout = QGridLayout(params_group)
        
        # 年份選擇器
        params_layout.addWidget(QLabel("年份:"), 0, 0)
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems(["2023", "2024", "2025"])
        self.year_combo.setCurrentText("2025")
        params_layout.addWidget(self.year_combo, 0, 1)
        
        # 賽事選擇器
        params_layout.addWidget(QLabel("賽事:"), 1, 0)
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        self.race_combo.addItems([
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", 
            "Miami", "Emilia Romagna", "Monaco", "Canada", "Spain",
            "Austria", "United Kingdom", "Hungary", "Belgium", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "Qatar", "United States",
            "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"
        ])
        self.race_combo.setCurrentText("Japan")
        params_layout.addWidget(self.race_combo, 1, 1)
        
        # 賽段選擇器
        params_layout.addWidget(QLabel("賽段:"), 2, 0)
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "SQ", "R"])
        self.session_combo.setCurrentText("R")
        params_layout.addWidget(self.session_combo, 2, 1)
        
        layout.addWidget(params_group)
        
        layout.addStretch()
        
        # 對話框按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setObjectName("DialogButtonBox")
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
    def accept_settings(self):
        """確認設定"""
        window_title = self.parent_window.windowTitle()
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        sync_windows = self.sync_windows_checkbox.isChecked()
        
        #print(f"[TOOL] [{window_title}] 設定已更新:")
        #print(f"   參數: {year} {race} {session}")
        #print(f"   視窗連動: {'是' if sync_windows else '否'}")
        
        # 應用設定邏輯
        self.apply_settings(year, race, session, sync_windows)
        self.accept()
        
    def apply_settings(self, year, race, session, sync_windows):
        """應用設定到父視窗"""
        # 在這裡實現設定應用邏輯
        if sync_windows:
            # 同步到其他視窗
            self.sync_to_other_windows(year, race, session)
        
        # 更新當前視窗
        self.update_current_window(year, race, session)
        
    def sync_to_other_windows(self, year, race, session):
        """同步參數到其他視窗"""
        window_title = self.parent_window.windowTitle()
        #print(f"[REFRESH] [{window_title}] 同步參數到其他視窗: {year} {race} {session}")
        
    def update_current_window(self, year, race, session):
        """更新當前視窗的分析數據"""
        window_title = self.parent_window.windowTitle()
        #print(f"[REFRESH] [{window_title}] 更新視窗數據: {year} {race} {session}")

class StyleHMainWindow(QMainWindow):
    """風格H: 專業賽車分析工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Professional Racing Analysis Workstation v8.0 - Style H")
        self.setMinimumSize(1600, 900)
        
        # 初始化分析追蹤屬性
        self.active_analysis_tabs = []
        
        self.init_ui()
        self.apply_style_h()
        
    def init_ui(self):
        """初始化用戶界面"""
        # 創建菜單欄
        self.create_professional_menubar()
        
        # 創建工具欄
        self.create_professional_toolbar()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局 - 移除參數面板
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(1, 1, 1, 1)
        main_layout.setSpacing(1)
        
        # 主要分析區域
        analysis_splitter = QSplitter(Qt.Horizontal)
        analysis_splitter.setChildrenCollapsible(False)
        
        # 左側功能樹和系統日誌
        left_panel = self.create_left_panel_with_log()
        analysis_splitter.addWidget(left_panel)
        
        # 中央工作區域 - MDI多視窗
        center_panel = self.create_professional_workspace()
        analysis_splitter.addWidget(center_panel)
        
        # 設置分割比例 - 移除右側面板
        analysis_splitter.setSizes([200, 1400])
        main_layout.addWidget(analysis_splitter)
        
        # 專業狀態列
        self.create_professional_status_bar()
        
    def create_professional_menubar(self):
        """創建專業菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu('檔案')
        file_menu.addAction('開啟會話...', self.open_session)
        file_menu.addAction('儲存工作區', self.save_workspace)
        file_menu.addAction('匯出報告...', self.export_report)
        file_menu.addSeparator()
        file_menu.addAction('離開', self.close)
        
        # 分析菜單
        analysis_menu = menubar.addMenu('分析')
        analysis_menu.addAction('[RAIN] 降雨分析', self.rain_analysis)
        analysis_menu.addSeparator()
        analysis_menu.addAction('圈速分析', self.lap_analysis)
        analysis_menu.addAction('遙測比較', self.telemetry_comparison)
        analysis_menu.addAction('車手比較', self.driver_comparison)
        analysis_menu.addAction('扇區分析', self.sector_analysis)
        
        # 檢視菜單
        view_menu = menubar.addMenu('檢視')
        view_menu.addAction('重新排列視窗', self.tile_windows)
        view_menu.addAction('層疊視窗', self.cascade_windows)
        view_menu.addSeparator()
        view_menu.addAction('最小化所有視窗', self.minimize_all_windows)
        view_menu.addAction('最大化所有視窗', self.maximize_all_windows)
        view_menu.addAction('還原所有視窗', self.restore_all_windows)
        view_menu.addSeparator()
        view_menu.addAction('關閉所有視窗', self.close_all_windows)
        view_menu.addSeparator()
        view_menu.addAction('全螢幕', self.toggle_fullscreen)
        
        # 工具菜單
        tools_menu = menubar.addMenu('工具')
        tools_menu.addAction('數據驗證', self.data_validation)
        tools_menu.addAction('系統設定', self.system_settings)
        tools_menu.addAction('清除日誌', self.clear_log)
        
    def create_professional_toolbar(self):
        """創建專業工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("ProfessionalToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        toolbar.setFixedHeight(24)
        self.addToolBar(toolbar)
        
        # 檔案操作
        toolbar.addAction("[FILES]", self.open_session)
        toolbar.addAction("[SAVE]", self.save_workspace)
        toolbar.addSeparator()
        
        # 參數輸入區域
        toolbar.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("ParameterCombo")
        self.year_combo.addItems(["2024", "2025"])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(50)
        toolbar.addWidget(self.year_combo)
        
        toolbar.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("ParameterCombo")
        self.race_combo.addItems(["Japan", "British", "Monaco", "Silverstone", "Spa", "Monza"])
        self.race_combo.setCurrentText("Japan")
        self.race_combo.setFixedWidth(80)
        toolbar.addWidget(self.race_combo)
        
        toolbar.addWidget(QLabel("賽段:"))
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("ParameterCombo")
        self.session_combo.addItems(["R", "Q", "P1", "P2", "P3", "S#print"])
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        toolbar.addWidget(self.session_combo)
        
        toolbar.addSeparator()
        
        # 分析工具
        toolbar.addAction("[FINISH]", self.lap_analysis)
        toolbar.addAction("[CHART]", self.telemetry_comparison)
        toolbar.addAction("[FAST]", self.driver_comparison)
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction("⊞", self.tile_windows)
        toolbar.addAction("⧉", self.cascade_windows)
        
    def create_left_panel_with_log(self):
        """創建左側面板包含功能樹和系統日誌"""
        widget = QWidget()
        widget.setObjectName("LeftPanel")  # 添加對象名稱
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        
        # 功能樹 - 設置拉伸因子
        function_tree = self.create_professional_function_tree()
        layout.addWidget(function_tree, 3)  # 拉伸因子3 (佔大部分空間)
        
        # 系統日誌 (放在左下角) - 設置拉伸因子
        log_frame = QFrame()
        log_frame.setObjectName("LogFrame")
        log_frame.setMaximumHeight(110)  # 限制最大高度
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(2, 2, 2, 2)
        log_layout.setSpacing(1)
        
        log_title = QLabel("系統日誌")
        log_title.setObjectName("LogTitle")
        log_title.setFixedHeight(12)  # 固定高度12像素
        log_layout.addWidget(log_title)
        
        system_log = SystemLogWidget()
        log_layout.addWidget(system_log)
        
        layout.addWidget(log_frame, 0)  # 拉伸因子0 (固定大小)
        
        return widget
        
    def create_professional_function_tree(self):
        """創建專業功能樹"""
        widget = QWidget()
        widget.setObjectName("FunctionTreeWidget")  # 添加對象名稱
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.setSpacing(1)
        
        # 標題
        title_frame = QFrame()
        title_frame.setObjectName("FunctionTreeTitle")
        title_frame.setFixedHeight(16)
        title_layout = QHBoxLayout(title_frame)
        title_layout.setContentsMargins(2, 1, 2, 1)
        title_layout.addWidget(QLabel("分析模組"))
        layout.addWidget(title_frame)
        
        # 支援右鍵選單的功能樹
        tree = ContextMenuTreeWidget(self)
        tree.setObjectName("ProfessionalFunctionTree")
        tree.setHeaderHidden(True)
        tree.setIndentation(8)
        tree.setRootIsDecorated(True)
        
        # 基礎分析模組
        basic_group = QTreeWidgetItem(tree, ["[FINISH] 基礎分析"])
        basic_group.setExpanded(True)
        QTreeWidgetItem(basic_group, ["降雨分析"])
        QTreeWidgetItem(basic_group, ["賽道分析"])
        QTreeWidgetItem(basic_group, ["進站分析"])
        QTreeWidgetItem(basic_group, ["事故分析"])
        
        # 單車手分析模組
        single_group = QTreeWidgetItem(tree, ["🚗 單車手分析"])
        single_group.setExpanded(True)
        QTreeWidgetItem(single_group, ["遙測分析"])
        QTreeWidgetItem(single_group, ["圈速分析"])
        QTreeWidgetItem(single_group, ["超車分析"])
        QTreeWidgetItem(single_group, ["DNF分析"])
        QTreeWidgetItem(single_group, ["彎道分析"])
        
        # 比較分析模組
        compare_group = QTreeWidgetItem(tree, ["[FAST] 比較分析"])
        compare_group.setExpanded(True)
        QTreeWidgetItem(compare_group, ["車手比較"])
        QTreeWidgetItem(compare_group, ["圈速比較"])
        QTreeWidgetItem(compare_group, ["遙測比較"])
        QTreeWidgetItem(compare_group, ["扇區比較"])
        
        # 進階分析模組
        advanced_group = QTreeWidgetItem(tree, ["[ANALYSIS] 進階分析"])
        QTreeWidgetItem(advanced_group, ["輪胎分析"])
        QTreeWidgetItem(advanced_group, ["燃料分析"])
        QTreeWidgetItem(advanced_group, ["策略分析"])
        QTreeWidgetItem(advanced_group, ["氣象分析"])
        
        layout.addWidget(tree)
        
        return widget
        
    def create_professional_workspace(self):
        """創建專業工作區 - 分頁式界面"""
        # 創建主容器
        main_container = QWidget()
        main_container.setObjectName("MainTabContainer")
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 創建分頁容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("ProfessionalTabWidget")
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabsClosable(True)  # 啟用分頁關閉按鈕
        
        # 連接分頁關閉信號
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        
        # 創建分頁右側控制按鈕容器
        tab_buttons_container = QWidget()
        tab_buttons_container.setObjectName("TabButtonsContainer")
        tab_buttons_layout = QHBoxLayout(tab_buttons_container)
        tab_buttons_layout.setContentsMargins(2, 2, 2, 2)
        tab_buttons_layout.setSpacing(2)
        
        # 新增分頁按鈕
        add_tab_btn = QPushButton("+")
        add_tab_btn.setObjectName("AddTabButton")
        add_tab_btn.setFixedSize(25, 25)
        add_tab_btn.setToolTip("新增分頁")
        add_tab_btn.clicked.connect(self.add_new_tab)
        tab_buttons_layout.addWidget(add_tab_btn)
        
        # 關閉當前分頁按鈕
        close_tab_btn = QPushButton("X")
        close_tab_btn.setObjectName("CloseTabButton")
        close_tab_btn.setFixedSize(25, 25)
        close_tab_btn.setToolTip("關閉當前分頁")
        close_tab_btn.clicked.connect(self.close_current_tab)
        tab_buttons_layout.addWidget(close_tab_btn)
        
        # 將按鈕容器設置為分頁小部件的右上角
        self.tab_widget.setCornerWidget(tab_buttons_container, Qt.TopRightCorner)
        
        # 隱藏的分頁數量標籤（保留以避免錯誤）
        self.tab_count_label = QLabel("分頁: 0")
        self.tab_count_label.setObjectName("TabCountLabel")
        self.tab_count_label.hide()  # 完全隱藏
        
        # 直接將分頁容器添加到主佈局
        main_layout.addWidget(self.tab_widget)
        
        # 初始化預設分頁
        self.init_default_tabs()
        
        return main_container
        
    def init_default_tabs(self):
        """初始化預設分頁 - 顯示歡迎畫面"""
        # 創建歡迎畫面作為預設主頁
        welcome_tab = self.create_welcome_tab()
        self.tab_widget.addTab(welcome_tab, "� 歡迎")
        
        self.update_tab_count()
        
    def add_new_tab(self):
        """新增分頁"""
        # 獲取當前分頁數量以生成新的標題
        count = self.tab_widget.count() + 1
        tab_types = [
            ("[CHART] 遙測分析", self.create_telemetry_analysis_tab),
            ("[FINISH] 圈速比較", self.create_laptime_comparison_tab),
            ("🗺️ 賽道分析", self.create_track_analysis_tab),
            ("[STATS] 數據總覽", self.create_data_overview_tab)
        ]
        
        # 輪流創建不同類型的分頁
        tab_type_index = (count - 1) % len(tab_types)
        tab_name, tab_creator = tab_types[tab_type_index]
        
        new_tab = tab_creator()
        self.tab_widget.addTab(new_tab, f"{tab_name} #{count}")
        self.tab_widget.setCurrentIndex(self.tab_widget.count() - 1)
        self.update_tab_count()
        
    def close_tab(self, index):
        """關閉指定索引的分頁"""
        # 檢查是否為歡迎分頁（索引0）
        if index == 0:
            #print("[INFO] 歡迎分頁無法關閉")
            return
            
        if self.tab_widget.count() > 1:  # 保留至少一個分頁
            self.tab_widget.removeTab(index)
            self.update_tab_count()
        
    def close_current_tab(self):
        """關閉當前分頁"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
            
    def update_tab_count(self):
        """更新分頁數量顯示"""
        count = self.tab_widget.count()
        self.tab_count_label.setText(f"分頁: {count}")
    
    def force_black_background(self, mdi_area):
        """深度修復QMdiArea灰底問題"""
        #print(f"[DESIGN] DEBUG: force_black_background called for {mdi_area.objectName()}")
        
        # 方法1: 設置調色板
        mdi_area.setAutoFillBackground(True)
        palette = mdi_area.palette()
        palette.setColor(QPalette.Background, QColor(0, 0, 0))
        palette.setColor(QPalette.Base, QColor(0, 0, 0))
        palette.setColor(QPalette.Window, QColor(0, 0, 0))
        palette.setColor(QPalette.AlternateBase, QColor(0, 0, 0))
        mdi_area.setPalette(palette)
        #print(f"[OK] Palette set for {mdi_area.objectName()}")
        
        # 方法2: 直接設置背景畫筆
        mdi_area.setBackground(QBrush(QColor(0, 0, 0)))
        #print(f"[OK] Background brush set for {mdi_area.objectName()}")
        
        # 方法3: 設置viewport背景（QMdiArea內部使用QScrollArea）
        def fix_viewport():
            try:
                #print(f"[TOOL] Fixing viewport for {mdi_area.objectName()}")
                # 查找內部的viewport小部件
                child_count = 0
                for child in mdi_area.findChildren(QWidget):
                    if hasattr(child, 'setAutoFillBackground'):
                        child.setAutoFillBackground(True)
                        child_palette = child.palette()
                        child_palette.setColor(QPalette.Background, QColor(0, 0, 0))
                        child_palette.setColor(QPalette.Base, QColor(0, 0, 0))
                        child_palette.setColor(QPalette.Window, QColor(0, 0, 0))
                        child.setPalette(child_palette)
                        child_count += 1
                        
                #print(f"[PACKAGE] Fixed {child_count} child widgets")
                        
                # 特別處理viewport
                if hasattr(mdi_area, 'viewport'):
                    viewport = mdi_area.viewport()
                    if viewport:
                        viewport.setAutoFillBackground(True)
                        viewport_palette = viewport.palette()
                        viewport_palette.setColor(QPalette.Background, QColor(0, 0, 0))
                        viewport_palette.setColor(QPalette.Base, QColor(0, 0, 0))
                        viewport_palette.setColor(QPalette.Window, QColor(0, 0, 0))
                        viewport.setPalette(viewport_palette)
                        
                # 強制重繪整個MDI區域
                mdi_area.repaint()
            except:
                pass  # 忽略任何錯誤，繼續其他修復方法
        
        # 延遲執行viewport修復（等MDI完全初始化）
        QTimer.singleShot(100, fix_viewport)
        QTimer.singleShot(200, fix_viewport)  # 再次執行確保修復
        
        # 方法4: 強制內聯樣式
        mdi_area.setStyleSheet(f"""
            QMdiArea#{mdi_area.objectName()} {{
                background-color: #000000 !important;
                background: #000000 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea {{
                background-color: #000000 !important;
                background: #000000 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea QWidget {{
                background-color: #000000 !important;
                background: #000000 !important;
            }}
            QMdiArea#{mdi_area.objectName()} > QWidget {{
                background-color: #000000 !important;
                background: #000000 !important;
            }}
        """)
        
        # 方法5: 創建黑色背景小部件覆蓋（終極方案）
        def create_black_overlay():
            try:
                # 創建一個黑色背景小部件作為底層
                overlay = QWidget(mdi_area)
                overlay.setStyleSheet("background-color: #000000;")
                overlay.setGeometry(mdi_area.rect())
                overlay.lower()  # 放到最底層
                overlay.show()
                
                # 連接resize事件，確保覆蓋層始終填滿MDI區域
                def resize_overlay():
                    if overlay and not overlay.isHidden():
                        overlay.setGeometry(mdi_area.rect())
                
                mdi_area.resizeEvent = lambda event: (
                    QMdiArea.resizeEvent(mdi_area, event),
                    resize_overlay()
                )[-1]
                
            except:
                pass
        
        # 延遲創建覆蓋層
        QTimer.singleShot(300, create_black_overlay)
        
    def create_welcome_tab(self):
        """創建歡迎畫面分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #222;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        title_label = QLabel("[FINISH] 主頁面")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 重置按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border: 1px solid #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 添加工具欄到主布局
        tab_layout.addWidget(toolbar)
        
        # 創建歡迎內容區域和MDI區域的分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 歡迎內容區域
        welcome_widget = QWidget()
        welcome_widget.setFixedHeight(300)  # 固定高度
        welcome_widget.setStyleSheet("""
            QWidget {
                background-color: #000000;
                border-bottom: 1px solid #333333;
            }
        """)
        
        welcome_layout = QVBoxLayout(welcome_widget)
        welcome_layout.setContentsMargins(50, 30, 50, 30)
        welcome_layout.setSpacing(20)
        
        # 主標題
        title_label = QLabel("[FINISH] F1T 專業賽車分析工作站")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #FFFFFF;
                font-size: 24px;
                font-weight: bold;
                background: transparent;
            }
        """)
        welcome_layout.addWidget(title_label)
        
        # 副標題
        subtitle_label = QLabel("專業級 F1 數據分析平台")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #CCCCCC;
                font-size: 14px;
                background: transparent;
            }
        """)
        welcome_layout.addWidget(subtitle_label)
        
        # 歡迎信息
        info_label = QLabel("請使用左側功能樹開啟所需的分析模組 • 支援多視窗同時分析 • Version 13.0")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("""
            QLabel {
                color: #AAAAAA;
                font-size: 12px;
                background: transparent;
                padding: 15px;
                border: 1px solid #333333;
                border-radius: 6px;
            }
        """)
        welcome_layout.addWidget(info_label)
        
        # 創建MDI工作區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("WelcomeMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 強制設置黑色背景
        self.force_black_background(mdi_area)
        
        # 連接重置按鈕到重置功能
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 將歡迎區域和MDI區域添加到分割器
        splitter.addWidget(welcome_widget)
        splitter.addWidget(mdi_area)
        splitter.setSizes([300, 600])  # 歡迎區域300px，MDI區域600px
        
        tab_layout.addWidget(splitter)
        return tab_container
        
    def create_data_overview_tab(self):
        """創建數據總覽分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border-color: #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[STATS] 數據總覽")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("OverviewMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 深度修復灰底問題 - 多層次設置
        self.force_black_background(mdi_area)
        
        # 添加統計視窗
        stats_window = PopoutSubWindow("統計數據", mdi_area)
        stats_content = QLabel("[CHART] 賽季統計數據\n• 總圈數: 1,247\n• 平均圈速: 1:18.456\n• 最快圈速: 1:16.123")
        stats_content.setObjectName("StatsContent")
        stats_window.setWidget(stats_content)
        stats_window.resize(300, 200)  # 改為resize，允許調整大小
        mdi_area.addSubWindow(stats_window)
        stats_window.move(10, 10)
        stats_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_telemetry_analysis_tab(self):
        """創建遙測分析分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border-color: #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[CHART] 遙測分析")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("ProfessionalMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 深度修復灰底問題 - 多層次設置
        self.force_black_background(mdi_area)
        
        # 1. 速度遙測曲線視窗 - 使用新的彈出式視窗
        speed_window = PopoutSubWindow("速度遙測 - VER vs LEC", mdi_area)
        speed_chart = TelemetryChartWidget("speed")
        speed_window.setWidget(speed_chart)
        speed_window.resize(500, 250)  # 改為resize
        mdi_area.addSubWindow(speed_window)
        #print(f"🏠 DEBUG: speed_window added to MDI, parent: {speed_window.parent()}")
        #print(f"[DESIGN] MDI QSS length after addSubWindow: {len(mdi_area.styleSheet())}")
        #print(f"[DESIGN] speed_window QSS length after addSubWindow: {len(speed_window.styleSheet())}")
        speed_window.move(10, 10)
        speed_window.show()
        
        # 2. 煞車遙測曲線視窗
        brake_window = PopoutSubWindow("煞車壓力 - 遙測分析", mdi_area)
        brake_chart = TelemetryChartWidget("brake")
        brake_window.setWidget(brake_chart)
        brake_window.resize(500, 250)  # 改為resize
        mdi_area.addSubWindow(brake_window)
        brake_window.move(520, 10)
        brake_window.show()
        
        # 3. 節流閥遙測曲線視窗
        throttle_window = PopoutSubWindow("節流閥位置 - 油門控制", mdi_area)
        throttle_chart = TelemetryChartWidget("throttle")
        throttle_window.setWidget(throttle_chart)
        throttle_window.resize(400, 180)  # 改為resize
        mdi_area.addSubWindow(throttle_window)
        throttle_window.move(10, 270)
        throttle_window.show()
        
        # 4. 方向盤角度曲線視窗
        steering_window = PopoutSubWindow("方向盤角度 - 轉向分析", mdi_area)
        steering_chart = TelemetryChartWidget("steering")
        steering_window.setWidget(steering_chart)
        steering_window.resize(400, 180)  # 改為resize
        mdi_area.addSubWindow(steering_window)
        steering_window.move(520, 270)
        steering_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_laptime_comparison_tab(self):
        """創建圈速比較分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border-color: #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[FINISH] 圈速比較")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("ProfessionalMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 圈速分析表格視窗
        lap_window = PopoutSubWindow("圈速分析 - 前10名", mdi_area)
        lap_content = self.create_lap_analysis_table()
        lap_window.setWidget(lap_content)
        lap_window.resize(500, 350)  # 改為resize
        mdi_area.addSubWindow(lap_window)
        lap_window.move(10, 10)
        lap_window.show()
        
        # 扇區比較圖表
        sector_window = PopoutSubWindow("扇區比較 - VER vs LEC", mdi_area)
        sector_chart = TelemetryChartWidget("speed")  # 重用遙測圖表
        sector_window.setWidget(sector_chart)
        sector_window.resize(500, 300)  # 改為resize
        mdi_area.addSubWindow(sector_window)
        sector_window.move(520, 10)
        sector_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_track_analysis_tab(self):
        """創建賽道分析分頁"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border-color: #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("🗺️ 賽道分析")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("ProfessionalMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 賽道地圖視窗
        track_window = PopoutSubWindow("賽道地圖 - Suzuka Circuit", mdi_area)
        track_map = TrackMapWidget()
        track_window.setWidget(track_map)
        track_window.resize(400, 300)  # 改為resize
        mdi_area.addSubWindow(track_window)
        track_window.move(10, 10)
        track_window.show()
        
        # 彎道分析視窗
        corner_window = PopoutSubWindow("彎道分析 - 速度分布", mdi_area)
        corner_chart = TelemetryChartWidget("brake")  # 重用遙測圖表
        corner_window.setWidget(corner_chart)
        corner_window.resize(400, 250)  # 改為resize
        mdi_area.addSubWindow(corner_window)
        corner_window.move(420, 10)
        corner_window.show()
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_lap_analysis_table(self):
        """創建圈速分析表格"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(1)
        
        table = QTableWidget(10, 4)
        table.setObjectName("ProfessionalDataTable")
        table.setHorizontalHeaderLabels(["位置", "車手", "最佳圈速", "差距"])
        table.verticalHeader().setVisible(False)
        
        # 圈速分析數據
        data = [
            ("1", "VER", "1:29.347", "-"),
            ("2", "LEC", "1:29.534", "+0.187"),
            ("3", "HAM", "1:29.678", "+0.331"),
            ("4", "RUS", "1:29.892", "+0.545"),
            ("5", "NOR", "1:30.125", "+0.778"),
            ("6", "PIA", "1:30.234", "+0.887"),
            ("7", "SAI", "1:30.456", "+1.109"),
            ("8", "ALO", "1:30.567", "+1.220"),
            ("9", "OCO", "1:30.789", "+1.442"),
            ("10", "GAS", "1:30.912", "+1.565")
        ]
        
        for row, (pos, driver, time, gap) in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(pos))
            table.setItem(row, 1, QTableWidgetItem(driver))
            table.setItem(row, 2, QTableWidgetItem(time))
            table.setItem(row, 3, QTableWidgetItem(gap))
            
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        return widget
        
    def create_professional_status_bar(self):
        """創建專業狀態列"""
        status_bar = QStatusBar()
        status_bar.setFixedHeight(16)
        self.setStatusBar(status_bar)
        
        # 狀態指示
        ready_label = QLabel("🟢 READY")
        ready_label.setObjectName("StatusReady")
        
        session_label = QLabel("[STATS] Japan 2025 Race")
        drivers_label = QLabel("[FINISH] VER vs LEC")
        time_label = QLabel("⏱️ 13:28:51")
        
        status_bar.addWidget(ready_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(session_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(drivers_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(time_label)
        
        # 右側版本信息
        version_label = QLabel("F1T Professional v8.0")
        version_label.setObjectName("VersionInfo")
        status_bar.addPermanentWidget(version_label)
        
        # 更新狀態列以顯示當前參數
        self.update_status_bar()
        
    def update_status_bar(self):
        """更新狀態列以顯示當前參數"""
        if hasattr(self, 'year_combo') and hasattr(self, 'race_combo') and hasattr(self, 'session_combo'):
            year = self.year_combo.currentText()
            race = self.race_combo.currentText()
            session = self.session_combo.currentText()
            
            # 更新狀態列中的會話信息
            self.findChild(QLabel).setText(f"[STATS] {race} {year} {session}")
            
    def get_current_parameters(self):
        """獲取當前參數設定"""
        return {
            'year': self.year_combo.currentText() if hasattr(self, 'year_combo') else '2025',
            'race': self.race_combo.currentText() if hasattr(self, 'race_combo') else 'Japan',
            'session': self.session_combo.currentText() if hasattr(self, 'session_combo') else 'R'
        }
        
    def check_and_remove_welcome_page(self):
        """檢查並移除歡迎頁面，創建新的分析分頁"""
        # 檢查第一個分頁是否為歡迎頁面
        if self.tab_widget.count() > 0:
            first_tab_text = self.tab_widget.tabText(0)
            if "歡迎" in first_tab_text:
                #print("[REFRESH] 首次使用分析功能，移除歡迎頁面並創建新分頁")
                
                # 移除歡迎分頁
                self.tab_widget.removeTab(0)
                
                # 創建新的空白分析分頁
                analysis_tab = self.create_empty_analysis_tab()
                self.tab_widget.addTab(analysis_tab, "[CHART] 分析工作區")
                self.tab_widget.setCurrentIndex(0)
                
                # 更新分頁計數
                self.update_tab_count()
                
                #print("[OK] 已創建新的分析工作區")
                
    def create_empty_analysis_tab(self):
        """創建空白的分析分頁，只包含MDI區域"""
        # 創建主容器
        tab_container = QWidget()
        tab_layout = QVBoxLayout(tab_container)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # 創建工具欄
        toolbar = QWidget()
        toolbar.setFixedHeight(35)
        toolbar.setStyleSheet("""
            QWidget {
                background: #1a1a1a;
                border-bottom: 1px solid #333;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        title_label = QLabel("[CHART] 分析工作區")
        title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("[REFRESH] 顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #444;
                border-color: #666;
            }
            QPushButton:pressed {
                background: #222;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建空白的MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("AnalysisMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 強制設置黑色背景
        self.force_black_background(mdi_area)
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_analysis_window(self, function_name):
        """為功能樹的分析項目創建新視窗"""
        # 檢查是否為首次使用分析功能
        self.check_and_remove_welcome_page()
        
        # 獲取當前活動的分頁
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
            
        if mdi_area is None:
            #print(f"[警告] 無法找到MDI區域來添加視窗: {function_name}")
            return
        
        # 根據功能名稱創建相應的分析視窗
        window_title = f"{function_name} - 分析"
        
        # 創建新的分析視窗
        analysis_window = PopoutSubWindow(window_title, mdi_area)
        
        # 根據功能類型創建相應的內容
        if "降雨分析" in function_name:
            # 使用新的雨量分析模組 (通用圖表系統)
            try:
                from modules.gui.rain_analysis_module import RainAnalysisModule
                params = self.get_current_parameters()
                content = RainAnalysisModule(
                    year=params['year'],
                    race=params['race'],
                    session=params['session']
                )
                print(f"[OK] 已載入降雨分析模組 (通用圖表) - {params['year']} {params['race']} {params['session']}")
                
            except ImportError as e:
                print(f"[ERROR] 降雨分析模組導入失敗: {e}")
                content = TelemetryChartWidget("speed")  # 後備方案
        elif "遙測" in function_name:
            content = TelemetryChartWidget("speed")
        elif "煞車" in function_name or "制動" in function_name:
            content = TelemetryChartWidget("brake")
        elif "油門" in function_name or "節流" in function_name:
            content = TelemetryChartWidget("throttle")
        elif "轉向" in function_name or "方向盤" in function_name:
            content = TelemetryChartWidget("steering")
        elif "賽道" in function_name:
            content = TrackMapWidget()
        elif "圈速" in function_name:
            content = self.create_lap_analysis_table()
        else:
            # 預設創建速度遙測圖表
            content = TelemetryChartWidget("speed")
        
        analysis_window.setWidget(content)
        
        # 根據功能類型設置視窗大小
        if "降雨分析" in function_name:
            analysis_window.resize(800, 600)  # 降雨分析需要較大的視窗來顯示雙Y軸圖表
        else:
            analysis_window.resize(450, 280)  # 其他分析使用預設大小
        
        # 添加到MDI區域
        mdi_area.addSubWindow(analysis_window)
        
        # 計算新視窗位置（避免重疊）
        existing_windows = mdi_area.subWindowList()
        window_count = len(existing_windows)
        
        # 使用階梯式排列
        offset_x = (window_count % 4) * 30
        offset_y = (window_count // 4) * 30
        base_x = 10 + offset_x
        base_y = 10 + offset_y
        
        analysis_window.move(base_x, base_y)
        analysis_window.show()
        
        #print(f"[分析] 已創建視窗: {window_title} 位置: ({base_x}, {base_y})")
        
    def reset_all_charts(self, mdi_area):
        """重置MDI區域中所有圖表以顯示完整數據範圍"""
        try:
            print(f"[REFRESH] 開始調整 MDI 區域中的所有圖表以顯示完整數據...")
            
            # 獲取所有子視窗
            subwindows = mdi_area.subWindowList()
            reset_count = 0
            
            print(f"[STATS] MDI區域中共有 {len(subwindows)} 個子視窗")
            
            def find_telemetry_widgets(widget):
                """遞歸查找 TelemetryChartWidget"""
                telemetry_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, TelemetryChartWidget):
                    telemetry_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            telemetry_widgets.extend(find_telemetry_widgets(child))
                
                return telemetry_widgets
            
            def find_universal_chart_widgets(widget):
                """遞歸查找 UniversalChartWidget"""
                from modules.gui.universal_chart_widget import UniversalChartWidget
                universal_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, UniversalChartWidget):
                    universal_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            universal_widgets.extend(find_universal_chart_widgets(child))
                
                return universal_widgets
            
            for i, subwindow in enumerate(subwindows):
                if subwindow and subwindow.widget():
                    widget = subwindow.widget()
                    widget_type = type(widget).__name__
                    print(f"[SEARCH] 檢查視窗 {i+1}: {widget_type}")
                    
                    # 遞歸查找所有 TelemetryChartWidget
                    telemetry_widgets = find_telemetry_widgets(widget)
                    # 遞歸查找所有 UniversalChartWidget
                    universal_widgets = find_universal_chart_widgets(widget)
                    
                    print(f"  找到 {len(telemetry_widgets)} 個遙測圖表, {len(universal_widgets)} 個通用圖表")
                    
                    if telemetry_widgets:
                        for telemetry_widget in telemetry_widgets:
                            #print(f"[TARGET] 調整遙測圖表以顯示完整數據: {telemetry_widget.chart_type}")
                            
                            # 獲取圖表的實際尺寸
                            chart_width = telemetry_widget.width()
                            chart_height = telemetry_widget.height()
                            
                            if chart_width > 0 and chart_height > 0:
                                # [SEARCH] 根據實際數據範圍動態計算最佳縮放比例
                                
                                # 獲取實際數據範圍
                                x_data = getattr(telemetry_widget, 'x_data', None)
                                y_data = getattr(telemetry_widget, 'y_data', None)
                                
                                if x_data is not None and y_data is not None and len(x_data) > 0 and len(y_data) > 0:
                                    # 計算數據的實際範圍
                                    x_min, x_max = min(x_data), max(x_data)
                                    y_min, y_max = min(y_data), max(y_data)
                                    
                                    x_range = x_max - x_min if x_max != x_min else 1.0
                                    y_range = y_max - y_min if y_max != y_min else 1.0
                                    
                                    # 計算縮放比例，讓數據填滿90%的視窗空間
                                    # 假設視窗的基礎顯示範圍是 X: 0-100, Y: 0-100
                                    base_x_range = 100.0
                                    base_y_range = 100.0
                                    
                                    # 計算縮放比例
                                    optimal_x_scale = (base_x_range * 0.9) / x_range
                                    optimal_y_scale = (base_y_range * 0.9) / y_range
                                    
                                    # 限制縮放範圍，避免過度縮放
                                    optimal_x_scale = max(0.1, min(20.0, optimal_x_scale))
                                    optimal_y_scale = max(0.1, min(20.0, optimal_y_scale))
                                    
                                    # 計算偏移，讓數據居中顯示
                                    data_center_x = (x_min + x_max) / 2
                                    data_center_y = (y_min + y_max) / 2
                                    
                                    # 將數據中心移到視窗中心 (50, 50)
                                    optimal_x_offset = 50.0 - (data_center_x * optimal_x_scale)
                                    optimal_y_offset = 50.0 - (data_center_y * optimal_y_scale)
                                    
                                    # 應用計算出的縮放和偏移
                                    telemetry_widget.x_scale = optimal_x_scale
                                    telemetry_widget.y_scale = optimal_y_scale
                                    telemetry_widget.x_offset = optimal_x_offset
                                    telemetry_widget.y_offset = optimal_y_offset
                                    
                                    #print(f"[STATS] 數據範圍分析 {telemetry_widget.chart_type}:")
                                    #print(f"   X範圍: {x_min:.2f} ~ {x_max:.2f} (差值: {x_range:.2f})")
                                    #print(f"   Y範圍: {y_min:.2f} ~ {y_max:.2f} (差值: {y_range:.2f})")
                                    #print(f"   最佳縮放: X={optimal_x_scale:.2f}, Y={optimal_y_scale:.2f}")
                                    #print(f"   居中偏移: X={optimal_x_offset:.2f}, Y={optimal_y_offset:.2f}")
                                    
                                else:
                                    # 如果沒有數據，使用預設值
                                    telemetry_widget.x_scale = 1.0
                                    telemetry_widget.y_scale = 1.0
                                    telemetry_widget.x_offset = 0.0
                                    telemetry_widget.y_offset = 0.0
                                    #print(f"[WARNING] 無法獲取 {telemetry_widget.chart_type} 的數據範圍，使用預設縮放")
                                
                                # 重置拖拽狀態
                                telemetry_widget.is_dragging = False
                                telemetry_widget.last_mouse_pos = None
                                
                                # 重新繪製圖表
                                telemetry_widget.update()
                                reset_count += 1
                                
                                #print(f"[OK] 調整完成 {telemetry_widget.chart_type} - X縮放: {telemetry_widget.x_scale:.2f}, Y縮放: {telemetry_widget.y_scale:.2f}, X偏移: {telemetry_widget.x_offset:.1f}, Y偏移: {telemetry_widget.y_offset:.1f}")
                            else:
                                #print(f"[WARNING] 圖表 {telemetry_widget.chart_type} 尺寸無效，跳過調整")
                                pass
                    
                    # 處理通用圖表 (UniversalChartWidget)
                    if universal_widgets:
                        for universal_widget in universal_widgets:
                            print(f"[TARGET] 重置通用圖表: {universal_widget.title}")
                            universal_widget.reset_view()
                            reset_count += 1
                            print(f"[OK] 通用圖表重置完成: {universal_widget.title}")
                    
                    # 檢查是否為其他類型的圖表或可縮放小部件
                    elif hasattr(widget, 'fit_to_view'):
                        # 如果小部件有適合視圖的方法
                        #print(f"[TOOL] 使用 fit_to_view 方法調整: {widget_type}")
                        widget.fit_to_view()
                        reset_count += 1
                        
                    elif hasattr(widget, 'zoom_to_fit'):
                        # 如果小部件有縮放適應方法
                        #print(f"[TOOL] 使用 zoom_to_fit 方法調整: {widget_type}")
                        widget.zoom_to_fit()
                        reset_count += 1
                    else:
                        #print(f"[WARNING] 視窗 {i+1} 中沒有找到可調整的圖表組件")
                        pass
                else:
                    #print(f"[WARNING] 視窗 {i+1} 沒有有效的widget")
                    pass
            
            print(f"[OK] 調整完成！共調整了 {reset_count} 個圖表以顯示完整數據")
            
        except Exception as e:
            print(f"[ERROR] 調整圖表時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    # 事件處理方法
            
    def open_session(self): 
        params = self.get_current_parameters()
        #print(f"[檔案] 開啟會話 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def save_workspace(self): 
        #print("[檔案] 儲存工作區")
        pass
        
    def export_report(self): 
        #print("[檔案] 匯出報告")
        pass
        
    def lap_analysis(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 圈速分析 - {params['year']} {params['race']} {params['session']}")
        pass
    
    def rain_analysis(self):
        """開啟降雨分析 - 使用通用圖表系統"""
        try:
            # 移除歡迎頁面（如果存在）
            self.remove_welcome_tab()
            
            params = self.get_current_parameters()
            print(f"[分析] [RAIN] 降雨分析 - {params['year']} {params['race']} {params['session']}")
            
            # 導入新的雨量分析模組 (使用通用圖表)
            from modules.gui.rain_analysis_module import RainAnalysisModule
            
            # 創建雨量分析模組
            rain_widget = RainAnalysisModule(
                year=params['year'],
                race=params['race'], 
                session=params['session']
            )
            
            # 創建新的分頁標籤
            tab_title = f"[RAIN] 降雨分析 - {params['year']} {params['race']}"
            
            # 添加到主分頁控件
            tab_index = self.tab_widget.addTab(rain_widget, tab_title)
            self.tab_widget.setCurrentIndex(tab_index)
            
            # 添加到活動分頁列表
            self.active_analysis_tabs.append(tab_title)
            
            print(f"[OK] 降雨分析頁面已開啟: {tab_title} (使用通用圖表系統)")
            
        except ImportError as e:
            print(f"[ERROR] 降雨分析組件導入失敗: {e}")
            self.show_error_message("模組錯誤", f"無法載入降雨分析組件: {e}")
        except Exception as e:
            print(f"[ERROR] 降雨分析開啟失敗: {e}")
            import traceback
            traceback.print_exc()
            self.show_error_message("降雨分析錯誤", f"開啟降雨分析時發生錯誤: {e}")
            
    def telemetry_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 遙測比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def driver_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 車手比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def sector_analysis(self): 
        #print("[分析] 扇區分析")
        pass
    def tile_windows(self):
        """重新排列視窗 - 智能平鋪當前活動MDI區域中的所有子視窗"""
        #print("[檢視] 重新排列視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗需要排列")
            return
            
        #print(f"[STATS] 開始重新排列 {len(subwindows)} 個子視窗")
        
        # 計算排列配置
        available_width = mdi_area.width() - 20  # 預留邊距
        available_height = mdi_area.height() - 20
        
        # 計算最佳的行列配置
        num_windows = len(subwindows)
        cols = int(num_windows ** 0.5)
        if cols * cols < num_windows:
            cols += 1
        rows = (num_windows + cols - 1) // cols
        
        # 計算每個視窗的尺寸
        window_width = available_width // cols
        window_height = available_height // rows
        
        # 確保最小尺寸
        min_width, min_height = 250, 150
        window_width = max(window_width, min_width)
        window_height = max(window_height, min_height)
        
        #print(f"📐 排列配置: {rows}行 x {cols}列, 每個視窗尺寸: {window_width}x{window_height}")
        
        # 排列視窗
        for i, subwindow in enumerate(subwindows):
            row = i // cols
            col = i % cols
            
            x = col * window_width + 10
            y = row * window_height + 10
            
            # 設置視窗位置和尺寸
            subwindow.setGeometry(x, y, window_width, window_height)
            
            # 確保視窗可見和正常化
            subwindow.showNormal()
            subwindow.raise_()
            
            #print(f"[TOOL] 視窗 {i+1}: '{subwindow.windowTitle()}' 移動到 ({x}, {y}) 尺寸 {window_width}x{window_height}")
        
        # 刷新MDI區域
        mdi_area.update()
        #print(f"[OK] 成功重新排列 {len(subwindows)} 個視窗")
    def cascade_windows(self):
        """層疊視窗 - 將當前活動MDI區域中的所有子視窗以階梯式排列"""
        #print("[檢視] 層疊視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        
        # 首先檢查當前分頁是否本身就是MDI區域
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            # 否則在分頁的子元件中查找
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗需要層疊")
            return
            
        #print(f"[STATS] 開始層疊排列 {len(subwindows)} 個子視窗")
        
        # 計算層疊參數
        cascade_offset = 30  # 每個視窗的偏移量
        base_width = 500     # 基礎寬度
        base_height = 350    # 基礎高度
        start_x = 20         # 起始X位置
        start_y = 20         # 起始Y位置
        
        # 確保視窗不會超出MDI區域邊界
        max_windows = min(len(subwindows), 
                         (mdi_area.width() - base_width) // cascade_offset + 1,
                         (mdi_area.height() - base_height) // cascade_offset + 1)
        
        #print(f"📐 層疊配置: 偏移量 {cascade_offset}px, 基礎尺寸 {base_width}x{base_height}")
        
        # 層疊排列視窗
        for i, subwindow in enumerate(subwindows):
            # 計算當前視窗的位置（循環使用偏移量）
            offset_multiplier = i % max_windows
            x = start_x + offset_multiplier * cascade_offset
            y = start_y + offset_multiplier * cascade_offset
            
            # 設置視窗位置和尺寸
            subwindow.setGeometry(x, y, base_width, base_height)
            
            # 確保視窗可見和正常化
            subwindow.showNormal()
            subwindow.raise_()
            
            #print(f"[TOOL] 視窗 {i+1}: '{subwindow.windowTitle()}' 層疊到 ({x}, {y}) 尺寸 {base_width}x{base_height}")
        
        # 將最後一個視窗帶到前面
        if subwindows:
            subwindows[-1].activateWindow()
            subwindows[-1].raise_()
        
        # 刷新MDI區域
        mdi_area.update()
        #print(f"[OK] 成功層疊排列 {len(subwindows)} 個視窗")
        
    def minimize_all_windows(self):
        """最小化所有視窗"""
        #print("[檢視] 最小化所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並最小化
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showMinimized()
            count += 1
            #print(f"[TREND] 最小化視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功最小化 {count} 個視窗")
        
    def maximize_all_windows(self):
        """最大化所有視窗"""
        #print("[檢視] 最大化所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並最大化
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showMaximized()
            count += 1
            #print(f"[CHART] 最大化視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功最大化 {count} 個視窗")
        
    def restore_all_windows(self):
        """還原所有視窗到正常狀態"""
        #print("[檢視] 還原所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並還原
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        for subwindow in subwindows:
            subwindow.showNormal()
            count += 1
            #print(f"[REFRESH] 還原視窗: '{subwindow.windowTitle()}'")
            
        #print(f"[OK] 成功還原 {count} 個視窗")
        
    def close_all_windows(self):
        """關閉所有視窗"""
        #print("[檢視] 關閉所有視窗")
        
        # 獲取當前活動的MDI區域
        current_tab = self.tab_widget.currentWidget()
        if current_tab is None:
            #print("[ERROR] 沒有活動的分頁")
            return
            
        # 查找當前分頁中的MDI區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break
                
        if mdi_area is None:
            #print("[ERROR] 當前分頁中沒有找到MDI區域")
            return
            
        # 獲取所有子視窗並關閉
        subwindows = mdi_area.subWindowList()
        if not subwindows:
            #print("[ERROR] MDI區域中沒有子視窗")
            return
            
        count = 0
        # 創建副本列表，因為關閉視窗會修改原列表
        windows_to_close = subwindows.copy()
        for subwindow in windows_to_close:
            title = subwindow.windowTitle()
            subwindow.close()
            count += 1
            #print(f"[ERROR] 關閉視窗: '{title}'")
            
        #print(f"[OK] 成功關閉 {count} 個視窗")
    def toggle_fullscreen(self):
        """切換全螢幕模式"""
        #print("[檢視] 全螢幕切換")
        
        if self.isFullScreen():
            # 退出全螢幕
            self.showNormal()
            #print("🔲 退出全螢幕模式")
        else:
            # 進入全螢幕
            self.showFullScreen()
            #print("🔳 進入全螢幕模式")
            
        # 強制刷新界面
        self.update()
        
    def data_validation(self): 
        #print("[工具] 數據驗證")
        pass
        
    def system_settings(self): 
        #print("[工具] 系統設定")
        pass
        
    def clear_log(self): 
        #print("[工具] 清除日誌")
        # 這裡可以添加清除日誌的邏輯
        pass
        
    def apply_style_h(self):
        """應用風格H樣式 - 專業賽車分析工作站 (純黑底)"""
        style = """
        /* 主視窗 - 純黑底專業主題 */
        QMainWindow {
            background-color: #000000;
            color: #FFFFFF;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 專業黑色 */
        QMenuBar {
            background-color: #000000;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-size: 8pt;
            padding: 1px;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 6px;
            border-radius: 0px;
        }
        QMenuBar::item:selected {
            background-color: #333333;
        }
        QMenu {
            background-color: #000000;
            border: 1px solid #333333;
            color: #FFFFFF;
            padding: 1px;
        }
        QMenu::item {
            padding: 2px 8px;
            border-radius: 0px;
        }
        QMenu::item:selected {
            background-color: #333333;
        }
        
        /* 右鍵選單 */
        #ContextMenu {
            background-color: #000000;
            border: 1px solid #555555;
            color: #FFFFFF;
            padding: 2px;
        }
        #ContextMenu::item {
            padding: 3px 12px;
            border-radius: 0px;
        }
        #ContextMenu::item:selected {
            background-color: #333333;
        }
        
        /* 左側面板強制黑底 */
        #LeftPanel {
            background-color: #000000;
            color: #FFFFFF;
        }
        #FunctionTreeWidget {
            background-color: #000000;
            color: #FFFFFF;
        }
        
        /* 專業工具欄 */
        #ProfessionalToolbar {
            background-color: #000000;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        #ProfessionalToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #FFFFFF;
            font-size: 9pt;
            border-radius: 0px;
        }
        #ProfessionalToolbar QToolButton:hover {
            background-color: #333333;
            border: 1px solid #555555;
        }
        #ProfessionalToolbar QToolButton:pressed {
            background-color: #111111;
        }
        #ProfessionalToolbar QLabel {
            color: #CCCCCC;
            font-size: 7pt;
            padding: 0px 2px;
        }
        
        /* 參數選擇框 */
        #ParameterCombo {
            background-color: #000000;
            border: 1px solid #333333;
            color: #FFFFFF;
            font-size: 7pt;
            padding: 1px 2px;
            border-radius: 0px;
        }
        #ParameterCombo::drop-down {
            border: none;
            background-color: #333333;
            width: 12px;
        }
        #ParameterCombo::down-arrow {
            image: none;
            border-left: 2px solid transparent;
            border-right: 2px solid transparent;
            border-top: 2px solid #FFFFFF;
            width: 0px;
            height: 0px;
        }
        #ParameterCombo QAbstractItemView {
            background-color: #000000;
            border: 1px solid #333333;
            selection-background-color: #333333;
            color: #FFFFFF;
        }
        
        /* 功能樹標題 */
        #FunctionTreeTitle {
            background-color: #000000;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-weight: bold;
        }
        
        /* 專業功能樹 */
        #ProfessionalFunctionTree {
            background-color: #000000;
            border: 1px solid #333333;
            color: #FFFFFF;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #111111;
        }
        #ProfessionalFunctionTree::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        #ProfessionalFunctionTree::item:hover {
            background-color: #111111;
        }
        #ProfessionalFunctionTree::item:selected {
            background-color: #333333;
            color: #FFFFFF;
        }
        
        /* 系統日誌框架 - 強制黑底 */
        #LogFrame {
            background-color: #000000;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        #LogTitle {
            background-color: #000000;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 7pt;
            height: 12px;
            padding: 1px;
        }
        
        /* 系統日誌 - 強制黑底 */
        #SystemLog {
            background-color: #000000;
            border: 1px solid #333333;
            color: #00FF00;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 7pt;
            border-radius: 0px;
            selection-background-color: #333333;
        }
        QTextEdit#SystemLog {
            background-color: #000000;
        }
        QScrollArea QTextEdit#SystemLog {
            background-color: #000000;
        }
        
        /* MDI工作區 - 強制黑底 - 增強版 */
        #ProfessionalMDIArea, #OverviewMDIArea {
            background-color: #000000 !important;
            background: #000000 !important;
            border: 1px solid #333333;
        }
        QMdiArea {
            background-color: #000000 !important;
            background: #000000 !important;
        }
        QMdiArea QScrollArea {
            background-color: #000000 !important;
            background: #000000 !important;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #000000 !important;
            background: #000000 !important;
        }
        QMdiArea > QWidget {
            background-color: #000000 !important;
            background: #000000 !important;
        }
        QMdiArea * {
            background-color: #000000 !important;
        }
        
        /* 分頁控件 - 黑色主題 */
        #ProfessionalTabWidget {
            background-color: #000000;
            border: none;
        }
        #ProfessionalTabWidget::pane {
            background-color: #000000;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        #ProfessionalTabWidget::tab-bar {
            alignment: left;
        }
        #ProfessionalTabWidget QTabBar::tab {
            background-color: #222222;
            color: #CCCCCC;
            padding: 4px 12px;
            margin: 0px 1px;
            border: 1px solid #333333;
            border-bottom: none;
            border-radius: 0px;
            font-size: 8pt;
        }
        #ProfessionalTabWidget QTabBar::tab:selected {
            background-color: #000000;
            color: #FFFFFF;
            border-bottom: 1px solid #000000;
        }
        #ProfessionalTabWidget QTabBar::tab:hover {
            background-color: #333333;
        }
        
        /* 分頁控制區域 */
        #TabControlArea {
            background-color: #000000;
            border-bottom: 1px solid #333333;
        }
        
        /* 分頁按鈕容器 */
        #TabButtonsContainer {
            background-color: #000000;
            border: none;
        }
        
        /* 新增分頁按鈕 */
        #AddTabButton {
            background-color: #000000;
            color: #00FF00;
            border: 1px solid #333333;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #AddTabButton:hover {
            background-color: #111111;
            border-color: #00FF00;
        }
        #AddTabButton:pressed {
            background-color: #222222;
        }
        
        /* 關閉分頁按鈕 */
        #CloseTabButton {
            background-color: #000000;
            color: #FFFFFF;
            border: 1px solid #333333;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #CloseTabButton:hover {
            background-color: #111111;
            border-color: #FFFFFF;
        }
        #CloseTabButton:pressed {
            background-color: #222222;
        }
        
        /* 分頁數量標籤 */
        #TabCountLabel {
            color: #CCCCCC;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 4px 8px;
        }
        
        /* 分析控制面板 */
        #AnalysisControlArea {
            background-color: #000000;
            border-bottom: 1px solid #333333;
            border-top: 1px solid #333333;
        }
        
        /* 連動控制勾選框 */
        #SyncWindowsCheckbox {
            color: #FFFFFF;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncWindowsCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #555555;
            background-color: #000000;
        }
        #SyncWindowsCheckbox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        #SyncWindowsCheckbox::indicator:hover {
            border-color: #777777;
        }
        
        /* 遙測同步勾選框 */
        #SyncTelemetryCheckbox {
            color: #FFFFFF;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncTelemetryCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #555555;
            background-color: #000000;
        }
        #SyncTelemetryCheckbox::indicator:checked {
            background-color: #00AA00;
            border-color: #00AA00;
        }
        #SyncTelemetryCheckbox::indicator:hover {
            border-color: #777777;
        }
        
        /* 控制標籤 */
        #ControlLabel {
            color: #CCCCCC;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
        }
        
        /* 分析下拉選單 */
        #AnalysisComboBox {
            background-color: #222222;
            color: #FFFFFF;
            border: 1px solid #555555;
            border-radius: 0px;
            padding: 3px 8px;
            font-size: 8pt;
            min-width: 80px;
        }
        #AnalysisComboBox::drop-down {
            background-color: #333333;
            border: none;
            width: 20px;
        }
        #AnalysisComboBox::down-arrow {
            border: none;
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #FFFFFF;
        }
        #AnalysisComboBox QAbstractItemView {
            background-color: #222222;
            color: #FFFFFF;
            border: 1px solid #555555;
            selection-background-color: #0078D4;
            font-size: 8pt;
        }
        #AnalysisComboBox:hover {
            border-color: #777777;
        }
        #AnalysisComboBox:focus {
            border-color: #0078D4;
        }
        
        /* 重新分析按鈕 */
        #ReanalyzeButton {
            background-color: #FF6B35;
            color: #FFFFFF;
            border: 1px solid #FF6B35;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #ReanalyzeButton:hover {
            background-color: #E55A2B;
            border-color: #E55A2B;
        }
        #ReanalyzeButton:pressed {
            background-color: #CC4A21;
        }
        
        /* 主分頁容器 */
        #MainTabContainer {
            background-color: #000000;
            border: none;
        }
        
        /* 數據總覽分頁 */
        #DataOverviewTab {
            background-color: #000000;
        }
        #TabTitleLabel {
            color: #FFFFFF;
            font-size: 10pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #OverviewMDIArea {
            background-color: #000000;
            border: 1px solid #333333;
        }
        #StatsContent {
            color: #FFFFFF;
            font-size: 8pt;
            background-color: transparent;
            border: none;
            padding: 10px;
        }
        
        /* 設定對話框 */
        #SettingsDialog {
            background-color: #000000;
            color: #FFFFFF;
            border: 2px solid #333333;
        }
        #DialogTitle {
            color: #FFFFFF;
            font-size: 12pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #SettingsGroup {
            color: #FFFFFF;
            font-size: 9pt;
            font-weight: bold;
            border: 1px solid #444444;
            border-radius: 3px;
            margin-top: 5px;
            padding-top: 5px;
        }
        #SettingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #CCCCCC;
        }
        #DialogButtonBox {
            background-color: transparent;
        }
        #DialogButtonBox QPushButton {
            background-color: #0078D4;
            color: #FFFFFF;
            border: 1px solid #0078D4;
            border-radius: 3px;
            padding: 5px 15px;
            font-size: 9pt;
            min-width: 60px;
        }
        #DialogButtonBox QPushButton:hover {
            background-color: #106EBE;
        }
        #DialogButtonBox QPushButton:pressed {
            background-color: #005A9E;
        }
        
        /* 專業MDI子視窗 - 使用自定義paintEvent繪製邊框 */
        #ProfessionalSubWindow {
            background-color: #000000;
            border: none;  /* 邊框由paintEvent繪製 */
            border-radius: 0px;
        }
        QMdiSubWindow {
            background-color: #000000;
            border: 0.5px solid #FFFFFF;  /* 減少邊框厚度 */
            margin: 0px;  /* 消除外邊距 */
            padding: 0px;  /* 消除內邊距 */
        }
        QMdiSubWindow QWidget {
            margin: 0px;  /* 確保子widget也沒有邊距 */
            padding: 0px;  /* 確保子widget也沒有內邊距 */
        }
        QMdiSubWindow::title {
            background: transparent;
            color: transparent;
            height: 0px;  /* 隱藏標題 */
            padding: 0px;
            margin: 0px;
            border: none;  /* 確保標題本身沒有邊框 */
            font-size: 0pt;
            font-weight: normal;
            min-height: 0px;  /* 強制最小高度為0 */
            max-height: 0px;  /* 強制最大高度為0 */
            subcontrol-position: top left;
            subcontrol-origin: margin;
            position: absolute;
            top: -1000px;  /* 移到螢幕外 */
            left: -1000px;  /* 移到螢幕外 */
        }
        }
        QMdiSubWindow QWidget {
            border: none;
        }
        
        /* 子視窗包裝器 */
        #SubWindowWrapper {
            background-color: transparent;  /* 改為透明，讓底層調整區域可見 */
            color: #FFFFFF;
            border: none;
        }
        
        /* 視窗控制面板 */
        #WindowControlPanel {
            background-color: #111111;
            border-bottom: 1px solid #333333;
            border-top: 1px solid #333333;
        }
        
        /* 自定義標題欄 */
        #CustomTitleBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #444444;
            border-top: none;
            border-left: none;
            border-right: none;
            color: #000000;
        }
        
        /* 視窗控制按鈕 */
        #WindowControlButton {
            background-color: #F0F0F0;  /* Windows 系統按鈕背景 */
            color: #000000;  /* 黑色文字 */
            border: 1px solid #D0D0D0;  /* 淺灰色邊框 */
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #WindowControlButton:hover {
            background-color: #E0E0E0;  /* 滑鼠懸停時稍深 */
        }
        #WindowControlButton:pressed {
            background-color: #D0D0D0;  /* 按下時更深 */
        }
        
        /* 恢復按鈕 */
        #RestoreButton {
            background-color: #2E8B57;
            color: #FFFFFF;
            border: 1px solid #3CB371;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #RestoreButton:hover {
            background-color: #3CB371;
        }
        #RestoreButton:pressed {
            background-color: #228B22;
        }
        
        /* X軸連動按鈕 */
        #SyncButton {
            background-color: #1E90FF;
            color: #FFFFFF;
            border: 1px solid #4169E1;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SyncButton:hover {
            background-color: #4169E1;
        }
        #SyncButton:pressed {
            background-color: #0000CD;
        }
        #SyncButton:checked {
            background-color: #32CD32;
            border: 1px solid #00FF00;
        }
        #SyncButton:checked:hover {
            background-color: #00FF00;
        }
        
        /* 設定按鈕 */
        #SettingsButton {
            background-color: #555555;
            color: #FFFFFF;
            border: 1px solid #777777;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SettingsButton:hover {
            background-color: #666666;
        }
        #SettingsButton:pressed {
            background-color: #333333;
        }
        
        /* 彈出按鈕 */
        #PopoutButton {
            background-color: #444444;
            color: #FFFFFF;
            border: 1px solid #666666;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #PopoutButton:hover {
            background-color: #555555;
        }
        #PopoutButton:pressed {
            background-color: #222222;
        }
        
        /* 子視窗標題 */
        #SubWindowTitle {
            color: #FFFFFF;
            font-size: 8pt;
            font-weight: bold;
        }
        
        /* 獨立視窗 */
        #StandaloneWindow {
            background-color: #000000;
            color: #FFFFFF;
        }
        #StandaloneToolbar {
            background-color: #000000;
            border-bottom: 1px solid #333333;
            color: #FFFFFF;
            font-size: 8pt;
        }
        #StandaloneToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px 6px;
            color: #FFFFFF;
            border-radius: 0px;
        }
        #StandaloneToolbar QToolButton:hover {
            background-color: #333333;
            border: 1px solid #555555;
        }
        
        /* 遙測圖表 */
        #TelemetryChart {
            background-color: #000000;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        
        /* 賽道地圖 */
        #TrackMap {
            background-color: #000000;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        
        /* 專業數據表格 */
        #ProfessionalDataTable {
            background-color: #000000;
            alternate-background-color: #111111;
            color: #FFFFFF;
            gridline-color: #333333;
            font-size: 8pt;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        #ProfessionalDataTable::item {
            padding: 1px;
            border: none;
        }
        #ProfessionalDataTable::item:selected {
            background-color: #333333;
        }
        #ProfessionalDataTable QHeaderView::section {
            background-color: #000000;
            color: #FFFFFF;
            padding: 1px;
            border: 1px solid #333333;
            font-weight: bold;
            font-size: 8pt;
            border-radius: 0px;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #000000;
            border-top: 1px solid #333333;
            color: #CCCCCC;
            font-size: 8pt;
        }
        #StatusReady {
            color: #00FF00;
            font-weight: bold;
        }
        #VersionInfo {
            color: #0078D4;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #FFFFFF;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #000000;
            width: 6px;
            border: 1px solid #333333;
            border-radius: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #555555;
            border-radius: 0px;
            min-height: 10px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #666666;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* 分割器 */
        QSplitter::handle {
            background-color: #333333;
        }
        QSplitter::handle:horizontal {
            width: 2px;
        }
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        /* 強制所有容器為黑底 */
        QWidget {
            background-color: #000000;
            color: #FFFFFF;
        }
        QFrame {
            background-color: #000000;
            color: #FFFFFF;
        }
        QSplitter {
            background-color: #000000;
        }
        QSplitter QWidget {
            background-color: #000000;
        }
        
        /* 強制所有MDI相關元素為黑底 */
        QMdiArea QWidget {
            background-color: #000000;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #000000;
        }
        QMdiArea > QWidget {
            background-color: #000000;
        }
        
        /* 左側面板所有子元素強制黑底 */
        QTreeWidget QWidget {
            background-color: #000000;
            color: #FFFFFF;
        }
        QTextEdit QWidget {
            background-color: #000000;
            color: #00FF00;
        }
        """
        
        #print("[DESIGN] DEBUG: Setting main window QSS styles...")
        #print(f"📄 QSS contains QMdiSubWindow border: {'QMdiSubWindow' in style and 'border:' in style}")
        #print(f"📄 QSS contains CustomTitleBar: {'CustomTitleBar' in style}")
        #print(f"📄 QSS total length: {len(style)} characters")
        self.setStyleSheet(style)
        #print("[OK] QSS styles applied successfully")
        
    def show_error_message(self, title, message):
        """顯示錯誤訊息對話框"""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    def remove_welcome_tab(self):
        """移除歡迎頁面 - 當使用者開始分析時"""
        try:
            for i in range(self.tab_widget.tabCount()):
                tab_text = self.tab_widget.tabText(i)
                if "歡迎" in tab_text or "Welcome" in tab_text:
                    self.tab_widget.removeTab(i)
                    #print(f"[OK] 已移除歡迎頁面: {tab_text}")
                    break
        except Exception as e:
            #print(f"[WARNING] 移除歡迎頁面時發生錯誤: {e}")
            pass


def main():
    """主函數"""
    app = QApplication(sys.argv)
    app.setApplicationName("F1T Professional Racing Analysis Workstation")
    app.setOrganizationName("F1T Professional Racing Analysis Team")
    
    # 設置應用程式字體
    font = QFont("Arial", 8)
    app.setFont(font)
    
    # 創建主視窗
    window = StyleHMainWindow()
    window.show()
    
    # 顯示歡迎訊息
    #print("[FINISH] F1T 專業賽車分析工作站已啟動")
    #print("[TARGET] 專業級F1數據分析平台")
    #print("🗺️ 多視窗分析界面，支援完整賽車數據處理")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
