# -*- coding: utf-8 -*-
"""
Live Traffic Timeline Widget
============================

即時/歷史回放的車流時間線模組。
每圈完成時更新，顯示各車手的 traffic 狀態熱圖。

功能:
- 支援 Historical 和 Realtime 雙模式
- 每圈完成時計算 traffic_ratio (基於 X/Y 座標距離)
- 黑底風格的熱圖視覺化
- 與 Track Map、Circle Map 風格一致

Author: F1T Team
Date: 2025-12-23
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from PyQt5.QtCore import Qt, QRectF, QTimer, pyqtSignal
from PyQt5.QtGui import (
    QColor, QFont, QPainter, QPen, QBrush, QFontMetrics, QPainterPath
)
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy

from core.gui_i18n import tr
from core.logger import get_logger
from ..core.base_live_mdi import BaseLiveTimingMDI
from modules.gui.themes import color_palette_provider

logger = get_logger("live_timing.live_traffic_timeline", component="gui")


# =============================================================================
# Constants
# =============================================================================
TRAFFIC_DISTANCE_THRESHOLD_M = 50.0  # 前車距離門檻 (公尺)
LAP_TRAFFIC_RATIO_THRESHOLD = 0.3    # 單圈 traffic 比例門檻 (30%)

# 顏色定義 (黑底風格)
COLOR_CLEAN = QColor(76, 175, 80)      # 綠色 - Clean Lap
COLOR_TRAFFIC = QColor(255, 152, 0)    # 橙色 - In Traffic
COLOR_SC_VSC = QColor(100, 100, 100)   # 灰色 - SC/VSC
COLOR_NO_DATA = QColor(50, 50, 50)     # 深灰 - No Data
COLOR_BACKGROUND = QColor(26, 26, 26)  # 黑底
COLOR_TEXT = QColor(220, 220, 220)     # 淺灰文字
COLOR_AXIS = QColor(80, 80, 80)        # 軸線顏色

# 排除的非比賽車輛
NON_RACE_CAR_NUMBERS = {'241', '242', '243'}


@dataclass
class DriverTrafficData:
    """單一車手的 Traffic 追蹤資料"""
    driver_num: str
    tla: str = ""
    team_color: str = "CCCCCC"
    
    # 圈速追蹤
    last_completed_lap: int = 0
    laps_in_traffic: int = 0
    total_laps_analyzed: int = 0
    
    # 當前圈累積
    current_lap_samples: int = 0
    current_lap_traffic_samples: int = 0
    
    # 每圈狀態記錄: {lap_num: state} (0=clean, 1=traffic, 2=sc/vsc, -1=no_data)
    lap_states: Dict[int, int] = field(default_factory=dict)


class LiveTrafficTimelineWidget(QWidget):
    """
    即時 Traffic Timeline 圖表組件 (QPainter 黑底風格)
    
    顯示每位車手每一圈的 traffic 狀態熱圖
    """
    
    # 信號
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定 Live Timing 識別屬性
        self.setProperty("is_live_timing_widget", True)
        
        # 數據存儲
        self._drivers_data: Dict[str, DriverTrafficData] = {}
        self._driver_order: List[str] = []  # 按 traffic 比例排序
        self._max_lap: int = 0
        self._total_laps: int = 58  # 預設總圈數
        
        # 賽道長度估算 (用於 XY 座標轉公尺)
        self._track_length_est_m: float = 5000.0
        self._xy_scale: float = 0.1  # 每個 XY 單位對應的公尺數
        
        # Track Status (SC/VSC)
        self._current_track_status: str = "1"  # 1=Green
        self._sc_laps: Set[int] = set()
        
        # 當前圈的 Position 累積 (用於計算 traffic)
        self._current_lap_positions: Dict[str, List[Tuple[float, float]]] = {}
        
        # Layout margins
        self.margin_left = 50
        self.margin_right = 15
        self.margin_top = 30
        self.margin_bottom = 50
        
        # Cell dimensions
        self.cell_width = 12
        self.cell_height = 16
        self.cell_gap = 2
        
        # Hover state
        self.hover_driver: Optional[str] = None
        self.hover_lap: Optional[int] = None
        
        # 設定 widget 屬性
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMouseTracking(True)
        
        logger.info("[LIVE_TRAFFIC_TIMELINE] Widget initialized")
    
    def set_total_laps(self, total_laps: int):
        """設定總圈數"""
        if total_laps > 0:
            self._total_laps = total_laps
            logger.debug("[LIVE_TRAFFIC_TIMELINE] Total laps set to %d", total_laps)
    
    def set_track_length(self, length_m: float, xy_scale: float = 0.1):
        """設定賽道長度和 XY 縮放比例"""
        self._track_length_est_m = length_m
        self._xy_scale = xy_scale
        logger.debug("[LIVE_TRAFFIC_TIMELINE] Track length: %.1fm, XY scale: %.4f", 
                     length_m, xy_scale)
    
    def update_track_status(self, status: str):
        """更新賽道狀態"""
        self._current_track_status = str(status)
    
    def update_positions(self, drivers_data: Dict[str, Any], current_lap: int):
        """
        更新車手位置資料 - 每個 snapshot 調用
        
        累積當前圈的位置樣本，用於計算 traffic
        
        Args:
            drivers_data: {driver_num: {x, y, lap, position, ...}}
            current_lap: 當前最大圈數
        """
        if not drivers_data:
            return
        
        # 按位置排序車手 (用於計算前車距離)
        sorted_drivers = sorted(
            [(num, data) for num, data in drivers_data.items() 
             if num not in NON_RACE_CAR_NUMBERS and isinstance(data, dict)],
            key=lambda x: x[1].get('position', 999)
        )
        
        # 計算每位車手與前車的距離
        for idx, (driver_num, driver_data) in enumerate(sorted_drivers):
            x = driver_data.get('x')
            y = driver_data.get('y')
            lap = driver_data.get('lap', 0) or 0
            
            if x is None or y is None:
                continue
            
            # 初始化車手數據
            if driver_num not in self._drivers_data:
                tla = driver_data.get('driver_tla', driver_num)
                team_color = driver_data.get('team_color', 'CCCCCC')
                self._drivers_data[driver_num] = DriverTrafficData(
                    driver_num=driver_num,
                    tla=tla,
                    team_color=team_color
                )
            
            driver = self._drivers_data[driver_num]
            
            # 檢查圈數變化
            if lap > driver.last_completed_lap and driver.last_completed_lap > 0:
                # 完成一圈！計算上一圈的 traffic ratio
                self._finalize_lap(driver_num, driver.last_completed_lap)
            
            driver.last_completed_lap = lap
            
            # 累積當前圈的樣本
            driver.current_lap_samples += 1
            
            # 計算與前車的距離
            if idx > 0:  # 不是 P1
                front_driver_num, front_data = sorted_drivers[idx - 1]
                front_x = front_data.get('x')
                front_y = front_data.get('y')
                
                if front_x is not None and front_y is not None:
                    # 計算 XY 距離並轉換為公尺
                    dx = x - front_x
                    dy = y - front_y
                    distance_xy = math.sqrt(dx * dx + dy * dy)
                    distance_m = distance_xy * self._xy_scale
                    
                    # 處理 wrap-around (車手可能在賽道另一端)
                    if distance_m < 0:
                        distance_m += self._track_length_est_m
                    if distance_m > self._track_length_est_m:
                        distance_m = self._track_length_est_m - distance_m
                    
                    # 判斷是否在 traffic 中
                    if 0 < distance_m <= TRAFFIC_DISTANCE_THRESHOLD_M:
                        driver.current_lap_traffic_samples += 1
        
        # 更新最大圈數
        if current_lap > self._max_lap:
            self._max_lap = current_lap
            self.update()
    
    def _finalize_lap(self, driver_num: str, lap_num: int):
        """
        完成一圈的 traffic 計算
        
        Args:
            driver_num: 車手編號
            lap_num: 剛完成的圈數
        """
        if driver_num not in self._drivers_data:
            return
        
        driver = self._drivers_data[driver_num]
        
        # 檢查是否為 SC/VSC 圈
        is_sc_lap = lap_num in self._sc_laps or self._current_track_status in ('4', '6', '7')
        
        if is_sc_lap:
            # SC/VSC 圈
            driver.lap_states[lap_num] = 2
        elif driver.current_lap_samples > 0:
            # 計算 traffic ratio
            ratio = driver.current_lap_traffic_samples / driver.current_lap_samples
            
            if ratio >= LAP_TRAFFIC_RATIO_THRESHOLD:
                driver.lap_states[lap_num] = 1  # In Traffic
                driver.laps_in_traffic += 1
            else:
                driver.lap_states[lap_num] = 0  # Clean
            
            driver.total_laps_analyzed += 1
        else:
            driver.lap_states[lap_num] = -1  # No Data
        
        # 重置當前圈計數器
        driver.current_lap_samples = 0
        driver.current_lap_traffic_samples = 0
        
        # 記錄 SC/VSC 圈
        if self._current_track_status in ('4', '6', '7'):
            self._sc_laps.add(lap_num)
        
        # 更新排序
        self._update_driver_order()
        
        logger.debug("[LIVE_TRAFFIC_TIMELINE] Driver %s lap %d: state=%d", 
                     driver_num, lap_num, driver.lap_states.get(lap_num, -1))
    
    def _update_driver_order(self):
        """按 traffic 圈數排序車手 (多的在上面)"""
        self._driver_order = sorted(
            self._drivers_data.keys(),
            key=lambda d: self._drivers_data[d].laps_in_traffic,
            reverse=True
        )
    
    def set_driver_info(self, driver_info: Dict[str, Dict]):
        """設定車手資訊 (TLA, team_color)"""
        for driver_num, info in driver_info.items():
            if driver_num in self._drivers_data:
                self._drivers_data[driver_num].tla = info.get('tla', driver_num)
                self._drivers_data[driver_num].team_color = info.get('team_color', 'CCCCCC')
    
    def clear(self):
        """清除所有數據"""
        self._drivers_data.clear()
        self._driver_order.clear()
        self._max_lap = 0
        self._sc_laps.clear()
        self._current_lap_positions.clear()
        self.update()
    
    # =========================================================================
    # 繪圖方法
    # =========================================================================
    def paintEvent(self, event):
        """繪製熱圖"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), COLOR_BACKGROUND)
        
        if not self._driver_order or self._max_lap == 0:
            self._draw_no_data(painter)
            painter.end()
            return
        
        # 計算動態 cell 大小
        self._calculate_cell_dimensions()
        
        # 繪製各部分
        self._draw_lap_axis(painter)
        self._draw_driver_labels(painter)
        self._draw_heatmap(painter)
        self._draw_legend(painter)
        
        if self.hover_driver and self.hover_lap:
            self._draw_tooltip(painter)
        
        painter.end()
    
    def _calculate_cell_dimensions(self):
        """動態計算 cell 大小"""
        available_width = self.width() - self.margin_left - self.margin_right
        available_height = self.height() - self.margin_top - self.margin_bottom - 30  # legend
        
        num_laps = max(1, self._max_lap)
        num_drivers = max(1, len(self._driver_order))
        
        self.cell_width = max(8, (available_width - num_laps * self.cell_gap) // num_laps)
        self.cell_height = max(12, (available_height - num_drivers * self.cell_gap) // num_drivers)
        
        # 限制最大尺寸
        self.cell_width = min(self.cell_width, 20)
        self.cell_height = min(self.cell_height, 24)
    
    def _draw_no_data(self, painter: QPainter):
        """繪製無數據提示"""
        painter.setPen(QPen(COLOR_TEXT))
        font = QFont()
        font.setPointSize(12)
        painter.setFont(font)
        
        text = tr("live_traffic_timeline.waiting", "Waiting for data...")
        painter.drawText(self.rect(), Qt.AlignCenter, text)
    
    def _draw_lap_axis(self, painter: QPainter):
        """繪製圈數軸 (頂部)"""
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        painter.setPen(QPen(COLOR_TEXT))
        
        for lap in range(1, self._max_lap + 1):
            x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap)
            
            # 每 5 圈顯示數字
            if lap == 1 or lap % 5 == 0 or lap == self._max_lap:
                painter.drawText(
                    QRectF(x, 5, self.cell_width + 10, 20),
                    Qt.AlignLeft | Qt.AlignVCenter,
                    str(lap)
                )
    
    def _draw_driver_labels(self, painter: QPainter):
        """繪製車手標籤 (左側) - 與 Tyre Strategy 樣式一致"""
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        for idx, driver_num in enumerate(self._driver_order):
            driver = self._drivers_data[driver_num]
            y = self.margin_top + idx * (self.cell_height + self.cell_gap)
            
            # 獲取車隊顏色 (優先使用 color_palette_provider)
            team_color_hex = None
            try:
                color_qcolor = color_palette_provider.get_driver_color(driver.tla, fallback=True)
                if color_qcolor:
                    team_color_hex = color_qcolor.name()
            except Exception:
                pass
            
            # 備選：使用 driver data 中的 team_color
            if not team_color_hex:
                try:
                    team_color_hex = driver.team_color
                    if not team_color_hex.startswith('#'):
                        team_color_hex = f'#{team_color_hex}'
                except:
                    team_color_hex = '#CCCCCC'
            
            # 車手標籤背景 - 填充整個標籤區域 (與 Tyre Strategy 一致)
            painter.fillRect(
                2, int(y), self.margin_left - 5, int(self.cell_height),
                QColor(team_color_hex)
            )
            
            # TLA - 根據背景亮度動態調整文字顏色
            label = driver.tla
            text_color = '#000000' if self._is_light_color(team_color_hex) else '#FFFFFF'
            painter.setPen(QColor(text_color))
            painter.drawText(
                QRectF(5, y, self.margin_left - 10, self.cell_height),
                Qt.AlignLeft | Qt.AlignVCenter,
                label
            )
    
    def _is_light_color(self, color_hex: str) -> bool:
        """判斷顏色是否為淺色 (與 Tyre Strategy 一致)"""
        if not color_hex.startswith('#'):
            color_hex = f'#{color_hex}'
        
        try:
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance > 0.5
        except:
            return False
    
    def _draw_heatmap(self, painter: QPainter):
        """繪製熱圖格子"""
        for idx, driver_num in enumerate(self._driver_order):
            driver = self._drivers_data[driver_num]
            y = self.margin_top + idx * (self.cell_height + self.cell_gap)
            
            for lap in range(1, self._max_lap + 1):
                x = self.margin_left + (lap - 1) * (self.cell_width + self.cell_gap)
                state = driver.lap_states.get(lap, -1)
                
                # 選擇顏色
                if state == 0:
                    color = COLOR_CLEAN
                elif state == 1:
                    color = COLOR_TRAFFIC
                elif state == 2:
                    color = COLOR_SC_VSC
                else:
                    color = COLOR_NO_DATA
                
                # 繪製格子
                painter.fillRect(x, y, self.cell_width, self.cell_height, color)
                
                # Hover 高亮
                if driver_num == self.hover_driver and lap == self.hover_lap:
                    painter.setPen(QPen(Qt.white, 2))
                    painter.drawRect(x, y, self.cell_width, self.cell_height)
    
    def _draw_legend(self, painter: QPainter):
        """繪製圖例 (底部)"""
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        y = self.height() - 25
        x = self.margin_left
        box_size = 12
        spacing = 20
        
        legends = [
            (COLOR_CLEAN, tr("live_traffic_timeline.clean", "Clean Lap")),
            (COLOR_TRAFFIC, tr("live_traffic_timeline.traffic", "In Traffic")),
            (COLOR_SC_VSC, tr("live_traffic_timeline.sc_vsc", "SC/VSC")),
            (COLOR_NO_DATA, tr("live_traffic_timeline.no_data", "No Data")),
        ]
        
        for color, label in legends:
            painter.fillRect(x, y, box_size, box_size, color)
            painter.setPen(QPen(COLOR_TEXT))
            
            fm = QFontMetrics(font)
            text_width = fm.horizontalAdvance(label)
            painter.drawText(x + box_size + 5, y + box_size - 2, label)
            
            x += box_size + text_width + spacing
    
    def _draw_tooltip(self, painter: QPainter):
        """繪製 hover tooltip"""
        if not self.hover_driver or not self.hover_lap:
            return
        
        driver = self._drivers_data.get(self.hover_driver)
        if not driver:
            return
        
        state = driver.lap_states.get(self.hover_lap, -1)
        state_text = {
            0: tr("live_traffic_timeline.clean", "Clean"),
            1: tr("live_traffic_timeline.traffic", "Traffic"),
            2: tr("live_traffic_timeline.sc_vsc", "SC/VSC"),
            -1: tr("live_traffic_timeline.no_data", "No Data"),
        }.get(state, "Unknown")
        
        text = f"{driver.tla} - Lap {self.hover_lap}: {state_text}"
        
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        fm = QFontMetrics(font)
        
        text_width = fm.horizontalAdvance(text)
        text_height = fm.height()
        
        # Tooltip 位置
        tx = self.width() - text_width - 20
        ty = 10
        
        # 背景
        painter.fillRect(tx - 5, ty - 2, text_width + 10, text_height + 4, 
                        QColor(40, 40, 40, 220))
        painter.setPen(QPen(COLOR_TEXT))
        painter.drawText(tx, ty + text_height - 3, text)
    
    # =========================================================================
    # 滑鼠事件
    # =========================================================================
    def mouseMoveEvent(self, event):
        """滑鼠移動 - 更新 hover 狀態"""
        x = event.x()
        y = event.y()
        
        # 計算 hover 的格子
        old_driver = self.hover_driver
        old_lap = self.hover_lap
        
        self.hover_driver = None
        self.hover_lap = None
        
        if x >= self.margin_left and y >= self.margin_top:
            lap_idx = (x - self.margin_left) // (self.cell_width + self.cell_gap)
            driver_idx = (y - self.margin_top) // (self.cell_height + self.cell_gap)
            
            if 0 <= lap_idx < self._max_lap and 0 <= driver_idx < len(self._driver_order):
                self.hover_lap = lap_idx + 1
                self.hover_driver = self._driver_order[driver_idx]
        
        if old_driver != self.hover_driver or old_lap != self.hover_lap:
            self.update()
    
    def leaveEvent(self, event):
        """滑鼠離開"""
        self.hover_driver = None
        self.hover_lap = None
        self.update()


class LiveTrafficTimelineMDI(BaseLiveTimingMDI):
    """
    Live Traffic Timeline MDI 視窗
    
    繼承 BaseLiveTimingMDI，自動訂閱 DataManager 信號
    """
    
    # ✅ Workspace 保存/載入所需屬性 (2025-01-13)
    analysis_type = 'live_traffic_timeline'
    module_name = 'live_traffic_timeline'
    display_name = 'Traffic Timeline (Live)'
    
    def __init__(self, parent=None, data_manager=None):
        # 追蹤狀態
        self._last_max_lap: int = 0
        self._driver_info: Dict[str, Dict] = {}
        
        super().__init__(parent, data_manager)
        
        logger.info("[LIVE_TRAFFIC_TIMELINE_MDI] Initialized")
    
    def _setup_ui(self):
        """設置 UI"""
        # 主要 Widget
        self._timeline_widget = LiveTrafficTimelineWidget(self)
        self._main_layout.addWidget(self._timeline_widget)
        
        # 設定視窗大小
        self.setMinimumSize(600, 400)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入"""
        logger.info("[LIVE_TRAFFIC_TIMELINE_MDI] Race loaded: %s", race_info)
        
        # 重置狀態
        self._last_max_lap = 0
        self._timeline_widget.clear()
        
        # 設定總圈數
        total_laps = race_info.get('total_laps', 58)
        self._timeline_widget.set_total_laps(total_laps)
        
        # 獲取車手資訊
        if self._data_manager:
            self._driver_info = self._data_manager.get_driver_info() or {}
            self._timeline_widget.set_driver_info(self._driver_info)
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        logger.info("[LIVE_TRAFFIC_TIMELINE_MDI] Race unloaded")
        self._timeline_widget.clear()
        self._last_max_lap = 0
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新
        
        性能優化: 只在圈數變化時更新圖表
        """
        drivers = snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 檢查最大圈數
        current_max_lap = 0
        for driver_data in drivers.values():
            if not isinstance(driver_data, dict):
                continue
            lap = driver_data.get('lap', 0)
            if lap and lap > current_max_lap:
                current_max_lap = lap
        
        # 更新 Track Status
        track_status = snapshot.get('track_status', '1')
        self._timeline_widget.update_track_status(track_status)
        
        # 更新位置數據 (每個 snapshot 都需要累積)
        self._timeline_widget.update_positions(drivers, current_max_lap)
        
        # 只在圈數變化時重繪
        if current_max_lap > self._last_max_lap:
            self._last_max_lap = current_max_lap
            self._timeline_widget.update()
    
    def _on_interpolation_updated(self, current_snap: dict, next_snap: dict, 
                                   alpha: float, race_time_seconds: float):
        """處理插值更新 - Traffic Timeline 不需要平滑動畫"""
        pass


# =============================================================================
# Module Factory Registration Helper
# =============================================================================
def create_live_traffic_timeline(parent=None, data_manager=None) -> LiveTrafficTimelineMDI:
    """
    工廠方法：創建 Live Traffic Timeline MDI 視窗
    
    Args:
        parent: 父視窗
        data_manager: LiveTimingDataManager 實例
        
    Returns:
        LiveTrafficTimelineMDI 實例
    """
    return LiveTrafficTimelineMDI(parent=parent, data_manager=data_manager)
