#!/usr/bin/env python3
"""
timediff分析圖表組件
使用 PyQt5 原生繪圖實現距離-timediff曲線圖表
支援雙車手對比和單場賽事車手分析，與系統其他組件保持一致的視覺風格
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

# 導入國際化模組
from core.gui_i18n import tr

# 導入全域信號管理器
try:
    from f1t_gui_main import global_signals
except ImportError:
    global_signals = None

# 導入新的連動管理器
try:
    from modules.gui.lap_analysis.linkage import LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin, linkage_manager
except ImportError:
    LapAnalysisLinkageMixin = object
    LapAnalysisLinkageDrawingMixin = object
    linkage_manager = None
    print("[WARNING] 連動管理器導入失敗，將使用舊版連動功能")

# 導入統一圖表基類的主題配置
try:
    from modules.gui.base.universal_chart_widget_base import ChartTheme
except ImportError:
    print("[WARNING] 統一圖表基類導入失敗，將使用預設配置")
    class ChartTheme:
        AXIS_TITLE_FONT = QFont("Microsoft YaHei", 7)
        TEXT_COLOR = QColor(50, 50, 50)

# 注意：此模組已完全採用PyQt5原生繪圖，不再依賴PyQt5.QtChart

class timediffChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """timediff圖表繪製組件 - 使用 PyQt5 原生繪圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動混入類
        self.__init_linkage__()
        
        # 🎯 設置統一的座標軸標題
        self.x_axis_title = tr('distance_m', '距離 (m)')
        self.y_axis_title = tr('cumulative_time_diff_s', 'Cumulative Time Difference (s)')  # ✅ 修正單位為 (s)
        self.x_title_position = "bottom-center"  # 置中顯示，避免文字被截斷
        self.y_title_position = "left-center"
        self.show_axis_titles = True
        
        # 初始化主題配置
        try:
            self.theme = ChartTheme()
        except:
            # 備用配置
            class DefaultTheme:
                AXIS_TITLE_FONT = QFont("Microsoft YaHei", 7)
                TEXT_COLOR = QColor(50, 50, 50)
            self.theme = DefaultTheme()
        
        # 圖表設置 - 與速度分析保持完全一致
        self.margin_left = 80
        self.margin_right = 20
        self.margin_top = 20
        self.margin_bottom = 20
        
        # 數據存儲
        self.distance_data = []
        self.driver1_timediff = []
        self.driver2_timediff = []
        self.driver1_name = "Driver 1"
        self.driver2_name = "Driver 2"
        self.sectors = []
        
        # 時間軸數據 (支援時間 vs 距離切換)
        self.use_time_axis = False
        self.driver1_time = []
        self.driver2_time = []
        
        # 數據範圍 - 累積時間差範圍設為-100到+100
        self.min_distance = 0
        self.max_distance = 5807
        self.min_timediff = -100  # 改為-100
        self.max_timediff = 100   # 改為+100
        
        # 視圖範圍 (用於縮放)
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_timediff = None
        self.view_max_timediff = None
        
        # 顏色設置 - 與速度分析完全一致
        self.bg_color = QColor(255, 255, 255)
        self.grid_color = QColor(200, 200, 200)  # 修正：與速度分析一致
        self.axis_color = QColor(50, 50, 50)     # 修正：與速度分析一致
        self.driver1_color = QColor(0, 100, 200)  # 柔和藍色 - 車手1
        self.driver2_color = QColor(200, 50, 50)  # 柔和紅色 - 車手2
        self.sector_color = QColor(100, 100, 100, 100)  # 修正：半透明灰色
        
        # 滑鼠交互
        self.mouse_x = -1
        self.mouse_y = -1
        self.fixed_line_x = -1
        self.dragging = False
        self.last_drag_pos = QPoint()
        
        # 中鍵拖拉功能 (與速度分析一致)
        self.middle_dragging = False
        self.show_fixed_line = False
        self.fixed_distance_value = None
        
        # 啟用鼠標追蹤，讓鼠標移動時即時觸發事件
        self.setMouseTracking(True)
        
        self.setMinimumSize(200, 100)  # 極小最小尺寸，提供更高的佈局靈活性
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 設置擴展策略
    
    def set_timediff_data(self, distance: List[float], driver1_timediff: List[float], 
                     driver2_timediff: List[float], driver1_name: str = "Driver 1", 
                     driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                     lap1: int = None, lap2: int = None,
                     driver1_time: List[float] = None, driver2_time: List[float] = None):
        """設置timediff數據 - 支援時間軸模式
        
        Args:
            distance: 距離數據
            driver1_timediff: 累積時間差數據
            driver2_timediff: (unused for single-curve mode)
            driver1_name: 時間差標籤名稱
            driver2_name: (unused for single-curve mode)
            sectors: 賽道區段信息
            lap1: 車手1的圈數（用於雙圈比較模式）
            lap2: 車手2的圈數（用於雙圈比較模式）
            driver1_time: 車手1的時間序列數據（秒）
            driver2_time: 車手2的時間序列數據（秒）
        """
        # 🆕 雙圈比較模式判斷（對於時間差，標籤會顯示 "VER 第10圈 vs 第50圈"）
        if lap1 is not None and lap2 is not None and lap1 != lap2:
            # 提取原始車手名稱（如 "VER vs LEC" → "VER" or單車手）
            if " vs " in driver1_name:
                driver_codes = driver1_name.split(" vs ")
                if len(driver_codes) == 2 and driver_codes[0] == driver_codes[1]:
                    # 同車手雙圈比較
                    original_driver = driver_codes[0]
                    # ✅ 使用 tr() 進行國際化 - vs 格式（單行標籤）
                    lap_vs_format = tr('lap_vs_lap_format', '{driver} 第{lap1}圈 vs 第{lap2}圈')
                    driver1_name = lap_vs_format.format(driver=original_driver, lap1=lap1, lap2=lap2)
                    print(f"[timediff_CHART] 🔄 雙圈比較模式: {driver1_name}")
        
        self.distance_data = distance
        self.driver1_timediff = driver1_timediff
        self.driver2_timediff = driver2_timediff
        self.driver1_name = driver1_name
        self.driver2_name = driver2_name
        self.sectors = sectors or []
        
        # 存儲時間數據
        self.driver1_time = driver1_time if driver1_time else []
        self.driver2_time = driver2_time if driver2_time else []
        
        # 計算數據範圍 - 根據時間軸模式選擇數據源
        if self.use_time_axis and self.driver1_time:
            self.min_distance = min(self.driver1_time)
            self.max_distance = max(self.driver1_time)
        elif distance:
            self.min_distance = min(distance)
            self.max_distance = max(distance)
        
        # 計算累積時間差的動態範圍
        all_timediffs = []
        if driver1_timediff:
            all_timediffs.extend(driver1_timediff)
        if driver2_timediff:
            all_timediffs.extend(driver2_timediff)
            
        if all_timediffs:
            # 為累積時間差計算合適的範圍
            data_min = min(all_timediffs)
            data_max = max(all_timediffs)
            
            # 添加一些邊距以便更好地顯示（時間差單位是秒，使用更合理的邊距）
            data_range = data_max - data_min
            if data_range < 0.5:
                # 數據範圍小於 0.5 秒，使用固定邊距
                margin = 0.1
            else:
                # 數據範圍較大，使用 10% 邊距
                margin = data_range * 0.1
            
            self.min_timediff = data_min - margin
            self.max_timediff = data_max + margin
            
            print(f"[timediff_CHART] 動態Y軸範圍: {self.min_timediff:.3f}s 到 {self.max_timediff:.3f}s (數據: {data_min:.3f}s ~ {data_max:.3f}s, 邊距: {margin:.3f}s)")
        else:
            # 沒有數據時使用預設範圍
            self.min_timediff = -1
            self.max_timediff = 1
        
        # 強制重繪
        self.repaint()
    
    def set_time_axis_mode(self, use_time: bool):
        """設置時間軸模式
        
        Args:
            use_time: True=使用時間軸, False=使用距離軸
        """
        if self.use_time_axis == use_time:
            return
        
        self.use_time_axis = use_time
        
        # 切換時重新計算 X 軸範圍
        if use_time and self.driver1_time:
            self.min_distance = min(self.driver1_time)
            self.max_distance = max(self.driver1_time)
        elif not use_time and self.distance_data:
            self.min_distance = min(self.distance_data)
            self.max_distance = max(self.distance_data)
        
        # 重置視圖範圍
        self.view_min_distance = None
        self.view_max_distance = None
        
        # 強制重繪
        self.update()
        self.repaint()
    
    def reset_view(self):
        """重置視圖到原始範圍"""
        print(f"[timediff_CHART] 🔄 reset_view() 被調用")
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_timediff = None
        self.view_max_timediff = None
        # 清除固定線 - 與速度分析保持一致
        self.show_fixed_line = False
        self.fixed_distance_value = None
        print(f"[timediff_CHART] ✅ 視圖範圍已重置，調用 repaint()")
        self.repaint()
        print(f"[timediff_CHART] ✅ reset_view() 完成")
    
    def reset_data(self):
        """重置所有數據和視圖"""
        self.distance_data = []
        self.driver1_timediff = []
        self.driver2_timediff = []
        self.sectors = []
        self.reset_view()
        self.repaint()
    
    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        try:
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
            
            # 1. 繪製網格
            self._draw_grid(painter, chart_rect)
            
            # 2. 繪製坐標軸
            self._draw_axes(painter, chart_rect)
            
            # 3. 繪製分段標記
            self._draw_sectors(painter, chart_rect)
            
            # 4. 繪製timediff曲線
            self._draw_timediff_curves(painter, chart_rect)
            
            # 5. 繪製連動線 (使用混入類方法)
            if hasattr(self, 'distance_data') and self.distance_data is not None:
                self.draw_linkage_line(
                    painter, 
                    chart_rect, 
                    self.distance_data,
                    getattr(self, 'driver1_name', 'Driver1'),
                    getattr(self, 'driver2_name', 'Driver2'),
                    getattr(self, 'driver1_timediff', []),
                    getattr(self, 'driver2_timediff', []),
                    "m"
                )
            
            # 6. 繪製圖例
            self._draw_legend(painter)
            
            # 7. 繪製垂直標籤線 (置頂層) - 確保標籤不被遮擋
            # 7.1 繪製固定線
            if self.show_fixed_line and self.fixed_distance_value is not None:
                current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
                current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
                distance_range = current_max_distance - current_min_distance
                
                if distance_range > 0 and current_min_distance <= self.fixed_distance_value <= current_max_distance:
                    # 計算固定距離值對應的X位置
                    relative_pos = (self.fixed_distance_value - current_min_distance) / distance_range
                    fixed_x = chart_rect.left() + relative_pos * chart_rect.width()
                    self._draw_tracking_line(painter, chart_rect, int(fixed_x), is_fixed=True)
            
            # 7.2 繪製滑鼠跟隨線
            if chart_rect.contains(self.mouse_x, self.mouse_y):
                self._draw_tracking_line(painter, chart_rect, self.mouse_x, is_fixed=False)
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        painter.setPen(QPen(self.grid_color, 1))
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_timediff = self.view_min_timediff if self.view_min_timediff is not None else self.min_timediff
        current_max_timediff = self.view_max_timediff if self.view_max_timediff is not None else self.max_timediff
        
        # 垂直網格線 (距離)
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            num_v_lines = 10
            for i in range(num_v_lines + 1):
                distance = current_min_distance + (distance_range * i / num_v_lines)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (timediff) - 修正：與速度分析保持一致使用10條線
        timediff_range = current_max_timediff - current_min_timediff
        if timediff_range > 0:
            num_h_lines = 10  # 修正：改為10條線與速度分析一致
            for i in range(num_h_lines + 1):
                timediff = current_min_timediff + (timediff_range * i / num_h_lines)
                y = chart_rect.bottom() - (timediff - current_min_timediff) / timediff_range * chart_rect.height()
                painter.drawLine(chart_rect.left(), int(y), chart_rect.right(), int(y))
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製坐標軸和標籤 - 與速度分析保持一致"""
        painter.setPen(QPen(self.axis_color, 2))
        
        # 繪製軸線 - 只繪製底邊和左邊，與速度分析一致
        painter.drawLine(chart_rect.left(), chart_rect.bottom(), chart_rect.right(), chart_rect.bottom())  # X軸
        painter.drawLine(chart_rect.left(), chart_rect.top(), chart_rect.left(), chart_rect.bottom())      # Y軸
        
        # 設置字體 - 與速度分析一致
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.setPen(QPen(self.axis_color, 1))
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_timediff = self.view_min_timediff if self.view_min_timediff is not None else self.min_timediff
        current_max_timediff = self.view_max_timediff if self.view_max_timediff is not None else self.max_timediff
        
        # X軸標籤 - 支援時間軸模式
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            num_labels = 10  # 使用10個間隔
            for i in range(0, num_labels + 1, 2):  # 只顯示偶數刻度
                distance = current_min_distance + (distance_range * i / num_labels)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                
                # 繪製刻度線
                painter.drawLine(int(x), chart_rect.bottom(), int(x), chart_rect.bottom() + 5)
                
                # 繪製標籤 - 時間模式使用 .1f (秒)，距離模式使用 .0f (米)
                if self.use_time_axis:
                    label = f"{distance:.1f}"
                else:
                    label = f"{distance:.0f}"
                painter.drawText(int(x - 20), chart_rect.bottom() + 20, 40, 20, 
                               Qt.AlignCenter, label)
        
        # Y軸標籤 (timediff) - 修正：與速度分析一致，只顯示偶數刻度
        timediff_range = current_max_timediff - current_min_timediff
        if timediff_range > 0:
            num_labels = 10  # 使用10個間隔
            for i in range(0, num_labels + 1, 2):  # 只顯示偶數刻度
                timediff = current_min_timediff + (timediff_range * i / num_labels)
                y = chart_rect.bottom() - (timediff - current_min_timediff) / timediff_range * chart_rect.height()
                
                # 繪製刻度線
                painter.drawLine(chart_rect.left() - 5, int(y), chart_rect.left(), int(y))
                
                # 繪製標籤（✅ 改為小數點後三位）
                label = f"{timediff:.3f}"
                painter.drawText(10, int(y - 10), self.margin_left - 20, 20, 
                               Qt.AlignRight | Qt.AlignVCenter, label)
        
        # 🎯 使用統一的座標軸標題繪製 
        if self.show_axis_titles:
            self._draw_axis_titles(painter, chart_rect)
    
    def _draw_sectors(self, painter: QPainter, chart_rect: QRect):
        """繪製分段標記"""
        if not self.sectors:
            return
            
        # 使用與速度分析相同的分段線設定
        sector_pen_color = QColor(120, 120, 120, 200)  # 更不透明的灰色
        painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))  # 增加線條寬度到2
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        
        distance_range = current_max_distance - current_min_distance
        if distance_range <= 0:
            return
            
        for sector in self.sectors:
            if 'end_distance' in sector:
                end_distance = sector['end_distance']
                x = chart_rect.left() + (end_distance - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
                
                # 繪製S1, S2, S3標籤 - 與速度分析完全一致
                if 'sector' in sector:
                    # 使用實線來繪製標籤
                    painter.setPen(QPen(self.sector_color, 1))
                    painter.setFont(QFont("Arial", 8))
                    label_y = chart_rect.bottom() + 50  # 在X軸下方
                    painter.drawText(int(x - 10), label_y, 20, 15,
                                   Qt.AlignCenter, f"S{sector['sector']}")
                    
                    # 恢復虛線樣式給下一條線
                    painter.setPen(QPen(sector_pen_color, 2, Qt.DashLine))
    
    def _draw_timediff_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製timediff曲線 - 支援時間軸模式"""
        if not self.distance_data:
            return
        
        # 設置裁剪區域，防止曲線繪製到圖表邊界之外
        painter.setClipRect(chart_rect)
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_timediff = self.view_min_timediff if self.view_min_timediff is not None else self.min_timediff
        current_max_timediff = self.view_max_timediff if self.view_max_timediff is not None else self.max_timediff
            
        distance_range = current_max_distance - current_min_distance
        timediff_range = current_max_timediff - current_min_timediff
        
        if distance_range <= 0 or timediff_range <= 0:
            return
        
        # 繪製零線 (Y=0 的水平線)
        if current_min_timediff <= 0 <= current_max_timediff:
            zero_y = chart_rect.bottom() - (0 - current_min_timediff) / timediff_range * chart_rect.height()
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))  # 灰色虛線
            painter.drawLine(chart_rect.left(), int(zero_y), chart_rect.right(), int(zero_y))
        
        # 繪製累積時間差異曲線 - 支援時間軸模式
        if self.driver1_timediff and len(self.driver1_timediff) == len(self.distance_data):
            points = []
            
            # 根據時間軸模式選擇 X 軸數據源
            x_data_source = self.driver1_time if self.use_time_axis else self.distance_data
            
            # 預先計算所有點位置
            for i, (x_value, timediff) in enumerate(zip(x_data_source, self.driver1_timediff)):
                if current_min_distance <= x_value <= current_max_distance:
                    x = chart_rect.left() + (x_value - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (timediff - current_min_timediff) / timediff_range * chart_rect.height()
                    points.append((QPoint(int(x), int(y)), timediff))
            
            # 根據數值正負分段繪製不同顏色
            for i in range(len(points) - 1):
                current_point, current_value = points[i]
                next_point, next_value = points[i + 1]
                
                # 根據當前段的數值決定顏色
                # 負值：driver1 比較快 (藍色)
                # 正值：driver2 比較快 (紅色)
                if current_value < 0 and next_value < 0:
                    # 整段都是負值，使用藍色
                    painter.setPen(QPen(QColor(0, 100, 200), 2))  # 藍色
                elif current_value > 0 and next_value > 0:
                    # 整段都是正值，使用紅色
                    painter.setPen(QPen(QColor(200, 50, 50), 2))   # 紅色
                else:
                    # 跨越零點的線段，使用中性顏色或漸變
                    painter.setPen(QPen(QColor(100, 100, 100), 2))  # 灰色
                
                painter.drawLine(current_point, next_point)
    
    def _draw_tracking_line(self, painter: QPainter, chart_rect: QRect, x_pos: int, is_fixed: bool):
        """繪製追蹤線和數值顯示"""
        if not chart_rect.contains(x_pos, chart_rect.center().y()):
            return
            
        # 設置線條樣式
        if is_fixed:
            # 固定線：實線，更明顯
            painter.setPen(QPen(QColor(0, 180, 0), 1.5, Qt.SolidLine))
        else:
            # 跟隨線：虛線，較淡
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
            
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 計算當前位置對應的距離和timediff值
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        distance_range = current_max_distance - current_min_distance
        
        if distance_range > 0 and self.distance_data:
            # 計算距離值
            relative_x = x_pos - chart_rect.left()
            distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
            
            # 找到最接近的數據點來獲取真實的timediff值
    def _draw_tracking_line(self, painter: QPainter, chart_rect: QRect, x_pos: int, is_fixed: bool):
        """繪製追蹤線和數值顯示 - 支援時間軸模式"""
        if not chart_rect.contains(x_pos, chart_rect.center().y()):
            return
            
        # 設置線條樣式
        if is_fixed:
            # 固定線：實線，更明顯
            painter.setPen(QPen(QColor(0, 180, 0), 1.5, Qt.SolidLine))
        else:
            # 跟隨線：虛線，較淡
            painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
            
        painter.drawLine(x_pos, chart_rect.top(), x_pos, chart_rect.bottom())
        
        # 計算當前位置對應的距離/時間和timediff值
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        distance_range = current_max_distance - current_min_distance
        
        if distance_range > 0 and self.distance_data:
            # 計算距離/時間值
            relative_x = x_pos - chart_rect.left()
            distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
            
            # 找到最接近的數據點來獲取真實的timediff值
            driver1_timediff_at_position = None
            driver2_timediff_at_position = None
            
            # 根據時間軸模式選擇搜索數據源
            search_data = self.driver1_time if self.use_time_axis else self.distance_data
            
            # 在數據中找到最接近的點
            if search_data and len(search_data) > 0:
                closest_index = 0
                min_time_diff = abs(search_data[0] - distance_value)
                
                for i, dist in enumerate(search_data):
                    time_diff = abs(dist - distance_value)
                    if time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_index = i
                
                # 獲取對應的timediff值
                if closest_index < len(self.driver1_timediff):
                    driver1_timediff_at_position = self.driver1_timediff[closest_index]
                if closest_index < len(self.driver2_timediff):
                    driver2_timediff_at_position = self.driver2_timediff[closest_index]
            
            # 計算需要顯示的車手數量來調整標籤大小
            drivers_to_show = []
            
            # 只添加有效且不重複的車手資訊
            if driver1_timediff_at_position is not None and self.driver1_name:
                drivers_to_show.append((self.driver1_name, driver1_timediff_at_position, self.driver1_color))
            
            # 只有在非單車手模式且第二個車手數據不同時才添加第二個車手
            if (not getattr(self, 'is_single_driver', False) and 
                driver2_timediff_at_position is not None and 
                self.driver2_name and 
                self.driver2_name != self.driver1_name):
                drivers_to_show.append((self.driver2_name, driver2_timediff_at_position, self.driver2_color))
            
            # 根據車手數量動態調整標籤高度
            base_height = 30  # 距離/時間資訊的基本高度
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
            
            # 繪製數值文字 - 條件化顯示距離或時間
            painter.setPen(QPen(QColor(50, 50, 50), 1))
            painter.setFont(QFont("Arial", 9))
            
            text_y = label_y + 15
            if self.use_time_axis:
                painter.drawText(label_x + 5, text_y, f"{tr('time_label', '時間')}: {distance_value:.2f} s")
            else:
                painter.drawText(label_x + 5, text_y, f"{tr('distance_label', 'Distance')}: {distance_value:.0f} m")
            
            # 顯示 timediff 資訊（僅顯示數值，不顯示車手名稱）
            for i, (driver_name, timediff, color) in enumerate(drivers_to_show):
                painter.setPen(QPen(color, 1))
                # ✅ 僅顯示數值，單位修正為 (s)
                painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{tr('time_diff_label', 'Time Diff')}: {timediff:.3f} s")
    
    def clear_fixed_line(self):
        """清除固定線條"""
        self.show_fixed_line = False
        self.fixed_distance_value = None
        self.update()
    
    def _draw_linkage_label(self, painter, chart_rect, x_pos, distance_data, 
                          driver1_name, driver2_name, driver1_data, driver2_data, data_label):
        """
        覆寫連動標籤繪製方法 - timediff 專用
        僅顯示數值，不顯示車手名稱和圈數
        """
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QColor, QFont, QBrush, QPen
        
        label_width = 160
        label_height = 45  # 減少高度（只有距離和數值兩行）
        label_x = x_pos + 10
        
        # 使用同步的Y軸位置計算標籤位置
        label_y = chart_rect.bottom() - int(self.linkage_y_relative * chart_rect.height()) - label_height // 2
        
        # 確保標籤不會超出圖表區域
        label_y = max(chart_rect.top() + 10, min(label_y, chart_rect.bottom() - label_height - 10))
        
        # 如果標籤會超出右邊界，則放在線的左邊
        if label_x + label_width > chart_rect.right():
            label_x = x_pos - label_width - 10
            
        # 繪製標籤背景
        painter.setBrush(QBrush(QColor(255, 255, 255, 230)))
        painter.setPen(QPen(QColor(128, 128, 128), 1))
        painter.drawRect(label_x, label_y, label_width, label_height)
        
        # 繪製距離或時間資訊（根據時間軸模式）
        painter.setPen(QPen(QColor(50, 50, 50), 1))
        painter.setFont(QFont("Arial", 9))
        
        # 檢查是否使用時間軸模式
        use_time_axis = getattr(self, 'use_time_axis', False)
        
        if use_time_axis:
            # 在時間軸模式下，linkage_distance_value 實際上已經是時間值（秒）
            painter.drawText(label_x + 5, label_y + 15, f"{tr('linkage_time', '連動時間')}: {self.linkage_distance_value:.2f} s")
        else:
            # 在距離模式下，linkage_distance_value 是距離值（米）
            painter.drawText(label_x + 5, label_y + 15, f"{tr('linkage_distance', '連動距離')}: {self.linkage_distance_value:.0f} m")
        
        # 顯示當前位置的數據資訊（僅數值）
        # 在時間軸模式下，使用 linkage_distance_value（時間值）在 driver1_time 中搜索
        # 在距離模式下，使用 linkage_distance_value（距離值）在 distance_data 中搜索
        driver1_time = getattr(self, 'driver1_time', None)
        
        if use_time_axis and driver1_time:
            search_data = driver1_time
        else:
            search_data = distance_data
            
        if search_data and driver1_data:
            closest_idx = self._find_closest_data_index(search_data, self.linkage_distance_value)
            
            if closest_idx is not None and closest_idx < len(driver1_data):
                value1 = self._coerce_numeric(driver1_data[closest_idx])
                painter.setPen(QPen(getattr(self, 'driver1_color', QColor(0, 100, 200)), 1))
                text_y = label_y + 30
                
                if value1 is not None:
                    # ✅ 僅顯示數值，不顯示車手名稱，單位修正為 (s)
                    painter.drawText(label_x + 5, text_y, f"{tr('time_diff_label', 'Time Diff')}: {value1:.3f} s")
                else:
                    painter.drawText(label_x + 5, text_y, f"{tr('time_diff_label', 'Time Diff')}: N/A")
        
    def reset_data(self):
        """重置所有數據和視圖"""
        self.distance_data = []
        self.driver1_timediff = []
        self.driver2_timediff = []
        self.sectors = []
        self.reset_view()
        self.update()
    
    def _draw_axis_titles(self, painter: QPainter, rect: QRect):
        """繪製座標軸標題 - 支援時間軸模式"""
        painter.setFont(self.theme.AXIS_TITLE_FONT)
        painter.setPen(QPen(self.theme.TEXT_COLOR))
        
        # X軸標題 - 支援時間軸模式
        if self.x_title_position == "bottom-left":
            # 🎯 位置在X軸0點左邊（水平顯示）
            x_title_rect = QRect(
                rect.left() - 40,           # 在X軸0點左邊
                rect.bottom() + 5,          # X軸下方一點點
                80, 20                      # 寬度足夠顯示標題
            )
            # ✅ Time Diff Analysis 的 X 軸永遠是時間，無論 use_time_axis 狀態
            painter.drawText(x_title_rect, Qt.AlignLeft | Qt.AlignVCenter, tr('time_s', 'Time (s)'))
        else:  # "bottom-center" (預設)
            # 位置在圖表底部中央
            x_title_rect = QRect(
                rect.center().x() - 50,     # 圖表中央
                rect.bottom() + 5,          # 圖表下方一點點
                100, 20
            )
            # ✅ Time Diff Analysis 的 X 軸永遠是時間，無論 use_time_axis 狀態
            painter.drawText(x_title_rect, Qt.AlignCenter, tr('time_s', 'Time (s)'))
        
        # Y軸標題
        if self.y_axis_title:
            painter.save()
            # 🎯 Y軸標題始終在Y軸中間（垂直顯示）
            y_center = rect.center().y()
            painter.translate(30, y_center)            # Y軸左側，確保可見
            painter.rotate(-90)                        # 逆時針旋轉90度
            y_title_rect = QRect(-50, -10, 100, 20)    # 更寬的矩形容納標題
            painter.drawText(y_title_rect, Qt.AlignCenter, self.y_axis_title)
            painter.restore()
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 - 顯示累積時間差異的含義"""
        legend_x = self.width() - 250  # 稍微左移以容納更長的文字
        legend_y = 30
        
        painter.setFont(QFont("Arial", 9))
        
        # 顯示累積時間差異的含義
        painter.setPen(QPen(QColor(0, 100, 200), 2))  # 藍色線條
        painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y - 5, 150, 20, Qt.AlignLeft | Qt.AlignVCenter, 
                        f"{self.driver1_name} {tr('leading', '領先')}")
        
        # 紅色線條和文字
        painter.setPen(QPen(QColor(200, 50, 50), 2))  # 紅色線條
        painter.drawLine(legend_x, legend_y + 20, legend_x + 20, legend_y + 20)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y + 15, 150, 20, Qt.AlignLeft | Qt.AlignVCenter, 
                        f"{self.driver2_name} {tr('leading', '領先')}")
        
        # 灰色零線
        painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.DashLine))
        painter.drawLine(legend_x, legend_y + 40, legend_x + 20, legend_y + 40)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y + 35, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, tr('zero_line', '零點線'))
    
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
                
                # Y軸移動（timediff）
                timediff_range = (self.view_max_timediff or self.max_timediff) - (self.view_min_timediff or self.min_timediff)
                timediff_move = dy * timediff_range / chart_rect.height()  # Y軸是倒置的
                
                # 更新視圖範圍
                if self.view_min_distance is None:
                    self.view_min_distance = self.min_distance
                    self.view_max_distance = self.max_distance
                if self.view_min_timediff is None:
                    self.view_min_timediff = self.min_timediff
                    self.view_max_timediff = self.max_timediff
                
                self.view_min_distance += distance_move
                self.view_max_distance += distance_move
                self.view_min_timediff += timediff_move
                self.view_max_timediff += timediff_move
            
            self.last_drag_pos = event.pos()
        
        # 發送X軸連動信號 (使用混入類方法)
        chart_rect = QRect(
            self.margin_left, self.margin_top,
            self.width() - self.margin_left - self.margin_right,
            self.height() - self.margin_top - self.margin_bottom
        )
        
        if chart_rect.contains(event.pos()):
            # 計算當前滑鼠對應的距離值
            current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
            current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
            distance_range = current_max_distance - current_min_distance
            
            if distance_range > 0:
                relative_x = event.x() - chart_rect.left()
                distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
                
                # 計算Y軸相對位置 (0.0=底部, 1.0=頂部)
                relative_y = (chart_rect.bottom() - event.y()) / chart_rect.height()
                relative_y = max(0.0, min(1.0, relative_y))  # 限制範圍
                
                # 使用連動管理器發送連動信號
                if linkage_manager and self._is_linkage_fully_enabled():
                    linkage_manager.send_x_linkage(distance_value, relative_y, self)
        
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
                    
                    # 使用連動管理器發送點擊連動信號
                    linkage_manager.send_click_linkage(self.fixed_distance_value, sender=self)
                    
                    self.update()
            
        elif event.button() == Qt.RightButton:
            # 右鍵點擊：清除固定線
            self.show_fixed_line = False
            self.fixed_distance_value = None
            
            # 使用連動管理器發送清除信號
            if linkage_manager and self.linkage_enabled:
                linkage_manager.send_click_linkage_clear(sender=self)
            
            self.update()
            
        elif event.button() == Qt.MiddleButton:
            # 中鍵按下：開始拖拉
            self.middle_dragging = True
            self.last_drag_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """滑鼠雙擊事件 - 清除固定線"""
        if event.button() == Qt.LeftButton:
            self.show_fixed_line = False
            self.fixed_distance_value = None
            
            # 使用連動管理器發送清除信號
            if linkage_manager and self.linkage_enabled:
                linkage_manager.send_click_linkage_clear(sender=self)
            
            self.update()
            
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
            if self.view_min_timediff is None:
                self.view_min_timediff = self.min_timediff
                self.view_max_timediff = self.max_timediff
            
            # 計算當前滑鼠對應的數據值
            distance_range = self.view_max_distance - self.view_min_distance
            timediff_range = self.view_max_timediff - self.view_min_timediff
            
            mouse_distance = self.view_min_distance + mouse_rel_x * distance_range
            mouse_timediff = self.view_min_timediff + mouse_rel_y * timediff_range
            
            # 計算新的範圍
            new_distance_range = distance_range / zoom_factor
            new_timediff_range = timediff_range / zoom_factor
            
            # 更新視圖範圍，保持滑鼠位置不變
            self.view_min_distance = max(self.min_distance, 
                                       mouse_distance - new_distance_range * mouse_rel_x)
            self.view_max_distance = min(self.max_distance, 
                                       mouse_distance + new_distance_range * (1 - mouse_rel_x))
            
            self.view_min_timediff = max(self.min_timediff, 
                                  mouse_timediff - new_timediff_range * mouse_rel_y)
            self.view_max_timediff = min(self.max_timediff, 
                                  mouse_timediff + new_timediff_range * (1 - mouse_rel_y))
            
            self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.mouse_y = -1
        # 使用連動管理器發送連動清除信號
        if linkage_manager and self._is_linkage_fully_enabled():
            linkage_manager.send_x_linkage_clear(self)
        self.update()


class timediffAnalysisChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """timediff分析圖表組件主容器"""
    
    # 信號定義
    lap_numbers_changed = pyqtSignal(int, int)  # 圈數變更信號
    data_updated = pyqtSignal(dict)  # 數據更新信號
    chart_updated = pyqtSignal()  # 圖表更新信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動混入類
        self.__init_linkage__()
        
        # 設置更新回調
        self.set_update_callback(self.update)
        
        # 數據狀態
        self.current_data = None
        
        # 初始化UI
        self._setup_ui()
        
        # 註冊到連動管理器
        if linkage_manager:
            linkage_manager.register_module(self, "timediff_analysis")
        
    def _setup_ui(self):
        """設置使用者介面 - 採用速度分析的垂直單欄布局"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)  # 移除外層邊距，避免與MDI雙重邊距
        main_layout.setSpacing(5)
        
        # 主內容分割器（垂直分割）
        self.main_splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(self.main_splitter)
        
        # 圖表區域
        chart_container = self._create_chart_area()
        self.main_splitter.addWidget(chart_container)
        
        # 統計信息容器（已隱藏）
        self.stats_container = self._create_stats_container()
        self.stats_container.setVisible(False)  # 🔒 永久隱藏統計面板
        self.main_splitter.addWidget(self.stats_container)
        
        # 設置分割器比例，讓圖表佔據全部空間（統計面板已隱藏）
        self.main_splitter.setSizes([1000, 0])  # 圖表:統計 = 1000:0（統計面板隱藏）
        
        # 設置分割器比例因子 (移除灰色樣式以使用系統默認)
        self.main_splitter.setStretchFactor(0, 1)  # 圖表區域可伸縮
        self.main_splitter.setStretchFactor(1, 0)  # 統計區域固定大小
        
    def _create_chart_area(self) -> QWidget:
        """創建圖表區域 - 採用速度分析的簡潔風格"""
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
        layout.setContentsMargins(0, 0, 0, 0)  # 實驗：移除圖表容器邊距
        
        # 創建圖表組件
        self.chart_widget = timediffChartWidget()
        layout.addWidget(self.chart_widget)
        
        # 確保內部圖表組件也註冊到連動管理器
        if linkage_manager:
            linkage_manager.register_module(self.chart_widget, "timediff_analysis_chart")
        
        return container
    
    def _create_stats_container(self) -> QWidget:
        """創建統計信息容器 - 採用速度分析的可摺疊設計"""
        container = QFrame()
        container.setFrameStyle(QFrame.StyledPanel)
        container.setMaximumHeight(60)  # 初始高度，僅顯示狀態資訊（狀態信息已隱藏）
        container.setMinimumHeight(60)
        container.setStyleSheet("""
            QFrame {
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                background-color: #ffffff;
            }
        """)
        
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(3)
        
        # 標題欄（包含標題和箭頭按鈕）
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 標題標籤
        title_label = QLabel(tr('detailed_statistics', '詳細統計信息'))
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
        self.toggle_button.setFixedSize(20, 20)
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
        
        # 車手狀態資訊欄（隱藏，只在主頁面工具欄顯示）
        self.status_info_widget = self._create_status_info_widget()
        self.status_info_widget.setVisible(False)  # 隱藏狀態信息區域
        main_layout.addWidget(self.status_info_widget)
        
        # 統計表格（預設隱藏）
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
        self.lap_time_label = QLabel(f"⏱️ {tr('lap_time', '圈時間')}: {tr('na', 'N/A')}")
        self.lap_time_label.setStyleSheet("font-size: 11px; color: #2c3e50;")
        layout.addWidget(self.lap_time_label)
        
        # 分隔線
        separator1 = QLabel("|")
        separator1.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator1)
        
        # 輪胎配方資訊  
        self.tyre_compound_label = QLabel(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('na', 'N/A')}")
        self.tyre_compound_label.setStyleSheet("font-size: 11px; color: #2c3e50;")
        layout.addWidget(self.tyre_compound_label)
        
        # 分隔線
        separator2 = QLabel("|")
        separator2.setStyleSheet("color: #bdc3c7;")
        layout.addWidget(separator2)
        
        # 輪胎圈數資訊
        tyre_life_container = QWidget()
        tyre_life_layout = QHBoxLayout(tyre_life_container)
        tyre_life_layout.setContentsMargins(0, 0, 0, 0)
        tyre_life_layout.setSpacing(5)
        
        # 標籤
        tyre_life_title = QLabel(tr('lap_number_label', '🔄 圈數:'))
        tyre_life_title.setStyleSheet("font-size: 11px; color: #2c3e50;")
        tyre_life_layout.addWidget(tyre_life_title)
        
        # 車手1圈數顯示（只讀）
        self.lap1_display = QLabel("1")
        self.lap1_display.setStyleSheet("""
            QLabel {
                font-size: 10px; 
                border: 1px solid #bdc3c7; 
                border-radius: 2px;
                padding: 2px;
                max-width: 40px;
                min-width: 40px;
                background-color: #ffffff;
                color: #2c3e50;
                text-align: center;
            }
        """)
        self.lap1_display.setAlignment(Qt.AlignCenter)
        tyre_life_layout.addWidget(self.lap1_display)
        
        # vs 標籤
        vs_label = QLabel("vs")
        vs_label.setStyleSheet("font-size: 10px; color: #7f8c8d;")
        tyre_life_layout.addWidget(vs_label)
        
        # 車手2圈數顯示（只讀）
        self.lap2_display = QLabel("1")
        self.lap2_display.setStyleSheet("""
            QLabel {
                font-size: 10px; 
                border: 1px solid #bdc3c7; 
                border-radius: 2px;
                padding: 2px;
                max-width: 40px;
                min-width: 40px;
                background-color: #ffffff;
                color: #2c3e50;
                text-align: center;
            }
        """)
        self.lap2_display.setAlignment(Qt.AlignCenter)
        tyre_life_layout.addWidget(self.lap2_display)
        
        layout.addWidget(tyre_life_container)
        
        layout.addStretch()  # 推到左側
        
        return status_widget
        
    def _setup_stats_table(self):
        """設置統計表格"""
        headers = [tr("item", "項目"), tr("driver1", "車手1"), tr("driver2", "車手2"), tr("difference", "差值")]
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
            self.stats_container.setMaximumHeight(60)  # 保持足夠高度顯示狀態欄（狀態信息已隱藏）
            self.stats_container.setMinimumHeight(60)
        else:
            # 顯示統計表格
            self.toggle_button.setText("▲")  # 向上箭頭表示可以收縮
            # 調用自適應高度函數
            self._adjust_table_height()
    
    def set_statistics_visibility(self, visible: bool) -> bool:
        """設置統計面板顯示狀態 - 供分析模組管理器調用"""
        try:
            print(f"[timediff_CHART] 📊 設置統計面板顯示狀態: {'顯示' if visible else '隱藏'}")
            
            if visible:
                # 顯示統計面板
                self.stats_container.setVisible(True)
                self.stats_table.setVisible(True)
                self.toggle_button.setText("▲")
                self._adjust_table_height()
            else:
                # 隱藏整個統計容器
                self.stats_container.setVisible(False)
            
            print(f"[timediff_CHART] ✅ 統計面板顯示狀態設置完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [timediff_CHART] 設置統計面板顯示狀態失敗: {e}")
            return False
            
    def _adjust_table_height(self):
        """自動調整表格高度"""
        if not self.stats_table.isVisible():
            return
            
        row_count = self.stats_table.rowCount()
        
        # 計算所需高度
        header_height = self.stats_table.horizontalHeader().height()
        row_height = self.stats_table.rowHeight(0) if row_count > 0 else 25
        
        # 總高度 = 標題欄高度 + 狀態欄高度 + 表格標題高度 + 所有行高度 + 邊距
        title_bar_height = 30  # 標題欄高度
        status_bar_height = 35  # 狀態資訊欄高度
        margins = 15  # 上下邊距
        
        # 即使沒有數據行，也要顯示表格標題
        if row_count == 0:
            # 最小展開高度：標題欄 + 狀態欄 + 表格標題 + 邊距 + 一些額外空間
            table_height = header_height + 30  # 保留一些空間
        else:
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
        
    def set_lap_numbers(self, lap1: int, lap2: int):
        """設置圈數顯示"""
        self.lap1_display.setText(str(lap1))
        self.lap2_display.setText(str(lap2))
        
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
                    lap_time1 = driver1.get('lap_time', tr('na', 'N/A'))
                    lap_time2 = driver2.get('lap_time', tr('na', 'N/A'))
                    self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {lap_time1} | {lap_time2}")
                    
                    # 輪胎配方
                    compound1 = driver1.get('compound', tr('na', 'N/A'))
                    compound2 = driver2.get('compound', tr('na', 'N/A'))
                    self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {compound1} | {compound2}")
                    
                    # 更新圈數輸入框（如果數據中有圈數信息）
                    if 'lap_number' in driver1 and 'lap_number' in driver2:
                        lap1 = driver1.get('lap_number', 1)
                        lap2 = driver2.get('lap_number', 1)
                        self.set_lap_numbers(lap1, lap2)
                
                # 單車手模式：顯示單一車手信息
                else:
                    driver = drivers[0]
                    lap_time = driver.get('lap_time', tr('na', 'N/A'))
                    compound = driver.get('compound', tr('na', 'N/A'))
                    
                    # 更新圈數輸入框（單車手模式）
                    if 'lap_number' in driver:
                        lap_number = driver.get('lap_number', 1)
                        self.set_lap_numbers(lap_number, lap_number)
                    
                    self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {lap_time}")
                    self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {compound}")
            else:
                # 沒有車手數據時的預設顯示
                self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {tr('na', 'N/A')}")
                self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('na', 'N/A')}")
                
        except Exception as e:
            print(f"[ERROR] 更新狀態資訊失敗: {e}")
            # 發生錯誤時顯示預設值
            self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {tr('error', '錯誤')}")
            self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('error', '錯誤')}")
    
    def update_timediff_data(self, data: Dict[str, Any]):
        """更新時間差數據 - 處理單一累積時間差曲線"""
        self.current_data = data
        
        try:
            print(f"[timediff_CHART] ========== 更新時間差數據 ==========")
            print(f"[timediff_CHART] 收到數據鍵: {list(data.keys()) if data else 'None'}")
            
            if not data:
                print(f"[ERROR] [timediff_CHART] 數據為空")
                return
            
            # 提取元數據
            metadata = data.get('metadata', {})
            timediff_data = data.get('timediff_data', {})
            statistics = data.get('statistics', {})
            
            print(f"[timediff_CHART] metadata 鍵: {list(metadata.keys()) if metadata else 'None'}")
            print(f"[timediff_CHART] timediff_data 鍵: {list(timediff_data.keys()) if timediff_data else 'None'}")
            print(f"[timediff_CHART] statistics 鍵: {list(statistics.keys()) if statistics else 'None'}")
            
            # 提取車手信息和賽道信息
            drivers = metadata.get('drivers', [])
            sectors = metadata.get('sectors', [])
            reference_info = metadata.get('reference_info', '')
            
            print(f"[timediff_CHART] 車手數量: {len(drivers)}")
            print(f"[timediff_CHART] 賽道區段: {len(sectors)}")
            print(f"[timediff_CHART] 參考信息: {reference_info}")
            
            # 提取時間差數據 - 單一累積時間差曲線
            # ⚠️ 原則1驗證：timediff 使用 'time' 作為 X 軸，不是 'distance'
            time_data = timediff_data.get('time', [])  # 使用 'time' 鍵名匹配 data loader 結構
            cumulative_diff = timediff_data.get('cumulative_time_difference', [])
            reference = timediff_data.get('reference', '')
            
            # 🆕 提取時間數據（用於時間軸模式）
            # ⚠️ Time Diff Analysis 直接使用 reference_time 作為 X 軸
            # 不需要 driver1_time_seconds，因為 time_data 已經是時間序列
            driver1_time = time_data  # 使用 reference_time 作為時間軸 X 軸數據
            driver2_time = []  # Time Diff 不需要第二個時間序列
            print(f"[timediff_CHART] 🕒 driver1_time 數據點 (使用 reference_time): {len(driver1_time)}")
            print(f"[timediff_CHART] 🕒 driver2_time 數據點: {len(driver2_time)}")
            driver1_name = timediff_data.get('driver1_name', 'Time Difference')
            
            print(f"[timediff_CHART] 時間數據點 (X軸): {len(time_data)}")  # 修正：time_data 不是 distance
            print(f"[timediff_CHART] 累積時間差數據點: {len(cumulative_diff)}")
            print(f"[timediff_CHART] 參考: {reference}")
            
            # 設置車手名稱（時間差分析為單一曲線）
            lap1 = None
            lap2 = None
            if drivers and len(drivers) >= 2:
                # 🆕 提取圈數信息（用於雙圈比較模式判斷）
                lap1 = drivers[0].get('lap_number')
                lap2 = drivers[1].get('lap_number')
                driver1_name = f"{drivers[0].get('code', 'Driver1')} vs {drivers[1].get('code', 'Driver2')}"
                print(f"[timediff_CHART] 🔢 提取圈數: lap1={lap1}, lap2={lap2}")
                print(f"[timediff_CHART] 時間差標籤: {driver1_name}")
            elif len(drivers) == 1:
                driver1_name = drivers[0].get('code', driver1_name)
                lap1 = drivers[0].get('lap_number')
                print(f"[timediff_CHART] 單車手模式: {driver1_name}")
            
            # 時間差分析總是單一累積時間差曲線模式
            print(f"[timediff_CHART] 🎯 使用單一累積時間差曲線模式")
            
            # 檢查數據完整性（原則1：驗證 time_data 而非 distance）
            if not time_data or not cumulative_diff:
                print(f"[ERROR] [timediff_CHART] 關鍵數據缺失")
                print(f"[timediff_CHART] time_data (X軸): {len(time_data) if time_data else 0} 點")
                print(f"[timediff_CHART] cumulative_diff (Y軸): {len(cumulative_diff) if cumulative_diff else 0} 點")
                return
            
            # 更新圖表 - 使用單一累積時間差曲線（原則1：使用 time_data 作為 X 軸）
            print(f"[timediff_CHART] 📊 更新時間差圖表...")
            self.chart_widget.set_timediff_data(
                distance=time_data,  # ⚠️ 參數名為 'distance' 但實際傳遞時間數據（保持接口兼容性）
                driver1_timediff=cumulative_diff,  # 累積時間差作為主要曲線
                driver2_timediff=[],  # 空的第二條曲線
                driver1_name=driver1_name,
                driver2_name="",  # 空的第二個名稱
                sectors=sectors,
                lap1=lap1,  # 🆕 傳遞圈數信息
                lap2=lap2,  # 🆕 傳遞圈數信息
                driver1_time=driver1_time,  # 🆕 時間軸數據
                driver2_time=driver2_time   # 🆕 時間軸數據
            )
            print(f"[timediff_CHART] ✅ 圖表更新完成")
            
            # 更新統計表格
            print(f"[timediff_CHART] 📋 更新統計表格...")
            self._update_statistics_table(statistics, driver1_name, "")
            
            # 更新狀態資訊顯示
            print(f"[timediff_CHART] 📋 更新狀態資訊...")
            self._update_status_info(data)
            
            self.chart_updated.emit()
            print(f"[timediff_CHART] ✅ 全部更新完成")
            
        except Exception as e:
            print(f"[ERROR] [timediff CHART WIDGET] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _prepare_chart_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """準備圖表數據"""
        try:
            if 'timediff_telemetry' in data:
                # 直接timediff數據
                return self._parse_timediff_telemetry(data['timediff_telemetry'])
            
            elif 'speed_data' in data:
                # 從速度數據模擬timediff數據
                return self._simulate_timediff_from_speed(data['speed_data'])
            
            else:
                # 生成模擬數據
                return self._generate_mock_timediff_data()
                
        except Exception as e:
            print(f"[ERROR] [timediff_CHART_WIDGET] 準備圖表數據失敗: {e}")
            return self._generate_mock_timediff_data()
    
    def _parse_timediff_telemetry(self, timediff_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析timediff遙測數據"""
        distance = []
        driver1_timediff = []
        driver2_timediff = []
        
        # 解析車手1數據
        if 'driver1_timediff_data' in timediff_data:
            for point in timediff_data['driver1_timediff_data']:
                distance.append(point.get('distance', 0))
                driver1_timediff.append(point.get('timediff', 0))
        
        # 解析車手2數據
        if 'driver2_timediff_data' in timediff_data:
            for point in timediff_data['driver2_timediff_data']:
                driver2_timediff.append(point.get('timediff', 0))
        
        return {
            'distance': distance,
            'driver1_timediff': driver1_timediff,
            'driver2_timediff': driver2_timediff,
            'driver1_name': timediff_data.get('driver1_name', 'Driver 1'),
            'driver2_name': timediff_data.get('driver2_name', 'Driver 2'),
            'sectors': timediff_data.get('sectors', []),
            'engine_info': timediff_data.get('engine_info', {}),
            'track_info': timediff_data.get('track_info', {})
        }
            
    def _update_statistics_table(self, statistics: Dict, driver1_name: str, driver2_name: str):
        """更新統計表格 - 時間差分析專用（單一累積時間差曲線）"""
        print(f"[timediff_CHART] 📊 統計表格更新 - 收到statistics: {statistics}")
        
        if not statistics:
            print(f"[timediff_CHART] ⚠️  statistics 為空")
            return
            
        try:
            # 時間差分析的統計結構：
            # statistics = {
            #     'difference': {max, min, avg, count},  # 累積時間差統計
            #     'time': {min, max, total_points}       # 時間範圍統計
            # }
            difference_stats = statistics.get('difference', {})
            time_stats = statistics.get('time', {})
            
            print(f"[timediff_CHART] difference_stats: {difference_stats}")
            print(f"[timediff_CHART] time_stats: {time_stats}")
            
            # 準備表格數據 - 時間差分析專用（原則2：參考 rain_analysis 單曲線模式）
            rows = [
                ("時間範圍", 
                 f"{time_stats.get('min', 0):.2f}s - {time_stats.get('max', 0):.2f}s",
                 "",
                 ""),
                ("最大時間差", 
                 f"{difference_stats.get('max', 0):.3f}s",
                 "",
                 ""),
                ("平均時間差",
                 f"{difference_stats.get('avg', 0):.3f}s",
                 "",
                 ""),
                ("最小時間差",
                 f"{difference_stats.get('min', 0):.3f}s",
                 "",
                 ""),
                ("數據點數",
                 f"{difference_stats.get('count', 0)}",
                 "",
                 "")
            ]
            
            print(f"[timediff_CHART] 表格數據行: {rows}")
            
            # 設置表格行數和數據
            self.stats_table.setRowCount(len(rows))
            
            for row_idx, (metric, val1, val2, diff) in enumerate(rows):
                self.stats_table.setItem(row_idx, 0, QTableWidgetItem(metric))
                self.stats_table.setItem(row_idx, 1, QTableWidgetItem(val1))
                self.stats_table.setItem(row_idx, 2, QTableWidgetItem(val2))
                self.stats_table.setItem(row_idx, 3, QTableWidgetItem(diff))
                
                # 設置右對齊（數值列）
                for col in [1, 2, 3]:
                    item = self.stats_table.item(row_idx, col)
                    if item:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            # 調整列寬
            header = self.stats_table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.Stretch)  # 項目列
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # 車手1
            header.setSectionResizeMode(2, QHeaderView.ResizeToContents)  # 車手2  
            header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # 差值
            
            # 自動調整表格高度
            self._adjust_table_height()
            
            # 強制 UI 刷新（原則1：確保界面更新）
            self.stats_table.viewport().update()
            self.stats_table.repaint()
            
            print(f"[timediff CHART WIDGET] ✅ 統計表格更新完成")
            
        except Exception as e:
            print(f"[ERROR] [timediff CHART WIDGET] 更新統計表格失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def set_time_axis_mode(self, use_time_axis: bool):
        """設置時間軸模式（代理方法）"""
        if hasattr(self, 'chart_widget') and self.chart_widget is not None:
            self.chart_widget.set_time_axis_mode(use_time_axis)
    
    def reload_data(self):
        """重新載入數據（提供給外部調用）"""
        if self.current_data:
            self.update_timediff_data(self.current_data)
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                             driver1: str = None, driver2: str = None,
                             lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """更新圈速參數並重新載入數據 - 與速度分析模組保持一致"""
        try:
            print(f"[timediff_CHART_WIDGET] 🔄 更新圈速參數: {year} {race} {session}")
            print(f"[timediff_CHART_WIDGET] 🏁 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            # 更新圈數顯示
            self.set_lap_numbers(lap1, lap2)
            
            # 如果有數據載入器，重新載入數據
            if hasattr(self, 'timediff_loader'):
                print(f"[timediff_CHART_WIDGET] 📦 找到timediff數據載入器，準備重新載入...")
                
                session_info = {
                    'year': int(year) if year.isdigit() else year,
                    'race': race,
                    'session': session,
                    'driver1': driver1 or 'VER',
                    'driver2': driver2 or 'VER',
                    'lap1': lap1,
                    'lap2': lap2,
                    'is_fastest_lap': is_fastest
                }
                
                self.timediff_loader.load_timediff_analysis_data(session_info)
                print(f"[timediff_CHART_WIDGET] ✅ 數據重新載入請求已發送")
                return True
            else:
                print(f"[timediff_CHART_WIDGET] ⚠️ 未找到timediff數據載入器，僅更新顯示")
                return True
                
        except Exception as e:
            print(f"[ERROR] [timediff_CHART_WIDGET] 更新圈速參數失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def resizeEvent(self, event):
        """視窗大小變化事件"""
        super().resizeEvent(event)
    
    def showEvent(self, event):
        """視窗顯示事件"""
        super().showEvent(event)
    
    def set_master_linkage_enabled(self, enabled: bool):
        """設置主視窗連動總開關狀態 - 轉發給圖表組件"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.set_master_linkage_enabled(enabled)
    
    def set_linkage_enabled(self, enabled: bool):
        """設置個別連動狀態 - 轉發給圖表組件"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.set_linkage_enabled(enabled)
    
    def reset_chart_view(self):
        """重置圖表視圖 - 與速度分析保持一致"""
        print(f"[timediff_ANALYSIS] 🔄 reset_chart_view() 被調用")
        if hasattr(self, 'chart_widget') and self.chart_widget:
            print(f"[timediff_ANALYSIS] ✅ 找到 chart_widget，調用 reset_view()")
            self.chart_widget.reset_view()
        else:
            print(f"[timediff_ANALYSIS] ❌ 未找到 chart_widget 屬性")
            
    def clear_fixed_line(self):
        """清除固定線條 - 與速度分析保持一致"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.clear_fixed_line()

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試timediff圖表組件
    widget = timediffAnalysisChartWidget()
    widget.setWindowTitle("🔄 timediff分析圖表測試")
    widget.resize(1000, 700)
    widget.show()
    
    # 載入測試數據
    QTimer.singleShot(1000, widget.reload_data)
    
    sys.exit(app.exec_())
