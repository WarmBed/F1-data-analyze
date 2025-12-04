"""
Live Timing Circle Map
======================

以圓環形式顯示所有車手在賽道上的相對位置。
使用真實 X/Y 座標計算車手在賽道上的位置，並映射到圓環上顯示。

參考: Live_timing_test/demo_live_position_tracking.py CircleMapWidget

Author: F1T Team
Date: 2025-12-03
"""

import math
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    print("[CIRCLE_MAP] color_palette_provider not available")


class CircleMapWidget(QWidget):
    """
    Circle Map Widget
    
    以圓環形式顯示所有車手在賽道上的相對位置。
    使用真實 X/Y 座標計算車手在賽道上的位置，
    並映射到圓環上顯示。
    
    支援插值平滑動畫：
    - 儲存當前快照和下一個快照
    - 使用 alpha 進行線性插值
    - 實現平滑的位置過渡
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        
        # 設定 Live Timing 識別屬性 (供 force_white_background 排除使用)
        self.setProperty("is_live_timing_widget", True)
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # 車手數據
        self.driver_positions: Dict[str, Dict[str, Any]] = {}
        self.driver_info: Dict[str, Dict[str, Any]] = {}
        
        # === 插值相關 ===
        self._current_snapshot: Optional[Dict[str, Any]] = None
        self._next_snapshot: Optional[Dict[str, Any]] = None
        self._interpolation_alpha: float = 0.0
        self._interpolated_positions: Dict[str, Dict[str, Any]] = {}
        
        # 賽道資訊
        self.track_points: List[Dict[str, float]] = []  # 賽道輪廓點 [{x, y, distance}]
        self.track_length = 5380.0
        self.total_laps = 55
        self.current_lap = 0
        self.race_time_str = "00:00:00"
        
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
        
        # 車號對應顏色
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
        
        # Track status (1=Green, 2=Yellow, 4=SC, 5=Red Flag, 6=VSC)
        self._track_status = "1"
        
        # Corner data for marking turns on the circle
        self._corners: List[Dict[str, Any]] = []
        self._show_corners = True  # 顯示彎道標記
        
        # Track status display mapping: status_code -> (text, bg_color, text_color)
        self._track_status_display = {
            '2': ('YELLOW FLAG', '#FFFF00', '#000000'),      # Yellow flag
            '4': ('SAFETY CAR', '#FF8000', '#000000'),       # Safety Car - Orange
            '5': ('RED FLAG', '#FF0000', '#FFFFFF'),         # Red flag
            '6': ('VIRTUAL SAFETY CAR', '#FF8000', '#000000'),  # VSC - Orange
        }
        
        print("[CIRCLE_MAP] CircleMapWidget initialized (GPS coordinate mode)")
    
    def load_track_data(self, track_data: Dict):
        """Load track outline data"""
        try:
            position_records = track_data.get('position_records', [])
            if not position_records:
                print("[CIRCLE_MAP] No track outline data")
                return
            
            self.track_points = []
            total_distance = 0.0
            prev_x, prev_y = None, None
            
            for record in position_records:
                x = record.get('position_x') or record.get('x')
                y = record.get('position_y') or record.get('y')
                if x is None or y is None:
                    continue
                
                # Calculate cumulative distance
                if prev_x is not None:
                    dx = x - prev_x
                    dy = y - prev_y
                    total_distance += (dx**2 + dy**2)**0.5
                
                self.track_points.append({
                    'x': x, 'y': y, 'distance': total_distance
                })
                prev_x, prev_y = x, y
            
            if self.track_points:
                self.track_length = self.track_points[-1]['distance']
                print(f"[CIRCLE_MAP] Track outline loaded: {len(self.track_points)} points, length {self.track_length:.0f}m")
            
        except Exception as e:
            print(f"[CIRCLE_MAP] Failed to load track outline: {e}")
    
    def set_track_length(self, length: float):
        """Set track length"""
        if length and length > 0:
            self.track_length = length
    
    def set_total_laps(self, laps: int):
        """Set total laps"""
        if laps and laps > 0:
            self.total_laps = laps
    
    def set_corners(self, corners: List[Dict[str, Any]]):
        """Set corner data for marking turns on the circle.
        
        Args:
            corners: List of corner dicts with 'number' and 'distance' or 'lap_distance' keys
        """
        self._corners = corners or []
        print(f"[CIRCLE_MAP] Corners set: {len(self._corners)} corners")
        self.update()
    
    def set_show_corners(self, show: bool):
        """Toggle corner marker visibility"""
        self._show_corners = show
        self.update()
    
    def set_driver_info(self, driver_info: Dict):
        """Set driver info"""
        self.driver_info = driver_info or {}
    
    def update_positions(self, drivers_data: Dict, current_lap: int = 0, race_time: str = "00:00:00"):
        """Update driver positions - filter DNF/Stopped drivers"""
        # Filter out DNF/Retired/Stopped drivers
        if drivers_data:
            filtered_drivers = {}
            for driver_num, driver_data in drivers_data.items():
                status = driver_data.get('status', '')
                if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                    continue
                filtered_drivers[driver_num] = driver_data
            self.driver_positions = filtered_drivers
        else:
            self.driver_positions = {}
        
        self.current_lap = current_lap
        self.race_time_str = race_time
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
        
        # 更新其他顯示資訊
        self.current_lap = current_snap.get('current_lap', 0)
        
        # 格式化時間
        hours = int(race_time_seconds // 3600)
        minutes = int((race_time_seconds % 3600) // 60)
        seconds = int(race_time_seconds % 60)
        self.race_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        # 觸發重繪
        self.update()
    
    def _compute_interpolated_positions(self, current_drivers: Dict, next_drivers: Dict, alpha: float) -> Dict:
        """
        計算插值後的車手位置
        
        使用線性插值計算 X/Y 座標
        """
        result = {}
        
        for driver_num, current_data in current_drivers.items():
            # 跳過 DNF 車手
            status = current_data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            # 複製當前數據
            interpolated = dict(current_data)
            
            # 如果下一個快照有這個車手，進行插值
            if driver_num in next_drivers:
                next_data = next_drivers[driver_num]
                
                # X 座標插值
                x0 = current_data.get('x')
                x1 = next_data.get('x')
                if x0 is not None and x1 is not None:
                    interpolated['x'] = x0 + alpha * (x1 - x0)
                
                # Y 座標插值
                y0 = current_data.get('y')
                y1 = next_data.get('y')
                if y0 is not None and y1 is not None:
                    interpolated['y'] = y0 + alpha * (y1 - y0)
            
            result[driver_num] = interpolated
        
        return result
    
    def update_track_status(self, status: str):
        """
        Update track status
        
        Args:
            status: Track status code (1=Green, 2=Yellow, 4=SC, 5=Red, 6=VSC)
        """
        new_status = str(status)
        if new_status != self._track_status:
            print(f"[CIRCLE_MAP] Track status changed: {self._track_status} -> {new_status}")
            self._track_status = new_status
            self.update()
    
    def paintEvent(self, event):
        """Paint circle track map"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        width = self.width()
        height = self.height()
        cx = width / 2
        cy = height / 2
        
        # Ring dimensions
        margin = 60
        radius = min(width, height) / 2 - margin
        inner_radius = radius * 0.85  # Track width
        track_center_r = (radius + inner_radius) / 2  # Track center line radius
        
        # Draw track ring
        self._draw_track_ring(painter, cx, cy, radius, inner_radius)
        
        # Draw corner markers (before sector markers)
        self._draw_corner_markers(painter, cx, cy, radius, inner_radius, track_center_r)
        
        # Draw sector markers
        self._draw_sector_markers(painter, cx, cy, radius)
        
        # Draw driver markers
        self._draw_driver_markers(painter, cx, cy, radius, inner_radius, track_center_r)
        
        # Draw center info
        self._draw_center_info(painter, cx, cy, inner_radius)
        
        # Draw track status bar (only for Yellow/SC/Red/VSC)
        self._draw_track_status_bar(painter, width, height)
    
    def _draw_track_status_bar(self, painter: QPainter, width: float, height: float):
        """
        Draw track status bar at the bottom
        Only shown for Yellow Flag, Safety Car, VSC, Red Flag
        """
        # Check if we need to display status bar
        status_info = self._track_status_display.get(self._track_status)
        # Debug output
        if self._track_status != '1':
            print(f"[CIRCLE_MAP] Drawing status bar: status={self._track_status}, info={status_info}")
        if not status_info:
            return  # Green flag or unknown - don't show bar
        
        text, bg_color, text_color = status_info
        
        # Bar dimensions - scale based on widget size
        min_bar_height = 20
        bar_height = max(min_bar_height, min(28, int(height * 0.08)))
        bar_margin = max(5, min(10, int(width * 0.02)))
        bar_width = width - 2 * bar_margin
        bar_y = height - bar_height - bar_margin
        
        # Skip if widget is too small
        if bar_width < 80 or bar_y < height * 0.5:
            return
        
        # Draw background
        painter.setBrush(QBrush(QColor(bg_color)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(
            int(bar_margin), int(bar_y), 
            int(bar_width), bar_height,
            5, 5
        )
        
        # Draw text - scale font size based on bar height
        font = QFont()
        font_size = max(8, min(12, int(bar_height * 0.4)))
        font.setPointSize(font_size)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(text_color))
        
        # Center the text
        rect = painter.fontMetrics().boundingRect(text)
        text_x = (width - rect.width()) / 2
        text_y = bar_y + (bar_height + rect.height()) / 2 - 3
        painter.drawText(int(text_x), int(text_y), text)
    
    def _draw_track_ring(self, painter: QPainter, cx: float, cy: float, 
                         outer_r: float, inner_r: float):
        """Draw track ring"""
        # Outer ring
        painter.setPen(QPen(QColor(80, 80, 80), 3))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), outer_r, outer_r)
        
        # Inner ring
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        painter.drawEllipse(QPointF(cx, cy), inner_r, inner_r)
        
        # Track fill
        path = QPainterPath()
        path.addEllipse(QPointF(cx, cy), outer_r, outer_r)
        inner_path = QPainterPath()
        inner_path.addEllipse(QPointF(cx, cy), inner_r, inner_r)
        track_path = path - inner_path
        
        painter.setBrush(QBrush(QColor(50, 50, 50, 100)))
        painter.setPen(Qt.NoPen)
        painter.drawPath(track_path)
    
    def _draw_corner_markers(self, painter: QPainter, cx: float, cy: float,
                              outer_r: float, inner_r: float, track_r: float):
        """Draw corner markers (T1, T2, ...) on the circle track.
        
        Corners are mapped to the circle based on their distance along the track.
        """
        if not self._corners or not self._show_corners:
            return
        
        if self.track_length <= 0:
            return
        
        # Color for corner markers - light green, subtle
        corner_color = QColor('#90EE90')
        corner_color.setAlpha(180)
        
        # Font for corner labels
        font = QFont()
        font.setPointSize(7)
        painter.setFont(font)
        
        for corner in self._corners:
            corner_num = corner.get('number', 0)
            # Get corner distance - try different possible keys
            corner_distance = (
                corner.get('lap_distance', 0) or 
                corner.get('distance', 0) or 
                corner.get('mapped_distance', 0)
            )
            
            if corner_distance <= 0:
                continue
            
            # Calculate progress (0-1) along the track
            progress = corner_distance / self.track_length
            
            # Convert to angle: start from -90 (top = start/finish)
            # Full lap = 360 degrees, going clockwise
            angle_deg = -90 + progress * 360
            angle_rad = math.radians(angle_deg)
            
            # Draw small tick mark on inner edge of track
            tick_inner = inner_r - 3
            tick_outer = inner_r + 5
            
            inner_x = cx + tick_inner * math.cos(angle_rad)
            inner_y = cy + tick_inner * math.sin(angle_rad)
            outer_x = cx + tick_outer * math.cos(angle_rad)
            outer_y = cy + tick_outer * math.sin(angle_rad)
            
            # Draw tick
            painter.setPen(QPen(corner_color, 1))
            painter.drawLine(QPointF(inner_x, inner_y), QPointF(outer_x, outer_y))
            
            # Draw corner number label inside the ring
            label_r = inner_r - 12
            label_x = cx + label_r * math.cos(angle_rad)
            label_y = cy + label_r * math.sin(angle_rad)
            
            painter.setPen(corner_color)
            label = f"T{corner_num}"
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(
                int(label_x - text_rect.width() / 2),
                int(label_y + text_rect.height() / 4),
                label
            )
    
    def _draw_sector_markers(self, painter: QPainter, cx: float, cy: float, outer_r: float):
        """Draw sector markers"""
        sectors = [
            ('FIN', -90),
            ('S1', 30),
            ('S2', 150),
        ]
        
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        for label, angle_deg in sectors:
            angle_rad = math.radians(angle_deg)
            
            # Line from outer edge outward
            start_x = cx + outer_r * math.cos(angle_rad)
            start_y = cy + outer_r * math.sin(angle_rad)
            end_x = cx + (outer_r + 10) * math.cos(angle_rad)
            end_y = cy + (outer_r + 10) * math.sin(angle_rad)
            
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(QPointF(start_x, start_y), QPointF(end_x, end_y))
            
            # Label
            label_r = outer_r + 22
            label_x = cx + label_r * math.cos(angle_rad)
            label_y = cy + label_r * math.sin(angle_rad)
            
            painter.setPen(QColor(255, 255, 255))
            text_rect = painter.fontMetrics().boundingRect(label)
            painter.drawText(int(label_x - text_rect.width()/2), 
                           int(label_y + text_rect.height()/4), label)
    
    def _draw_driver_markers(self, painter: QPainter, cx: float, cy: float,
                             outer_r: float, inner_r: float, track_r: float):
        """Draw driver markers - use real coordinates to calculate position
        
        優先使用插值位置以獲得平滑動畫效果
        """
        # 優先使用插值位置，其次使用普通位置
        positions_to_use = self._interpolated_positions if self._interpolated_positions else self.driver_positions
        
        if not positions_to_use:
            return
        
        # Collect all driver data and calculate angles
        markers = []
        
        for driver_num, data in positions_to_use.items():
            x = data.get('x')
            y = data.get('y')
            position = data.get('position', 99)
            gap_str = data.get('gap_to_leader_display', '')
            driver_tla = data.get('driver_tla', driver_num)
            color = self._get_driver_color(driver_num, data)
            
            # Calculate angle (based on coordinates or position)
            if x is not None and y is not None and self.track_points:
                # Use real coordinates
                angle_deg = self._xy_to_angle(x, y)
            else:
                # Use position to calculate when no coordinates
                angle_deg = -90 + (position - 1) * (330 / 20)
            
            markers.append({
                'driver_num': driver_num,
                'driver_tla': driver_tla,
                'position': position,
                'gap_str': gap_str,
                'angle_deg': angle_deg,
                'color': color
            })
        
        # Sort by position (P1 on top)
        markers.sort(key=lambda x: -x['position'])
        
        # Draw all drivers (allow overlap, fixed radius)
        for m in markers:
            angle_rad = math.radians(m['angle_deg'])
            color = QColor(m['color'])
            
            # Colored line on track
            track_band = (outer_r - inner_r) / 2
            line_inner = track_r - track_band * 0.4
            line_outer = track_r + track_band * 0.4
            
            inner_x = cx + line_inner * math.cos(angle_rad)
            inner_y = cy + line_inner * math.sin(angle_rad)
            outer_x = cx + line_outer * math.cos(angle_rad)
            outer_y = cy + line_outer * math.sin(angle_rad)
            
            # Draw colored marker line on track
            painter.setPen(QPen(color, 4))
            painter.drawLine(QPointF(inner_x, inner_y), QPointF(outer_x, outer_y))
            
            # Flag position (shorter distance to avoid exceeding window)
            flag_r = outer_r + 12
            flag_x = cx + flag_r * math.cos(angle_rad)
            flag_y = cy + flag_r * math.sin(angle_rad)
            
            # Connection line (from track outer edge to flag)
            painter.setPen(QPen(color, 2))
            painter.drawLine(QPointF(outer_x, outer_y), QPointF(flag_x, flag_y))
            
            # Draw flag
            self._draw_flag(painter, flag_x, flag_y, m['driver_tla'], color)
    
    def _xy_to_angle(self, x: float, y: float) -> float:
        """Convert X/Y coordinates to circle angle"""
        if not self.track_points:
            return -90  # Default to top
        
        # Find nearest track point
        min_dist = float('inf')
        nearest_idx = 0
        
        for i, pt in enumerate(self.track_points):
            dx = x - pt['x']
            dy = y - pt['y']
            dist = dx*dx + dy*dy
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        # Calculate progress on track (0-1)
        track_distance = self.track_points[nearest_idx]['distance']
        progress = track_distance / self.track_length if self.track_length > 0 else 0
        
        # Convert to angle (-90 is top/finish line, clockwise increasing)
        # progress=0 (start) -> -90 degrees
        # progress=0.5 -> 90 degrees (bottom)
        # progress=1 (finish) -> 270 degrees -> -90 degrees
        angle_deg = -90 + progress * 360
        
        return angle_deg
    
    def _get_driver_color(self, driver_num: str, data: dict = None) -> str:
        """獲取車手顏色 - 優先使用 color_palette_provider"""
        # 優先使用通用顏色系統
        if COLOR_PALETTE_AVAILABLE:
            try:
                # 嘗試從 data 獲取 driver_tla
                driver_tla = None
                if data:
                    driver_tla = data.get('driver_tla')
                if not driver_tla and driver_num in self.driver_info:
                    driver_tla = self.driver_info[driver_num].get('tla', driver_num)
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
        
        # 備選：driver_info
        if driver_num in self.driver_info:
            team = self.driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return self.team_colors[team]
        
        # 備選：車號顏色映射
        if driver_num in self.driver_colors:
            return self.driver_colors[driver_num]
        
        return self.team_colors['default']
    
    def _draw_flag(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """Draw flag label"""
        w, h = 28, 12
        flag_x = x - w/2
        flag_y = y - h/2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(7)
        font.setBold(True)
        painter.setFont(font)
        
        rect = painter.fontMetrics().boundingRect(tla)
        painter.drawText(int(flag_x + (w - rect.width())/2), int(flag_y + h - 2), tla)
    
    def _draw_center_info(self, painter: QPainter, cx: float, cy: float, inner_r: float):
        """Draw center info"""
        # Lap count
        lap_text = f"Lap {self.current_lap}/{self.total_laps}"
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QColor(255, 255, 255))
        
        rect = painter.fontMetrics().boundingRect(lap_text)
        painter.drawText(int(cx - rect.width()/2), int(cy - 10), lap_text)
        
        # Time
        font.setPointSize(14)
        painter.setFont(font)
        painter.setPen(QColor(200, 200, 200))
        
        rect = painter.fontMetrics().boundingRect(self.race_time_str)
        painter.drawText(int(cx - rect.width()/2), int(cy + 20), self.race_time_str)


