"""
Live Timing 賽道地圖
=====================

顯示賽道輪廓和車手位置的 MDI 子視窗。

Author: F1T Team
Date: 2025-12-03
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    print("[TRACK_MAP] color_palette_provider not available")


class TrackMapWidget(QWidget):
    """
    賽道地圖顯示元件
    
    功能：
    - 繪製賽道輪廓
    - 繪製車手位置（彩色圓點 + 標籤）
    - 繪製彎道標記
    - 繪製 Sector 標記 (FIN/S1/S2)
    
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
        
        # 賽道資料
        self.track_outline: List[Tuple[float, float]] = []
        self.track_points: List[Dict[str, float]] = []
        self.track_bounds: Dict[str, float] = {}
        self.track_length: float = 0.0
        
        # 車手位置
        self.driver_positions: Dict[str, Dict[str, Any]] = {}
        self._marker_positions: List[Dict[str, Any]] = []
        
        # === 插值相關 ===
        self._current_snapshot: Optional[Dict[str, Any]] = None
        self._next_snapshot: Optional[Dict[str, Any]] = None
        self._interpolation_alpha: float = 0.0
        self._interpolated_positions: Dict[str, Dict[str, Any]] = {}
        
        # 車手資訊
        self.driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 彎道資料
        self.official_corners: List[Dict[str, Any]] = []
        
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
        
        # 車號顏色映射
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
    
    def load_track_outline(self, track_data: Dict):
        """載入賽道輪廓資料"""
        try:
            position_records = track_data.get('position_records', [])
            if not position_records:
                print("[TRACK_MAP] No position records found")
                return

            self.track_outline = []
            self.track_points = []
            self.track_bounds = track_data.get('track_bounds', {}) or {}
            self.track_length = 0.0

            for record in position_records:
                x = record.get('position_x')
                y = record.get('position_y')
                distance = record.get('distance_m') or record.get('distance')
                
                if x is None or y is None:
                    continue
                
                self.track_outline.append((x, y))
                
                if distance is None:
                    if self.track_points:
                        prev = self.track_points[-1]
                        dx = x - prev['x']
                        dy = y - prev['y']
                        distance = prev['distance'] + (dx ** 2 + dy ** 2) ** 0.5
                    else:
                        distance = 0.0
                
                self.track_points.append({'x': x, 'y': y, 'distance': float(distance)})
                
                if distance > self.track_length:
                    self.track_length = float(distance)

            self.track_points.sort(key=lambda item: item['distance'])
            print(f"[TRACK_MAP] Track loaded: {len(self.track_outline)} points, length: {self.track_length:.1f}m")
            self.update()

        except Exception as e:
            print(f"[TRACK_MAP] Failed to load track: {e}")
    
    def set_driver_info(self, driver_info: Dict):
        """設置車手資訊"""
        self.driver_info = driver_info or {}
    
    def set_official_corners(self, corners: List[Dict[str, Any]]):
        """設置彎道資料"""
        self.official_corners = corners or []
        if self.official_corners:
            print(f"[TRACK_MAP] Set {len(self.official_corners)} corner markers")
        self.update()
    
    def update_driver_positions(
        self,
        drivers_data: Dict,
        frame_index: int = 0,
        total_frames: int = 1,
        race_time_seconds: float = 0.0,
    ):
        """更新車手位置"""
        self.driver_positions = drivers_data or {}
        self._prepare_marker_positions()
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
        
        # 使用插值位置準備標記
        self._prepare_marker_positions_from_interpolated()
        
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
    
    def _prepare_marker_positions_from_interpolated(self):
        """從插值位置準備車手標記"""
        if not self._interpolated_positions:
            self._marker_positions = []
            return

        markers = []
        for driver_num, driver_data in self._interpolated_positions.items():
            x = driver_data.get('x')
            y = driver_data.get('y')
            
            if x is None or y is None:
                continue
            
            driver_tla = driver_data.get('driver_tla', driver_num)
            
            markers.append({
                'driver': driver_num,
                'driver_tla': driver_tla,
                'x': x,
                'y': y,
                'position': driver_data.get('position'),
                'status': driver_data.get('status', 'Unknown'),
                'team_color': driver_data.get('team_color')
            })
        
        self._marker_positions = markers
    
    def _prepare_marker_positions(self):
        """準備車手標記位置"""
        if not self.driver_positions:
            self._marker_positions = []
            return

        markers = []
        for driver_num, driver_data in self.driver_positions.items():
            status = driver_data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            x = driver_data.get('x')
            y = driver_data.get('y')
            
            if x is None or y is None:
                continue
            
            driver_tla = driver_data.get('driver_tla', driver_num)
            
            markers.append({
                'driver': driver_num,
                'driver_tla': driver_tla,
                'x': x,
                'y': y,
                'position': driver_data.get('position'),
                'status': driver_data.get('status', 'Unknown'),
                'team_color': driver_data.get('team_color')
            })
        
        self._marker_positions = markers
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))

        transform = self._compute_transform()
        if transform and self.track_outline:
            self._draw_track_outline(painter, transform)
            self._draw_corner_markers(painter, transform)
            self._draw_sector_markers(painter, transform)
            self._draw_driver_markers(painter, transform)
        else:
            # 顯示提示訊息
            painter.setPen(QColor(200, 200, 200))
            font = QFont()
            font.setPointSize(12)
            painter.setFont(font)
            
            # 根據狀態顯示不同訊息
            if not self.track_outline:
                hint_text = tr("Please select a race and click Load")
            else:
                hint_text = tr("Loading track...")
            
            painter.drawText(self.rect(), Qt.AlignCenter, hint_text)
    
    def _compute_transform(self) -> Optional[Dict[str, float]]:
        """計算座標轉換參數"""
        if not self.track_outline:
            return None

        margin = 50
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin

        x_min = self.track_bounds.get('x_min') if self.track_bounds else min(x for x, _ in self.track_outline)
        x_max = self.track_bounds.get('x_max') if self.track_bounds else max(x for x, _ in self.track_outline)
        y_min = self.track_bounds.get('y_min') if self.track_bounds else min(y for _, y in self.track_outline)
        y_max = self.track_bounds.get('y_max') if self.track_bounds else max(y for _, y in self.track_outline)

        x_range = x_max - x_min if x_max != x_min else 1
        y_range = y_max - y_min if y_max != y_min else 1

        scale = min(width / x_range, height / y_range)
        offset_x = (width - x_range * scale) / 2
        offset_y = (height - y_range * scale) / 2

        return {
            'margin': margin,
            'scale': scale,
            'offset_x': offset_x,
            'offset_y': offset_y,
            'x_min': x_min,
            'y_min': y_min,
        }
    
    def _world_to_screen(self, point: Tuple[float, float], transform: Dict[str, float]) -> Tuple[float, float]:
        """世界座標轉螢幕座標"""
        x, y = point
        margin = transform['margin']
        scale = transform['scale']
        x_min = transform['x_min']
        y_min = transform['y_min']
        offset_x = transform['offset_x']
        offset_y = transform['offset_y']
        screen_x = margin + offset_x + (x - x_min) * scale
        screen_y = margin + offset_y + (y - y_min) * scale
        return screen_x, screen_y
    
    def _draw_track_outline(self, painter: QPainter, transform: Dict[str, float]):
        """繪製賽道輪廓"""
        painter.setPen(QPen(QColor(100, 100, 100), 3))
        for i in range(len(self.track_outline) - 1):
            x1, y1 = self._world_to_screen(self.track_outline[i], transform)
            x2, y2 = self._world_to_screen(self.track_outline[i + 1], transform)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
    
    def _draw_driver_markers(self, painter: QPainter, transform: Dict[str, float]):
        """繪製車手標記"""
        if not self._marker_positions:
            return

        for marker in self._marker_positions:
            screen_x, screen_y = self._world_to_screen((marker['x'], marker['y']), transform)
            driver_num = marker.get('driver', '')
            driver_tla = marker.get('driver_tla', driver_num)
            
            color = self._get_driver_color(driver_num, marker)
            
            # 繪製圓點
            dot_radius = 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawEllipse(QPointF(screen_x, screen_y), dot_radius, dot_radius)
            
            # 計算標籤位置
            position = marker.get('position', 99)
            offset_x = 25
            offset_y = -15 + (position % 5) * 5
            
            flag_x = screen_x + offset_x
            flag_y = screen_y + offset_y
            
            # 繪製連接線
            painter.setPen(QPen(color, 1))
            painter.drawLine(QPointF(screen_x, screen_y), QPointF(flag_x, flag_y))
            
            # 繪製標籤
            self._draw_flag_label(painter, flag_x, flag_y, driver_tla, color)
    
    def _get_driver_color(self, driver_num: str, marker: dict = None) -> QColor:
        """獲取車手顏色 - 優先使用 color_palette_provider"""
        # 優先使用通用顏色系統
        if COLOR_PALETTE_AVAILABLE:
            try:
                # 嘗試從 marker 獲取 driver_tla
                driver_tla = None
                if marker:
                    driver_tla = marker.get('driver_tla')
                if not driver_tla and driver_num in self.driver_info:
                    driver_tla = self.driver_info[driver_num].get('tla', driver_num)
                if driver_tla:
                    color_qcolor = color_palette_provider.get_driver_color(driver_tla, fallback=True)
                    if color_qcolor:
                        return color_qcolor
            except Exception:
                pass
        
        # 備選：使用 marker 中的 team_color
        if marker:
            tc = marker.get('team_color')
            if tc:
                color_str = f'#{tc}' if not tc.startswith('#') else tc
                return QColor(color_str)
        
        # 備選：driver_info
        if driver_num in self.driver_info:
            team = self.driver_info[driver_num].get('team', '')
            if team in self.team_colors:
                return QColor(self.team_colors[team])
        
        # 備選：車號顏色映射
        if driver_num in self.driver_colors:
            return QColor(self.driver_colors[driver_num])
        
        return QColor(self.team_colors['default'])
    
    def _draw_flag_label(self, painter: QPainter, x: float, y: float, tla: str, color: QColor):
        """繪製標籤"""
        w, h = 30, 14
        flag_x = x
        flag_y = y - h / 2
        
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(QRectF(flag_x, flag_y, w, h))
        
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        rect = painter.fontMetrics().boundingRect(tla)
        text_x = flag_x + (w - rect.width()) / 2
        text_y = flag_y + h - 3
        painter.drawText(int(text_x), int(text_y), tla)
    
    def _draw_corner_markers(self, painter: QPainter, transform: Dict[str, float]):
        """繪製彎道編號標記 - 垂直於賽道切線的淺綠色線條 + 標籤"""
        if not self.official_corners or not self.track_points:
            return
        
        corner_color = QColor(144, 238, 144)  # LightGreen
        
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        for corner in self.official_corners:
            corner_num = corner.get('number', 0)
            corner_x = corner.get('x', 0)
            corner_y = corner.get('y', 0)
            corner_distance = corner.get('distance', 0)
            
            # 如果沒有 x/y 座標，嘗試從 distance 計算
            if corner_x == 0 and corner_y == 0:
                if corner_distance > 0 and self.track_length > 0:
                    progress = corner_distance / self.track_length
                    target_distance = progress * self.track_length
                    
                    for pt in self.track_points:
                        if pt['distance'] >= target_distance:
                            corner_x = pt['x']
                            corner_y = pt['y']
                            break
            
            if corner_x == 0 and corner_y == 0:
                continue
            
            # 找最近的賽道點索引來計算法線方向
            nearest_idx = 0
            min_dist = float('inf')
            for i, pt in enumerate(self.track_points):
                dx = corner_x - pt['x']
                dy = corner_y - pt['y']
                dist = dx*dx + dy*dy
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = i
            
            # 取得相鄰點來計算切線方向
            prev_idx = max(0, nearest_idx - 1)
            next_idx = min(len(self.track_points) - 1, nearest_idx + 1)
            prev_pt = self.track_points[prev_idx]
            next_pt = self.track_points[next_idx]
            
            # 計算賽道切線方向
            dx = next_pt['x'] - prev_pt['x']
            dy = next_pt['y'] - prev_pt['y']
            length = (dx**2 + dy**2)**0.5
            if length == 0:
                continue
            
            # 法線方向 (垂直於賽道)
            nx = -dy / length
            ny = dx / length
            
            screen_x, screen_y = self._world_to_screen((corner_x, corner_y), transform)
            
            line_length = 10
            
            # 繪製垂直於賽道的線條
            painter.setPen(QPen(corner_color, 1))
            painter.drawLine(
                QPointF(screen_x - nx * line_length, screen_y - ny * line_length),
                QPointF(screen_x + nx * line_length, screen_y + ny * line_length)
            )
            
            # 繪製編號（在法線方向外側）
            painter.setPen(corner_color)
            label = str(corner_num)
            text_rect = painter.fontMetrics().boundingRect(label)
            label_x = screen_x + nx * (line_length + 6) - text_rect.width() / 2
            label_y = screen_y + ny * (line_length + 6) + text_rect.height() / 4
            painter.drawText(int(label_x), int(label_y), label)
    
    def _draw_sector_markers(self, painter: QPainter, transform: Dict[str, float]):
        """繪製 Sector 標記 (FIN/S1/S2) - 垂直於賽道切線的白色線條"""
        if not self.track_points or len(self.track_points) < 3:
            return
        
        sector_positions = [
            ('FIN', 0.0),
            ('S1', 0.33),
            ('S2', 0.66),
        ]
        
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        
        for label, progress in sector_positions:
            target_distance = progress * self.track_length
            
            # 找最近的賽道點索引
            nearest_idx = 0
            for i, pt in enumerate(self.track_points):
                if pt['distance'] >= target_distance:
                    nearest_idx = i
                    break
            
            # 取得當前點和相鄰點來計算切線方向
            curr_pt = self.track_points[nearest_idx]
            prev_idx = max(0, nearest_idx - 1)
            next_idx = min(len(self.track_points) - 1, nearest_idx + 1)
            prev_pt = self.track_points[prev_idx]
            next_pt = self.track_points[next_idx]
            
            # 計算賽道切線方向
            dx = next_pt['x'] - prev_pt['x']
            dy = next_pt['y'] - prev_pt['y']
            length = (dx**2 + dy**2)**0.5
            if length == 0:
                continue
            
            # 法線方向 (垂直於賽道)
            nx = -dy / length
            ny = dx / length
            
            screen_x, screen_y = self._world_to_screen((curr_pt['x'], curr_pt['y']), transform)
            
            line_length = 15
            
            # 繪製垂直於賽道的白色線條
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(
                QPointF(screen_x - nx * line_length, screen_y - ny * line_length),
                QPointF(screen_x + nx * line_length, screen_y + ny * line_length)
            )
            
            # 繪製標籤（在法線方向外側）
            painter.setPen(QColor(255, 255, 255))
            text_rect = painter.fontMetrics().boundingRect(label)
            label_x = screen_x + nx * (line_length + 8) - text_rect.width() / 2
            label_y = screen_y + ny * (line_length + 8) + text_rect.height() / 4
            painter.drawText(int(label_x), int(label_y), label)


