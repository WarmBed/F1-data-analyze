"""
Live Timing 控制面板 Dock Widget
=================================

固定在主視窗頂部的控制面板，參照 demo_live_position_tracking.py 設計。
包含：
- 模式選擇（即時 / 歷史回放）
- 即時模式：連接控制、連接狀態
- 歷史模式：賽事選擇、載入按鈕
- 時間軸控制（歷史模式）：播放/暫停、速度、進度條

賽事選擇邏輯與主視窗一致，使用 SeasonCalendarProvider。

Author: F1T Team
Date: 2025-12-03
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, TYPE_CHECKING

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider, QComboBox, QSpinBox,
    QRadioButton, QButtonGroup, QFrame, QSizePolicy,
    QProgressBar
)
from PyQt5.QtGui import QFont

from ..core.data_manager import LiveTimingDataManager
from core.gui_i18n import tr

# 導入賽季日曆相關
try:
    from modules.gui.shared.season_calendar_provider import (
        SeasonCalendarError,
        SeasonCalendarProvider,
        SeasonEvent,
    )
    SEASON_CALENDAR_AVAILABLE = True
except ImportError:
    SEASON_CALENDAR_AVAILABLE = False
    print("[CONTROL_DOCK] SeasonCalendarProvider not available, using fallback")


class RaceLoaderThread(QThread):
    """
    背景載入賽事數據的執行緒
    
    避免載入大量 JSON 檔案時阻塞 GUI。
    報告真實的載入進度。
    """
    
    # 信號
    load_started = pyqtSignal()
    load_progress = pyqtSignal(int, str)  # (進度百分比, 狀態訊息)
    load_finished = pyqtSignal(bool, str)  # (成功與否, 訊息)
    
    def __init__(self, data_manager, year: int, race_key: str, session_name: str, parent=None):
        super().__init__(parent)
        self._data_manager = data_manager
        self._year = year
        self._race_key = race_key
        self._session_name = session_name
    
    def run(self):
        """執行背景載入"""
        try:
            self.load_started.emit()
            
            # 進度回調 - 從 DataManager 接收真實進度
            def progress_callback(percent, message):
                self.load_progress.emit(percent, message)
            
            # 調用 DataManager 載入（帶進度回調）
            success = self._data_manager.load_race(
                self._year, 
                self._race_key, 
                self._session_name, 
                source_type="local",
                progress_callback=progress_callback
            )
            
            if success:
                self.load_finished.emit(True, tr("Race data loaded successfully", "Race data loaded successfully"))
            else:
                self.load_finished.emit(False, tr("Failed to load race data", "Failed to load race data"))
                
        except Exception as e:
            print(f"[RACE_LOADER] Error: {e}")
            import traceback
            traceback.print_exc()
            self.load_finished.emit(False, str(e))

class LiveTimingControlDock(QDockWidget):
    """
    Live Timing 控制面板 Dock Widget
    
    固定在主視窗頂部，控制所有 Live Timing 模組的數據源。
    
    信號:
    - mode_changed(str): 模式變更 ('realtime' / 'historical')
    - race_loaded(dict): 賽事載入完成
    """
    
    # 模式常數
    MODE_REALTIME = "realtime"
    MODE_HISTORICAL = "historical"
    
    # 信號
    mode_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(tr("Live Timing Control", "Live Timing Control"), parent)
        
        # 保存主視窗引用
        self._main_window = parent
        
        # 設置 Dock 屬性
        self.setObjectName("LiveTimingControlDock")
        self.setAllowedAreas(Qt.TopDockWidgetArea | Qt.BottomDockWidgetArea)
        self.setFeatures(
            QDockWidget.DockWidgetClosable |
            QDockWidget.DockWidgetMovable
        )
        
        # 內部狀態
        self._mode = self.MODE_HISTORICAL  # 預設歷史模式（因為即時需要額外設置）
        self._is_playing = False
        self._slider_dragging = False
        
        # 賽季日曆相關
        self._season_provider = None
        self._season_events_cache: Dict[int, List[Any]] = {}
        self._race_event_lookup: Dict[str, Any] = {}
        self._display_to_race_key: Dict[str, str] = {}
        
        if SEASON_CALENDAR_AVAILABLE:
            self._season_provider = SeasonCalendarProvider()
        
        # 獲取 DataManager
        self._data_manager = LiveTimingDataManager.instance()
        
        # 創建 UI
        self._setup_ui()
        
        # 連接 DataManager 信號
        self._connect_data_manager_signals()
        
        # 初始化狀態
        self._update_mode_ui()
        
        # 初始化賽事列表（與主視窗同步）
        self._initialize_race_combo()
        
        print("[CONTROL_DOCK] LiveTimingControlDock initialized")
    
    def _setup_ui(self):
        """設置 UI"""
        # 主容器
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)
        
        # === 第一行：模式選擇 + 控制按鈕 ===
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(8)
        
        # 模式選擇
        row1_layout.addWidget(QLabel(tr("Mode", "Mode") + ":"))
        
        self.btn_group_mode = QButtonGroup(self)
        
        self.radio_realtime = QRadioButton(tr("Realtime Live Timing", "Realtime"))
        self.radio_realtime.toggled.connect(self._on_mode_changed)
        self.btn_group_mode.addButton(self.radio_realtime)
        row1_layout.addWidget(self.radio_realtime)
        
        self.radio_historical = QRadioButton(tr("Historical Playback", "Historical"))
        self.radio_historical.setChecked(True)  # 預設歷史模式
        self.btn_group_mode.addButton(self.radio_historical)
        row1_layout.addWidget(self.radio_historical)
        
        # 分隔線
        row1_layout.addWidget(self._create_separator())
        
        # === 即時模式控制區 ===
        self.realtime_widget = QWidget()
        realtime_layout = QHBoxLayout(self.realtime_widget)
        realtime_layout.setContentsMargins(0, 0, 0, 0)
        realtime_layout.setSpacing(6)
        
        self.btn_connect = QPushButton(tr("Connect Live Timing", "Connect"))
        self.btn_connect.setStyleSheet("font-weight: bold; padding: 4px 12px;")
        self.btn_connect.clicked.connect(self._on_connect_clicked)
        realtime_layout.addWidget(self.btn_connect)
        
        self.btn_disconnect = QPushButton(tr("Disconnect", "Disconnect"))
        self.btn_disconnect.setStyleSheet("padding: 4px 8px;")
        self.btn_disconnect.setEnabled(False)
        self.btn_disconnect.clicked.connect(self._on_disconnect_clicked)
        realtime_layout.addWidget(self.btn_disconnect)
        
        self.lbl_connection_status = QLabel(tr("Disconnected", "Disconnected"))
        self.lbl_connection_status.setStyleSheet("color: #888888; font-weight: bold;")
        realtime_layout.addWidget(self.lbl_connection_status)
        
        self.realtime_widget.hide()  # 預設隱藏
        row1_layout.addWidget(self.realtime_widget)
        
        # === 歷史模式控制區 ===
        self.historical_widget = QWidget()
        historical_layout = QHBoxLayout(self.historical_widget)
        historical_layout.setContentsMargins(0, 0, 0, 0)
        historical_layout.setSpacing(6)
        
        # 年份選擇
        historical_layout.addWidget(QLabel(tr("Year", "Year") + ":"))
        self.cmb_year = QComboBox()
        self.cmb_year.setMinimumWidth(70)
        # 年份列表將在 _initialize_race_combo() 中填充
        self.cmb_year.addItems([str(y) for y in range(2025, 2019, -1)])
        self.cmb_year.currentTextChanged.connect(self._on_year_changed)
        historical_layout.addWidget(self.cmb_year)
        
        # 賽事選擇
        historical_layout.addWidget(QLabel(tr("Race", "Race") + ":"))
        self.cmb_race = QComboBox()
        self.cmb_race.setMinimumWidth(250)  # 加寬以容納完整賽事名稱
        # 賽事列表將在 _initialize_race_combo() 中填充
        self.cmb_race.currentIndexChanged.connect(self._on_race_changed)
        historical_layout.addWidget(self.cmb_race)
        
        # 會話選擇
        historical_layout.addWidget(QLabel(tr("Session", "Session") + ":"))
        self.cmb_session = QComboBox()
        self.cmb_session.addItems(["Race", "Qualifying", "Sprint", "FP1", "FP2", "FP3"])
        self.cmb_session.setMinimumWidth(90)
        historical_layout.addWidget(self.cmb_session)
        
        # 載入按鈕
        self.btn_load = QPushButton(tr("Load Race", "Load"))
        self.btn_load.setStyleSheet("font-weight: bold; padding: 4px 12px;")
        self.btn_load.clicked.connect(self._on_load_clicked)
        historical_layout.addWidget(self.btn_load)
        
        # 狀態標籤
        self.lbl_race_status = QLabel(tr("Please select a race", "Select race"))
        self.lbl_race_status.setStyleSheet("color: #888888;")
        historical_layout.addWidget(self.lbl_race_status)
        
        # 載入進度條（初始隱藏）
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFixedWidth(150)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.hide()
        historical_layout.addWidget(self.progress_bar)
        
        row1_layout.addWidget(self.historical_widget)
        
        row1_layout.addStretch()
        main_layout.addLayout(row1_layout)
        
        # === 第二行：時間軸控制（僅歷史模式） ===
        self.timeline_widget = QWidget()
        timeline_layout = QHBoxLayout(self.timeline_widget)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(8)
        
        # 時間顯示
        self.lbl_time = QLabel("00:00:00")
        time_font = QFont()
        time_font.setPointSize(10)
        time_font.setBold(True)
        self.lbl_time.setFont(time_font)
        self.lbl_time.setMinimumWidth(70)
        timeline_layout.addWidget(self.lbl_time)
        
        # 停止按鈕
        self.btn_stop = QPushButton("\u23f9")  # ⏹
        self.btn_stop.setToolTip(tr("Stop", "Stop"))
        self.btn_stop.setFixedSize(32, 28)
        self.btn_stop.setStyleSheet("font-size: 14px;")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        self.btn_stop.setEnabled(False)
        timeline_layout.addWidget(self.btn_stop)
        
        # 播放/暫停按鈕
        self.btn_play_pause = QPushButton("\u25b6")  # ▶
        self.btn_play_pause.setToolTip(tr("Play", "Play"))
        self.btn_play_pause.setFixedSize(40, 28)
        self.btn_play_pause.setStyleSheet("font-size: 16px;")
        self.btn_play_pause.clicked.connect(self._on_play_pause_clicked)
        self.btn_play_pause.setEnabled(False)
        timeline_layout.addWidget(self.btn_play_pause)
        
        # 速度選擇
        timeline_layout.addWidget(QLabel(tr("Speed", "Speed") + ":"))
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["0.5x", "1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x"])
        self.cmb_speed.setCurrentText("1x")
        self.cmb_speed.setFixedWidth(70)
        self.cmb_speed.currentTextChanged.connect(self._on_speed_changed)
        self.cmb_speed.setEnabled(False)
        timeline_layout.addWidget(self.cmb_speed)
        
        # 時間軸滑桿
        self.slider_timeline = QSlider(Qt.Horizontal)
        self.slider_timeline.setMinimum(0)
        self.slider_timeline.setMaximum(1000)
        self.slider_timeline.setValue(0)
        self.slider_timeline.sliderPressed.connect(self._on_slider_pressed)
        self.slider_timeline.sliderReleased.connect(self._on_slider_released)
        self.slider_timeline.sliderMoved.connect(self._on_slider_moved)
        self.slider_timeline.setEnabled(False)
        timeline_layout.addWidget(self.slider_timeline, stretch=1)
        
        # 進度顯示
        self.lbl_progress = QLabel("0 / 0")
        self.lbl_progress.setMinimumWidth(80)
        timeline_layout.addWidget(self.lbl_progress)
        
        # 總時間
        self.lbl_total_time = QLabel("/ 00:00:00")
        self.lbl_total_time.setMinimumWidth(80)
        timeline_layout.addWidget(self.lbl_total_time)
        
        self.timeline_widget.hide()  # 預設隱藏
        main_layout.addWidget(self.timeline_widget)
        
        # 設置到 Dock
        self.setWidget(container)
    
    def _create_separator(self) -> QFrame:
        """創建垂直分隔線"""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setFrameShadow(QFrame.Sunken)
        sep.setStyleSheet("color: #555555;")
        return sep
    
    def _populate_races(self):
        """填充賽事列表"""
        self.cmb_race.clear()
        year = self.cmb_year.currentText()
        
        if year in self._available_races:
            races = self._available_races[year]
            self.cmb_race.addItems(races)
        else:
            # 預設賽事列表
            self.cmb_race.addItems([
                "Japanese_Race", "Australian_Race", "Chinese_Race",
                "Bahrain_Race", "Saudi_Arabian_Race"
            ])
    
    def _connect_data_manager_signals(self):
        """連接 DataManager 信號"""
        dm = self._data_manager
        dm.race_loaded.connect(self._on_race_loaded)
        dm.race_unloaded.connect(self._on_race_unloaded)
        dm.playback_state_changed.connect(self._on_playback_state_changed)
        dm.time_changed.connect(self._on_time_changed)
        dm.progress_changed.connect(self._on_progress_changed)
    
    # ===========================================
    # 模式切換
    # ===========================================
    def _on_mode_changed(self, checked: bool):
        """模式切換"""
        if self.radio_realtime.isChecked():
            self._mode = self.MODE_REALTIME
        else:
            self._mode = self.MODE_HISTORICAL
        
        self._update_mode_ui()
        self.mode_changed.emit(self._mode)
        print(f"[CONTROL_DOCK] Mode changed to: {self._mode}")
    
    def _update_mode_ui(self):
        """更新模式 UI"""
        is_realtime = (self._mode == self.MODE_REALTIME)
        
        self.realtime_widget.setVisible(is_realtime)
        self.historical_widget.setVisible(not is_realtime)
        self.timeline_widget.setVisible(not is_realtime)
    
    # ===========================================
    # 即時模式控制
    # ===========================================
    def _on_connect_clicked(self):
        """連接即時 Live Timing"""
        print("[CONTROL_DOCK] Connect clicked - realtime mode not yet implemented")
        self.lbl_connection_status.setText(tr("Connecting...", "Connecting..."))
        self.lbl_connection_status.setStyleSheet("color: #FF9800; font-weight: bold;")
        # TODO: 實現即時連接
    
    def _on_disconnect_clicked(self):
        """斷開連接"""
        print("[CONTROL_DOCK] Disconnect clicked")
        self.lbl_connection_status.setText(tr("Disconnected", "Disconnected"))
        self.lbl_connection_status.setStyleSheet("color: #888888; font-weight: bold;")
    
    # ===========================================
    # 歷史模式控制
    # ===========================================
    def _on_year_changed(self, year: str):
        """年份變更 - 重新載入賽事列表"""
        if year:
            self._refresh_race_combo_for_year(int(year))
    
    def _on_race_changed(self, index: int):
        """賽事選擇變更 - 更新會話列表"""
        self._update_session_combo()
    
    def _on_load_clicked(self):
        """載入賽事（使用背景執行緒）"""
        year = int(self.cmb_year.currentText())
        race_key = self.get_selected_race_key()
        session_code = self.get_selected_session_code()
        
        if not race_key:
            self.lbl_race_status.setText(tr("Please select a race", "Select race"))
            self.lbl_race_status.setStyleSheet("color: #F44336;")
            return
        
        # 轉換會話代碼為完整名稱（Live Timing 使用完整名稱）
        session_map = {
            "R": "Race",
            "Q": "Qualifying",
            "S": "Sprint",
            "SQ": "Sprint Qualifying",
            "FP1": "Practice 1",
            "FP2": "Practice 2",
            "FP3": "Practice 3",
        }
        session_name = session_map.get(session_code, session_code)
        
        print(f"[CONTROL_DOCK] Loading: {year} / {race_key} / {session_name}")
        
        # 禁用載入按鈕，顯示進度條
        self.btn_load.setEnabled(False)
        self.lbl_race_status.setText(tr("Loading...", "Loading..."))
        self.lbl_race_status.setStyleSheet("color: #FF9800;")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # 使用背景執行緒載入
        self._loader_thread = RaceLoaderThread(
            self._data_manager, year, race_key, session_name, self
        )
        self._loader_thread.load_progress.connect(self._on_load_progress)
        self._loader_thread.load_finished.connect(self._on_load_finished)
        self._loader_thread.start()
    
    @pyqtSlot(int, str)
    def _on_load_progress(self, progress: int, message: str):
        """載入進度更新"""
        self.progress_bar.setValue(progress)
        self.lbl_race_status.setText(message)
    
    @pyqtSlot(bool, str)
    def _on_load_finished(self, success: bool, message: str):
        """載入完成"""
        self.btn_load.setEnabled(True)
        self.progress_bar.hide()
        
        if success:
            self.lbl_race_status.setText(tr("Loaded", "Loaded"))
            self.lbl_race_status.setStyleSheet("color: #4CAF50; font-weight: bold;")
        else:
            self.lbl_race_status.setText(tr("Load Failed", "Failed"))
            self.lbl_race_status.setStyleSheet("color: #F44336;")
        
        # 清理執行緒引用
        if hasattr(self, '_loader_thread'):
            self._loader_thread = None
    
    # ===========================================
    # 播放控制
    # ===========================================
    def _on_play_pause_clicked(self):
        """播放/暫停切換"""
        dm = self._data_manager
        
        if dm.get_playback_state() == 'playing':
            dm.pause()
        else:
            dm.play()
    
    def _on_stop_clicked(self):
        """停止"""
        self._data_manager.stop()
    
    def _on_speed_changed(self, speed_text: str):
        """速度變更"""
        speed = float(speed_text.replace('x', ''))
        self._data_manager.set_speed(speed)
    
    def _on_slider_pressed(self):
        """滑桿按下"""
        self._slider_dragging = True
    
    def _on_slider_released(self):
        """滑桿釋放"""
        self._slider_dragging = False
        progress = self.slider_timeline.value() / 1000.0
        self._data_manager.seek_by_progress(progress)
    
    def _on_slider_moved(self, value: int):
        """滑桿移動（預覽時間）"""
        if self._slider_dragging:
            progress = value / 1000.0
            race_info = self._data_manager.get_race_info()
            if race_info:
                duration = race_info.get('duration_seconds', 0)
                preview_time = duration * progress
                self.lbl_time.setText(self._format_time(preview_time))
    
    # ===========================================
    # DataManager 信號處理
    # ===========================================
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成"""
        print(f"[CONTROL_DOCK] Race loaded: {race_info.get('race_name', 'Unknown')}")
        
        total_snapshots = race_info.get('total_snapshots', 0)
        duration = race_info.get('duration_seconds', 0)
        
        self.lbl_total_time.setText(f"/ {self._format_time(duration)}")
        self.lbl_progress.setText(f"0 / {total_snapshots}")
        self.slider_timeline.setValue(0)
        
        # 啟用播放控制
        self._set_playback_controls_enabled(True)
        
        # 顯示時間軸
        if self._mode == self.MODE_HISTORICAL:
            self.timeline_widget.show()
    
    def _on_race_unloaded(self):
        """賽事卸載"""
        print("[CONTROL_DOCK] Race unloaded")
        
        self.lbl_time.setText("00:00:00")
        self.lbl_total_time.setText("/ 00:00:00")
        self.lbl_progress.setText("0 / 0")
        self.slider_timeline.setValue(0)
        
        self._set_playback_controls_enabled(False)
        self._update_play_button('stopped')
    
    def _on_playback_state_changed(self, state: str):
        """播放狀態變更"""
        print(f"[CONTROL_DOCK] Playback state: {state}")
        self._update_play_button(state)
    
    def _on_time_changed(self, time_seconds: float):
        """時間變更"""
        self.lbl_time.setText(self._format_time(time_seconds))
    
    def _on_progress_changed(self, progress: float):
        """進度變更"""
        if not self._slider_dragging:
            self.slider_timeline.setValue(int(progress * 1000))
        
        # 更新快照計數
        current_idx = self._data_manager.get_current_index()
        total = self._data_manager.get_total_snapshots()
        self.lbl_progress.setText(f"{current_idx} / {total}")
    
    # ===========================================
    # 工具方法
    # ===========================================
    def _set_playback_controls_enabled(self, enabled: bool):
        """設置播放控制可用狀態"""
        self.btn_play_pause.setEnabled(enabled)
        self.btn_stop.setEnabled(enabled)
        self.slider_timeline.setEnabled(enabled)
        self.cmb_speed.setEnabled(enabled)
    
    def _update_play_button(self, state: str):
        """更新播放按鈕狀態"""
        if state == 'playing':
            self.btn_play_pause.setText("\u23f8")  # ⏸
            self.btn_play_pause.setToolTip(tr("Pause", "Pause"))
        else:
            self.btn_play_pause.setText("\u25b6")  # ▶
            self.btn_play_pause.setToolTip(tr("Play", "Play"))
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化時間"""
        if seconds is None or seconds < 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    # ===========================================
    # 公開方法
    # ===========================================
    def get_data_manager(self) -> LiveTimingDataManager:
        """獲取 DataManager"""
        return self._data_manager
    
    def get_current_mode(self) -> str:
        """獲取當前模式"""
        return self._mode
    
    # ===========================================
    # 賽季日曆方法（與主視窗一致）
    # ===========================================
    def _initialize_race_combo(self):
        """初始化賽事選擇器 - 與主視窗同步"""
        # 嘗試從主視窗獲取當前年份
        initial_year = 2025
        if self._main_window and hasattr(self._main_window, 'year_combo'):
            try:
                initial_year = int(self._main_window.year_combo.currentText())
            except (ValueError, AttributeError):
                pass
        
        # 設置年份
        self.cmb_year.blockSignals(True)
        index = self.cmb_year.findText(str(initial_year))
        if index >= 0:
            self.cmb_year.setCurrentIndex(index)
        self.cmb_year.blockSignals(False)
        
        # 載入賽事列表
        self._refresh_race_combo_for_year(initial_year)
        
        print(f"[CONTROL_DOCK] Initialized race combo for year {initial_year}")
    
    def _get_calendar_events(self, year: int) -> List[Any]:
        """獲取指定年份的賽事列表（優先使用主視窗快取）"""
        # 優先從主視窗獲取（確保與主視窗一致）
        if self._main_window and hasattr(self._main_window, '_get_calendar_events'):
            return self._main_window._get_calendar_events(year)
        
        # 自行獲取
        if year in self._season_events_cache and self._season_events_cache[year]:
            return self._season_events_cache[year]
        
        if not SEASON_CALENDAR_AVAILABLE or not self._season_provider:
            return []
        
        try:
            events = self._season_provider.get_completed_events(year)
            if events:
                self._season_events_cache[year] = events
            return events
        except Exception as e:
            print(f"[CONTROL_DOCK] Failed to get calendar events: {e}")
            return self._season_events_cache.get(year, [])
    
    def _refresh_race_combo_for_year(self, year: int):
        """刷新賽事選擇器 - 與主視窗邏輯一致"""
        events = self._get_calendar_events(year)
        
        self.cmb_race.blockSignals(True)
        self.cmb_race.clear()
        self._race_event_lookup.clear()
        self._display_to_race_key.clear()
        
        if events and SEASON_CALENDAR_AVAILABLE:
            # 分離已完成和即將舉行的賽事
            completed_events = [e for e in events if e.is_completed]
            upcoming_events = [e for e in events if not e.is_completed]
            
            def add_event_to_combo(event) -> None:
                label = self._format_race_display(event)
                self._race_event_lookup[event.race_key] = event
                self._display_to_race_key[label] = event.race_key
                self._display_to_race_key[event.display_label] = event.race_key
                self.cmb_race.addItem(label, event)
            
            # 添加已完成賽事
            for event in completed_events:
                add_event_to_combo(event)
            
            # 添加分隔線
            if completed_events and upcoming_events:
                self.cmb_race.insertSeparator(self.cmb_race.count())
            
            # 添加即將舉行賽事
            for event in upcoming_events:
                add_event_to_combo(event)
            
            # 選擇最近的已完成賽事
            if completed_events:
                preferred_event = completed_events[-1]
                index = self.cmb_race.findData(preferred_event)
                if index >= 0:
                    self.cmb_race.setCurrentIndex(index)
            elif self.cmb_race.count() > 0:
                self.cmb_race.setCurrentIndex(0)
        else:
            # 回退：使用靜態列表
            placeholder = tr("No completed races", "[No races]")
            self.cmb_race.addItem(placeholder, None)
        
        self.cmb_race.blockSignals(False)
        
        # 更新會話選擇器
        self._update_session_combo()
        
        print(f"[CONTROL_DOCK] Refreshed race combo: {self.cmb_race.count()} items")
    
    def _format_race_display(self, event) -> str:
        """格式化賽事顯示名稱（與主視窗一致）"""
        # 優先使用主視窗的格式化方法
        if self._main_window and hasattr(self._main_window, '_format_race_display'):
            return self._main_window._format_race_display(event)
        
        # 自行格式化
        if SEASON_CALENDAR_AVAILABLE and hasattr(event, 'display_label'):
            date_str = ""
            if hasattr(event, 'date') and event.date:
                date_str = event.date.strftime("%Y.%m.%d")
            
            if date_str:
                return f"{event.display_label} ({date_str})"
            return event.display_label
        
        return str(event)
    
    def _update_session_combo(self):
        """更新會話選擇器 - 根據選中的賽事"""
        self.cmb_session.blockSignals(True)
        self.cmb_session.clear()
        
        # 獲取當前選中的賽事
        event = self.cmb_race.currentData()
        
        if SEASON_CALENDAR_AVAILABLE and hasattr(event, 'sessions') and event.sessions:
            # 從賽事獲取可用會話
            for session in event.sessions:
                self.cmb_session.addItem(session.code, session)
            
            # 預設選擇 R (Race)
            index = self.cmb_session.findText("R")
            if index >= 0:
                self.cmb_session.setCurrentIndex(index)
            elif self.cmb_session.count() > 0:
                self.cmb_session.setCurrentIndex(0)
        else:
            # 回退：使用靜態列表
            for code in ["R", "Q", "S", "SQ", "FP3", "FP2", "FP1"]:
                self.cmb_session.addItem(code)
            self.cmb_session.setCurrentIndex(0)
        
        self.cmb_session.blockSignals(False)
    
    def get_selected_race_key(self) -> Optional[str]:
        """獲取當前選中的賽事 key"""
        event = self.cmb_race.currentData()
        if SEASON_CALENDAR_AVAILABLE and hasattr(event, 'race_key'):
            return event.race_key
        return self.cmb_race.currentText()
    
    def get_selected_session_code(self) -> str:
        """獲取當前選中的會話代碼"""
        session = self.cmb_session.currentData()
        if SEASON_CALENDAR_AVAILABLE and hasattr(session, 'code'):
            return session.code
        return self.cmb_session.currentText()
