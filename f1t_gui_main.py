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
        """添加子視窗並強制執行最小尺寸 - 簡化版本"""
        #print(f"🔒 CustomMdiArea: addSubWindow 被調用，widget 類型: {type(widget)}")
        
        if flags is not None:
            subwindow = super().addSubWindow(widget, flags)
        else:
            subwindow = super().addSubWindow(widget)
            
        #print(f"🔒 CustomMdiArea: 創建的子視窗類型: {type(subwindow)}")
        
        # 移除最小尺寸限制，允許完全自由縮放
        if isinstance(subwindow, PopoutSubWindow):
            # 不設置最小尺寸限制
            #print(f"🔒 CustomMdiArea: 子視窗無尺寸限制")
            pass
        
        # [修改] 保留邊框，使用CSS隱藏標題列
        if subwindow:
            # 不再設置 FramelessWindowHint，以保留邊框
            # subwindow.setWindowFlags(subwindow.windowFlags() | Qt.FramelessWindowHint)
            
            # 使用樣式表隱藏標題列但保留邊框
            subwindow.setStyleSheet("""
                QMdiSubWindow::title {
                    height: 0px;
                    margin: 0px;
                    padding: 0px;
                    background: transparent;
                    border: none;
                }
                QMdiSubWindow {
                    border: 2px solid #666666;
                    border-radius: 2px;
                    background-color: #FFFFFF;
                }
            """)
            #print(f"🔒 CustomMdiArea: 已隱藏標題列但保留邊框")
        
        return subwindow

# 全域信號管理器
class GlobalSignalManager(QObject):
    """全域信號管理器 - 用於跨視窗同步"""
    sync_x_position = pyqtSignal(int)  # X軸位置同步信號 (滑鼠位置)
    sync_x_range = pyqtSignal(float, float)  # X軸範圍同步信號 (偏移, 縮放)
    
    def __init__(self):
        super().__init__()
        
# 創建全域信號管理器實例
global_signals = GlobalSignalManager()

