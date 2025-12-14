"""
Track & Weather Status Module (MDI Version)
=============================================

獨立的 Live Timing 模組，顯示賽道狀態與天氣資訊。
雙行設計：
- 第一行：賽事名稱、時間、圈數、Track Status
- 第二行：空氣溫度、賽道溫度、濕度、氣壓、風速風向

Author: F1T Team
Date: 2025-12-08
"""

from typing import Dict, Any, Optional

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QSizePolicy
)
from PyQt5.QtGui import QFont, QPalette, QColor

from core.gui_i18n import tr
from ..core.data_manager import LiveTimingDataManager
from ..core.base_live_mdi import BaseLiveTimingMDI

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger("live_timing.track_weather", component="gui")


class TrackWeatherWidget(QWidget):
    """
    Track & Weather 狀態顯示 Widget
    
    顯示：
    - 賽事名稱 (Abu Dhabi GP: Race)
    - 比賽時間 (1:12:32)
    - 圈數 (Lap 32/58)
    - Track Status (Track Clear / Yellow Flag / Red Flag / VSC / SC)
    - 空氣溫度 (Air 28.5°C)
    - 賽道溫度 (Track 42.3°C)
    - 濕度 (Humidity 45%)
    - 氣壓 (Pressure 1013mb)
    - 風速風向 (Wind 3.2m/s NW)
    """
    
    # Track Status 對應表：status_code -> (text, bg_color, text_color)
    TRACK_STATUS_MAP = {
        '1': ('Track Clear', '#90EE90', '#000000'),      # Light green (暖色系淺綠)
        '2': ('Yellow Flag', '#FFFF00', '#000000'),      # Yellow
        '4': ('Safety Car', '#FF8000', '#000000'),       # Orange
        '5': ('Red Flag', '#FF0000', '#FFFFFF'),         # Red
        '6': ('VSC', '#FF00FF', '#FFFFFF'),              # Purple/Magenta
        '7': ('VSC Ending', '#FF00FF', '#FFFFFF'),       # VSC Ending
    }
    
    # 風向角度對應
    WIND_DIRECTIONS = [
        (0, 'N'), (22.5, 'NNE'), (45, 'NE'), (67.5, 'ENE'),
        (90, 'E'), (112.5, 'ESE'), (135, 'SE'), (157.5, 'SSE'),
        (180, 'S'), (202.5, 'SSW'), (225, 'SW'), (247.5, 'WSW'),
        (270, 'W'), (292.5, 'WNW'), (315, 'NW'), (337.5, 'NNW'),
        (360, 'N')
    ]
    
    def __init__(self, data_manager=None, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        
        # 當前狀態
        self._race_name = "---"
        self._session_type = "---"
        self._race_time = "0:00:00"
        self._current_lap = 0
        self._total_laps = 0
        self._track_status = "1"
        
        # 天氣數據
        self._air_temp = 0.0
        self._track_temp = 0.0
        self._humidity = 0.0
        self._pressure = 0.0
        self._wind_speed = 0.0
        self._wind_direction = 0
        self._rainfall = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        """設置 UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 設置整體背景
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor('#1a1a1a'))
        self.setPalette(palette)
        
        # 第一行：賽事資訊
        row1 = QFrame()
        row1.setStyleSheet("background-color: #1a1a1a;")
        row1_layout = QHBoxLayout(row1)
        row1_layout.setContentsMargins(10, 8, 10, 4)
        row1_layout.setSpacing(15)
        
        # 賽事名稱
        self._race_label = QLabel("---: ---")
        self._race_label.setStyleSheet("color: #FFFFFF; font-weight: bold; font-size: 14px;")
        row1_layout.addWidget(self._race_label)
        
        # 分隔線
        row1_layout.addWidget(self._create_separator())
        
        # 比賽時間
        self._time_label = QLabel("0:00:00")
        self._time_label.setStyleSheet("color: #FFFFFF; font-size: 14px; font-family: 'Consolas', monospace;")
        row1_layout.addWidget(self._time_label)
        
        # 分隔線
        row1_layout.addWidget(self._create_separator())
        
        # 圈數
        self._lap_label = QLabel("Lap 0/0")
        self._lap_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        row1_layout.addWidget(self._lap_label)
        
        # 分隔線
        row1_layout.addWidget(self._create_separator())
        
        # Track Status (帶底色)
        self._status_label = QLabel("---")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setMinimumWidth(120)
        self._status_label.setStyleSheet("""
            background-color: #555555;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 3px;
        """)
        row1_layout.addWidget(self._status_label)
        
        row1_layout.addStretch()
        main_layout.addWidget(row1)
        
        # 第二行：天氣資訊
        row2 = QFrame()
        row2.setStyleSheet("background-color: #252525;")
        row2_layout = QHBoxLayout(row2)
        row2_layout.setContentsMargins(10, 4, 10, 8)
        row2_layout.setSpacing(20)
        
        # 空氣溫度
        self._air_temp_label = QLabel("Air --°C")
        self._air_temp_label.setStyleSheet("color: #88CCFF; font-size: 12px;")
        row2_layout.addWidget(self._air_temp_label)
        
        # 賽道溫度
        self._track_temp_label = QLabel("Track --°C")
        self._track_temp_label.setStyleSheet("color: #FFAA44; font-size: 12px;")
        row2_layout.addWidget(self._track_temp_label)
        
        # 濕度
        self._humidity_label = QLabel("Humidity --%")
        self._humidity_label.setStyleSheet("color: #88FF88; font-size: 12px;")
        row2_layout.addWidget(self._humidity_label)
        
        # 氣壓
        self._pressure_label = QLabel("Pressure --mb")
        self._pressure_label.setStyleSheet("color: #CCCCCC; font-size: 12px;")
        row2_layout.addWidget(self._pressure_label)
        
        # 風速風向
        self._wind_label = QLabel("Wind -- m/s")
        self._wind_label.setStyleSheet("color: #AAAAFF; font-size: 12px;")
        row2_layout.addWidget(self._wind_label)
        
        # 降雨狀態 (獨立顯示)
        self._rainfall_label = QLabel(tr("rainfall_dry", "Dry"))
        self._rainfall_label.setAlignment(Qt.AlignCenter)
        self._rainfall_label.setMinimumWidth(60)
        self._rainfall_label.setStyleSheet("""
            background-color: #228B22;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 3px;
        """)
        row2_layout.addWidget(self._rainfall_label)
        
        row2_layout.addStretch()
        main_layout.addWidget(row2)
        
        # 讓 Widget 自適應大小，不設固定高度
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    def _create_separator(self) -> QLabel:
        """創建分隔線"""
        sep = QLabel("|")
        sep.setStyleSheet("color: #555555; font-size: 14px;")
        return sep
    
    def _degree_to_direction(self, degree: float) -> str:
        """將角度轉換為風向文字"""
        degree = degree % 360
        for angle, direction in self.WIND_DIRECTIONS:
            if degree < angle + 11.25:
                return direction
        return 'N'
    
    def set_data_manager(self, data_manager):
        """設置數據管理器"""
        self._data_manager = data_manager
    
    def update_race_info(self, race_name: str, session_type: str, total_laps: int):
        """更新賽事基本資訊"""
        self._race_name = race_name
        self._session_type = session_type
        self._total_laps = total_laps
        
        display_name = f"{race_name}: {session_type}"
        self._race_label.setText(display_name)
        self._update_lap_display()
    
    def _update_lap_display(self):
        """更新圈數顯示"""
        if self._total_laps > 0:
            remaining = self._total_laps - self._current_lap
            self._lap_label.setText(f"Lap {self._current_lap}/{self._total_laps} ({remaining} left)")
        else:
            self._lap_label.setText(f"Lap {self._current_lap}")
    
    @pyqtSlot(dict)
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """從 snapshot 更新顯示"""
        if not snapshot:
            return
        
        # 更新比賽時間
        race_time = snapshot.get('race_time', '0:00:00')
        self._race_time = race_time
        self._time_label.setText(race_time)
        
        # 更新當前圈數
        current_lap = snapshot.get('current_lap', 0)
        if current_lap:
            self._current_lap = current_lap
            self._update_lap_display()
        
        # 從 data_manager 獲取 track status
        if self._data_manager:
            track_status = self._data_manager.get_track_status_at_time(race_time)
            self.update_track_status(track_status)
            
            # 獲取天氣數據
            weather = self._data_manager.get_weather_at_time(race_time)
            self.update_weather(weather)
    
    def update_track_status(self, status: str):
        """更新賽道狀態"""
        self._track_status = status
        
        status_info = self.TRACK_STATUS_MAP.get(status)
        if status_info:
            text, bg_color, text_color = status_info
            self._status_label.setText(text)
            self._status_label.setStyleSheet(f"""
                background-color: {bg_color};
                color: {text_color};
                font-weight: bold;
                font-size: 12px;
                padding: 3px 10px;
                border-radius: 3px;
            """)
        else:
            # 未知狀態
            self._status_label.setText(f"Status {status}")
            self._status_label.setStyleSheet("""
                background-color: #555555;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                padding: 3px 10px;
                border-radius: 3px;
            """)
    
    def update_weather(self, weather: Dict[str, Any]):
        """更新天氣數據"""
        if not weather:
            return
        
        # 空氣溫度
        if 'AirTemp' in weather:
            self._air_temp = weather['AirTemp']
            self._air_temp_label.setText(f"Air {self._air_temp:.1f}°C")
        
        # 賽道溫度
        if 'TrackTemp' in weather:
            self._track_temp = weather['TrackTemp']
            self._track_temp_label.setText(f"Track {self._track_temp:.1f}°C")
        
        # 濕度
        if 'Humidity' in weather:
            self._humidity = weather['Humidity']
            self._humidity_label.setText(f"Humidity {self._humidity:.0f}%")
        
        # 氣壓
        if 'Pressure' in weather:
            self._pressure = weather['Pressure']
            self._pressure_label.setText(f"Pressure {self._pressure:.0f}mb")
        
        # 風速風向
        if 'WindSpeed' in weather:
            self._wind_speed = weather['WindSpeed']
        if 'WindDirection' in weather:
            self._wind_direction = weather['WindDirection']
        
        direction_str = self._degree_to_direction(self._wind_direction)
        self._wind_label.setText(f"Wind {self._wind_speed:.1f}m/s {direction_str}")
        
        # 降雨狀態 - 獨立顯示
        if 'Rainfall' in weather:
            self._rainfall = weather['Rainfall']
            if self._rainfall:
                # 下雨狀態
                self._rainfall_label.setText(tr("rainfall_wet", "Wet"))
                self._rainfall_label.setStyleSheet("""
                    background-color: #1E90FF;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 2px 8px;
                    border-radius: 3px;
                """)
            else:
                # 乾燥狀態
                self._rainfall_label.setText(tr("rainfall_dry", "Dry"))
                self._rainfall_label.setStyleSheet("""
                    background-color: #228B22;
                    color: #FFFFFF;
                    font-weight: bold;
                    font-size: 11px;
                    padding: 2px 8px;
                    border-radius: 3px;
                """)
    
    def clear(self):
        """清除所有顯示"""
        self._race_label.setText("---: ---")
        self._time_label.setText("0:00:00")
        self._lap_label.setText("Lap 0/0")
        self._status_label.setText("---")
        self._status_label.setStyleSheet("""
            background-color: #555555;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 3px;
        """)
        self._air_temp_label.setText("Air --°C")
        self._track_temp_label.setText("Track --°C")
        self._humidity_label.setText("Humidity --%")
        self._pressure_label.setText("Pressure --mb")
        self._wind_label.setText("Wind -- m/s")
        self._rainfall_label.setText(tr("rainfall_dry", "Dry"))
        self._rainfall_label.setStyleSheet("""
            background-color: #228B22;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 3px;
        """)


class TrackWeatherMDI(BaseLiveTimingMDI):
    """
    Track & Weather MDI 視窗
    
    繼承 BaseLiveTimingMDI 以自動訂閱 DataManager 信號。
    
    性能優化: 每 60 秒更新一次 (天氣變化極慢)
    """
    
    _window_title_key = "track_weather"
    _default_title = "Track & Weather"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr(self._window_title_key, self._default_title))
        self.setMinimumSize(500, 60)
        self.resize(700, 70)
        
        # 性能優化: 追蹤上次更新的賽事時間
        self._last_update_time: float = 0.0
        self._update_interval: float = 60.0  # 60 秒
        
        logger.info("[TRACK_WEATHER_MDI] initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self._widget = TrackWeatherWidget(self._data_manager, self)
        self._main_layout.addWidget(self._widget)
        
        # 如果已經載入賽事，初始化顯示
        if self._data_manager.is_race_loaded():
            race_info = self._data_manager.get_race_info()
            if race_info:
                self._on_race_loaded(race_info)
                snapshot = self._data_manager.get_current_snapshot()
                if snapshot:
                    self._on_snapshot_updated(snapshot)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入"""
        race_name = race_info.get('race', race_info.get('race_name', 'Unknown'))
        session_type = race_info.get('session', 'Race')
        total_laps = race_info.get('total_laps', 0)
        self._widget.update_race_info(race_name, session_type, total_laps)
        logger.info("[TRACK_WEATHER_MDI] Race loaded: %s %s", race_name, session_type)
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        self._widget.clear()
        logger.info("[TRACK_WEATHER_MDI] Race unloaded")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新
        
        性能優化: 每 60 秒更新一次
        """
        current_time = snapshot.get('race_time_seconds', 0)
        
        # 性能優化: 檢查是否達到更新間隔
        if current_time - self._last_update_time < self._update_interval and self._last_update_time > 0:
            return
        
        self._last_update_time = current_time
        self._widget.update_from_snapshot(snapshot)
