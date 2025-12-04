"""
Live Timing Lap Time Distribution
=================================

顯示所有車手的圈速差距分佈視覺化。

參考: Live_timing_test/demo_live_position_tracking.py LapTimeDistributionWidget

Author: F1T Team
Date: 2025-12-04
"""

from typing import Dict, Any, Optional

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QBrush, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

# 嘗試導入通用顏色系統
COLOR_PALETTE_AVAILABLE = False
color_palette_provider = None
try:
    from modules.gui.themes import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
    print("[LAP_TIME_DIST] color_palette_provider 導入成功")
except ImportError as e:
    print(f"[LAP_TIME_DIST] color_palette_provider 不可用: {e}")


class LapTimeDistributionWidget(QWidget):
    """
    Lap Time Distribution Widget
    
    顯示所有車手的圈速差距分佈：
    - Y 軸：以最快圈速為基準，向下遞增顯示差距
    - 左側：Y 軸刻度
    - 中間：車隊顏色圓點 + 連接線 + Flag 標籤
    - 右側：輪胎配方圓形標記
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(180, 300)
        
        # 車手數據: {driver_num: {tla, lap_time, gap, team_color, compound}}
        self._driver_data: Dict[str, Dict[str, Any]] = {}
        self._fastest_time: float = 0.0
        self._fastest_time_str: str = ""
        self._fastest_driver: str = ""
        
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
        
        # 輪胎顏色
        self.tyre_colors = {
            'SOFT': '#FF3333',
            'MEDIUM': '#FFDD00',
            'HARD': '#FFFFFF',
            'INTERMEDIATE': '#43B02A',
            'WET': '#0066FF',
            'UNKNOWN': '#888888'
        }
        
        print("[LAP_TIME_DIST] LapTimeDistributionWidget initialized")
    
    def _get_driver_color(self, data: Dict[str, Any]) -> QColor:
        """
        獲取車手顏色 - 優先使用 color_palette_provider
        
        Args:
            data: 車手數據字典
            
        Returns:
            QColor: 車手顏色
        """
        # 優先使用通用顏色系統
        if COLOR_PALETTE_AVAILABLE and color_palette_provider:
            try:
                driver_tla = data.get('driver_tla')
                if driver_tla:
                    color_qcolor = color_palette_provider.get_driver_color(driver_tla, fallback=True)
                    if color_qcolor:
                        return color_qcolor
            except Exception:
                pass
        
        # 備選：從 data 的 team_color
        team_color = data.get('team_color', '#888888')
        if not team_color.startswith('#'):
            team_color = f'#{team_color}'
        return QColor(team_color)
    
    def update_data(self, drivers_data: Dict[str, Dict[str, Any]]):
        """
        更新車手圈速數據
        
        Args:
            drivers_data: {driver_num: {
                'driver_tla': str,
                'best_lap_time': float or str,
                'last_lap_time': float or str,
                'team_color': str,
                'compound': str,
                'status': str
            }}
        """
        self._driver_data = {}
        self._fastest_time = float('inf')
        self._fastest_driver = ""
        
        for driver_num, data in drivers_data.items():
            # 過濾 DNF/Retired/Stopped 車手
            status = data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            # 解析圈速 (優先使用 best_lap_time)
            lap_time = data.get('best_lap_time') or data.get('last_lap_time')
            if lap_time is None:
                continue
            
            lap_time_sec = self._parse_lap_time(lap_time)
            if lap_time_sec is None or lap_time_sec <= 0:
                continue
            
            self._driver_data[driver_num] = {
                'driver_tla': data.get('driver_tla', driver_num),
                'lap_time_sec': lap_time_sec,
                'team_color': data.get('team_color', '888888'),
                'compound': data.get('compound', 'UNKNOWN'),
            }
            
            if lap_time_sec < self._fastest_time:
                self._fastest_time = lap_time_sec
                self._fastest_driver = driver_num
        
        # 計算差距
        for driver_num, data in self._driver_data.items():
            data['gap'] = data['lap_time_sec'] - self._fastest_time
        
        # 格式化最快圈速
        if self._fastest_time < float('inf'):
            self._fastest_time_str = self._format_lap_time(self._fastest_time)
        else:
            self._fastest_time_str = "--:--.---"
        
        self.update()
    
    def _parse_lap_time(self, lap_time) -> Optional[float]:
        """解析圈速為秒數"""
        if lap_time is None:
            return None
        
        if isinstance(lap_time, (int, float)):
            return float(lap_time)
        
        if isinstance(lap_time, str):
            try:
                if ':' in lap_time:
                    parts = lap_time.split(':')
                    minutes = int(parts[0])
                    seconds = float(parts[1])
                    return minutes * 60 + seconds
                else:
                    return float(lap_time)
            except:
                return None
        
        return None
    
    def _format_lap_time(self, seconds: float) -> str:
        """格式化秒數為圈速字串"""
        if seconds <= 0 or seconds == float('inf'):
            return "--:--.---"
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:06.3f}"
    
    def paintEvent(self, event):
        """繪製單圈時間分佈"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        if not self._driver_data:
            painter.setPen(QColor(128, 128, 128))
            font = QFont()
            font.setPointSize(10)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignCenter, tr("waiting_for_data", "Waiting for data..."))
            return
        
        width = self.width()
        height = self.height()
        
        margin_top = 30
        margin_bottom = 10
        margin_left = 10
        margin_right = 10
        
        chart_height = height - margin_top - margin_bottom
        
        sorted_drivers = sorted(
            self._driver_data.items(),
            key=lambda x: x[1]['gap']
        )
        
        if not sorted_drivers:
            return
        
        max_gap = max(d[1]['gap'] for d in sorted_drivers)
        max_gap = max(max_gap, 0.5)
        
        # 繪製最快圈速標題
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(margin_left, 18, self._fastest_time_str)
        
        self._draw_y_axis_and_drivers(painter, sorted_drivers, 
                                       margin_left, margin_top, 
                                       width - margin_left - margin_right,
                                       chart_height, max_gap)
    
    def _draw_y_axis_and_drivers(self, painter: QPainter, sorted_drivers: list,
                                  left: int, top: int, width: int, height: int,
                                  max_gap: float):
        """繪製 Y 軸刻度和車手標記"""
        tick_interval = 0.2
        num_ticks = int(max_gap / tick_interval) + 2
        
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        y_axis_x = left + 35
        
        # 繪製 Y 軸刻度
        painter.setPen(QColor(100, 100, 100))
        for i in range(num_ticks + 1):
            gap_value = i * tick_interval
            if gap_value > max_gap + tick_interval:
                break
            
            y = top + (gap_value / (max_gap + tick_interval)) * height
            
            painter.setPen(QPen(QColor(80, 80, 80), 1))
            painter.drawLine(int(y_axis_x - 5), int(y), int(y_axis_x), int(y))
            
            painter.setPen(QColor(120, 120, 120))
            if i == 0:
                label = ""
            else:
                label = f"+ {gap_value:.1f}"
            painter.drawText(int(left), int(y + 4), label)
        
        # 繪製 Y 軸主線
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawLine(int(y_axis_x), int(top), int(y_axis_x), int(top + height))
        
        # 計算車手位置
        markers = []
        for driver_num, data in sorted_drivers:
            gap = data['gap']
            y = top + (gap / (max_gap + tick_interval)) * height
            markers.append({
                'driver_num': driver_num,
                'data': data,
                'original_y': y,
                'flag_y': y
            })
        
        # 避免 Flag 重疊
        flag_height = 14
        min_spacing = flag_height + 2
        
        for i, marker in enumerate(markers):
            if i == 0:
                continue
            for j in range(i - 1, -1, -1):
                prev_flag_y = markers[j]['flag_y']
                current_y = marker['flag_y']
                if abs(current_y - prev_flag_y) < min_spacing:
                    marker['flag_y'] = prev_flag_y + min_spacing
        
        dot_x = y_axis_x + 8
        
        # 繪製圓點 - 使用 color_palette_provider
        for marker in markers:
            data = marker['data']
            original_y = marker['original_y']
            color = self._get_driver_color(data)
            
            dot_radius = 5
            painter.setBrush(QBrush(color))
            painter.setPen(QPen(color, 1))
            painter.drawEllipse(QPointF(dot_x, original_y), dot_radius, dot_radius)
        
        # 繪製連接線和 Flag
        for marker in markers:
            data = marker['data']
            original_y = marker['original_y']
            flag_y = marker['flag_y']
            self._draw_driver_marker(painter, data, dot_x, original_y, flag_y, width, left)
    
    def _draw_driver_marker(self, painter: QPainter, data: Dict,
                            dot_x: float, original_y: float, flag_y: float,
                            width: int, left: int):
        """繪製車手標記"""
        tla = data['driver_tla']
        gap = data['gap']
        compound = data['compound']
        
        # 使用 color_palette_provider 獲取顏色
        color = self._get_driver_color(data)
        
        line_start_x = dot_x + 7
        flag_x = dot_x + 25
        
        # 連接線
        painter.setPen(QPen(color, 2))
        painter.drawLine(QPointF(line_start_x, original_y), QPointF(flag_x, flag_y))
        
        # 車手代碼和差距
        text_x = flag_x + 5
        painter.setPen(QColor(255, 255, 255))
        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        
        if gap < 0.001:
            gap_str = ""
        else:
            gap_str = f"+ {gap:.3f}"
        
        display_text = f"{tla}  {gap_str}"
        painter.drawText(int(text_x), int(flag_y + 4), display_text)
        
        # 輪胎配方圓形
        tyre_x = left + width - 8
        tyre_radius = 6
        tyre_color = QColor(self.tyre_colors.get(compound, self.tyre_colors['UNKNOWN']))
        
        painter.setBrush(QBrush(tyre_color))
        if compound in ['HARD', 'MEDIUM']:
            painter.setPen(QPen(QColor(0, 0, 0), 1))
        else:
            painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(QPointF(tyre_x, flag_y), tyre_radius, tyre_radius)