class MainWindowParameterProvider:
    """主視窗參數提供者 - 實現 IParameterProvider 介面"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def get_current_year(self) -> str:
        """從主視窗獲取當前年份"""
        try:
            if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                return self.main_window.year_combo.currentText()
        except Exception as e:
            print(f"⚠️ [PARAM_PROVIDER] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race(self) -> str:
        """從主視窗獲取當前賽事"""
        try:
            if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                return self.main_window.race_combo.currentText()
        except Exception as e:
            print(f"⚠️ [PARAM_PROVIDER] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session(self) -> str:
        """從主視窗獲取當前賽段"""
        try:
            if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                return self.main_window.session_combo.currentText()
        except Exception as e:
            print(f"⚠️ [PARAM_PROVIDER] 獲取賽段失敗: {e}")
        return "R"  # 預設值

class TelemetryChartWidget(QWidget):
    """遙測曲線圖表小部件 - 支援縮放、拖拉、X軸同步"""
    
    def __init__(self, chart_type="speed"):
        super().__init__()
        self.chart_type = chart_type
        # 移除最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(400, 200) - 已移除
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
        # 移除最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(300, 200) - 已移除
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
        
        # 🔗 接收同步控制按鈕
        self.sync_btn = QPushButton("🔗")
        self.sync_btn.setObjectName("SyncButton")
        self.sync_btn.setFixedSize(16, 16)
        self.sync_btn.setToolTip("接收主程式同步：啟用 (綠色) / 停用 (紅色)")
        self.sync_btn.setCheckable(True)
        self.sync_btn.setChecked(True)  # 預設啟用
        self.sync_btn.clicked.connect(self.toggle_x_sync)
        layout.addWidget(self.sync_btn)
        
        # 初始化顏色狀態 - 確保預設綠色正確顯示
        print(f"🟢 接收同步初始化為啟動狀態")
        
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
            #print(f"[CLICK] 雙擊標題欄恢復視窗大小")
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
        """切換接收同步狀態 - 綠色=接收主程式同步，紅色=獨立運作"""
        is_enabled = self.sync_btn.isChecked()
        
        # 更新按鈕外觀和提示
        if is_enabled:
            self.sync_btn.setText("🔗")
            self.sync_btn.setToolTip("接收主程式同步：啟用 (綠色)")
            # 強制更新為綠色樣式
            print(f"🟢 接收同步已啟動 - 將接收主程式參數")
        else:
            self.sync_btn.setText("🔗̸")  # 帶斜線的連結圖示
            self.sync_btn.setToolTip("接收主程式同步：停用 (紅色)")
            # 強制更新為紅色樣式
            print(f"🔴 接收同步已停用 - 獨立運作模式")
        
        # 強制重新應用樣式確保顏色更新
        self.sync_btn.style().unpolish(self.sync_btn)
        self.sync_btn.style().polish(self.sync_btn)
        self.sync_btn.update()
        
        # 更新父視窗的同步狀態
        if hasattr(self.parent_window, 'sync_enabled'):
            self.parent_window.sync_enabled = is_enabled
            print(f"🔄 視窗 '{self.parent_window.windowTitle()}' 同步接收狀態已更新: {is_enabled}")
            
            # 🔧 新增：立即更新標題（同步狀態改變時）
            if hasattr(self.parent_window, 'update_window_title'):
                self.parent_window.update_window_title()
        
        # 找到對應的圖表小部件並設置同步狀態（用於X軸連動）
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
    """支援彈出功能和調整大小的MDI子視窗 - 升級為通用模組容器"""
    
    # 添加自定義信號
    resized = pyqtSignal()  # 尺寸調整信號
    
    def __init__(self, title="", parent_mdi=None, analysis_module=None):
        super().__init__()
        #print(f"[START] DEBUG: Creating PopoutSubWindow '{title}'")
        self.parent_mdi = parent_mdi
        self.is_popped_out = False
        self.original_widget = None
        self.content_widget = None
        
        # 🔧 新增：模組支援
        self.analysis_module = analysis_module
        self._parameter_provider = None
        
        # 🔧 新增：本地參數存儲 (用於非同步狀態)
        self.local_year = "2025"
        self.local_race = "Japan"
        self.local_session = "R"
        
        # 🔧 修正：正確提取模組名稱
        self.module_name = self._extract_module_name_from_title(title)
        
        self.setWindowTitle(title)
        self.setObjectName("ProfessionalSubWindow")
        
        # 初始化同步設定狀態
        self.sync_enabled = True  # 預設開啟同步功能
        
        # 嘗試獲取主視窗引用
        self.main_window = None
        if parent_mdi:
            # 向上查找主視窗
            current_parent = parent_mdi.parent()
            while current_parent:
                if hasattr(current_parent, 'year_combo') and hasattr(current_parent, 'race_combo'):
                    self.main_window = current_parent
                    # 🔧 新增：設置參數提供者
                    self._parameter_provider = MainWindowParameterProvider(current_parent)
                    print(f"🔗 [INIT] {title} 已找到主視窗引用")
                    break
                current_parent = current_parent.parent()
        
        # 🔧 新增：如果有模組，進行初始化
        if self.analysis_module and self._parameter_provider:
            self.analysis_module.parameter_provider = self._parameter_provider
            # 連接模組信號
            if hasattr(self.analysis_module, 'signals'):
                self.analysis_module.signals.module_error.connect(self._handle_module_error)
                self.analysis_module.signals.parameters_updated.connect(self._handle_parameters_updated)
        
        # 初始化最小化狀態
        self.is_minimized = False
        self.original_geometry = None
        
        # 🔧 [FIX] 確保調整大小相關屬性被初始化
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        # 🔧 [FIX] 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
        print(f"✅ [INIT] PopoutSubWindow '{title}' 初始化完成 - 包含調整大小支援")
    
    def _extract_module_name_from_title(self, title):
        """從標題中提取模組名稱"""
        try:
            # 處理各種可能的標題格式
            if title.startswith("[RAIN]"):
                return "降雨分析"
            elif title.startswith("[LAP]"):
                return "單圈分析" 
            elif title.startswith("[COMPARE]"):
                return "比較分析"
            elif title.startswith("[TELEMETRY]"):
                return "遙測分析"
            elif "_" in title:
                # 新格式：模組名稱_年份_賽事_賽段
                return title.split('_')[0]
            elif " - " in title:
                # 舊格式：[TAG] 模組名稱 - 詳細資訊
                if "]" in title:
                    # 移除標籤部分
                    without_tag = title.split("]", 1)[1].strip()
                    # 取 " - " 之前的部分
                    return without_tag.split(" - ")[0].strip()
                else:
                    return title.split(" - ")[0].strip()
            else:
                # 純模組名稱
                return title.strip()
                
        except Exception as e:
            print(f"⚠️ [TITLE] 提取模組名稱失敗: {e}, 使用原標題: {title}")
            return title
        
    def _handle_module_error(self, error_message):
        """處理模組錯誤"""
        print(f"❌ [MODULE] {self.windowTitle()} 模組錯誤: {error_message}")
    
    def _handle_parameters_updated(self, params):
        """處理模組參數更新"""
        print(f"🔄 [MODULE] {self.windowTitle()} 參數已更新: {params}")
    
    def update_current_window(self):
        """更新當前視窗 - 委託給模組處理"""
        if self.analysis_module:
            # 如果有模組，委託給模組處理
            try:
                params = {}
                if self.sync_enabled and self._parameter_provider:
                    # 同步模式：使用主視窗參數
                    params = {
                        'year': self._parameter_provider.get_current_year(),
                        'race': self._parameter_provider.get_current_race(),
                        'session': self._parameter_provider.get_current_session()
                    }
                    # 更新本地參數
                    self.local_year = params['year']
                    self.local_race = params['race'] 
                    self.local_session = params['session']
                else:
                    # 非同步模式：使用本地參數
                    params = {
                        'year': self.local_year,
                        'race': self.local_race,
                        'session': self.local_session
                    }
                
                # 更新標題
                self.update_window_title()
                
                print(f"🔄 [{self.windowTitle()}] 更新視窗數據: {params['year']} {params['race']} {params['session']}")
                
                # 🔧 重新載入模組而不是委託更新
                success = self.analysis_module.update_parameters(**params)
                if success:
                    print(f"✅ [MODULE] {self.windowTitle()} 模組更新成功")
                else:
                    print(f"⚠️ [MODULE] {self.windowTitle()} 模組更新失敗")
                return success
                
            except Exception as e:
                print(f"❌ [MODULE] {self.windowTitle()} 更新異常: {e}")
                return False
        else:
            # 舊版模式：直接調用原有邏輯
            print(f"⚠️ [LEGACY] {self.windowTitle()} 使用舊版更新模式")
            return self._legacy_update_current_window()
    
    def update_window_title(self):
        """更新視窗標題"""
        try:
            new_title = f"{self.module_name}_{self.local_year}_{self.local_race}_{self.local_session}"
            self.setWindowTitle(new_title)
            
            # 同時更新自定義標題欄
            if hasattr(self, 'title_bar') and self.title_bar:
                self.title_bar.update_title(new_title)
                
            print(f"🏷️ [TITLE] 標題已更新: {new_title}")
            
        except Exception as e:
            print(f"❌ [TITLE] 標題更新失敗: {e}")
    
    def update_local_parameters(self, year=None, race=None, session=None):
        """更新本地參數（用於非同步模式）"""
        if year is not None:
            self.local_year = year
        if race is not None:
            self.local_race = race
        if session is not None:
            self.local_session = session
            
        # 立即更新標題
        self.update_window_title()
        
        print(f"🔄 [LOCAL] {self.windowTitle()} 本地參數已更新: {self.local_year} {self.local_race} {self.local_session}")
    
    def get_current_parameters(self):
        """獲取當前參數"""
        if self.sync_enabled and self._parameter_provider:
            # 同步模式：返回主視窗參數
            return {
                'year': self._parameter_provider.get_current_year(),
                'race': self._parameter_provider.get_current_race(), 
                'session': self._parameter_provider.get_current_session()
            }
        else:
            # 非同步模式：返回本地參數
            return {
                'year': self.local_year,
                'race': self.local_race,
                'session': self.local_session
            }
    
    def _legacy_update_current_window(self):
        """舊版視窗更新邏輯 - 保持向後相容性"""
        try:
            # 嘗試從主視窗獲取參數（舊版方式）
            year = "2025"
            race = "Japan" 
            session = "R"
            
            if self._parameter_provider:
                year = self._parameter_provider.get_current_year()
                race = self._parameter_provider.get_current_race()
                session = self._parameter_provider.get_current_session()
            
            print(f"🔄 [LEGACY] {self.windowTitle()} 舊版更新: {year} {race} {session}")
            
            # 如果內容widget有更新方法，調用它
            if self.content_widget and hasattr(self.content_widget, 'update'):
                self.content_widget.update()
                return True
            
            return True
            
        except Exception as e:
            print(f"❌ [LEGACY] 舊版更新失敗: {e}")
            return False
        
        # �[HOT] 設置最小尺寸防止縮小到無法使用 - 已取消限制
        # self.setMinimumSize(250, 150)  # 移除最小尺寸限制
        #print(f"🔒 最小尺寸限制已取消")
        
        # [HOT] 隱藏所有 MDI 子窗口的標題列
        # [修改] 保留邊框，只隱藏標題列
        # 使用自定義方式隱藏標題列但保留邊框
        self.setWindowFlags(Qt.SubWindow)  # 移除 FramelessWindowHint 以保留邊框
        #print(f"[LABEL] MDI子窗口 - 保留邊框，隱藏標題列")
        
        # 設置邊距以適應邊框
        self.setContentsMargins(2, 2, 2, 2)  # 為邊框留出空間
        
        # [HOT] 強化邊框樣式設置 - 確保邊框可見
        subwindow_qss = """
            PopoutSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 加粗邊框以確保可見 */
                border-radius: 2px;
            }
            QMdiSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;
                margin: 0px;
                padding: 2px;
                border-radius: 2px;
            }
            QMdiSubWindow[objectName="ProfessionalSubWindow"] {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 強化邊框 */
                border-radius: 2px;
            }
            
            /* 隱藏標題列但保留邊框 */
            QMdiSubWindow::title {
                height: 0px;
                margin: 0px;
                padding: 0px;
                background: transparent;
                border: none;
            }
            
            /* 接收同步按鈕 - 紅綠狀態指示 (子窗口專用) */
            #SyncButton {
                background-color: #FF4444;  /* 預設紅色 - 獨立模式 */
                color: #FFFFFF;
                border: 1px solid #CC0000;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SyncButton:hover {
                background-color: #FF6666;  /* 紅色懸停 */
            }
            #SyncButton:pressed {
                background-color: #CC0000;  /* 紅色按下 */
            }
            #SyncButton:checked {
                background-color: #00CC00;  /* 綠色 - 接收同步 */
                border: 1px solid #009900;
            }
            #SyncButton:checked:hover {
                background-color: #00FF00;  /* 綠色懸停 */
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
            
            /* 設定按鈕 */
            #SettingsButton {
                background-color: #F0F0F0;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SettingsButton:hover {
                background-color: #E8E8E8;
            }
            #SettingsButton:pressed {
                background-color: #D8D8D8;
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
        margin = getattr(self, 'resize_margin', 3)  # 安全訪問，預設3像素
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
        
        # [移除] 不再設置最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(250, 150) - 已移除
        #print(f"🔒 移除尺寸限制，允許自由縮放")
        
        # [移除] 不再計算標題欄最小高度限制
        # title_height = self.title_bar.height() if hasattr(self, 'title_bar') else 20
        # min_height = max(150, title_height + 100) - 已移除
        #print(f"🔒 無尺寸限制")
        
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
        """移除強制最小尺寸，返回系統預設"""
        # 不再強制返回固定尺寸，讓系統自然處理
        return super().minimumSize()
        
    def minimumSizeHint(self):
        """移除強制最小尺寸提示，返回系統預設"""
        # 不再強制返回固定尺寸提示，讓系統自然處理
        return super().minimumSizeHint()
        
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
        
        # 視窗同步名稱勾選框
        self.sync_windows_checkbox = QCheckBox("🔗 同步其他視窗")
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        self.sync_windows_checkbox.setChecked(True)
        self.sync_windows_checkbox.setToolTip("同步其他視窗 (賽事/賽段/年份同步)")
        self.sync_windows_checkbox.toggled.connect(self.on_sync_windows_toggled)
        control_layout.addWidget(self.sync_windows_checkbox)
        
        control_layout.addStretch()
        
        # 年份選擇器
        year_label = QLabel("年:")
        year_label.setObjectName("ControlLabel")
        control_layout.addWidget(year_label)
        
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems(["2024", "2025"])  # 🔧 修復: 與主視窗一致，移除2023
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(140)
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        control_layout.addWidget(self.year_combo)
        
        # 賽事選擇器
        race_label = QLabel("賽事:")
        race_label.setObjectName("ControlLabel")
        control_layout.addWidget(race_label)
        
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # 🔧 修復: 使用動態賽事列表而非硬編碼
        current_year = self.year_combo.currentText()
        self.update_races_for_year(current_year)
        self.race_combo.setCurrentText("Japan")
        self.race_combo.setFixedWidth(140)
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
        self.session_combo.setFixedWidth(70)
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        control_layout.addWidget(self.session_combo)
        
        # 重新分析按鈕
        reanalyze_btn = QPushButton("R")
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
        
        # 🔧 新增: 動態更新賽事列表
        self.update_races_for_year(year)
        
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
        """執行重新分析 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # 🔧 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        #print(f"[REFRESH] [{window_title}] 開始重新分析")
        #print(f"   參數: {year} {race} {session}")
        #print(f"   視窗連動: {'是' if self.sync_windows_checkbox.isChecked() else '否'}")
        
        # 重新分析當前視窗
        self.update_current_window()
        
        # 如果啟用連動，也更新其他視窗
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
            
    def sync_to_other_windows(self):
        """同步參數到其他視窗 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # 🔧 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        print(f"🔄 [{window_title}] 同步參數到其他視窗: {year} {race} {session}")
        
        # 同步到同一MDI區域中的其他子視窗
        synced_count = 0
        if self.parent_mdi:
            for subwindow in self.parent_mdi.subWindowList():
                if subwindow != self and hasattr(subwindow, 'set_analysis_parameters'):
                    # 檢查其他子視窗是否啟用同步
                    if hasattr(subwindow, 'sync_windows_checkbox') and \
                       subwindow.sync_windows_checkbox.isChecked():
                        
                        params = {
                            'year': year,
                            'race': race,
                            'session': session
                        }
                        subwindow.set_analysis_parameters(params, skip_sync=True)
                        synced_count += 1
                        print(f"🔄 同步到子視窗: {subwindow.windowTitle()}")
        
        print(f"✅ 完成子視窗同步，共更新 {synced_count} 個視窗")
            
    def _legacy_update_current_window(self):
        """舊版更新當前視窗的分析數據 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # 🔧 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        print(f"🔄 [{window_title}] 舊版更新視窗數據: {year} {race} {session}")
        
        # 啟動資料載入流程
        self.load_race_data(year, race, session)
    
    def load_race_data(self, year, race, session):
        """載入比賽資料 - 完整的JSON載入流程"""
        # Step 1: 載入JSON
        json_data = self.try_load_json(year, race, session)
        
        if json_data:
            # JSON存在，直接使用
            print(f"✅ 找到JSON檔案，直接載入資料")
            self.update_charts_and_analysis(json_data)
        else:
            # Step 2: 無JSON則進行CLI參數呼叫
            print(f"❌ 未找到JSON檔案，啟動CLI分析...")
            self.call_cli_analysis(year, race, session)
            
            # Step 3: 等待JSON產生
            self.wait_for_json_generation(year, race, session)
    
    def try_load_json(self, year, race, session):
        """嘗試載入JSON檔案 - 與RainAnalysisCache保持一致"""
        import glob
        import os
        
        # 嘗試與 RainAnalysisCache 相同的搜尋邏輯
        # 1. 先嘗試降雨分析的標準格式
        rain_analysis_file = f"json/rain_analysis_{year}_{race}_{session}.json"
        if os.path.exists(rain_analysis_file):
            try:
                with open(rain_analysis_file, 'r', encoding='utf-8') as f:
                    print(f"📁 找到降雨分析JSON檔案: {rain_analysis_file}")
                    return json.load(f)
            except Exception as e:
                print(f"❌ 降雨分析JSON載入錯誤: {e}")
        
        # 2. 備用搜尋 - 構建JSON檔案搜尋模式
        json_patterns = [
            f"json/*{year}*{race}*{session}*.json",
            f"json_exports/*{year}*{race}*{session}*.json", 
            f"cache/*{year}*{race}*{session}*.json"
        ]
        
        for pattern in json_patterns:
            json_files = glob.glob(pattern)
            if json_files:
                # 過濾掉非JSON檔案
                json_files = [f for f in json_files if f.lower().endswith('.json')]
                if json_files:
                    json_file = json_files[0]  # 取第一個符合的檔案
                    print(f"📁 找到JSON檔案: {json_file}")
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        print(f"❌ JSON載入錯誤: {e}")
                        continue
        
        print(f"⚠️ 未找到適合的JSON檔案: {year}/{race}/{session}")
        return None
    
    def get_races_for_year_in_subwindow(self, year):
        """子視窗中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            # 與主視窗相同的賽事定義
            race_options = {
                2024: [
                    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
                    "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                    "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ],
                2025: [
                    "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
                    "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain",
                    "Belgium", "Hungary", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ]
            }
            
            year_int = int(year)
            races = race_options.get(year_int, race_options[2025])
            
            print(f"[SUBWINDOW] 載入 {year} 年的賽事列表: {len(races)} 個賽事")
            return races
            
        except Exception as e:
            print(f"[SUBWINDOW ERROR] 獲取賽事列表時出錯: {e}")
            return ["Japan", "Great Britain", "Monaco"]  # 回退列表
    
    def update_races_for_year(self, year):
        """為指定年份更新賽事列表"""
        if not hasattr(self, 'race_combo') or not self.race_combo:
            return
            
        # 記住當前選擇的賽事
        current_race = self.race_combo.currentText()
        
        # 獲取新年份的賽事列表
        races = self.get_races_for_year_in_subwindow(year)
        
        # 更新賽事選擇器
        self.race_combo.blockSignals(True)  # 阻止信號避免循環觸發
        self.race_combo.clear()
        self.race_combo.addItems(races)
        
        # 嘗試保持相同的賽事選擇（如果在新年份中存在）
        race_index = self.race_combo.findText(current_race)
        if race_index >= 0:
            self.race_combo.setCurrentIndex(race_index)
        else:
            # 如果當前賽事不存在，則選擇日本或第一個賽事
            japan_index = self.race_combo.findText("Japan")
            if japan_index >= 0:
                self.race_combo.setCurrentIndex(japan_index)
            elif self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        
        self.race_combo.blockSignals(False)  # 恢復信號
        
        print(f"[SUBWINDOW] 已更新賽事列表，當前選擇: {self.race_combo.currentText()}")
    
    def call_cli_analysis(self, year, race, session):
        """呼叫CLI參數進行分析"""
        import subprocess
        import sys
        
        # 構建CLI命令
        cmd = [
            sys.executable,
            "f1_analysis_modular_main.py",
            "-f", "1",  # 強制模式
            "-y", str(year),
            "-r", race,
            "-s", session
        ]
        
        print(f"🚀 執行CLI命令: {' '.join(cmd)}")
        
        try:
            # 非阻塞式執行
            self.cli_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            print(f"⚡ CLI分析已啟動 (PID: {self.cli_process.pid})")
            
        except Exception as e:
            print(f"❌ CLI執行錯誤: {e}")
    
    def wait_for_json_generation(self, year, race, session):
        """等待JSON產生"""
        from PyQt5.QtCore import QTimer
        
        # 設置JSON檢查計時器
        self.json_check_timer = QTimer()
        self.json_check_timer.timeout.connect(
            lambda: self.check_json_ready(year, race, session)
        )
        self.json_check_timer.start(2000)  # 每2秒檢查一次
        
        # 設置最大等待時間 (60秒)
        self.max_wait_timer = QTimer()
        self.max_wait_timer.setSingleShot(True)
        self.max_wait_timer.timeout.connect(self.on_json_wait_timeout)
        self.max_wait_timer.start(60000)  # 60秒超時
        
        print(f"⏳ 等待JSON檔案產生... (最多等待60秒)")
    
    def check_json_ready(self, year, race, session):
        """檢查JSON是否已準備好"""
        # Step 4: 讀取JSON
        json_data = self.try_load_json(year, race, session)
        
        if json_data:
            # JSON已產生，停止計時器
            self.json_check_timer.stop()
            self.max_wait_timer.stop()
            
            print(f"✅ JSON檔案已產生，開始載入資料")
            self.update_charts_and_analysis(json_data)
        else:
            print(f"⏳ 繼續等待JSON檔案產生...")
    
    def on_json_wait_timeout(self):
        """JSON等待超時處理"""
        self.json_check_timer.stop()
        print(f"⏰ JSON等待超時，可能分析失敗")
        
        # 可以在這裡添加錯誤處理邏輯
        # 例如：顯示錯誤訊息、重試機制等
    
    def update_charts_and_analysis(self, json_data):
        """更新圖表和分析結果"""
        print(f"📊 開始更新圖表和分析結果...")
        
        try:
            # 更新遙測圖表
            if 'telemetry' in json_data:
                self.update_telemetry_chart(json_data['telemetry'])
                
            # 更新軌道地圖
            if 'track_data' in json_data:
                self.update_track_map(json_data['track_data'])
                
            # 更新分析數據
            if 'analysis_results' in json_data:
                self.update_analysis_data(json_data['analysis_results'])
                
            print(f"✅ 圖表和分析結果更新完成")
            
        except Exception as e:
            print(f"❌ 圖表更新錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def update_telemetry_chart(self, telemetry_data):
        """更新遙測圖表"""
        print(f"📈 更新遙測圖表資料")
        # 實現具體的遙測圖表更新邏輯
        pass
    
    def update_track_map(self, track_data):
        """更新軌道地圖"""
        print(f"🗺️ 更新軌道地圖資料")
        # 實現具體的軌道地圖更新邏輯
        pass
    
    def update_analysis_data(self, analysis_data):
        """更新分析數據"""
        print(f"📊 更新分析數據")
        # 實現具體的分析數據更新邏輯
        pass
        
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
        
    def set_analysis_parameters(self, params, skip_sync=False):
        """設置分析參數，支援跳過同步"""
        if hasattr(self, 'year_combo') and params:
            # 暫時斷開信號連接避免循環同步
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            # 更新參數
            self.year_combo.setCurrentText(params.get('year', '2025'))
            self.race_combo.setCurrentText(params.get('race', 'Japan'))
            self.session_combo.setCurrentText(params.get('session', 'R'))
            
            # 恢復信號連接
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            # 更新資料（如果不是跳過同步）
            if not skip_sync:
                self.update_current_window()
            
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
            # self.standalone_window.setMinimumSize(400, 300) - 尺寸限制已移除
            
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
            
    def resizeEvent(self, event):
        """處理視窗大小調整事件 - 簡化版本，避免重複處理"""
        super().resizeEvent(event)
        
        # 只處理內容組件的基本更新，避免多重縮放處理
        if hasattr(self, 'content_widget') and self.content_widget:
            try:
                # 簡化處理：只調用基本的update，讓Qt的佈局系統自動處理
                self.content_widget.update()
                #print(f"[RESIZE] 子視窗內容已更新: {event.size().width()}x{event.size().height()}")
            except Exception as e:
                #print(f"[RESIZE_ERROR] 內容更新失敗: {e}")
                pass


        # 發射resize信號
        self.resized.emit()
            
    def show_settings_dialog(self):
        """顯示設定對話框"""
        dialog = WindowSettingsDialog(self)
        dialog.exec_()

    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數變更通知"""
        window_title = self.windowTitle()
        print(f"📢 [NOTIFICATION] {window_title} 收到主視窗更新通知: {param_type}={value}")
        
        # 檢查同步狀態 - 支援多種同步狀態檢查方式
        sync_enabled = False
        
        # 方法1: 檢查 sync_windows_checkbox (用於有控制面板的子視窗)
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox:
            sync_enabled = self.sync_windows_checkbox.isChecked()
            print(f"🔍 [NOTIFICATION] {window_title} 使用 checkbox 檢查同步狀態: {sync_enabled}")
        
        # 方法2: 檢查 sync_enabled 屬性 (用於 PopoutSubWindow 等)
        elif hasattr(self, 'sync_enabled'):
            sync_enabled = self.sync_enabled
            print(f"🔍 [NOTIFICATION] {window_title} 使用屬性檢查同步狀態: {sync_enabled}")
        
        # 如果未啟用同步，直接返回
        if not sync_enabled:
            print(f"🔴 [NOTIFICATION] {window_title} 同步已停用，忽略更新通知")
            return
        
        print(f"🟢 [NOTIFICATION] {window_title} 同步已啟用，處理參數更新")
        
        # 🔧 更新本地參數（同步模式）
        if param_type == 'year':
            self.local_year = value
        elif param_type == 'race':
            self.local_race = value
        elif param_type == 'session':
            self.local_session = value
        
        # 🔧 立即更新標題
        self.update_window_title()
        
        # 使用統一的方法更新視窗內容
        try:
            success = self.update_current_window()
            if success:
                print(f"✅ [NOTIFICATION] {window_title} 內容更新成功")
            else:
                print(f"⚠️ [NOTIFICATION] {window_title} 內容更新完成但可能有問題")
        except Exception as e:
            print(f"❌ [NOTIFICATION] {window_title} 內容更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_year') and self.local_year:
                return self.local_year
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                    return self.main_window.year_combo.currentText()
            
            # 🔧 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"⚠️ [GET_YEAR] 獲取主視窗年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_race') and self.local_race:
                return self.local_race
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                    return self.main_window.race_combo.currentText()
            
            # 🔧 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"⚠️ [GET_RACE] 獲取主視窗賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_session') and self.local_session:
                return self.local_session
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                    return self.main_window.session_combo.currentText()
            
            # 🔧 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            print(f"⚠️ [GET_SESSION] 獲取主視窗賽段失敗: {e}")
        return "R"  # 預設值
        return "R"  # 預設值

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
                border: 2px solid #CCCCCC;
                background-color: #FFFFFF;
            }
            QMainWindow:hover {
                border: 2px solid #999999;
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
        sync_group = QGroupBox("視窗同步控制")
        sync_group.setObjectName("SettingsGroup")
        sync_layout = QVBoxLayout(sync_group)
        
        # 連動控制勾選框
        self.sync_windows_checkbox = QCheckBox("🔗 接收主程式同步 (年份/賽事/賽段)")
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        # 🔧 修復: 從父視窗獲取當前同步狀態
        current_sync_state = getattr(parent_window, 'sync_enabled', True)
        self.sync_windows_checkbox.setChecked(current_sync_state)
        self.sync_windows_checkbox.setToolTip("勾選時接收主程式參數同步，下方分析參數將變為不可編輯")
        # 🔧 新增: 當同步狀態改變時，切換分析參數的可編輯性
        self.sync_windows_checkbox.toggled.connect(self.on_sync_checkbox_toggled)
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
        self.year_combo.addItems(["2024", "2025"])  # 🔧 修復: 與主視窗一致，移除2023
        # 🔧 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_year') and parent_window.local_year:
            current_year = parent_window.local_year
        else:
            current_year = self.get_current_year_from_main_window()
        self.year_combo.setCurrentText(current_year)
        # 🔧 新增: 年份變更時動態更新賽事列表
        self.year_combo.currentTextChanged.connect(self.on_year_changed_in_dialog)
        params_layout.addWidget(self.year_combo, 0, 1)
        
        # 賽事選擇器
        params_layout.addWidget(QLabel("賽事:"), 1, 0)
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # 🔧 修復: 使用動態賽事列表而非硬編碼
        self.populate_races_for_year(current_year)
        # 🔧 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_race') and parent_window.local_race:
            current_race = parent_window.local_race
        else:
            current_race = self.get_current_race_from_main_window()
        self.race_combo.setCurrentText(current_race)
        params_layout.addWidget(self.race_combo, 1, 1)
        
        # 賽段選擇器
        params_layout.addWidget(QLabel("賽段:"), 2, 0)
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "SQ", "R"])
        # 🔧 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_session') and parent_window.local_session:
            current_session = parent_window.local_session
        else:
            current_session = self.get_current_session_from_main_window()
        self.session_combo.setCurrentText(current_session)
        params_layout.addWidget(self.session_combo, 2, 1)
        
        layout.addWidget(params_group)
        
        # 🔧 新增: 根據同步狀態設置分析參數的可編輯性
        self.update_analysis_params_editability()
        
        layout.addStretch()
        
        # 對話框按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setObjectName("DialogButtonBox")
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_sync_checkbox_toggled(self, checked):
        """處理同步勾選框狀態變化"""
        print(f"🔗 [SETTING] 同步接收狀態變更為: {'啟用' if checked else '停用'}")
        self.update_analysis_params_editability()
        
        # 🔧 移除錯誤的同步調用 - 不需要從主程式同步，保持當前設定
        # if checked:
        #     self.sync_params_from_main_window()  # 這個調用會產生錯誤
    
    def update_analysis_params_editability(self):
        """根據同步狀態更新分析參數的可編輯性"""
        is_sync_enabled = self.sync_windows_checkbox.isChecked()
        
        # 設置分析參數控件的可編輯性（同步時不可編輯）
        self.year_combo.setEnabled(not is_sync_enabled)
        self.race_combo.setEnabled(not is_sync_enabled)
        self.session_combo.setEnabled(not is_sync_enabled)
        
        # 更新提示文字
        if is_sync_enabled:
            self.year_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.race_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            self.session_combo.setToolTip("已啟用同步接收，參數由主程式控制")
            print(f"🔒 [SETTING] 分析參數已鎖定 - 接收主程式同步")
        else:
            self.year_combo.setToolTip("手動設定年份")
            self.race_combo.setToolTip("手動設定賽事")
            self.session_combo.setToolTip("手動設定賽段")
            print(f"🔓 [SETTING] 分析參數已解鎖 - 可手動編輯")
    
    def sync_params_from_main_window(self):
        """從主程式同步參數到設定對話框"""
        try:
            current_year = self.get_current_year_from_main_window()
            current_race = self.get_current_race_from_main_window()
            current_session = self.get_current_session_from_main_window()
            
            print(f"📥 [SETTING] 從主程式同步參數: {current_year} {current_race} {current_session}")
            
            # 更新對話框中的參數
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            self.year_combo.setCurrentText(current_year)
            # 需要先更新賽事列表
            self.populate_races_for_year(current_year)
            self.race_combo.setCurrentText(current_race)
            self.session_combo.setCurrentText(current_session)
            
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            print(f"✅ [SETTING] 參數同步完成")
            
        except Exception as e:
            print(f"❌ [SETTING] 從主程式同步參數失敗: {e}")
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'year_combo') and main_window.year_combo:
                    return main_window.year_combo.currentText()
            # 🔧 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'year_combo') and self.parent_window.year_combo:
            #     return self.parent_window.year_combo.currentText()
        except Exception as e:
            print(f"⚠️ [SETTING] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'race_combo') and main_window.race_combo:
                    return main_window.race_combo.currentText()
            # 🔧 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'race_combo') and self.parent_window.race_combo:
            #     return self.parent_window.race_combo.currentText()
        except Exception as e:
            print(f"⚠️ [SETTING] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'session_combo') and main_window.session_combo:
                    return main_window.session_combo.currentText()
            # 🔧 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'session_combo') and self.parent_window.session_combo:
            #     return self.parent_window.session_combo.currentText()
        except Exception as e:
            print(f"⚠️ [SETTING] 獲取賽段失敗: {e}")
        return "R"  # 預設值
    
    def get_races_for_year_in_dialog(self, year):
        """在設定對話框中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            # 與主視窗相同的賽事定義
            race_options = {
                2024: [
                    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
                    "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                    "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ],
                2025: [
                    "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
                    "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain",
                    "Belgium", "Hungary", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ]
            }
            
            year_int = int(year)
            races = race_options.get(year_int, race_options[2025])
            
            print(f"[DIALOG] 載入 {year} 年的賽事列表: {len(races)} 個賽事")
            return races
            
        except Exception as e:
            print(f"[DIALOG ERROR] 獲取賽事列表時出錯: {e}")
            return ["Japan", "Great Britain", "Monaco"]  # 回退列表
    
    def populate_races_for_year(self, year):
        """為指定年份填充賽事列表"""
        races = self.get_races_for_year_in_dialog(year)
        self.race_combo.clear()
        self.race_combo.addItems(races)
        
    def on_year_changed_in_dialog(self, year):
        """處理設定對話框中的年份變更"""
        print(f"[DIALOG] 年份變更為: {year}")
        
        # 記住當前選擇的賽事
        current_race = self.race_combo.currentText()
        
        # 更新賽事列表
        self.populate_races_for_year(year)
        
        # 嘗試保持相同的賽事選擇（如果在新年份中存在）
        race_index = self.race_combo.findText(current_race)
        if race_index >= 0:
            self.race_combo.setCurrentIndex(race_index)
        else:
            # 如果當前賽事不存在，則選擇日本或第一個賽事
            japan_index = self.race_combo.findText("Japan")
            if japan_index >= 0:
                self.race_combo.setCurrentIndex(japan_index)
            elif self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        
    def accept_settings(self):
        """確認設定"""
        window_title = self.parent_window.windowTitle()
        year = self.year_combo.currentText()
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        sync_windows = self.sync_windows_checkbox.isChecked()
        
        print(f"🔧 [SETTING] [{window_title}] 設定已更新:")
        print(f"   參數: {year} {race} {session}")
        print(f"   同步接收狀態: {'啟用' if sync_windows else '停用'}")
        
        # 保存同步狀態到父視窗
        self.parent_window.sync_enabled = sync_windows
        
        # 🔧 修改邏輯：根據同步狀態決定行為
        if sync_windows:
            # 當啟用同步時，只接收不發送，確保與主程式一致
            print(f"🔄 [SETTING] [{window_title}] 同步接收模式 - 僅更新當前視窗")
            self.update_current_window_only()
        else:
            # 當停用同步時，允許手動設定並應用到當前視窗
            print(f"🔧 [SETTING] [{window_title}] 手動設定模式 - 應用自定義參數")
            self.apply_manual_settings(year, race, session)
        
        self.accept()
        
    def update_current_window_only(self):
        """僅更新當前視窗（同步接收模式）"""
        window_title = self.parent_window.windowTitle()
        print(f"🔄 [SETTING] [{window_title}] 更新視窗數據（同步模式）")
        
        try:
            # 如果當前視窗有update_current_window方法，調用它
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                print(f"✅ [SETTING] 當前視窗數據更新完成（同步模式）")
        except Exception as e:
            print(f"❌ [SETTING] 更新當前視窗失敗: {e}")
    
    def apply_manual_settings(self, year, race, session):
        """應用手動設定（獨立模式）"""
        window_title = self.parent_window.windowTitle()
        print(f"🔧 [SETTING] [{window_title}] 應用手動設定: {year} {race} {session}")
        
        try:
            # 更新當前視窗的內容（使用手動設定的參數）
            self.update_current_window_with_params(year, race, session)
            print(f"✅ [SETTING] 手動設定應用完成")
        except Exception as e:
            print(f"❌ [SETTING] 應用手動設定失敗: {e}")
    
    def update_current_window_with_params(self, year, race, session):
        """使用指定參數更新當前視窗"""
        window_title = self.parent_window.windowTitle()
        print(f"🔄 [SETTING] [{window_title}] 使用參數更新視窗: {year} {race} {session}")
        
        try:
            # 🔧 新方法：直接更新子視窗的本地參數
            if hasattr(self.parent_window, 'update_local_parameters'):
                # 更新本地參數（這會自動更新標題）
                self.parent_window.update_local_parameters(year, race, session)
                
                # 調用視窗更新
                if hasattr(self.parent_window, 'update_current_window'):
                    self.parent_window.update_current_window()
                    
                print(f"✅ [SETTING] 參數更新完成（新方法）: {year} {race} {session}")
                return
            
            # 🔧 舊方法向後兼容：直接調用更新
            print(f"⚠️ [SETTING] 使用舊方法向後兼容模式")
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                print(f"✅ [SETTING] 當前視窗數據更新完成（向後兼容模式）")
            else:
                print(f"⚠️ [SETTING] 視窗沒有 update_current_window 方法")
                
        except Exception as e:
            print(f"❌ [SETTING] 更新當前視窗失敗: {e}")
            print(f"📋 [SETTING] 錯誤詳情: {type(e).__name__}: {str(e)}")
    
    def apply_settings(self, year, race, session, sync_windows):
        """應用設定到父視窗（已棄用，由新方法取代）"""
        # 🔧 此方法已被 update_current_window_only 和 apply_manual_settings 取代
        print(f"⚠️ [SETTING] apply_settings 方法已棄用")
        pass
        
    def sync_to_other_windows(self, year, race, session):
        """同步參數到其他視窗（已棄用，避免命令混亂）"""
        # 🔧 移除此功能，避免MDI子視窗向主程式發送控制命令
        print(f"⚠️ [SETTING] sync_to_other_windows 方法已停用 - 避免多視窗命令混亂")
        print(f"� [SETTING] 子視窗應僅接收主程式同步，不應發送控制命令")
        pass
        
    def update_current_window(self, year, race, session):
        """更新當前視窗的分析數據（已棄用，由新方法取代）"""
        # 🔧 此方法已被 update_current_window_only 取代
        print(f"⚠️ [SETTING] update_current_window 方法已棄用")
        pass

class StyleHMainWindow(QMainWindow):
    """風格H: 專業賽車分析工作站主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("F1 Professional Racing Analysis Workstation v8.0 - Style H")
        # self.setMinimumSize(1600, 900) - 主視窗尺寸限制已移除
        
        # 初始化分析追蹤屬性
        self.active_analysis_tabs = []
        
        # 初始化MDI區域引用（用於同步功能）
        self.mdi_areas = []  # 存儲所有MDI區域的引用
        
        self.init_ui()
        self.apply_style_h()
        
        # 延遲檢查標籤欄隱藏狀態
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, self.check_and_hide_tabs)
        
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
        toolbar.setFixedHeight(35)
        self.addToolBar(toolbar)
        
        # 參數輸入區域
        toolbar.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("ParameterCombo")
        self.year_combo.addItems(["2024", "2025"])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(140)
        toolbar.addWidget(self.year_combo)
        
        toolbar.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("ParameterCombo")
        # 賽事項目將由 on_year_changed 方法動態填充
        self.race_combo.setFixedWidth(120)  # 增加寬度以容納較長的賽事名稱
        toolbar.addWidget(self.race_combo)
        
        toolbar.addWidget(QLabel("賽段:"))
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("ParameterCombo")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "SQ", "R"])  # 🔧 修復: 與子視窗一致
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        toolbar.addWidget(self.session_combo)
        
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction("[TILE]", self.tile_windows)
        toolbar.addAction("[CASCADE]", self.cascade_windows)
        
        # 連接年份變更事件
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        
        # 連接賽事和會話變更事件 - 添加同步功能
        self.race_combo.currentTextChanged.connect(self.on_main_race_changed)
        self.session_combo.currentTextChanged.connect(self.on_main_session_changed)
        
        # 初始化賽事列表
        self.on_year_changed(self.year_combo.currentText())
    
    def get_races_for_year(self, year):
        """根據年份獲取可用的賽事列表（使用與CLI相同的race_options）"""
        try:
            # 與 f1_analysis_modular_main.py 相同的賽事定義
            race_options = {
                2024: [
                    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
                    "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                    "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ],
                2025: [
                    "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
                    "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain",
                    "Belgium", "Hungary", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                    "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
                ]
            }
            
            # 賽事名稱映射：顯示名稱 -> FastF1 API 期望的名稱
            self.race_name_mapping = {
                "Great Britain": "British",  # 關鍵映射
                "United States": "United States",
                "Emilia Romagna": "Emilia Romagna",
                "Saudi Arabia": "Saudi Arabia",
                "Las Vegas": "Las Vegas",
                "Abu Dhabi": "Abu Dhabi"
            }
            
            # 反向映射：FastF1 名稱 -> 顯示名稱
            self.display_name_mapping = {v: k for k, v in self.race_name_mapping.items()}
            
            # 賽事日期映射（可選顯示用）
            race_dates = {
                2024: {
                    "Bahrain": "2024-03-02",
                    "Saudi Arabia": "2024-03-09", 
                    "Australia": "2024-03-24",
                    "Japan": "2024-04-07",
                    "China": "2024-04-21",
                    "Miami": "2024-05-05",
                    "Emilia Romagna": "2024-05-19",
                    "Monaco": "2024-05-26",
                    "Canada": "2024-06-09",
                    "Spain": "2024-06-23",
                    "Austria": "2024-06-30",
                    "Great Britain": "2024-07-07",
                    "Hungary": "2024-07-21",
                    "Belgium": "2024-07-28",
                    "Netherlands": "2024-09-01",
                    "Italy": "2024-09-01",
                    "Azerbaijan": "2024-09-15",
                    "Singapore": "2024-09-22",
                    "United States": "2024-10-20",
                    "Mexico": "2024-10-27",
                    "Brazil": "2024-11-03",
                    "Las Vegas": "2024-11-23",
                    "Qatar": "2024-12-01",
                    "Abu Dhabi": "2024-12-08"
                },
                2025: {
                    "Australia": "2025-03-16",
                    "China": "2025-03-23",
                    "Japan": "2025-04-06", 
                    "Bahrain": "2025-04-13",
                    "Saudi Arabia": "2025-04-20",
                    "Miami": "2025-05-04",
                    "Emilia Romagna": "2025-05-18",
                    "Monaco": "2025-05-25",
                    "Spain": "2025-06-01",
                    "Canada": "2025-06-15",
                    "Austria": "2025-06-29",
                    "Great Britain": "2025-07-06",
                    "Hungary": "2025-08-03",
                    "Belgium": "2025-07-27",
                    "Netherlands": "2025-08-31",
                    "Italy": "2025-09-07",
                    "Azerbaijan": "2025-09-21",
                    "Singapore": "2025-10-05",
                    "United States": "2025-10-19",
                    "Mexico": "2025-10-26",
                    "Brazil": "2025-11-09",
                    "Las Vegas": "2025-11-22",
                    "Qatar": "2025-11-30",
                    "Abu Dhabi": "2025-12-07"
                }
            }
            
            # 轉換年份為整數
            year_int = int(year)
            
            # 獲取對應年份的賽事列表
            races = race_options.get(year_int, race_options[2025])
            
            print(f"[RACE_OPTIONS] 載入 {year} 年的完整賽事列表: {len(races)} 個賽事")
            print(f"[RACE_LIST] {', '.join(races)}")
            
            return races
            
        except Exception as e:
            print(f"[ERROR] 獲取賽事列表時出錯: {e}")
            # 回退到基本列表
            return ["Japan", "Great Britain", "Monaco"]
    
    def get_fastf1_race_name(self, display_name):
        """將顯示名稱轉換為 FastF1 API 期望的名稱"""
        return self.race_name_mapping.get(display_name, display_name)
    
    def on_year_changed(self, year):
        """處理年份變更事件"""
        try:
            # 獲取該年份的賽事列表
            races = self.get_races_for_year(year)
            
            # 清空並更新賽事選擇器
            self.race_combo.clear()
            self.race_combo.addItems(races)
            
            # 設置預設選擇（如果 Japan 存在則選擇，否則選擇第一個）
            if "Japan" in races:
                self.race_combo.setCurrentText("Japan")
            elif races:
                self.race_combo.setCurrentText(races[0])
                
            print(f"已載入 {year} 年的 {len(races)} 個賽事")
            
            # 更新狀態列
            self.update_status_bar()
            
            # 同步年份到MDI子視窗
            self.sync_to_all_mdi_subwindows('year', year)
            
        except Exception as e:
            print(f"更新賽事列表時出錯: {e}")
    
    def on_main_race_changed(self, race):
        """主視窗賽事變更處理"""
        print(f"🏁 [MAIN] 主視窗賽事變更為: {race}")
        self.update_status_bar()
        # 同步賽事到MDI子視窗
        self.sync_to_all_mdi_subwindows('race', race)
    
    def on_main_session_changed(self, session):
        """主視窗賽段變更處理"""
        print(f"🏎️ [MAIN] 主視窗賽段變更為: {session}")
        self.update_status_bar()
        # 同步賽段到MDI子視窗
        self.sync_to_all_mdi_subwindows('session', session)
        
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
        basic_group = QTreeWidgetItem(tree, ["🔧 基礎分析"])
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
        compare_group = QTreeWidgetItem(tree, ["[COMPARE] 比較分析"])
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
        
        # 隱藏標籤欄
        self.tab_widget.tabBar().setVisible(False)
        print(f"[DEBUG] 標籤欄可見性設為: {self.tab_widget.tabBar().isVisible()}")
        print(f"[DEBUG] 標籤欄高度: {self.tab_widget.tabBar().height()}")
        
        # 強制更新標籤欄設置
        self.tab_widget.tabBar().hide()
        print(f"[DEBUG] 強制隱藏後標籤欄可見性: {self.tab_widget.tabBar().isVisible()}")
        
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
        
        # [HIDE] 隱藏標籤按鈕容器（這就是用戶看到的"降雨分析 - 分析"）
        tab_buttons_container.setVisible(False)
        tab_buttons_container.hide()
        print(f"[TAB_DEBUG] TabButtonsContainer 已隱藏: {not tab_buttons_container.isVisible()}")
        
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
        # 創建歡迎畫面作為預設主頁 (隱藏標題)
        welcome_tab = self.create_welcome_tab()
        welcome_tab.setObjectName("welcome_tab")  # 添加標識符
        self.tab_widget.addTab(welcome_tab, "")
        
        self.update_tab_count()
        
    def add_new_tab(self):
        """新增分頁"""
        # 獲取當前分頁數量以生成新的標題
        count = self.tab_widget.count() + 1
        tab_types = [
            ("[TELE] 遙測分析", self.create_telemetry_analysis_tab),
            ("[LAP] 圈速比較", self.create_laptime_comparison_tab),
            ("[TRACK] 賽道分析", self.create_track_analysis_tab),
            ("[DATA] 數據總覽", self.create_data_overview_tab)
        ]
        
        # 輪流創建不同類型的分頁
        tab_type_index = (count - 1) % len(tab_types)
        tab_name, tab_creator = tab_types[tab_type_index]
        
        new_tab = tab_creator()
        self.tab_widget.addTab(new_tab, "")  # 隱藏標題
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
        
    def check_and_hide_tabs(self):
        """檢查並強制隱藏標籤欄 - 簡化版本"""
        print(f"[TAB_HIDE] 檢查標籤隱藏狀態...")
        print(f"[TAB_HIDE] QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
        # 確保隱藏
        self.tab_widget.tabBar().setVisible(False)
        self.tab_widget.tabBar().hide()
        self.tab_widget.tabBar().setFixedHeight(0)
        
        print(f"[TAB_HIDE] 隱藏後 QTabBar 高度: {self.tab_widget.tabBar().height()}")
        print(f"[TAB_HIDE] 標籤隱藏檢查完成")
        
    def second_tab_check(self):
        """第二次標籤檢查（延遲2秒後）- 簡化版本"""
        print(f"[TAB_HIDE] 延遲檢查 - QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] 延遲檢查 - QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
    def third_tab_check(self):
        """第三次標籤檢查（延遲5秒後）- 簡化版本"""
        print(f"[TAB_HIDE] 最終檢查 - QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        print(f"[TAB_HIDE] 最終檢查 - QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
        # 檢查 TabButtonsContainer 狀態
        corner_widget = self.tab_widget.cornerWidget(Qt.TopRightCorner)
        if corner_widget:
            print(f"[TAB_HIDE] TabButtonsContainer 可見性: {corner_widget.isVisible()}")
            print(f"[TAB_HIDE] TabButtonsContainer 大小: {corner_widget.size()}")
        print(f"[TAB_HIDE] 所有標籤隱藏檢查完成")
    
    # ==================== 同步功能實現 ====================
    
    def create_and_register_mdi_area(self, object_name):
        """創建MDI區域並自動註冊到主視窗"""
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName(object_name)
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 註冊到主視窗的MDI區域列表
        self.register_mdi_area(mdi_area)
        
        return mdi_area
    
    def register_mdi_area(self, mdi_area):
        """註冊MDI區域到主視窗（用於同步功能）"""
        print(f"🔗 [DEBUG] 嘗試註冊MDI區域: {mdi_area.objectName() if mdi_area else 'None'}")
        print(f"🔗 [DEBUG] 當前已註冊的MDI區域數量: {len(self.mdi_areas)}")
        print(f"🔗 [DEBUG] 主視窗類型: {type(self).__name__}")
        
        if mdi_area not in self.mdi_areas:
            self.mdi_areas.append(mdi_area)
            print(f"✅ [MDI] MDI區域已註冊: {mdi_area.objectName()}")
            print(f"✅ [MDI] 註冊後MDI區域總數: {len(self.mdi_areas)}")
        else:
            print(f"⚠️ [MDI] MDI區域已存在，跳過註冊: {mdi_area.objectName()}")
    
    def sync_to_all_mdi_subwindows(self, param_type, value):
        """同步參數到所有MDI子視窗"""
        print(f"🔄 [SYNC] 開始同步 {param_type} = {value} 到所有MDI子視窗")
        print(f"🔗 [SYNC] 已註冊的MDI區域數量: {len(self.mdi_areas)}")
        
        synced_count = 0
        for i, mdi_area in enumerate(self.mdi_areas):
            print(f"🔍 [SYNC] 檢查MDI區域 {i+1}/{len(self.mdi_areas)}: {mdi_area.objectName()}")
            synced_count += self.sync_to_mdi_area(mdi_area, param_type, value)
        
        print(f"✅ [SYNC] 完成同步，共更新 {synced_count} 個子視窗")
    
    def sync_to_mdi_area(self, mdi_area, param_type, value):
        """通知MDI區域內所有子視窗主頁面參數變更"""
        if not mdi_area:
            print(f"⚠️ [SYNC] MDI區域為空，跳過通知")
            return 0
            
        notified_count = 0
        subwindow_list = mdi_area.subWindowList()
        print(f"� [SYNC] 向MDI區域 {mdi_area.objectName()} 的 {len(subwindow_list)} 個子視窗發送參數變更通知")
        
        for subwindow in subwindow_list:
            window_title = subwindow.windowTitle() if subwindow else "未知視窗"
            print(f"� [SYNC] 發送通知到子視窗: {window_title} ({param_type}={value})")
            
            # 總是發送通知，讓子視窗自己決定是否響應
            if hasattr(subwindow, 'receive_main_window_update_notification'):
                try:
                    subwindow.receive_main_window_update_notification(param_type, value)
                    notified_count += 1
                    print(f"✅ [SYNC] 已發送通知到: {window_title}")
                except Exception as e:
                    print(f"❌ [SYNC] 發送通知失敗: {window_title}, 錯誤: {e}")
            else:
                print(f"⚠️ [SYNC] 子視窗 {window_title} 不支援通知機制")
        
        print(f"📊 [SYNC] MDI區域 {mdi_area.objectName()} 通知完成，共發送 {notified_count} 個通知")
        return notified_count
    
    # ==================== 同步功能實現結束 ====================
    
    def force_white_background(self, mdi_area):
        """深度修復QMdiArea背景問題 - 設定為白色"""
        #print(f"[DESIGN] DEBUG: force_white_background called for {mdi_area.objectName()}")
        
        # 方法1: 設置調色板
        mdi_area.setAutoFillBackground(True)
        palette = mdi_area.palette()
        palette.setColor(QPalette.Background, QColor(245, 245, 245))
        palette.setColor(QPalette.Base, QColor(245, 245, 245))
        palette.setColor(QPalette.Window, QColor(245, 245, 245))
        palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
        mdi_area.setPalette(palette)
        #print(f"[OK] Palette set for {mdi_area.objectName()}")
        
        # 方法2: 直接設置背景畫筆
        mdi_area.setBackground(QBrush(QColor(245, 245, 245)))
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
                        child_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        child_palette.setColor(QPalette.Window, QColor(245, 245, 245))
                        child.setPalette(child_palette)
                        child_count += 1
                        
                #print(f"[PACKAGE] Fixed {child_count} child widgets")
                        
                # 特別處理viewport
                if hasattr(mdi_area, 'viewport'):
                    viewport = mdi_area.viewport()
                    if viewport:
                        viewport.setAutoFillBackground(True)
                        viewport_palette = viewport.palette()
                        viewport_palette.setColor(QPalette.Background, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Base, QColor(245, 245, 245))
                        viewport_palette.setColor(QPalette.Window, QColor(245, 245, 245))
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
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} QScrollArea QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
            QMdiArea#{mdi_area.objectName()} > QWidget {{
                background-color: #F5F5F5 !important;
                background: #F5F5F5 !important;
            }}
        """)
        
        # 方法5: 創建白色背景小部件覆蓋（終極方案）
        def create_white_overlay():
            try:
                # 創建一個白色背景小部件作為底層
                overlay = QWidget(mdi_area)
                overlay.setStyleSheet("background-color: #F5F5F5;")
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
        QTimer.singleShot(300, create_white_overlay)
        
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
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        title_label = QLabel("🏠 主頁面")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 重置按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
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
                background-color: #FFFFFF;
                border-bottom: 1px solid #CCCCCC;
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
                color: #333333;
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
                color: #666666;
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
                color: #666666;
                font-size: 12px;
                background: transparent;
                padding: 15px;
                border: 1px solid #CCCCCC;
                border-radius: 6px;
            }
        """)
        welcome_layout.addWidget(info_label)
        
        # 創建MDI工作區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("WelcomeMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 強制設置白色背景
        self.force_white_background(mdi_area)
        
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
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[STATS] 數據總覽")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
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
        
        # 深度修復背景問題 - 多層次設置
        self.force_white_background(mdi_area)
        
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
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[CHART] 遙測分析")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建 MDI 區域（使用新的註冊方法）
        mdi_area = self.create_and_register_mdi_area("TelemetryAnalysisMDI")
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 深度修復背景問題 - 多層次設置
        self.force_white_background(mdi_area)
        
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
                background: #E8E8E8;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[FINISH] 圈速比較")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
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
                background: #F0F0F0;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #F8F8F8;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #E8E8E8;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #DDDDDD;
            }
        """)
        
        # 標題標籤
        title_label = QLabel("[TRACK] 賽道分析")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
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
        ready_label = QLabel("[OK] READY")
        ready_label.setObjectName("StatusReady")
        
        self.stats_label = QLabel("[STATS] Japan 2025 R")
        self.stats_label.setObjectName("StatusStats")
        
        drivers_label = QLabel("[FINISH] VER vs LEC")
        time_label = QLabel("[TIME] 13:28:51")
        
        status_bar.addWidget(ready_label)
        status_bar.addWidget(QLabel(" | "))
        status_bar.addWidget(self.stats_label)
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
        if hasattr(self, 'year_combo') and hasattr(self, 'race_combo') and hasattr(self, 'session_combo') and hasattr(self, 'stats_label'):
            year = self.year_combo.currentText()
            race = self.race_combo.currentText()
            session = self.session_combo.currentText()
            
            # 更新狀態列中的 STATS 信息
            self.stats_label.setText(f"[STATS] {race} {year} {session}")
            print(f"[STATUS] 更新狀態列: {race} {year} {session}")
            
            # 更新所有子窗口的標題
            self.update_all_window_titles()
            
    def get_current_parameters(self):
        """獲取當前參數設定"""
        display_race = self.race_combo.currentText() if hasattr(self, 'race_combo') else 'Japan'
        fastf1_race = self.get_fastf1_race_name(display_race)  # 轉換為 FastF1 期望的名稱
        
        return {
            'year': self.year_combo.currentText() if hasattr(self, 'year_combo') else '2025',
            'race': fastf1_race,  # 使用轉換後的名稱
            'session': self.session_combo.currentText() if hasattr(self, 'session_combo') else 'R'
        }
    
    def format_window_title(self, module_name):
        """格式化視窗標題為: 模組名稱_年分_賽事_賽段"""
        params = self.get_current_parameters()
        return f"{module_name}_{params['year']}_{params['race']}_{params['session']}"
    
    def update_all_window_titles(self):
        """更新所有子窗口的標題為新格式"""
        try:
            # 查找所有 MDI 區域
            for child in self.findChildren(CustomMdiArea):
                if child:
                    # 遍歷所有子窗口
                    for subwindow in child.subWindowList():
                        if isinstance(subwindow, PopoutSubWindow):
                            # 從當前標題提取模組名稱 (簡化提取邏輯)
                            current_title = subwindow.windowTitle()
                            if current_title and '_' in current_title:
                                # 如果已經是新格式，提取模組名稱
                                module_name = current_title.split('_')[0]
                            elif current_title:
                                # 如果是舊格式，直接使用
                                module_name = current_title.replace(' - 分析', '')
                            else:
                                # 如果沒有標題，跳過
                                continue
                            
                            # 生成新標題並更新
                            new_title = self.format_window_title(module_name)
                            subwindow.setWindowTitle(new_title)
                            
                            # 如果有自定義標題欄，也更新它
                            if hasattr(subwindow, 'title_bar') and subwindow.title_bar:
                                subwindow.title_bar.update_title(new_title)
                            
                            print(f"[TITLE] 更新子窗口標題: {module_name} -> {new_title}")
        except Exception as e:
            print(f"[ERROR] 更新標題時發生錯誤: {e}")
        
    def check_and_remove_welcome_page(self):
        """檢查並移除歡迎頁面，創建新的分析分頁"""
        # 檢查第一個分頁是否為歡迎頁面 (通過objectName識別)
        if self.tab_widget.count() > 0:
            first_tab_widget = self.tab_widget.widget(0)
            if first_tab_widget and first_tab_widget.objectName() == "welcome_tab":
                #print("[REFRESH] 首次使用分析功能，移除歡迎頁面並創建新分頁")
                
                # 移除歡迎分頁
                self.tab_widget.removeTab(0)
                
                # 創建新的空白分析分頁 (隱藏標題)
                analysis_tab = self.create_empty_analysis_tab()
                self.tab_widget.addTab(analysis_tab, "")
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
                background: #F0F0F0;
                border-bottom: 1px solid #CCCCCC;
            }
        """)
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)
        
        # 標題標籤
        title_label = QLabel("[CHART] 分析工作區")
        title_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
            }
        """)
        
        # 顯示所有資料按鈕
        reset_btn = QPushButton("顯示所有資料")
        reset_btn.setFixedSize(120, 25)
        reset_btn.setStyleSheet("""
            QPushButton {
                background: #F8F8F8;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 3px;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #E8E8E8;
                border-color: #999999;
            }
            QPushButton:pressed {
                background: #DDDDDD;
            }
        """)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(reset_btn)
        
        # 創建空白的MDI區域
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName("AnalysisMDIArea")
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 🔧 修復: 註冊MDI區域到主視窗
        self.register_mdi_area(mdi_area)
        print(f"✅ [MDI] 已註冊分析MDI區域: {mdi_area.objectName()}")
        
        # 連接重置按鈕
        reset_btn.clicked.connect(lambda: self.reset_all_charts(mdi_area))
        
        # 強制設置白色背景
        self.force_white_background(mdi_area)
        
        # 將工具欄和MDI添加到容器
        tab_layout.addWidget(toolbar)
        tab_layout.addWidget(mdi_area)
        
        return tab_container
        
    def create_analysis_window(self, function_name):
        """為功能樹的分析項目創建新視窗 - 升級支援模組化架構"""
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

        # 🔧 新增：嘗試使用模組化架構
        analysis_module = self._create_analysis_module(function_name)
        
        if analysis_module:
            # 使用新的模組化方式
            window_title = analysis_module.get_title()
            analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            
            # 設置模組的widget
            content_widget = analysis_module.get_widget()
            analysis_window.setWidget(content_widget)
            
            # 使用模組推薦的尺寸
            width, height = analysis_module.get_default_size()
            analysis_window.resize(width, height)
            
            print(f"✅ [MODULE] 使用模組化架構創建視窗: {window_title}")
            
        else:
            # 🔧 保留：舊版相容性邏輯
            window_title = self.format_window_title(self._extract_module_name(function_name))
            analysis_window = PopoutSubWindow(window_title, mdi_area)
            
            # 舊版內容創建邏輯
            content_widget = self._create_legacy_content(function_name)
            analysis_window.setWidget(content_widget)
            
            # 舊版尺寸設定
            if "降雨分析" in function_name:
                analysis_window.resize(800, 600)
            else:
                analysis_window.resize(450, 280)
            
            print(f"⚠️ [LEGACY] 使用舊版架構創建視窗: {window_title}")

        # 通用視窗設定
        mdi_area.addSubWindow(analysis_window)
        print(f"✅ [MDI] 已創建MDI子視窗: {analysis_window.windowTitle()}")
        
        analysis_window.show()
        
        # 計算新視窗位置（避免重疊）
        existing_windows = mdi_area.subWindowList()
        window_count = len(existing_windows)
        
        # 使用階梯式排列
        offset_x = (window_count % 4) * 30
        offset_y = (window_count // 4) * 30
        base_x = 10 + offset_x
        base_y = 10 + offset_y
        
        analysis_window.move(base_x, base_y)
    
    def _create_analysis_module(self, function_name):
        """創建分析模組實例"""
        try:
            # 導入模組工廠
            from modules.gui.base_analysis_module import ModuleFactory, ModuleTypes
            
            # 確保所有模組都被註冊
            import modules.gui.telemetry_modules  # 遙測模組
            import modules.gui.rain_analysis_module  # 降雨分析模組 - 會自動註冊適配器
            
            # 根據功能名稱映射到模組類型
            module_mapping = {
                "降雨分析": ModuleTypes.RAIN_ANALYSIS,
                "遙測": ModuleTypes.TELEMETRY_SPEED,
                "速度": ModuleTypes.TELEMETRY_SPEED,
                "煞車": ModuleTypes.TELEMETRY_BRAKE,
                "制動": ModuleTypes.TELEMETRY_BRAKE,
                "油門": ModuleTypes.TELEMETRY_THROTTLE,
                "節流": ModuleTypes.TELEMETRY_THROTTLE,
                "轉向": ModuleTypes.TELEMETRY_STEERING,
                "方向盤": ModuleTypes.TELEMETRY_STEERING,
                "統計": ModuleTypes.STATISTICS,
                "賽道": ModuleTypes.TRACK_MAP,
                "圈速": ModuleTypes.LAP_ANALYSIS
            }
            
            # 尋找匹配的模組類型
            module_type = None
            for keyword, mod_type in module_mapping.items():
                if keyword in function_name:
                    module_type = mod_type
                    break
            
            if module_type and ModuleFactory.module_exists(module_type):
                # 創建參數提供者
                parameter_provider = MainWindowParameterProvider(self)
                
                # 創建模組
                module = ModuleFactory.create_module(module_type, parameter_provider=parameter_provider)
                
                if module:
                    print(f"✅ [MODULE_FACTORY] 成功創建模組: {module_type} ({function_name})")
                    return module
                else:
                    print(f"❌ [MODULE_FACTORY] 模組創建失敗: {module_type}")
            else:
                print(f"⚠️ [MODULE_FACTORY] 未找到模組類型: {function_name} -> {module_type}")
                print(f"   可用模組: {ModuleFactory.get_available_modules()}")
            
        except ImportError as e:
            print(f"⚠️ [MODULE_FACTORY] 模組導入失敗: {e}")
        except Exception as e:
            print(f"❌ [MODULE_FACTORY] 模組創建異常: {e}")
        
        return None
    
    def _extract_module_name(self, function_name):
        """從功能名稱提取模組名稱"""
        return function_name.replace(" - 分析", "").replace("分析", "")
    
    def _create_legacy_content(self, function_name):
        """創建舊版內容 - 保持向後相容性"""
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
                return content
                
            except ImportError as e:
                print(f"[ERROR] 降雨分析模組導入失敗: {e}")
                return TelemetryChartWidget("speed")  # 後備方案
        elif "遙測" in function_name:
            return TelemetryChartWidget("speed")
        elif "煞車" in function_name or "制動" in function_name:
            return TelemetryChartWidget("brake")
        elif "油門" in function_name or "節流" in function_name:
            return TelemetryChartWidget("throttle")
        elif "轉向" in function_name or "方向盤" in function_name:
            return TelemetryChartWidget("steering")
        elif "賽道" in function_name:
            return TrackMapWidget()
        elif "圈速" in function_name:
            return self.create_lap_analysis_table()
        else:
            # 預設創建速度遙測圖表
            return TelemetryChartWidget("speed")
    
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
            
            # 🔧 修正：使用新的標題格式
            tab_title = f"降雨分析_{params['year']}_{params['race']}_{params['session']}"
            
            # 添加到主分頁控件 (使用空字串隱藏標題)
            tab_index = self.tab_widget.addTab(rain_widget, "")
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
        """應用風格H樣式 - 專業賽車分析工作站 (白色主題)"""
        style = """
        /* 主視窗 - 白色專業主題 */
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 標準白色 */
        QMenuBar {
            background-color: #F8F8F8;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 1px;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 6px;
            border-radius: 0px;
        }
        QMenuBar::item:selected {
            background-color: #E8E8E8;
        }
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            padding: 1px;
        }
        QMenu::item {
            padding: 2px 8px;
            border-radius: 0px;
        }
        QMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 右鍵選單 */
        #ContextMenu {
            background-color: #FFFFFF;
            border: 1px solid #AAAAAA;
            color: #333333;
            padding: 2px;
        }
        #ContextMenu::item {
            padding: 3px 12px;
            border-radius: 0px;
        }
        #ContextMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 左側面板白色主題 */
        #LeftPanel {
            background-color: #F8F8F8;
            color: #333333;
        }
        #FunctionTreeWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        
        /* 通用工具欄 - 白色主題 */
        QToolBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        QToolBar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        QToolBar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        QToolBar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 專業工具欄 */
        #ProfessionalToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        #ProfessionalToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        #ProfessionalToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        #ProfessionalToolbar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        #ProfessionalToolbar QLabel {
            color: #666666;
            font-size: 7pt;
            padding: 0px 2px;
        }
        
        /* 通用下拉選單 - 白色主題 */
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 2px 4px;
            border-radius: 0px;
        }
        QComboBox::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 15px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 3px solid #333333;
            width: 0px;
            height: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        QComboBox:hover {
            border-color: #888888;
        }
        
        /* 通用勾選框 - 白色主題 */
        QCheckBox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        QCheckBox::indicator:hover {
            border-color: #888888;
        }
        
        /* 通用按鈕 - 白色主題 */
        QPushButton {
            background-color: #F8F8F8;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 8pt;
            color: #333333;
        }
        QPushButton:hover {
            background-color: #E8E8E8;
            border-color: #999999;
        }
        QPushButton:pressed {
            background-color: #D8D8D8;
        }
        QPushButton:disabled {
            background-color: #F0F0F0;
            border-color: #E0E0E0;
            color: #999999;
        }
        
        /* 參數選擇框 */
        #ParameterCombo {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 7pt;
            padding: 1px 2px;
            border-radius: 0px;
        }
        #ParameterCombo::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 12px;
        }
        #ParameterCombo::down-arrow {
            image: none;
            border-left: 2px solid transparent;
            border-right: 2px solid transparent;
            border-top: 2px solid #333333;
            width: 0px;
            height: 0px;
        }
        #ParameterCombo QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        
        /* 功能樹標題 */
        #FunctionTreeTitle {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-weight: bold;
        }
        
        /* 通用樹狀控件 - 白色主題 */
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        QTreeWidget::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        QTreeWidget::item:hover {
            background-color: #F0F0F0;
        }
        QTreeWidget::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* 專業功能樹 */
        #ProfessionalFunctionTree {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        #ProfessionalFunctionTree::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        #ProfessionalFunctionTree::item:hover {
            background-color: #F0F0F0;
        }
        #ProfessionalFunctionTree::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* 系統日誌框架 - 白色主題 */
        #LogFrame {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        #LogTitle {
            background-color: #F0F0F0;
            color: #333333;
            font-weight: bold;
            font-size: 7pt;
            height: 12px;
            padding: 1px;
        }
        
        /* 系統日誌 - 白色主題 */
        #SystemLog {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #006600;
            font-family: "Consolas", "Courier New", monospace;
            font-size: 7pt;
            border-radius: 0px;
            selection-background-color: #E8E8E8;
        }
        QTextEdit#SystemLog {
            background-color: #FFFFFF;
        }
        QScrollArea QTextEdit#SystemLog {
            background-color: #FFFFFF;
        }
        
        /* MDI工作區 - 白色主題 - 增強版 */
        #ProfessionalMDIArea, #OverviewMDIArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
            border: 1px solid #CCCCCC;
        }
        QMdiArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea > QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea * {
            background-color: #F5F5F5 !important;
        }
        
        /* 通用分頁控件 - 白色主題 */
        QTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        QTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QTabWidget::tab-bar {
            alignment: left;
            height: 0px !important;  /* 強制隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
        }
        QTabWidget QTabBar {
            height: 0px !important;  /* 完全隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
            background: transparent !important;
            border: none !important;
        }
        QTabWidget QTabBar::tab {
            height: 0px !important;   /* 強制高度為0 */
            max-height: 0px !important;
            min-height: 0px !important;
            padding: 0px !important;  /* 移除內距 */
            margin: 0px !important;   /* 移除邊距 */
            border: none !important;  /* 移除邊框 */
            font-size: 0pt !important; /* 字體大小設為0 */
            background: transparent !important;
            color: transparent !important;
        }
        QTabWidget QTabBar::tab:selected {
            background-color: transparent;
            color: transparent;
            border: none;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        QTabWidget QTabBar::tab:hover {
            background-color: transparent;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        
        /* 專業分頁控件 - 白色主題 (完全隱藏標籤欄) */
        #ProfessionalTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        #ProfessionalTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            border-top: none !important;  /* 移除上方邊框 */
        }
        #ProfessionalTabWidget::tab-bar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            padding: 0px !important;
            margin: 0px !important;
            border: none !important;
            background: transparent !important;
            color: transparent !important;
            font-size: 0pt !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:selected {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:hover {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        
        /* 分頁控制區域 */
        #TabControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
        }
        
        /* 分頁按鈕容器 - 完全隱藏 */
        #TabButtonsContainer {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
            padding: 0px !important;
            margin: 0px !important;
        }
        
        /* 新增分頁按鈕 */
        #AddTabButton {
            background-color: #FFFFFF;
            color: #006600;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #AddTabButton:hover {
            background-color: #F0F0F0;
            border-color: #006600;
        }
        #AddTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 關閉分頁按鈕 */
        #CloseTabButton {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #CloseTabButton:hover {
            background-color: #F0F0F0;
            border-color: #333333;
        }
        #CloseTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 分頁數量標籤 */
        #TabCountLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 4px 8px;
        }
        
        /* 分析控制面板 */
        #AnalysisControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 連動控制勾選框 */
        #SyncWindowsCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncWindowsCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncWindowsCheckbox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        #SyncWindowsCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 遙測同步勾選框 */
        #SyncTelemetryCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncTelemetryCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncTelemetryCheckbox::indicator:checked {
            background-color: #00AA00;
            border-color: #00AA00;
        }
        #SyncTelemetryCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 控制標籤 */
        #ControlLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
        }
        
        /* 分析下拉選單 */
        #AnalysisComboBox {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            border-radius: 0px;
            padding: 3px 8px;
            font-size: 8pt;
            min-width: 80px;
        }
        #AnalysisComboBox::drop-down {
            background-color: #E8E8E8;
            border: none;
            width: 20px;
        }
        #AnalysisComboBox::down-arrow {
            border: none;
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #333333;
        }
        #AnalysisComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            selection-background-color: #0078D4;
            font-size: 8pt;
        }
        #AnalysisComboBox:hover {
            border-color: #888888;
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
            background-color: #FFFFFF;
            border: none;
        }
        
        /* 數據總覽分頁 */
        #DataOverviewTab {
            background-color: #FFFFFF;
        }
        #TabTitleLabel {
            color: #333333;
            font-size: 10pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #OverviewMDIArea {
            background-color: #F5F5F5;
            border: 1px solid #CCCCCC;
        }
        #StatsContent {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
            padding: 10px;
        }
        
        /* 設定對話框 */
        #SettingsDialog {
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #CCCCCC;
        }
        #DialogTitle {
            color: #333333;
            font-size: 12pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #SettingsGroup {
            color: #333333;
            font-size: 9pt;
            font-weight: bold;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            margin-top: 5px;
            padding-top: 5px;
        }
        #SettingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #666666;
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
            background-color: #FFFFFF;
            border: none;  /* 邊框由paintEvent繪製 */
            border-radius: 0px;
        }
        QMdiSubWindow {
            background-color: #FFFFFF;
            border: 2px solid #0078D4;  /* Windows 10/11標準藍色邊框，更明顯 */
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow:active {
            border: 2px solid #106EBE;  /* 活動視窗使用更深的藍色 */
        }
        QMdiSubWindow QWidget {
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow::title {
            background: #0078D4;  /* Windows 標準藍色標題欄 */
            color: #FFFFFF;  /* 白色文字 */
            height: 22px;
            padding: 2px 5px;
            margin: 0px;
            border: none;
            font-size: 11px;
            font-weight: normal;
            text-align: left;
        }
        
        QMdiSubWindow QWidget {
            border: none;
        }
        
        /* 子視窗包裝器 */
        #SubWindowWrapper {
            background-color: transparent;  /* 改為透明，讓底層調整區域可見 */
            color: #333333;
            border: none;
        }
        
        /* 視窗控制面板 */
        #WindowControlPanel {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 自定義標題欄 */
        #CustomTitleBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
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
        
        /* X軸連動按鈕 - 紅綠狀態指示 */
        #SyncButton {
            background-color: #FF4444;  /* 預設紅色 - 未連動 */
            color: #FFFFFF;
            border: 1px solid #CC0000;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SyncButton:hover {
            background-color: #FF6666;  /* 紅色懸停 */
        }
        #SyncButton:pressed {
            background-color: #CC0000;  /* 紅色按下 */
        }
        #SyncButton:checked {
            background-color: #00CC00;  /* 綠色 - 已連動 */
            border: 1px solid #009900;
        }
        #SyncButton:checked:hover {
            background-color: #00FF00;  /* 綠色懸停 */
        }
        
        /* 設定按鈕 */
        #SettingsButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SettingsButton:hover {
            background-color: #E8E8E8;
        }
        #SettingsButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 彈出按鈕 */
        #PopoutButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #PopoutButton:hover {
            background-color: #E8E8E8;
        }
        #PopoutButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 子視窗標題 */
        #SubWindowTitle {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
        }
        
        /* 獨立視窗 */
        #StandaloneWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        #StandaloneToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StandaloneToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px 6px;
            color: #333333;
            border-radius: 0px;
        }
        #StandaloneToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #CCCCCC;
        }
        
        /* 遙測圖表 */
        #TelemetryChart {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 賽道地圖 */
        #TrackMap {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 專業數據表格 */
        #ProfessionalDataTable {
            background-color: #FFFFFF;
            alternate-background-color: #F8F8F8;
            color: #333333;
            gridline-color: #CCCCCC;
            font-size: 8pt;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        #ProfessionalDataTable::item {
            padding: 1px;
            border: none;
        }
        #ProfessionalDataTable::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        #ProfessionalDataTable QHeaderView::section {
            background-color: #F0F0F0;
            color: #333333;
            padding: 1px;
            border: 1px solid #CCCCCC;
            font-weight: bold;
            font-size: 8pt;
            border-radius: 0px;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #F0F0F0;
            border-top: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StatusReady {
            color: #00AA00;
            font-weight: bold;
        }
        #VersionInfo {
            color: #0078D4;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #333333;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #F0F0F0;
            width: 6px;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #AAAAAA;
            border-radius: 0px;
            min-height: 10px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #888888;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* 分割器 */
        QSplitter::handle {
            background-color: #CCCCCC;
        }
        QSplitter::handle:horizontal {
            width: 2px;
        }
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        /* 強制所有容器為白底 */
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QFrame {
            background-color: #FFFFFF;
            color: #333333;
        }
        QSplitter {
            background-color: #F5F5F5;
        }
        QSplitter QWidget {
            background-color: #FFFFFF;
        }
        
        /* 強制所有MDI相關元素為白底 */
        QMdiArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea > QWidget {
            background-color: #FFFFFF;
        }
        
        /* 左側面板所有子元素強制白底 */
        QTreeWidget QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QTextEdit QWidget {
            background-color: #FFFFFF;
            color: #006600;
        }
        """
        
        #print("[DESIGN] DEBUG: Setting main window QSS styles...")
        #print(f"📄 QSS contains QMdiSubWindow border: {'QMdiSubWindow' in style and 'border:' in style}")
        #print(f"📄 QSS contains CustomTitleBar: {'CustomTitleBar' in style}")
        #print(f"📄 QSS total length: {len(style)} characters")
        # 臨時禁用有問題的樣式表，改用簡化版本
        simple_style = """
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        """
        self.setStyleSheet(simple_style)
        #print("[OK] 簡化版QSS styles applied successfully")
        
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
    #print("[MULTI] 多視窗分析界面，支援完整賽車數據處理")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