class LiveTimingCircleMap(BaseLiveTimingMDI):
    """
    Live Timing Circle Map MDI Window
    
    以圓環形式顯示所有車手在賽道上的相對位置。
    賽道資料自動從 race_loaded 信號獲取，無需手動選擇。
    """
    
    # Track name mapping (LiveF1 -> FastF1)
    TRACK_NAME_MAP = {
        # Asian races
        "Japanese": "Japan",
        "Japan": "Japan",
        "Chinese": "China",
        "China": "China",
        "Singapore": "Singapore",
        "Azerbaijan": "Azerbaijan",
        "Bahrain": "Bahrain",
        "Saudi Arabian": "Saudi Arabia",
        "Saudi_Arabian": "Saudi Arabia",
        "Qatar": "Qatar",
        "Abu Dhabi": "Abu Dhabi",
        "Abu_Dhabi": "Abu Dhabi",
        # European races
        "British": "Great Britain",
        "Great Britain": "Great Britain",
        "Belgian": "Belgium",
        "Belgium": "Belgium",
        "Dutch": "Netherlands",
        "Netherlands": "Netherlands",
        "Italian": "Italy",
        "Italy": "Italy",
        "Spanish": "Spain",
        "Spain": "Spain",
        "Hungarian": "Hungary",
        "Hungary": "Hungary",
        "Austrian": "Austria",
        "Austria": "Austria",
        "Monaco": "Monaco",
        "Emilia Romagna": "Emilia Romagna",
        "Emilia_Romagna": "Emilia Romagna",
        # American races
        "United States": "United States",
        "United_States": "United States",
        "Las Vegas": "Las Vegas",
        "Las_Vegas": "Las Vegas",
        "Mexico City": "Mexico",
        "Mexico": "Mexico",
        "Mexican": "Mexico",
        "Sao Paulo": "Brazil",
        "Brazilian": "Brazil",
        "Brazil": "Brazil",
        "Miami": "Miami",
        "Canadian": "Canada",
        "Canada": "Canada",
        # Oceania races
        "Australian": "Australia",
        "Australia": "Australia",
    }
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        # Set window properties
        self.setWindowTitle(tr("Circle Map"))
        self.setMinimumSize(400, 400)
        self.resize(450, 450)
        
        # Track data
        self._track_data = None
        self._current_race_key = None
        
        print("[CIRCLE_MAP_MDI] LiveTimingCircleMap initialized")
    
    def _setup_ui(self):
        """Setup UI components - no selector needed"""
        # Circle Map Widget (add directly, no selector needed)
        self.circle_widget = CircleMapWidget()
        self._main_layout.addWidget(self.circle_widget)
    
    def _normalize_race_name(self, race_key: str) -> str:
        """Normalize race name"""
        # Remove "_Race" suffix
        race_name = race_key.replace("_Race", "").replace("_", " ")
        # Find mapping
        return self.TRACK_NAME_MAP.get(race_name, race_name)
    
    def _load_track_for_race(self, year: int, race_key: str) -> bool:
        """
        Load track data for specified race
        
        Search json/track_position_analysis_{year}_{track}_R.json
        """
        track_name = self._normalize_race_name(race_key)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        json_dir = project_root / "json"
        
        # Define search priority: current year > other years
        years_to_try = [str(year)]
        for fallback_year in ["2025", "2024", "2023"]:
            if fallback_year != str(year):
                years_to_try.append(fallback_year)
        
        for try_year in years_to_try:
            # Try different naming patterns
            patterns = [
                f"track_position_analysis_{try_year}_{track_name}_R.json",
                f"track_position_analysis_{try_year}_{race_key}_R.json",
                f"track_position_analysis_{try_year}_{race_key.replace('_', ' ')}_R.json",
            ]
            
            for pattern in patterns:
                json_file = json_dir / pattern
                if json_file.exists():
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            api_response = json.load(f)
                        
                        data = api_response.get('data', {})
                        self._track_data = {
                            'position_records': data.get('position_records', []),
                            'track_bounds': data.get('track_bounds', {}),
                        }
                        
                        # Load to widget
                        self.circle_widget.load_track_data(self._track_data)
                        
                        # Load corner data if available
                        official_corners = data.get('official_corners', {})
                        if official_corners.get('available', False):
                            corners = official_corners.get('corners', [])
                            # Use mapped_distance as lap_distance for circle mapping
                            for corner in corners:
                                if 'mapped_distance' in corner:
                                    corner['lap_distance'] = corner['mapped_distance']
                            self.circle_widget.set_corners(corners)
                            print(f"[CIRCLE_MAP_MDI] Corners loaded: {len(corners)} corners")
                        
                        if try_year != str(year):
                            print(f"[CIRCLE_MAP_MDI] Using {try_year} track data (original {year} not found)")
                        print(f"[CIRCLE_MAP_MDI] Track loaded: {track_name}, {len(self._track_data['position_records'])} points")
                        return True
                        
                    except Exception as e:
                        print(f"[CIRCLE_MAP_MDI] Failed to load {json_file}: {e}")
        
        print(f"[CIRCLE_MAP_MDI] Track data not found for {year} {race_key}")
        return False
    
    # ===========================================
    # DataManager Signal Handlers
    # ===========================================
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded - automatically load corresponding track"""
        year = race_info.get('year', 2025)
        race_key = race_info.get('race', '')
        
        print(f"[CIRCLE_MAP_MDI] Race loaded: {year} {race_key}")
        
        # Set driver info
        driver_info = race_info.get('driver_info', {})
        self.circle_widget.set_driver_info(driver_info)
        
        # Set total laps
        total_laps = race_info.get('total_laps', 55)
        self.circle_widget.set_total_laps(total_laps)
        
        # Load track (only reload when race changes)
        if race_key != self._current_race_key:
            self._current_race_key = race_key
            self._load_track_for_race(year, race_key)
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        print("[CIRCLE_MAP_MDI] Race unloaded")
        self.circle_widget.driver_positions = {}
        self.circle_widget.update()
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated"""
        drivers = snapshot.get('drivers', {})
        race_time = snapshot.get('race_time_seconds', 0)
        current_lap = snapshot.get('current_lap', 0)
        
        # Convert race_time_seconds to string format
        if isinstance(race_time, (int, float)):
            hours = int(race_time // 3600)
            minutes = int((race_time % 3600) // 60)
            seconds = int(race_time % 60)
            race_time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            race_time_str = str(race_time) if race_time else "00:00:00"
        
        self.circle_widget.update_positions(
            drivers,
            current_lap=current_lap,
            race_time=race_time_str
        )
        
        # Update track status
        race_time_for_status = snapshot.get('race_time', '')
        if race_time_for_status and self._data_manager:
            track_status = self._data_manager.get_track_status_at_time(race_time_for_status)
            print(f"[CIRCLE_MAP_MDI] Track status at {race_time_for_status}: {track_status}")
            self.circle_widget.update_track_status(track_status)
    
    def _on_interpolation_updated(self, current_snap: Dict[str, Any], next_snap: Dict[str, Any],
                                   alpha: float, race_time_seconds: float):
        """處理插值更新 - 實現平滑動畫"""
        # 使用插值數據更新 Widget
        self.circle_widget.update_interpolation(current_snap, next_snap, alpha, race_time_seconds)
        
        # 更新 Track Status（使用當前快照的時間）
        race_time_for_status = current_snap.get('race_time', '')
        if race_time_for_status and self._data_manager:
            track_status = self._data_manager.get_track_status_at_time(race_time_for_status)
            self.circle_widget.update_track_status(track_status)