class LiveTimingLapDistribution(BaseLiveTimingMDI):
    """
    Live Timing Lap Time Distribution MDI Window
    
    顯示所有車手的圈速差距分佈視覺化。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr("lap_time_distribution", "Lap Time Distribution"))
        self.setMinimumSize(250, 400)
        self.resize(280, 500)
        
        print("[LAP_DIST_MDI] LiveTimingLapDistribution initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.distribution_widget = LapTimeDistributionWidget()
        self._main_layout.addWidget(self.distribution_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        print(f"[LAP_DIST_MDI] Race loaded: {race_info.get('year')} {race_info.get('race')}")
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        print("[LAP_DIST_MDI] Race unloaded")
        self.distribution_widget._driver_data = {}
        self.distribution_widget.update()
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated - 合併 drivers 數據和輪胎狀態"""
        drivers = snapshot.get('drivers', {})
        
        # 從 DataManager 獲取輪胎狀態（參考 ranking_tower 的實現）
        tyre_state = {}
        if self._data_manager:
            if hasattr(self._data_manager, 'get_tyre_state'):
                tyre_state = self._data_manager.get_tyre_state()
            elif hasattr(self._data_manager, 'get_tyre_state_at_time'):
                timestamp = snapshot.get('race_time', '')
                if timestamp:
                    tyre_state = self._data_manager.get_tyre_state_at_time(timestamp)
        
        # 合併輪胎配方到 drivers 數據
        merged_drivers = {}
        for driver_num, data in drivers.items():
            merged_data = dict(data)  # 複製原數據
            
            # 從 tyre_state 獲取 compound
            if driver_num in tyre_state:
                tyre_info = tyre_state[driver_num]
                compound = tyre_info.get('compound', 'UNKNOWN')
                merged_data['compound'] = compound
            
            merged_drivers[driver_num] = merged_data
        
        self.distribution_widget.update_data(merged_drivers)