class LiveTimingTrackMap(BaseLiveTimingMDI):
    """
    Live Timing 賽道地圖 MDI 子視窗
    
    賽道資料自動從 race_loaded 信號獲取，無需手動選擇。
    """
    
    # 賽道名稱映射（LiveF1 → FastF1）
    TRACK_NAME_MAP = {
        # 亞洲賽事
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
        # 歐洲賽事
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
        # 美洲賽事
        "United States": "United States",
        "United_States": "United States",
        "Las Vegas": "Las Vegas",
        "Las_Vegas": "Las Vegas",
        "Mexico City": "Mexico",
        "Mexico": "Mexico",
        "Mexican": "Mexico",
        "São Paulo": "Brazil",
        "Sao Paulo": "Brazil",
        "Brazilian": "Brazil",
        "Brazil": "Brazil",
        "Miami": "Miami",
        "Canadian": "Canada",
        "Canada": "Canada",
        # 大洋洲賽事
        "Australian": "Australia",
        "Australia": "Australia",
    }
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        # 設置視窗屬性
        self.setWindowTitle(tr("Track Map"))
        self.setMinimumSize(400, 400)
        self.resize(500, 500)
        
        # 賽道資料
        self._track_data = None
        self._current_race_key = None
        
        print("[TRACK_MAP_MDI] LiveTimingTrackMap initialized")
    
    def _setup_ui(self):
        """設置 UI 組件 - 移除賽道選擇器"""
        # 賽道地圖 Widget（直接添加，不需要選擇器）
        self.track_widget = TrackMapWidget()
        self._main_layout.addWidget(self.track_widget)
    
    def _normalize_race_name(self, race_key: str) -> str:
        """標準化賽道名稱"""
        # 移除 "_Race" 後綴
        race_name = race_key.replace("_Race", "").replace("_", " ")
        # 查找映射
        return self.TRACK_NAME_MAP.get(race_name, race_name)
    
    def _load_track_for_race(self, year: int, race_key: str) -> bool:
        """
        載入指定賽事的賽道資料
        
        搜索 json/track_position_analysis_{year}_{track}_R.json
        """
        track_name = self._normalize_race_name(race_key)
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        json_dir = project_root / "json"
        
        # 定義搜索優先級：當年 > 其他年份
        years_to_try = [str(year)]
        for fallback_year in ["2025", "2024", "2023"]:
            if fallback_year != str(year):
                years_to_try.append(fallback_year)
        
        for try_year in years_to_try:
            # 嘗試不同的命名模式
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
                            'official_corners': data.get('official_corners', {})
                        }
                        
                        # 載入到 widget
                        self.track_widget.load_track_outline(self._track_data)
                        
                        # 載入彎道資料
                        corners = self._track_data.get('official_corners', {}).get('corners', [])
                        if corners:
                            self.track_widget.set_official_corners(corners)
                        
                        if try_year != str(year):
                            print(f"[TRACK_MAP_MDI] Using {try_year} track data (original {year} not found)")
                        print(f"[TRACK_MAP_MDI] Track loaded: {track_name}, {len(self._track_data['position_records'])} points")
                        return True
                        
                    except Exception as e:
                        print(f"[TRACK_MAP_MDI] Failed to load {json_file}: {e}")
        
        print(f"[TRACK_MAP_MDI] Track data not found for {year} {race_key}")
        return False
    
    # ===========================================
    # DataManager 信號處理
    # ===========================================
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成 - 自動載入對應賽道"""
        year = race_info.get('year', 2025)
        race_key = race_info.get('race', '')
        
        print(f"[TRACK_MAP_MDI] Race loaded: {year} {race_key}")
        
        # 設置車手資訊
        driver_info = race_info.get('driver_info', {})
        self.track_widget.set_driver_info(driver_info)
        
        # 載入賽道（只有賽事變更時才重新載入）
        if race_key != self._current_race_key:
            self._current_race_key = race_key
            self._load_track_for_race(year, race_key)
    
    def _on_race_unloaded(self):
        """賽事卸載"""
        print("[TRACK_MAP_MDI] Race unloaded")
        self.track_widget.driver_positions = {}
        self.track_widget.update()
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """快照更新"""
        drivers = snapshot.get('drivers', {})
        race_time = snapshot.get('race_time_seconds', 0)
        
        self.track_widget.update_driver_positions(
            drivers,
            frame_index=0,
            total_frames=1,
            race_time_seconds=race_time
        )
    
    def _on_interpolation_updated(self, current_snap: Dict[str, Any], next_snap: Dict[str, Any],
                                   alpha: float, race_time_seconds: float):
        """處理插值更新 - 實現平滑動畫"""
        # 使用插值數據更新 Widget
        self.track_widget.update_interpolation(current_snap, next_snap, alpha, race_time_seconds)
