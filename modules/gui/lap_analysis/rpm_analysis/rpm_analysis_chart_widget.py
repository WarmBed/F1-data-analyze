#!/usr/bin/env python3
"""
RPM分析圖表組件
使用 PyQt5 原生繪圖實現距離-RPM曲線圖表
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
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)
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
    logger.warning("連動管理器導入失敗，將使用舊版連動功能")

# 注意：此模組已完全採用PyQt5原生繪圖，不再依賴PyQt5.QtChart

class RPMChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """RPM圖表繪製組件 - 使用 PyQt5 原生繪圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化連動混入類
        self.__init_linkage__()
        
        # 設置更新回調（讓 Mixin 的連動方法能觸發 UI 更新）
        self.update_callback = self.update
        
        # 圖表設置 - 與速度分析保持完全一致
        self.margin_left = 80
        self.margin_right = 20
        self.margin_top = 20
        self.margin_bottom = 20
        
        # 數據存儲
        self.distance_data = []
        self.driver1_rpm = []
        self.driver2_rpm = []
        self.driver1_name = "Driver 1"
        self.driver2_name = "Driver 2"
        self.sectors = []
        
        # 🆕 時間軸數據（用於時間模式）
        self.use_time_axis = False
        self.driver1_time = []
        self.driver2_time = []
        
        # 數據範圍
        self.min_distance = 0
        self.max_distance = 5807
        self.min_rpm = 1000
        self.max_rpm = 12000
        
        # 視圖範圍 (用於縮放)
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_rpm = None
        self.view_max_rpm = None
        
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
        
        # ✅ 註冊到連動管理器（與 Speed Analysis 完全一致）
        if linkage_manager:
            linkage_manager.register_module(self, "rpm_analysis")
            # 🔧 同步當前的主連動開關狀態
            try:
                current_master_state = linkage_manager.is_master_linkage_enabled()
                self.set_master_linkage_enabled(current_master_state)
                logger.info(f"[RPM_CHART] ✅ 已註冊到連動管理器，主開關狀態: {'啟用' if current_master_state else '停用'}")
            except Exception as e:
                logger.error(f"[RPM_CHART] 同步連動狀態失敗: {e}")
        else:
            logger.warning(f"[RPM_CHART] 連動管理器不可用，連動功能將無法使用")
        
        # 拖拉狀態
        self.last_drag_pos = QPoint()
        
        # 視圖範圍（用於縮放和拖拉）
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_rpm = None
        self.view_max_rpm = None
        
        self.setMinimumSize(200, 100)  # 極小最小尺寸，提供更高的佈局靈活性
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)  # 設置擴展策略
    
    def set_rpm_data(self, distance: List[float], driver1_rpm: List[float], 
                     driver2_rpm: List[float], driver1_name: str = "Driver 1", 
                     driver2_name: str = "Driver 2", sectors: List[Dict] = None,
                     lap1: int = None, lap2: int = None,
                     driver1_time: List[float] = None, driver2_time: List[float] = None):
        """設置RPM數據
        
        Args:
            distance: 圈速距離數據
            driver1_rpm: 車手1的RPM數據
            driver2_rpm: 車手2的RPM數據
            driver1_name: 車手1名稱
            driver2_name: 車手2名稱
            sectors: 賽道區段信息
            lap1: 車手1的圈數（用於雙圈比較模式）
            lap2: 車手2的圈數（用於雙圈比較模式）
            driver1_time: 🆕 車手1時間軸數據（秒）
            driver2_time: 🆕 車手2時間軸數據（秒）
        """
        # 🆕 雙圈比較模式判斷
        is_single_driver_dual_lap = False
        if lap1 is not None and lap2 is not None and lap1 != lap2 and driver1_name == driver2_name:
            # 同車手不同圈數 → 雙圈比較模式
            is_single_driver_dual_lap = True
            original_driver = driver1_name
            # ✅ 使用 tr() 進行國際化 - 僅顯示圈數
            lap_format = tr('lap_only_format', '第{lap}圈')
            driver1_name = lap_format.format(lap=lap1)
            driver2_name = lap_format.format(lap=lap2)
            logger.debug(f"[RPM_CHART] 🔄 雙圈比較模式: {original_driver} {driver1_name} vs {driver2_name}")
        
        self.distance_data = distance
        self.driver1_rpm = driver1_rpm
        self.driver2_rpm = driver2_rpm
        self.driver1_name = driver1_name
        self.driver2_name = driver2_name
        self.sectors = sectors or []
        
        # 🆕 存儲時間軸數據
        self.driver1_time = driver1_time or []
        self.driver2_time = driver2_time or []
        
        # 計算數據範圍（🆕 支持時間軸模式）
        if self.use_time_axis and self.driver1_time:
            self.min_distance = min(self.driver1_time)
            self.max_distance = max(self.driver1_time)
        elif distance:
            self.min_distance = min(distance)
            self.max_distance = max(distance)
        
        all_rpms = []
        if driver1_rpm:
            all_rpms.extend(driver1_rpm)
        if driver2_rpm:
            all_rpms.extend(driver2_rpm)
            
        if all_rpms:
            self.min_rpm = max(1000, min(all_rpms) - 500)
            self.max_rpm = max(all_rpms) + 500
        
        # 強制重繪
        self.repaint()
    
    def set_time_axis_mode(self, use_time_axis: bool):
        """🆕 設置時間軸模式
        
        Args:
            use_time_axis: True=使用時間軸, False=使用距離軸
        """
        if self.use_time_axis != use_time_axis:
            self.use_time_axis = use_time_axis
            logger.debug(f"[RPM_CHART] 🕒 時間軸模式切換: {use_time_axis}")
            
            # 重新計算 X 軸範圍
            if self.use_time_axis and self.driver1_time:
                self.min_distance = min(self.driver1_time)
                self.max_distance = max(self.driver1_time)
                logger.debug(f"[RPM_CHART] 時間範圍: {self.min_distance:.2f}s - {self.max_distance:.2f}s")
            elif self.distance_data:
                self.min_distance = min(self.distance_data)
                self.max_distance = max(self.distance_data)
                logger.debug(f"[RPM_CHART] 距離範圍: {self.min_distance:.0f}m - {self.max_distance:.0f}m")
            
            # 重置視圖範圍
            self.view_min_distance = None
            self.view_max_distance = None
            
            # 重繪圖表
            self.repaint()
    
    def reset_view(self):
        """重置視圖到原始範圍"""
        self.view_min_distance = None
        self.view_max_distance = None
        self.view_min_rpm = None
        self.view_max_rpm = None
        # 清除固定線 - 與速度分析保持一致
        self.show_fixed_line = False
        self.fixed_distance_value = None
        self.repaint()
    
    def reset_data(self):
        """重置所有數據和視圖"""
        self.distance_data = []
        self.driver1_rpm = []
        self.driver2_rpm = []
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
            
            # 4. 繪製RPM曲線
            self._draw_rpm_curves(painter, chart_rect)
            
            # 5.5. 繪製連動線 (使用混入類方法)
            if hasattr(self, 'distance_data') and self.distance_data is not None:
                self.draw_linkage_line(
                    painter, 
                    chart_rect, 
                    self.distance_data,
                    getattr(self, 'driver1_name', 'Driver1'),
                    getattr(self, 'driver2_name', 'Driver2'),
                    getattr(self, 'driver1_rpm', []),
                    getattr(self, 'driver2_rpm', []),
                    "RPM"
                )
            
            # 6. 繪製圖例
            self._draw_legend(painter)
            
            # 7. 繪製垂直線在最頂層（最後繪製，確保可見性）
            # 繪製固定線
            if self.show_fixed_line and self.fixed_distance_value is not None:
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
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
    
    def _draw_grid(self, painter: QPainter, chart_rect: QRect):
        """繪製網格"""
        painter.setPen(QPen(self.grid_color, 1))
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_rpm = self.view_min_rpm if self.view_min_rpm is not None else self.min_rpm
        current_max_rpm = self.view_max_rpm if self.view_max_rpm is not None else self.max_rpm
        
        # 垂直網格線 (距離)
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            num_v_lines = 10
            for i in range(num_v_lines + 1):
                distance = current_min_distance + (distance_range * i / num_v_lines)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                painter.drawLine(int(x), chart_rect.top(), int(x), chart_rect.bottom())
        
        # 水平網格線 (RPM) - 修正：與速度分析保持一致使用10條線
        rpm_range = current_max_rpm - current_min_rpm
        if rpm_range > 0:
            num_h_lines = 10  # 修正：改為10條線與速度分析一致
            for i in range(num_h_lines + 1):
                rpm = current_min_rpm + (rpm_range * i / num_h_lines)
                y = chart_rect.bottom() - (rpm - current_min_rpm) / rpm_range * chart_rect.height()
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
        current_min_rpm = self.view_min_rpm if self.view_min_rpm is not None else self.min_rpm
        current_max_rpm = self.view_max_rpm if self.view_max_rpm is not None else self.max_rpm
        
        # X軸標籤 (距離/時間) - 修正：與速度分析一致，只顯示偶數刻度
        distance_range = current_max_distance - current_min_distance
        if distance_range > 0:
            num_labels = 10  # 使用10個間隔
            for i in range(0, num_labels + 1, 2):  # 只顯示偶數刻度
                distance = current_min_distance + (distance_range * i / num_labels)
                x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                
                # 繪製刻度線
                painter.drawLine(int(x), chart_rect.bottom(), int(x), chart_rect.bottom() + 5)
                
                # 🆕 繪製標籤（根據時間軸模式選擇格式）
                if self.use_time_axis:
                    label = f"{distance:.1f}"  # 時間格式：一位小數
                else:
                    label = f"{distance:.0f}"  # 距離格式：整數
                painter.drawText(int(x - 20), chart_rect.bottom() + 20, 40, 20, 
                               Qt.AlignCenter, label)
        
        # Y軸標籤 (RPM) - 修正：與速度分析一致，只顯示偶數刻度
        rpm_range = current_max_rpm - current_min_rpm
        if rpm_range > 0:
            num_labels = 10  # 使用10個間隔
            for i in range(0, num_labels + 1, 2):  # 只顯示偶數刻度
                rpm = current_min_rpm + (rpm_range * i / num_labels)
                y = chart_rect.bottom() - (rpm - current_min_rpm) / rpm_range * chart_rect.height()
                
                # 繪製刻度線
                painter.drawLine(chart_rect.left() - 5, int(y), chart_rect.left(), int(y))
                
                # 繪製標籤
                label = f"{rpm:.0f}"
                painter.drawText(10, int(y - 10), self.margin_left - 20, 20, 
                               Qt.AlignRight | Qt.AlignVCenter, label)
        
        # 座標軸標題 - 使用統一字體
        title_font = QFont("Microsoft YaHei", 7)
        painter.setFont(title_font)
        
        # 🆕 X軸標題 - 根據時間軸模式選擇文字
        x_title_width = 100
        x_title_x = chart_rect.left() + (chart_rect.width() - x_title_width) // 2
        x_title_y = chart_rect.bottom() + 5
        if self.use_time_axis:
            painter.drawText(x_title_x, x_title_y, x_title_width, 20, Qt.AlignCenter, tr('time_s', '時間 (s)'))
        else:
            painter.drawText(x_title_x, x_title_y, x_title_width, 20, Qt.AlignCenter, tr('distance_m', '距離 (m)'))
        
        # Y軸標題 (旋轉文字) - 修正：與速度分析一致的位置
        painter.save()
        painter.translate(20, chart_rect.center().y())
        painter.rotate(-90)
        painter.drawText(-50, -10, 100, 20, Qt.AlignCenter, tr('telemetry_rpm', 'RPM'))
        painter.restore()
    
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
    
    def _draw_rpm_curves(self, painter: QPainter, chart_rect: QRect):
        """繪製RPM曲線"""
        if not self.distance_data:
            return
        
        # 🆕 根據時間軸模式選擇 X 軸數據源
        if self.use_time_axis and self.driver1_time and self.driver2_time:
            x_data_source = self.driver1_time  # 時間模式：使用時間數據
        else:
            x_data_source = self.distance_data  # 距離模式：使用距離數據
        
        # 設置裁剪區域，防止曲線繪製到圖表邊界之外
        painter.setClipRect(chart_rect)
        
        # 使用當前視圖範圍或原始範圍
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        current_min_rpm = self.view_min_rpm if self.view_min_rpm is not None else self.min_rpm
        current_max_rpm = self.view_max_rpm if self.view_max_rpm is not None else self.max_rpm
            
        distance_range = current_max_distance - current_min_distance
        rpm_range = current_max_rpm - current_min_rpm
        
        if distance_range <= 0 or rpm_range <= 0:
            return
        
        # 繪製車手1RPM曲線
        if self.driver1_rpm and len(self.driver1_rpm) == len(x_data_source):
            painter.setPen(QPen(self.driver1_color, 2))
            points = []
            
            for i, (distance, rpm) in enumerate(zip(x_data_source, self.driver1_rpm)):
                if current_min_distance <= distance <= current_max_distance:
                    x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                    y = chart_rect.bottom() - (rpm - current_min_rpm) / rpm_range * chart_rect.height()
                    points.append(QPoint(int(x), int(y)))
            
            # 繪製連線
            for i in range(len(points) - 1):
                painter.drawLine(points[i], points[i + 1])
        
        # 繪製車手2RPM曲線（🆕 使用 driver2_time）
        if self.driver2_rpm:
            # 🆕 車手2可能使用不同的時間數據（雙圈比較模式）
            if self.use_time_axis and self.driver2_time:
                x_data_source_driver2 = self.driver2_time
            else:
                x_data_source_driver2 = self.distance_data
            
            if len(self.driver2_rpm) == len(x_data_source_driver2):
                painter.setPen(QPen(self.driver2_color, 2))
                points = []
                
                for i, (distance, rpm) in enumerate(zip(x_data_source_driver2, self.driver2_rpm)):
                    if current_min_distance <= distance <= current_max_distance:
                        x = chart_rect.left() + (distance - current_min_distance) / distance_range * chart_rect.width()
                        y = chart_rect.bottom() - (rpm - current_min_rpm) / rpm_range * chart_rect.height()
                        points.append(QPoint(int(x), int(y)))
                
                # 繪製連線
                for i in range(len(points) - 1):
                    painter.drawLine(points[i], points[i + 1])
    
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
        
        # 計算當前位置對應的距離和RPM值
        current_min_distance = self.view_min_distance if self.view_min_distance is not None else self.min_distance
        current_max_distance = self.view_max_distance if self.view_max_distance is not None else self.max_distance
        distance_range = current_max_distance - current_min_distance
        
        # 🆕 根據時間軸模式選擇搜索數據源
        if self.use_time_axis and self.driver1_time:
            search_data = self.driver1_time
        else:
            search_data = self.distance_data
        
        if distance_range > 0 and search_data:
            # 計算距離/時間值
            relative_x = x_pos - chart_rect.left()
            distance_value = current_min_distance + (relative_x / chart_rect.width()) * distance_range
            
            # 找到最接近的數據點來獲取真實的RPM值
            driver1_rpm_at_position = None
            driver2_rpm_at_position = None
            
            # 在距離/時間數據中找到最接近的點
            if search_data and len(search_data) > 0:
                closest_index = 0
                min_distance_diff = abs(search_data[0] - distance_value)
                
                for i, dist in enumerate(search_data):
                    distance_diff = abs(dist - distance_value)
                    if distance_diff < min_distance_diff:
                        min_distance_diff = distance_diff
                        closest_index = i
                
                # 獲取對應的RPM值
                if closest_index < len(self.driver1_rpm):
                    driver1_rpm_at_position = self.driver1_rpm[closest_index]
                if closest_index < len(self.driver2_rpm):
                    driver2_rpm_at_position = self.driver2_rpm[closest_index]
            
            # 計算需要顯示的車手數量來調整標籤大小
            drivers_to_show = []
            
            # 只添加有效且不重複的車手資訊
            if driver1_rpm_at_position is not None and self.driver1_name:
                drivers_to_show.append((self.driver1_name, driver1_rpm_at_position, self.driver1_color))
            
            # 只有在非單車手模式且第二個車手數據不同時才添加第二個車手
            if (not getattr(self, 'is_single_driver', False) and 
                driver2_rpm_at_position is not None and 
                self.driver2_name and 
                self.driver2_name != self.driver1_name):
                drivers_to_show.append((self.driver2_name, driver2_rpm_at_position, self.driver2_color))
            
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
            # 🆕 根據時間軸模式選擇顯示格式
            if self.use_time_axis:
                painter.drawText(label_x + 5, text_y, f"{tr('time_label', '時間')}: {distance_value:.2f} s")
            else:
                painter.drawText(label_x + 5, text_y, f"{tr('distance_label', '距離')}: {distance_value:.0f} m")
            
            # 顯示車手RPM資訊
            for i, (driver_name, rpm, color) in enumerate(drivers_to_show):
                painter.setPen(QPen(color, 1))
                painter.drawText(label_x + 5, text_y + 15 + (i * 15), f"{driver_name}: {rpm:.0f} RPM")
    
    def clear_fixed_line(self):
        """清除固定線條"""
        self.show_fixed_line = False
        self.fixed_distance_value = None
        self.update()
        
    def reset_data(self):
        """重置所有數據和視圖"""
        self.distance_data = []
        self.driver1_rpm = []
        self.driver2_rpm = []
        self.sectors = []
        self.reset_view()
        self.update()
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 - 與速度分析完全一致"""
        legend_x = self.width() - 200  # 與速度分析一致的位置
        legend_y = 30                   # 與速度分析一致的位置
        
        painter.setFont(QFont("Arial", 9))  # 與速度分析一致的字體
        
        # 檢查是否為單車手模式
        is_single_driver = (self.driver1_name == self.driver2_name or 
                           not self.driver2_name or 
                           not self.driver2_rpm)
        
        # 車手1圖例 - 移除背景框，與速度分析保持一致
        painter.setPen(QPen(self.driver1_color, 2))  # 改為2像素粗細
        painter.drawLine(legend_x, legend_y, legend_x + 20, legend_y)
        painter.setPen(QPen(self.axis_color, 1))
        painter.drawText(legend_x + 25, legend_y - 5, 100, 20, Qt.AlignLeft | Qt.AlignVCenter, self.driver1_name)
        
        # 只有在非單車手模式且車手名稱不同時才顯示車手2圖例
        if not is_single_driver and self.driver2_name != self.driver1_name:
            painter.setPen(QPen(self.driver2_color, 2))  # 改為2像素粗細
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
                
                # Y軸移動（RPM）
                rpm_range = (self.view_max_rpm or self.max_rpm) - (self.view_min_rpm or self.min_rpm)
                rpm_move = dy * rpm_range / chart_rect.height()  # Y軸是倒置的
                
                # 更新視圖範圍
                if self.view_min_distance is None:
                    self.view_min_distance = self.min_distance
                    self.view_max_distance = self.max_distance
                if self.view_min_rpm is None:
                    self.view_min_rpm = self.min_rpm
                    self.view_max_rpm = self.max_rpm
                
                self.view_min_distance += distance_move
                self.view_max_distance += distance_move
                self.view_min_rpm += rpm_move
                self.view_max_rpm += rpm_move
            
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
            if self.view_min_rpm is None:
                self.view_min_rpm = self.min_rpm
                self.view_max_rpm = self.max_rpm
            
            # 計算當前滑鼠對應的數據值
            distance_range = self.view_max_distance - self.view_min_distance
            rpm_range = self.view_max_rpm - self.view_min_rpm
            
            mouse_distance = self.view_min_distance + mouse_rel_x * distance_range
            mouse_rpm = self.view_min_rpm + mouse_rel_y * rpm_range
            
            # 計算新的範圍
            new_distance_range = distance_range / zoom_factor
            new_rpm_range = rpm_range / zoom_factor
            
            # 更新視圖範圍，保持滑鼠位置不變
            self.view_min_distance = max(self.min_distance, 
                                       mouse_distance - new_distance_range * mouse_rel_x)
            self.view_max_distance = min(self.max_distance, 
                                       mouse_distance + new_distance_range * (1 - mouse_rel_x))
            
            self.view_min_rpm = max(self.min_rpm, 
                                  mouse_rpm - new_rpm_range * mouse_rel_y)
            self.view_max_rpm = min(self.max_rpm, 
                                  mouse_rpm + new_rpm_range * (1 - mouse_rel_y))
            
            self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        self.mouse_x = -1
        self.mouse_y = -1
        # 使用連動管理器發送連動清除信號
        if linkage_manager and self._is_linkage_fully_enabled():
            linkage_manager.send_x_linkage_clear(self)
        self.update()


class RPMAnalysisChartWidget(QWidget, LapAnalysisLinkageMixin, LapAnalysisLinkageDrawingMixin):
    """RPM分析圖表組件主容器"""
    
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
        
        # 🔴 移除容器類的重複註冊（內部的 RPMChartWidget 將在 _create_chart_area() 中註冊）
        # 避免雙重註冊導致的記憶體洩漏問題
        # if linkage_manager:
        #     linkage_manager.register_module(self, "rpm_analysis")
        #     # 🔧 修復：同步當前的主連動開關狀態
        #     try:
        #         current_master_state = linkage_manager.is_master_linkage_enabled()
        #         self.set_master_linkage_enabled(current_master_state)
        #         print(f"[RPM_CHART] ✅ 已註冊到連動管理器，主開關狀態: {'啟用' if current_master_state else '停用'}")
        #     except Exception as e:
        #         print(f"[ERROR] [RPM_CHART] 同步連動狀態失敗: {e}")
        # else:
        #     print(f"[WARNING] [RPM_CHART] 連動管理器不可用，連動功能將無法使用")
        
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
        self.chart_widget = RPMChartWidget()
        layout.addWidget(self.chart_widget)
        
        # 確保內部圖表組件也註冊到連動管理器
        if linkage_manager:
            linkage_manager.register_module(self.chart_widget, "rpm_analysis_chart")
        
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
        tyre_life_title = QLabel(f"🔄 {tr('lap_number_short', '圈數')}:")
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
            logger.debug(f"[RPM_CHART] 📊 設置統計面板顯示狀態: {'顯示' if visible else '隱藏'}")
            
            if visible:
                # 顯示統計面板
                self.stats_container.setVisible(True)
                self.stats_table.setVisible(True)
                self.toggle_button.setText("▲")
                self._adjust_table_height()
            else:
                # 隱藏整個統計容器
                self.stats_container.setVisible(False)
            
            logger.info(f"[RPM_CHART] ✅ 統計面板顯示狀態設置完成")
            return True
            
        except Exception as e:
            logger.error(f"[RPM_CHART] 設置統計面板顯示狀態失敗: {e}")
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
    
    def set_time_axis_mode(self, use_time_axis: bool):
        """🆕 設置時間軸模式（代理方法）"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.set_time_axis_mode(use_time_axis)
            logger.info(f"[RPM_WRAPPER] ✅ 時間軸模式已設置: {use_time_axis}")
        
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
            logger.error(f"更新狀態資訊失敗: {e}")
            # 發生錯誤時顯示預設值
            self.lap_time_label.setText(f"⏱️ {tr('lap_time', '圈時間')}: {tr('error', '錯誤')}")
            self.tyre_compound_label.setText(f"🛞 {tr('tire_compound', '輪胎配方')}: {tr('error', '錯誤')}")
    
    def update_rpm_data(self, data: Dict[str, Any]):
        """更新RPM數據 - 採用速度分析的更新邏輯"""
        self.current_data = data
        
        try:
            logger.debug(f"[RPM_CHART] ========== 更新RPM數據 ==========")
            logger.debug(f"[RPM_CHART] 收到數據鍵: {list(data.keys()) if data else 'None'}")
            
            if not data:
                logger.error(f"[RPM_CHART] 數據為空")
                return
            
            # 提取元數據
            metadata = data.get('metadata', {})
            rpm_data = data.get('rpm_data', {})
            statistics = data.get('statistics', {})
            
            logger.debug(f"[RPM_CHART] metadata 鍵: {list(metadata.keys()) if metadata else 'None'}")
            logger.debug(f"[RPM_CHART] rpm_data 鍵: {list(rpm_data.keys()) if rpm_data else 'None'}")
            logger.debug(f"[RPM_CHART] statistics 鍵: {list(statistics.keys()) if statistics else 'None'}")
            
            # 提取車手信息
            drivers = metadata.get('drivers', [])
            sectors = metadata.get('sectors', [])
            
            logger.debug(f"[RPM_CHART] 車手數量: {len(drivers)}")
            logger.debug(f"[RPM_CHART] 賽道區段: {len(sectors)}")
            
            # 提取RPM數據
            distance = rpm_data.get('distance', [])
            driver1_rpm = rpm_data.get('driver1_rpm', [])
            driver2_rpm = rpm_data.get('driver2_rpm', [])
            driver1_name = rpm_data.get('driver1_name', 'Driver 1')
            driver2_name = rpm_data.get('driver2_name', 'Driver 2')
            
            # 🆕 提取時間軸數據（用於時間模式）
            driver1_time = rpm_data.get('driver1_time_seconds', [])
            driver2_time = rpm_data.get('driver2_time_seconds', [])
            
            logger.debug(f"[RPM_CHART] 距離數據點: {len(distance)}")
            logger.debug(f"[RPM_CHART] 車手1 RPM數據點: {len(driver1_rpm)}")
            logger.debug(f"[RPM_CHART] 車手2 RPM數據點: {len(driver2_rpm)}")
            logger.debug(f"[RPM_CHART] 🕒 車手1 時間數據點: {len(driver1_time)}")
            logger.debug(f"[RPM_CHART] 🕒 車手2 時間數據點: {len(driver2_time)}")
            
            # 如果有車手信息，使用車手代碼作為名稱
            lap1 = None
            lap2 = None
            if len(drivers) >= 2:
                driver1_name = drivers[0].get('code', driver1_name)
                driver2_name = drivers[1].get('code', driver2_name)
                # 🆕 提取圈數信息（用於雙圈比較模式判斷）
                lap1 = drivers[0].get('lap_number')
                lap2 = drivers[1].get('lap_number')
                logger.debug(f"[RPM_CHART] 🔢 提取圈數: lap1={lap1}, lap2={lap2}")
                logger.debug(f"[RPM_CHART] 車手名稱更新: {driver1_name} vs {driver2_name}")
            elif len(drivers) == 1:
                driver1_name = drivers[0].get('code', driver1_name)
                lap1 = drivers[0].get('lap_number')
                logger.debug(f"[RPM_CHART] 單車手模式: {driver1_name}")
            
            # 🆕 雙圈比較模式判斷邏輯
            is_single_driver_mode = False
            is_dual_lap_mode = False
            
            if metadata.get('is_single_driver', False):
                # 明確標記的單車手模式
                is_single_driver_mode = True
                logger.debug(f"[RPM_CHART] 🔍 檢測到單車手模式標記")
            elif driver1_name == driver2_name:
                # 相同車手：需要進一步判斷是單車手還是雙圈比較
                if lap1 is not None and lap2 is not None and lap1 != lap2:
                    # 🆕 同車手不同圈數 → 雙圈比較模式
                    is_dual_lap_mode = True
                    is_single_driver_mode = False
                    logger.debug(f"[RPM_CHART] � 檢測到雙圈比較模式: {driver1_name} 第{lap1}圈 vs 第{lap2}圈")
                else:
                    # 同車手相同圈數或無圈數信息 → 單車手模式
                    is_single_driver_mode = True
                    logger.debug(f"[RPM_CHART] 🔍 檢測到相同車手比較（單車手模式）: {driver1_name}")
            elif len(drivers) == 1:
                # 只有一個車手的數據
                is_single_driver_mode = True
                logger.debug(f"[RPM_CHART] 🔍 檢測到單車手數據: {driver1_name}")
            
            if is_single_driver_mode:
                logger.debug(f"[RPM_CHART] 🎯 使用單車手模式顯示")
                # 清空車手2的數據，只顯示車手1
                driver2_rpm = []
                driver2_name = ""  # 單車手模式才清空車手2名稱
                lap2 = None  # 清空 lap2
            elif is_dual_lap_mode:
                logger.debug(f"[RPM_CHART] 🔄 使用雙圈比較模式顯示: {driver1_name} 第{lap1}圈 vs 第{lap2}圈")
                # 保持雙車手模式，但標籤會在 set_rpm_data 中修改
            else:
                # 雙車手模式 - 保持車手名稱不變
                logger.debug(f"[RPM_CHART] 🎯 使用雙車手模式顯示: {driver1_name} vs {driver2_name}")
            
            # 檢查數據完整性
            if not distance or not driver1_rpm:
                logger.error(f"[RPM_CHART] 關鍵數據缺失")
                logger.debug(f"[RPM_CHART] distance: {len(distance) if distance else 0} 點")
                logger.debug(f"[RPM_CHART] driver1_rpm: {len(driver1_rpm) if driver1_rpm else 0} 點")
                return
            
            # 更新圖表
            logger.debug(f"[RPM_CHART] 📊 更新圖表...")
            self.chart_widget.set_rpm_data(
                distance=distance,
                driver1_rpm=driver1_rpm,
                driver2_rpm=driver2_rpm,
                driver1_name=driver1_name,
                driver2_name=driver2_name,
                sectors=sectors,
                lap1=lap1,  # 🆕 傳遞圈數信息
                lap2=lap2,   # 🆕 傳遞圈數信息
                driver1_time=driver1_time,  # 🆕 時間軸數據
                driver2_time=driver2_time   # 🆕 時間軸數據
            )
            logger.info(f"[RPM_CHART] ✅ 圖表更新完成")
            
            # 更新統計表格
            logger.debug(f"[RPM_CHART] 📋 更新統計表格...")
            self._update_statistics_table(statistics, driver1_name, driver2_name)
            
            # 更新狀態資訊顯示
            logger.debug(f"[RPM_CHART] 📋 更新狀態資訊...")
            self._update_status_info(data)
            
            self.chart_updated.emit()
            logger.info(f"[RPM_CHART] ✅ 全部更新完成")
            
        except Exception as e:
            logger.error(f"[RPM CHART WIDGET] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _prepare_chart_data(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """準備圖表數據"""
        try:
            if 'rpm_telemetry' in data:
                # 直接RPM數據
                return self._parse_rpm_telemetry(data['rpm_telemetry'])
            
            elif 'speed_data' in data:
                # 從速度數據模擬RPM數據
                return self._simulate_rpm_from_speed(data['speed_data'])
            
            else:
                # 生成模擬數據
                return self._generate_mock_rpm_data()
                
        except Exception as e:
            logger.error(f"[RPM_CHART_WIDGET] 準備圖表數據失敗: {e}")
            return self._generate_mock_rpm_data()
    
    def _parse_rpm_telemetry(self, rpm_data: Dict[str, Any]) -> Dict[str, Any]:
        """解析RPM遙測數據"""
        distance = []
        driver1_rpm = []
        driver2_rpm = []
        
        # 解析車手1數據
        if 'driver1_rpm_data' in rpm_data:
            for point in rpm_data['driver1_rpm_data']:
                distance.append(point.get('distance', 0))
                driver1_rpm.append(point.get('rpm', 0))
        
        # 解析車手2數據
        if 'driver2_rpm_data' in rpm_data:
            for point in rpm_data['driver2_rpm_data']:
                driver2_rpm.append(point.get('rpm', 0))
        
        return {
            'distance': distance,
            'driver1_rpm': driver1_rpm,
            'driver2_rpm': driver2_rpm,
            'driver1_name': rpm_data.get('driver1_name', 'Driver 1'),
            'driver2_name': rpm_data.get('driver2_name', 'Driver 2'),
            'sectors': rpm_data.get('sectors', []),
            'engine_info': rpm_data.get('engine_info', {}),
            'track_info': rpm_data.get('track_info', {})
        }
            
    def _update_statistics_table(self, statistics: Dict, driver1_name: str, driver2_name: str):
        """更新統計表格 - 採用速度分析的表格風格"""
        logger.debug(f"[RPM_CHART] 📊 統計表格更新 - 收到statistics: {statistics}")
        
        if not statistics:
            logger.warning(f"[RPM_CHART] ⚠️  statistics 為空")
            return
            
        try:
            driver1_stats = statistics.get('driver1_stats', {})
            driver2_stats = statistics.get('driver2_stats', {})
            comparison = statistics.get('comparison', {})
            
            logger.debug(f"[RPM_CHART] driver1_stats: {driver1_stats}")
            logger.debug(f"[RPM_CHART] driver2_stats: {driver2_stats}")
            logger.debug(f"[RPM_CHART] comparison: {comparison}")
            
            # 準備表格數據
            rows = [
                ("最高轉速 (rpm)", 
                 f"{driver1_stats.get('max_rpm', 0):.0f}",
                 f"{driver2_stats.get('max_rpm', 0):.0f}",
                 f"{comparison.get('max_rpm_diff', 0):.0f}"),
                ("平均轉速 (rpm)",
                 f"{driver1_stats.get('avg_rpm', 0):.0f}",
                 f"{driver2_stats.get('avg_rpm', 0):.0f}",
                 f"{comparison.get('avg_rpm_diff', 0):.0f}"),
                ("最低轉速 (rpm)",
                 f"{driver1_stats.get('min_rpm', 0):.0f}",
                 f"{driver2_stats.get('min_rpm', 0):.0f}",
                 f"{comparison.get('min_rpm_diff', 0):.0f}")
            ]
            
            logger.debug(f"[RPM_CHART] 表格數據行: {rows}")
            
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
            
            logger.info(f"[RPM CHART WIDGET] ✅ 統計表格更新完成")
            
        except Exception as e:
            logger.error(f"[RPM CHART WIDGET] 更新統計表格失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def reload_data(self):
        """重新載入數據（提供給外部調用）"""
        if self.current_data:
            self.update_rpm_data(self.current_data)
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                             driver1: str = None, driver2: str = None,
                             lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """更新圈速參數並重新載入數據 - 與速度分析模組保持一致"""
        try:
            logger.debug(f"[RPM_CHART_WIDGET] 🔄 更新圈速參數: {year} {race} {session}")
            logger.debug(f"[RPM_CHART_WIDGET] 🏁 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            # 更新圈數顯示
            self.set_lap_numbers(lap1, lap2)
            
            # 如果有數據載入器，重新載入數據
            if hasattr(self, 'rpm_loader'):
                logger.debug(f"[RPM_CHART_WIDGET] 📦 找到RPM數據載入器，準備重新載入...")
                
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
                
                self.rpm_loader.load_rpm_analysis_data(session_info)
                logger.info(f"[RPM_CHART_WIDGET] ✅ 數據重新載入請求已發送")
                return True
            else:
                logger.warning(f"[RPM_CHART_WIDGET] ⚠️ 未找到RPM數據載入器，僅更新顯示")
                return True
                
        except Exception as e:
            logger.error(f"[RPM_CHART_WIDGET] 更新圈速參數失敗: {e}")
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
        logger.debug(f"[RPM_ANALYSIS] 🔄 reset_chart_view() 被調用")
        if hasattr(self, 'chart_widget') and self.chart_widget:
            logger.info(f"[RPM_ANALYSIS] ✅ 找到 chart_widget，調用 reset_view()")
            self.chart_widget.reset_view()
        else:
            logger.error(f"[RPM_ANALYSIS] ❌ 未找到 chart_widget 屬性")
            
    def clear_fixed_line(self):
        """清除固定線條 - 與速度分析保持一致"""
        if hasattr(self, 'chart_widget') and self.chart_widget:
            self.chart_widget.clear_fixed_line()

    
    def cleanup(self):
        """清理 Chart Widget 資源 - 防止記憶體洩漏"""
        try:
            logger.debug(f"[RPM_CHART] 🧹 開始清理資源...")
            
            # 0. 從連動管理器解除註冊（與 Speed Analysis 一致）
            try:
                from modules.gui.lap_analysis.linkage.linkage_manager import linkage_manager
                if linkage_manager:
                    linkage_manager.unregister_module(self)
                    logger.info(f"[RPM_CHART] ✅ 已從連動管理器解除註冊")
            except Exception as e:
                logger.warning(f"[RPM_CHART] ⚠️ 解除註冊警告: {e}")
            
            # 1. 清理 Matplotlib 圖表
            if hasattr(self, 'chart_widget') and self.chart_widget:
                if hasattr(self.chart_widget, 'figure') and self.chart_widget.figure:
                    try:
                        self.chart_widget.figure.clear()
                        import matplotlib.pyplot as plt
                        plt.close(self.chart_widget.figure)
                        self.chart_widget.figure = None
                        logger.info(f"[RPM_CHART] ✅ Matplotlib 圖表已清理")
                    except Exception as e:
                        logger.warning(f"[RPM_CHART] ⚠️ Matplotlib 清理警告: {e}")
                
                if hasattr(self.chart_widget, 'canvas') and self.chart_widget.canvas:
                    try:
                        self.chart_widget.canvas.deleteLater()
                        self.chart_widget.canvas = None
                        logger.info(f"[RPM_CHART] ✅ Canvas 已清理")
                    except Exception as e:
                        logger.warning(f"[RPM_CHART] ⚠️ Canvas 清理警告: {e}")
            
            # 2. 清理 QTableWidget 中的所有 Item
            if hasattr(self, 'stats_table') and self.stats_table:
                try:
                    for row in range(self.stats_table.rowCount()):
                        for col in range(self.stats_table.columnCount()):
                            item = self.stats_table.item(row, col)
                            if item:
                                self.stats_table.takeItem(row, col)
                                del item
                    self.stats_table.clear()
                    self.stats_table.deleteLater()
                    self.stats_table = None
                    logger.info(f"[RPM_CHART] ✅ QTableWidget 已完全清理")
                except Exception as e:
                    logger.warning(f"[RPM_CHART] ⚠️ QTableWidget 清理警告: {e}")
            
            # 3. 斷開 Signal 連接
            if hasattr(self, 'receiver') and self.receiver:
                try:
                    self.receiver.deleteLater()
                    self.receiver = None
                    logger.info(f"[RPM_CHART] ✅ Signal Receiver 已清理")
                except Exception as e:
                    logger.warning(f"[RPM_CHART] ⚠️ Receiver 清理警告: {e}")
            
            # 4. 清理數據引用
            data_attrs = ['telemetry_data', 'lap_data', 'rpm_data', 'driver1_data', 'driver2_data', 'cached_data']
            for attr in data_attrs:
                if hasattr(self, attr):
                    setattr(self, attr, None)
            logger.info(f"[RPM_CHART] ✅ 數據引用已清空")
            
            # 5. 清理 ChartWidget
            if hasattr(self, 'chart_widget') and self.chart_widget:
                try:
                    self.chart_widget.deleteLater()
                    self.chart_widget = None
                    logger.info(f"[RPM_CHART] ✅ ChartWidget 已清理")
                except Exception as e:
                    logger.warning(f"[RPM_CHART] ⚠️ ChartWidget 清理警告: {e}")
            
            # 6. 清理資料載入器引用
            if hasattr(self, 'rpm_loader'):
                self.rpm_loader = None
                logger.info(f"[RPM_CHART] ✅ 資料載入器引用已清空")
            
            logger.info(f"[RPM_CHART] ✅ 資源清理完成")
            
        except Exception as e:
            logger.error(f"[RPM_CHART] cleanup 失敗: {e}")
            import traceback
            traceback.print_exc()

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QTimer
    import sys

    
    app = QApplication(sys.argv)
    
    # 測試RPM圖表組件
    widget = RPMAnalysisChartWidget()
    widget.setWindowTitle("🔄 RPM分析圖表測試")
    widget.resize(1000, 700)
    widget.show()
    
    # 載入測試數據
    QTimer.singleShot(1000, widget.reload_data)
    
    sys.exit(app.exec_())
