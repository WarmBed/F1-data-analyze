"""
Live Timing Pit Window
======================

顯示車手相對位置與進站損失時間的關係視覺化。

參考: Live_timing_test/demo_live_position_tracking.py PitWindowWidget

Author: F1T Team
Date: 2025-12-04
"""

from typing import Dict, Any, Optional

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtWidgets import QWidget, QMenu, QInputDialog
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr
from core.logger import get_logger


logger = get_logger("live_timing.pit_window", component="gui")

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    logger.warning("[PIT_WINDOW] color_palette_provider not available")


class PitWindowWidget(QWidget):
    """
    Pit Window Widget - 進站策略視覺化工具
    
    顯示車手相對位置與進站損失時間的關係：
    - X 軸: 相對時間差 (秒)
    - 深紅色區域: Pit Loss Zone (進站損失時間約 20-25 秒)
    - 白色垂直線: 綠旗狀態下的預估掉落位置
    - 黃色區域: SC/VSC 狀態下的預估掉落位置
    """
    
    # 車手選擇請求信號
    driver_change_requested = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(600, 80)
        
        # 設定 Live Timing 識別屬性 (供 force_white_background 排除使用)
        self.setProperty("is_live_timing_widget", True)
        self.setStyleSheet("background-color: #1E1E1E;")
        
        # 數據
        self._driver_positions: Dict[str, Dict[str, Any]] = {}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        self._reference_driver: Optional[str] = None
        self._use_p1_as_reference = True
        self._track_status = "GREEN"
        
        # 插值相關
        self._interpolation_alpha: float = 0.0
        self._current_snapshot: Dict[str, Any] = {}
        self._next_snapshot: Dict[str, Any] = {}
        self._interpolated_positions: Dict[str, Dict[str, Any]] = {}
        
        # 進站時間設定
        self._time_range = 30.0
        self._pit_loss_green = 22.0
        self._pit_loss_sc = 12.0
        self._pit_loss_vsc = 8.0
        
        # 繪圖參數
        self._margin_left = 50
        self._margin_right = 20
        self._margin_top = 30
        self._margin_bottom = 25
        
        # 右鍵選單
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # 車隊顏色
        self.team_colors = {
            'Red Bull Racing': '#3671C6',
            'Ferrari': '#E8002D',
            'Mercedes': '#27F4D2',
            'McLaren': '#FF8000',
            'Aston Martin': '#229971',
            'Alpine': '#FF87BC',
            'Williams': '#64C4FF',
            'RB': '#6692FF',
            'Kick Sauber': '#52E252',
            'Haas F1 Team': '#B6BABD',
            'default': '#888888'
        }
        
        # 車號顏色
        self.driver_colors = {
            '1': '#3671C6', '11': '#3671C6',
            '16': '#E8002D', '55': '#E8002D',
            '44': '#27F4D2', '63': '#27F4D2',
            '4': '#FF8000', '81': '#FF8000',
            '14': '#229971', '18': '#229971',
            '10': '#FF87BC', '31': '#FF87BC',
            '23': '#64C4FF', '2': '#64C4FF',
            '22': '#6692FF', '30': '#6692FF',
            '77': '#52E252', '24': '#52E252',
            '20': '#B6BABD', '27': '#B6BABD',
        }
        
        logger.info("[PIT_WINDOW] PitWindowWidget initialized")
    
    def set_driver_info(self, driver_info: Dict):
        """設置車手資訊"""
        self._driver_info = driver_info or {}
    
    def set_pit_loss(self, green: float = 22.0, sc: float = 12.0, vsc: float = 8.0):
        """設置進站損失時間"""
        self._pit_loss_green = green
        self._pit_loss_sc = sc
        self._pit_loss_vsc = vsc
    
    def set_track_status(self, status: str):
        """設置賽道狀態"""
        if status in ("GREEN", "SC", "VSC"):
            self._track_status = status
            self.update()
    
    def set_time_range(self, range_seconds: float):
        """設置顯示時間範圍"""
        if range_seconds > 0:
            self._time_range = range_seconds
    
    def set_reference_driver(self, driver_num: str):
        """設置參考車手"""
        self._reference_driver = driver_num
        self._use_p1_as_reference = False
        self.update()
    
    def reset_to_p1(self):
        """重設為 P1 作為參考點"""
        self._use_p1_as_reference = True
        self._reference_driver = None
        self.update()
    
    def _on_driver_selected_from_menu(self, driver_num: str):
        """處理右鍵選單中選擇車手"""
        self.set_reference_driver(driver_num)
        # 發出信號通知其他模組
        self.driver_change_requested.emit(driver_num)
        tla = self._driver_positions.get(driver_num, {}).get('driver_tla', driver_num)
        logger.info("[PIT_WINDOW] Driver selected from menu: %s (%s)", tla, driver_num)
    
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        menu = QMenu(self)
        
        # 設置深色主題樣式 (覆蓋主 GUI 的白色主題)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                border: 1px solid #555555;
                color: #FFFFFF;
                padding: 2px;
            }
            QMenu::item {
                padding: 4px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
            QMenu::item:disabled {
                color: #888888;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 2px 5px;
            }
        """)
        
        reset_action = menu.addAction(tr("reset_to_p1"))
        reset_action.triggered.connect(self.reset_to_p1)
        
        if self._reference_driver and not self._use_p1_as_reference:
            ref_tla = self._driver_positions.get(self._reference_driver, {}).get('driver_tla', self._reference_driver)
            menu.addSeparator()
            current_action = menu.addAction(f"Current: {ref_tla}")
            current_action.setEnabled(False)
        
        menu.addSeparator()
        
        # 車手選擇子選單
        if self._driver_positions:
            driver_menu = menu.addMenu(tr("Select Driver"))
            
            # 按位置排序
            sorted_drivers = sorted(
                self._driver_positions.items(),
                key=lambda x: x[1].get('position', 99) if isinstance(x[1], dict) else 99
            )
            
            for driver_num, info in sorted_drivers:
                if not isinstance(info, dict):
                    continue
                    
                tla = info.get('driver_tla', driver_num)
                position = info.get('position', '')
                
                # 顯示格式: P1 VER (位置 + 車手代碼)
                display_text = f"P{position} {tla}" if position else tla
                action = driver_menu.addAction(display_text)
                action.setData(driver_num)
                
                # 標記當前選中
                if driver_num == self._reference_driver:
                    action.setCheckable(True)
                    action.setChecked(True)
                
                action.triggered.connect(lambda checked, d=driver_num: self._on_driver_selected_from_menu(d))
            
            menu.addSeparator()
        
        # 修改 Pit Loss 時間子選單
        pit_loss_menu = menu.addMenu(tr("modify_pit_loss_time"))
        
        # 顯示當前設定
        green_action = pit_loss_menu.addAction(tr("pit_loss_green").format(self._pit_loss_green))
        green_action.triggered.connect(lambda: self._modify_pit_loss("GREEN"))
        
        sc_action = pit_loss_menu.addAction(tr("pit_loss_sc").format(self._pit_loss_sc))
        sc_action.triggered.connect(lambda: self._modify_pit_loss("SC"))
        
        vsc_action = pit_loss_menu.addAction(tr("pit_loss_vsc").format(self._pit_loss_vsc))
        vsc_action.triggered.connect(lambda: self._modify_pit_loss("VSC"))
        
        menu.exec_(self.mapToGlobal(pos))
    
    def _modify_pit_loss(self, mode: str):
        """修改進站損失時間"""
        if mode == "GREEN":
            current = self._pit_loss_green
            title = tr("modify_pit_loss_green_title")
            prompt = tr("modify_pit_loss_green_prompt")
        elif mode == "SC":
            current = self._pit_loss_sc
            title = tr("modify_pit_loss_sc_title")
            prompt = tr("modify_pit_loss_sc_prompt")
        else:  # VSC
            current = self._pit_loss_vsc
            title = tr("modify_pit_loss_vsc_title")
            prompt = tr("modify_pit_loss_vsc_prompt")
        
        new_value, ok = QInputDialog.getDouble(
            self,
            title,
            prompt,
            current,  # 預設值
            5.0,      # 最小值
            40.0,     # 最大值
            1         # 小數位數
        )
        
        if ok:
            if mode == "GREEN":
                self._pit_loss_green = new_value
            elif mode == "SC":
                self._pit_loss_sc = new_value
            else:
                self._pit_loss_vsc = new_value
            
            logger.info("[PIT_WINDOW] Updated %s pit loss to %.1fs", mode, new_value)
            self.update()
    
    def update_positions(self, drivers_data: Dict[str, Dict[str, Any]]):
        """更新車手位置數據（非插值模式）"""
        self._driver_positions = drivers_data or {}
        
        if self._use_p1_as_reference:
            for driver_num, data in self._driver_positions.items():
                if data.get('position') == 1:
                    self._reference_driver = driver_num
                    break
        
        self.update()
    
    def update_interpolation(self, current_snap: Dict, next_snap: Dict, alpha: float, race_time_seconds: float):
        """
        更新插值數據 - 用於平滑動畫
        
        Args:
            current_snap: 當前快照
            next_snap: 下一個快照
            alpha: 插值因子 (0.0 ~ 1.0)
            race_time_seconds: 當前賽事時間（秒）
        """
        self._current_snapshot = current_snap
        self._next_snapshot = next_snap
        self._interpolation_alpha = alpha
        
        # 計算插值後的位置
        self._interpolated_positions = self._compute_interpolated_positions(
            current_snap.get('drivers', {}),
            next_snap.get('drivers', {}),
            alpha
        )
        
        # 更新車手位置數據為插值後的數據
        self._driver_positions = self._interpolated_positions
        
        # 更新參考車手
        if self._use_p1_as_reference:
            for driver_num, data in self._driver_positions.items():
                if data.get('position') == 1:
                    self._reference_driver = driver_num
                    break
        
        # 觸發重繪
        self.update()
    
    def _compute_interpolated_positions(self, current_drivers: Dict, next_drivers: Dict, alpha: float) -> Dict:
        """
        計算插值後的車手位置
        
        使用線性插值計算 gap_to_leader（相對時間差）
        """
        result = {}
        
        for driver_num, current_data in current_drivers.items():
            # 跳過 DNF 車手
            status = current_data.get('status', '')
            if status and str(status).upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            # 複製當前數據
            interpolated = dict(current_data)
            
            # 如果下一個快照有這個車手，進行插值
            if driver_num in next_drivers:
                next_data = next_drivers[driver_num]
                
                # gap_to_leader 插值（這是 Pit Window 的主要顯示數據）
                gap0 = current_data.get('gap_to_leader')
                gap1 = next_data.get('gap_to_leader')
                if gap0 is not None and gap1 is not None:
                    try:
                        gap0_float = float(gap0) if not isinstance(gap0, (int, float)) else gap0
                        gap1_float = float(gap1) if not isinstance(gap1, (int, float)) else gap1
                        interpolated['gap_to_leader'] = gap0_float + alpha * (gap1_float - gap0_float)
                    except (ValueError, TypeError):
                        pass  # 保持原值
                
                # interval 插值
                interval0 = current_data.get('interval')
                interval1 = next_data.get('interval')
                if interval0 is not None and interval1 is not None:
                    try:
                        int0_float = float(interval0) if not isinstance(interval0, (int, float)) else interval0
                        int1_float = float(interval1) if not isinstance(interval1, (int, float)) else interval1
                        interpolated['interval'] = int0_float + alpha * (int1_float - int0_float)
                    except (ValueError, TypeError):
                        pass  # 保持原值
            
            result[driver_num] = interpolated
        
        return result
    
    def paintEvent(self, event):
        """繪製 Pit Window"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, QColor('#1E1E1E'))
        
        chart_left = self._margin_left
        chart_right = width - self._margin_right
        chart_top = self._margin_top
        chart_bottom = height - self._margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        axis_y = chart_top + chart_height / 2
        
        # 繪製 Pit Loss Zone
        self._draw_pit_loss_zone(painter, chart_left, chart_top, chart_width, chart_height, axis_y)
        
        # 繪製 X 軸
        self._draw_x_axis(painter, chart_left, chart_right, axis_y, chart_width, chart_bottom)
        
        # 繪製車手標記
        self._draw_driver_markers(painter, chart_left, chart_width, axis_y)
        
        if not self._driver_positions:
            painter.setPen(QColor(150, 150, 150))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(int(width / 2 - 60), int(height / 2), tr("waiting_for_data", "Waiting for data..."))
    
    def _draw_pit_loss_zone(self, painter: QPainter, left: float, top: float,
                            width: float, height: float, axis_y: float):
        """繪製 Pit Loss Zone"""
        center_x = left + width / 2
        
        green_width_px = (self._pit_loss_green / self._time_range) * (width / 2)
        sc_width_px = (self._pit_loss_sc / self._time_range) * (width / 2)
        vsc_width_px = (self._pit_loss_vsc / self._time_range) * (width / 2)
        
        # 左側
        pit_zone_left = center_x - green_width_px
        sc_zone_left = center_x - sc_width_px
        vsc_zone_left = center_x - vsc_width_px
        
        # 深紅色區域 (Green Flag)
        painter.fillRect(int(pit_zone_left), int(top),
            int(green_width_px - sc_width_px), int(height),
            QColor(80, 20, 20))
        
        # 橙色區域 (SC)
        painter.fillRect(int(sc_zone_left), int(top),
            int(sc_width_px - vsc_width_px), int(height),
            QColor(180, 80, 0))
        
        # 黃色區域 (VSC)
        painter.fillRect(int(vsc_zone_left), int(top),
            int(vsc_width_px), int(height),
            QColor(180, 150, 0))
        
        # 白色虛線
        pen_white_dash = QPen(QColor(255, 255, 255), 1, Qt.DashLine)
        pen_white_dash.setDashPattern([4, 4])
        painter.setPen(pen_white_dash)
        painter.drawLine(int(pit_zone_left), int(top), int(pit_zone_left), int(top + height))
        painter.drawLine(int(sc_zone_left), int(top), int(sc_zone_left), int(top + height))
        painter.drawLine(int(vsc_zone_left), int(top), int(vsc_zone_left), int(top + height))
        
        # 右側 (對稱)
        pit_zone_right = center_x + green_width_px
        sc_zone_right = center_x + sc_width_px
        vsc_zone_right = center_x + vsc_width_px
        
        painter.fillRect(int(center_x), int(top), int(vsc_width_px), int(height), QColor(180, 150, 0))
        painter.fillRect(int(vsc_zone_right), int(top), int(sc_width_px - vsc_width_px), int(height), QColor(180, 80, 0))
        painter.fillRect(int(sc_zone_right), int(top), int(green_width_px - sc_width_px), int(height), QColor(80, 20, 20))
        
        painter.setPen(pen_white_dash)
        painter.drawLine(int(pit_zone_right), int(top), int(pit_zone_right), int(top + height))
        painter.drawLine(int(sc_zone_right), int(top), int(sc_zone_right), int(top + height))
        painter.drawLine(int(vsc_zone_right), int(top), int(vsc_zone_right), int(top + height))
        
        # 中央虛線
        painter.setPen(QPen(QColor(150, 150, 150), 1, Qt.DashLine))
        painter.drawLine(int(center_x), int(top), int(center_x), int(top + height))
    
    def _draw_x_axis(self, painter: QPainter, left: float, right: float,
                     axis_y: float, width: float, bottom: float):
        """繪製 X 軸"""
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.drawLine(int(left), int(axis_y), int(right), int(axis_y))
        
        tick_interval = 5.0
        center_x = left + width / 2
        
        painter.setPen(QColor(200, 200, 200))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        current = -self._time_range
        while current <= self._time_range:
            x = center_x + (current / self._time_range) * (width / 2)
            
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawLine(int(x), int(axis_y - 3), int(x), int(axis_y + 3))
            
            display_value = -current
            if display_value == 0:
                label = "0"
            elif display_value > 0:
                label = f"+{display_value:.0f}"
            else:
                label = f"{display_value:.0f}"
            
            painter.setPen(QColor(200, 200, 200))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(int(x - text_rect.width() / 2), int(bottom + 15), label)
            
            current += tick_interval
    
    def _draw_driver_markers(self, painter: QPainter, left: float, width: float, axis_y: float):
        """繪製車手標記"""
        if not self._driver_positions:
            return
        
        center_x = left + width / 2
        
        ref_gap = 0.0
        if self._reference_driver and self._reference_driver in self._driver_positions:
            ref_gap = self._driver_positions[self._reference_driver].get('gap_to_leader', 0.0) or 0.0
        
        markers = []
        for driver_num, data in self._driver_positions.items():
            # 過濾 DNF/Retired/Stopped 車手
            status = data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            position = data.get('position', 99)
            gap_to_leader = data.get('gap_to_leader', 0.0)
            gap_laps = data.get('gap_to_leader_laps', 0)
            driver_tla = data.get('driver_tla', driver_num)
            pit_count = data.get('pit_count') or data.get('PitCount') or data.get('num_pit_stops') or 0
            
            if gap_laps and gap_laps > 0:
                continue
            
            # 防禦性檢查：確保 gap_to_leader 是數字
            if gap_to_leader is None:
                gap_to_leader = 0.0
            elif isinstance(gap_to_leader, str):
                # gap_to_leader 可能是字串如 "LAP" 或 "+1 LAP"，跳過這些車手
                continue
            else:
                try:
                    gap_to_leader = float(gap_to_leader)
                except (ValueError, TypeError):
                    continue
            
            relative_gap = gap_to_leader - ref_gap
            
            if abs(relative_gap) > self._time_range:
                continue
            
            x = center_x - (relative_gap / self._time_range) * (width / 2)
            color = self._get_driver_color(driver_num, data)
            
            markers.append({
                'driver_num': driver_num,
                'driver_tla': driver_tla,
                'position': position,
                'gap': gap_to_leader,
                'pit_count': pit_count if isinstance(pit_count, int) else 0,
                'x': x,
                'color': color
            })
        
        markers.sort(key=lambda m: -m['position'])
        
        for m in markers:
            self._draw_single_marker(painter, m, axis_y)
    
    def _draw_single_marker(self, painter: QPainter, marker: Dict, axis_y: float):
        """繪製單個車手標記"""
        x = marker['x']
        tla = marker['driver_tla']
        pit_count = marker['pit_count']
        color = QColor(marker['color'])
        
        # 圓點
        dot_radius = 5
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawEllipse(QPointF(x, axis_y), dot_radius, dot_radius)
        
        # 連接線
        line_length = 18
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(x, axis_y - dot_radius), QPointF(x, axis_y - dot_radius - line_length))
        
        # Flag 標籤
        flag_y = axis_y - dot_radius - line_length - 8
        self._draw_flag(painter, x, flag_y, tla, color)
        
        # 進站次數氣泡
        bubble_x = x + 18
        bubble_y = flag_y - 8
        self._draw_pit_bubble(painter, bubble_x, bubble_y, pit_count)
    
    def _draw_flag(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """繪製 Flag 標籤"""
        w, h = 30, 14
        flag_x = x - w / 2
        flag_y = y - h / 2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        text_color = QColor(255, 255, 255) if self._is_dark_color(color) else QColor(0, 0, 0)
        painter.setPen(text_color)
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        text_rect = painter.fontMetrics().boundingRect(tla)
        text_x = flag_x + (w - text_rect.width()) / 2
        text_y = flag_y + h - 3
        painter.drawText(int(text_x), int(text_y), tla)
    
    def _draw_pit_bubble(self, painter: QPainter, x: float, y: float, pit_count: int):
        """繪製進站次數氣泡"""
        if pit_count is None:
            pit_count = 0
        try:
            pit_count = int(pit_count)
        except (ValueError, TypeError):
            pit_count = 0
        
        radius = 7
        # 根據換胎次數決定顏色
        if pit_count == 0:
            bg_color = QColor(0, 180, 0)      # 綠色: 未換胎
        elif pit_count == 1:
            bg_color = QColor(0, 100, 255)    # 藍色: 1次換胎
        elif pit_count == 2:
            bg_color = QColor(255, 180, 0)    # 黃色: 2次換胎
        else:  # pit_count >= 3
            bg_color = QColor(220, 40, 40)    # 紅色: 3次以上換胎
        
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(QPointF(x, y), radius, radius)
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        
        text = str(pit_count)
        text_rect = painter.fontMetrics().boundingRect(text)
        painter.drawText(int(x - text_rect.width() / 2), int(y + text_rect.height() / 4), text)
    
    def _get_driver_color(self, driver_num: str, data: Dict = None) -> str:
        """獲取車手顏色 - 優先使用 color_palette_provider"""
        # 優先使用通用顏色系統
        if COLOR_PALETTE_AVAILABLE:
            try:
                # 嘗試從 data 獲取 driver_tla
                driver_tla = None
                if data:
                    driver_tla = data.get('driver_tla')
                if not driver_tla and driver_num in self._driver_info:
                    driver_tla = self._driver_info[driver_num].get('tla', driver_num)
                if driver_tla:
                    color_qcolor = color_palette_provider.get_driver_color(driver_tla, fallback=True)
                    if color_qcolor:
                        return color_qcolor.name()
            except Exception:
                pass
        
        # 備選：從 data 的 team_color
        if data:
            tc = data.get('team_color')
            if tc:
                return f'#{tc}' if not tc.startswith('#') else tc
        
        # 備選：_driver_info
        if driver_num in self._driver_info:
            team = self._driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return self.team_colors[team]
        
        # 備選：車號顏色映射
        if driver_num in self.driver_colors:
            return self.driver_colors[driver_num]
        
        return self.team_colors['default']
    
    def _is_dark_color(self, color: QColor) -> bool:
        """判斷顏色是否為深色"""
        luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
        return luminance < 0.5


class LiveTimingPitWindow(BaseLiveTimingMDI):
    """
    Live Timing Pit Window MDI Window
    
    顯示車手相對位置與進站損失時間的關係。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr("pit_window", "Pit Window"))
        self.setMinimumSize(650, 120)
        self.resize(800, 150)
        
        # 連接 driver_selected 信號
        self._connect_driver_selection_signal()
        
        logger.info("[PIT_WINDOW_MDI] LiveTimingPitWindow initialized")
    
    def _connect_driver_selection_signal(self):
        """連接 DataManager 的 driver_selected 信號"""
        try:
            if self._data_manager:
                self._data_manager.driver_selected.connect(self._on_driver_selected)
                logger.info("[PIT_WINDOW_MDI] Connected to driver_selected signal")
        except Exception:
            logger.exception("[PIT_WINDOW_MDI] Failed to connect driver_selected signal")
    
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇 - 設置為參考車手 (從 DataManager snapshot 獲取車手資訊)"""
        if self.pit_widget:
            # 先確保 widget 有車手資訊 (從 DataManager 獲取 snapshot)
            if self._data_manager:
                snapshot = self._data_manager.get_current_snapshot()
                if snapshot:
                    drivers = snapshot.get('drivers', {})
                    driver_info = drivers.get(driver_num, {})
                    if driver_info:
                        # 確保 _driver_positions 已填充
                        tla = driver_info.get('driver_tla', driver_num)
                        team_color = driver_info.get('team_color', 'FFFFFF')
                        if driver_num not in self.pit_widget._driver_positions:
                            self.pit_widget._driver_positions[driver_num] = {}
                        self.pit_widget._driver_positions[driver_num]['driver_tla'] = tla
                        self.pit_widget._driver_positions[driver_num]['team_color'] = team_color
                        logger.debug(
                            "[PIT_WINDOW_MDI] Driver info from snapshot: %s (%s)",
                            tla,
                            team_color,
                        )
            
            self.pit_widget.set_reference_driver(driver_num)
            driver_tla = self.pit_widget._driver_positions.get(driver_num, {}).get('driver_tla', driver_num)
            logger.info(
                "[PIT_WINDOW_MDI] Reference driver set to: %s (%s)",
                driver_tla,
                driver_num,
            )
    
    def _setup_ui(self):
        """Setup UI components"""
        self.pit_widget = PitWindowWidget()
        self._main_layout.addWidget(self.pit_widget)
        
        # 連接車手選擇信號
        self.pit_widget.driver_change_requested.connect(self._on_driver_change_requested)
    
    def _on_driver_change_requested(self, driver_num: str):
        """處理車手切換請求 - 發送信號給其他模組"""
        logger.info("[PIT_WINDOW_MDI] Driver change requested: %s", driver_num)
        if self._data_manager:
            self._data_manager.driver_selected.emit(driver_num)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        driver_info = race_info.get('driver_info', {})
        self.pit_widget.set_driver_info(driver_info)
        
        logger.info(
            "[PIT_WINDOW_MDI] Race loaded: %s %s",
            race_info.get('year'),
            race_info.get('race'),
        )
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        logger.info("[PIT_WINDOW_MDI] Race unloaded")
        self.pit_widget._driver_positions = {}
        self.pit_widget.update()
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated - 僅在沒有插值數據時使用"""
        # 如果有插值數據，使用插值更新，否則使用快照更新
        if not self.pit_widget._interpolated_positions:
            drivers = snapshot.get('drivers', {})
            self.pit_widget.update_positions(drivers)
    
    def _on_interpolation_updated(self, current_snap: Dict[str, Any], next_snap: Dict[str, Any],
                                   alpha: float, race_time_seconds: float):
        """
        處理插值更新 - 用於平滑動畫
        
        使用插值數據更新 Pit Window，實現平滑的位置過渡。
        """
        if self.pit_widget:
            self.pit_widget.update_interpolation(current_snap, next_snap, alpha, race_time_seconds)
    
    def _cleanup(self):
        """清理資源 - 斷開 driver_selected 信號"""
        try:
            if self._data_manager:
                self._data_manager.driver_selected.disconnect(self._on_driver_selected)
                logger.debug("[PIT_WINDOW_MDI] Disconnected from driver_selected signal")
        except Exception:
            pass  # 信號可能已經斷開
