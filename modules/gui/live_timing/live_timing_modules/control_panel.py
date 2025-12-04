"""
Live Timing 控制面板
=====================

播放控制 MDI 子視窗，包含：
- 播放/暫停/停止按鈕
- 進度條/時間軸
- 速度控制
- 賽事選擇

Author: F1T Team
Date: 2025-12-03
"""

import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QSlider, QComboBox, QGroupBox,
    QProgressBar, QSpinBox, QRadioButton, QButtonGroup,
    QSizePolicy, QFrame
)
from PyQt5.QtGui import QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from ..core.data_manager import LiveTimingDataManager
from core.gui_i18n import tr


class LiveTimingControlPanel(BaseLiveTimingMDI):
    """
    Live Timing 控制面板 MDI 子視窗
    
    功能：
    - 選擇賽事（年份/賽事/會話）
    - 播放控制（播放/暫停/停止）
    - 時間軸滑桿
    - 速度控制（1x/2x/4x/8x/16x）
    - 顯示當前時間和進度
    """
    
    # 信號
    race_selection_changed = pyqtSignal(int, str, str)  # year, race, session
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        # 設置視窗屬性
        self.setWindowTitle(tr("Live Timing Control Panel"))
        self.setMinimumSize(600, 180)
        self.resize(700, 200)
        
        # 內部狀態
        self._is_playing = False
        self._slider_dragging = False
        
        print("[CONTROL_PANEL] LiveTimingControlPanel initialized")
    
    def _setup_ui(self):
        """設置 UI 組件"""
        # 主佈局
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)
        
        # === 第一行：賽事選擇 ===
        race_frame = QFrame()
        race_frame.setFrameShape(QFrame.StyledPanel)
        race_layout = QHBoxLayout(race_frame)
        race_layout.setContentsMargins(8, 4, 8, 4)
        
        race_layout.addWidget(QLabel(tr("Year") + ":"))
        self.spin_year = QSpinBox()
        self.spin_year.setRange(2018, 2030)
        self.spin_year.setValue(2025)
        self.spin_year.setFixedWidth(70)
        race_layout.addWidget(self.spin_year)
        
        race_layout.addWidget(QLabel(tr("Race") + ":"))
        self.cmb_race = QComboBox()
        self.cmb_race.setMinimumWidth(150)
        self._populate_races()
        race_layout.addWidget(self.cmb_race)
        
        race_layout.addWidget(QLabel(tr("Session") + ":"))
        self.cmb_session = QComboBox()
        self.cmb_session.addItems(["Race", "Qualifying", "Sprint", "FP1", "FP2", "FP3"])
        self.cmb_session.setFixedWidth(100)
        race_layout.addWidget(self.cmb_session)
        
        self.btn_load = QPushButton(tr("Load Race"))
        self.btn_load.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_load.clicked.connect(self._on_load_clicked)
        race_layout.addWidget(self.btn_load)
        
        race_layout.addStretch()
        main_layout.addWidget(race_frame)
        
        # === 第二行：時間軸 ===
        timeline_frame = QFrame()
        timeline_frame.setFrameShape(QFrame.StyledPanel)
        timeline_layout = QHBoxLayout(timeline_frame)
        timeline_layout.setContentsMargins(8, 4, 8, 4)
        
        # 當前時間顯示
        self.lbl_current_time = QLabel("00:00:00")
        time_font = QFont()
        time_font.setPointSize(11)
        time_font.setBold(True)
        self.lbl_current_time.setFont(time_font)
        self.lbl_current_time.setMinimumWidth(80)
        timeline_layout.addWidget(self.lbl_current_time)
        
        # 時間軸滑桿
        self.slider_timeline = QSlider(Qt.Horizontal)
        self.slider_timeline.setMinimum(0)
        self.slider_timeline.setMaximum(1000)
        self.slider_timeline.setValue(0)
        self.slider_timeline.sliderPressed.connect(self._on_slider_pressed)
        self.slider_timeline.sliderReleased.connect(self._on_slider_released)
        self.slider_timeline.sliderMoved.connect(self._on_slider_moved)
        timeline_layout.addWidget(self.slider_timeline, stretch=1)
        
        # 總時間/進度顯示
        self.lbl_total_time = QLabel("/ 00:00:00")
        self.lbl_total_time.setFont(time_font)
        self.lbl_total_time.setMinimumWidth(100)
        timeline_layout.addWidget(self.lbl_total_time)
        
        main_layout.addWidget(timeline_frame)
        
        # === 第三行：播放控制 ===
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(8, 4, 8, 4)
        
        # 停止按鈕
        self.btn_stop = QPushButton("⏹")
        self.btn_stop.setToolTip(tr("Stop"))
        self.btn_stop.setFixedSize(40, 32)
        self.btn_stop.setStyleSheet("font-size: 16px;")
        self.btn_stop.clicked.connect(self._on_stop_clicked)
        control_layout.addWidget(self.btn_stop)
        
        # 播放/暫停按鈕
        self.btn_play_pause = QPushButton("▶")
        self.btn_play_pause.setToolTip(tr("Play"))
        self.btn_play_pause.setFixedSize(50, 32)
        self.btn_play_pause.setStyleSheet(
            "font-size: 18px; background-color: #2196F3; color: white;"
        )
        self.btn_play_pause.clicked.connect(self._on_play_pause_clicked)
        control_layout.addWidget(self.btn_play_pause)
        
        control_layout.addSpacing(20)
        
        # 速度控制
        control_layout.addWidget(QLabel(tr("Speed") + ":"))
        self.cmb_speed = QComboBox()
        self.cmb_speed.addItems(["0.5x", "1x", "2x", "4x", "8x", "16x", "32x", "64x", "128x"])
        self.cmb_speed.setCurrentText("1x")
        self.cmb_speed.setFixedWidth(70)
        self.cmb_speed.currentTextChanged.connect(self._on_speed_changed)
        control_layout.addWidget(self.cmb_speed)
        
        control_layout.addSpacing(20)
        
        # 狀態顯示
        self.lbl_status = QLabel(tr("Ready"))
        self.lbl_status.setStyleSheet("color: #888;")
        control_layout.addWidget(self.lbl_status)
        
        control_layout.addStretch()
        
        # 快照計數
        self.lbl_snapshot_count = QLabel("0 / 0")
        control_layout.addWidget(self.lbl_snapshot_count)
        
        main_layout.addWidget(control_frame)
        
        # 設置主佈局
        self._main_layout.addLayout(main_layout)
        
        # 初始狀態：禁用播放控制
        self._set_controls_enabled(False)
    
    def _populate_races(self):
        """填充賽事列表"""
        # 掃描本地 JSON 目錄
        project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
        livef1_dir = project_root / "json" / "LiveF1"
        
        races = []
        if livef1_dir.exists():
            year_dirs = [d for d in livef1_dir.iterdir() if d.is_dir()]
            for year_dir in year_dirs:
                for race_dir in year_dir.iterdir():
                    if race_dir.is_dir():
                        races.append(race_dir.name)
        
        # 去重並排序
        races = sorted(set(races))
        
        if races:
            self.cmb_race.addItems(races)
        else:
            self.cmb_race.addItems(["Japanese_Race", "Australian_Race", "Chinese_Race"])
    
    def _set_controls_enabled(self, enabled: bool):
        """設置播放控制可用狀態"""
        self.btn_play_pause.setEnabled(enabled)
        self.btn_stop.setEnabled(enabled)
        self.slider_timeline.setEnabled(enabled)
        self.cmb_speed.setEnabled(enabled)
    
    # ===========================================
    # 事件處理
    # ===========================================
    def _on_load_clicked(self):
        """載入賽事"""
        year = self.spin_year.value()
        race = self.cmb_race.currentText()
        session = self.cmb_session.currentText()
        
        if not race:
            self._show_warning(tr("Warning"), tr("Please select a race"))
            return
        
        self.lbl_status.setText(tr("Loading..."))
        self.lbl_status.setStyleSheet("color: #FF9800;")
        self.btn_load.setEnabled(False)
        
        # 調用 DataManager 載入賽事
        dm = self.get_data_manager()
        
        # 轉換 session 名稱
        session_map = {
            "Race": "Race",
            "Qualifying": "Qualifying",
            "Sprint": "Sprint",
            "FP1": "Practice 1",
            "FP2": "Practice 2",
            "FP3": "Practice 3",
        }
        session_name = session_map.get(session, session)
        
        success = dm.load_race(year, race, session_name, source_type="local")
        
        self.btn_load.setEnabled(True)
        
        if success:
            self.lbl_status.setText(tr("Loaded"))
            self.lbl_status.setStyleSheet("color: #4CAF50;")
            self._set_controls_enabled(True)
            
            # 發送信號
            self.race_selection_changed.emit(year, race, session)
        else:
            self.lbl_status.setText(tr("Load Failed"))
            self.lbl_status.setStyleSheet("color: #F44336;")
            self._set_controls_enabled(False)
    
    def _on_play_pause_clicked(self):
        """播放/暫停切換"""
        dm = self.get_data_manager()
        
        if dm.get_playback_state() == 'playing':
            dm.pause()
        else:
            dm.play()
    
    def _on_stop_clicked(self):
        """停止播放"""
        dm = self.get_data_manager()
        dm.stop()
    
    def _on_speed_changed(self, speed_text: str):
        """速度變更"""
        speed = float(speed_text.replace('x', ''))
        dm = self.get_data_manager()
        dm.set_speed(speed)
    
    def _on_slider_pressed(self):
        """滑桿按下"""
        self._slider_dragging = True
    
    def _on_slider_released(self):
        """滑桿釋放"""
        self._slider_dragging = False
        
        # 跳轉到指定位置
        progress = self.slider_timeline.value() / 1000.0
        dm = self.get_data_manager()
        dm.seek_by_progress(progress)
    
    def _on_slider_moved(self, value: int):
        """滑桿拖動"""
        if self._slider_dragging:
            # 預覽時間
            progress = value / 1000.0
            dm = self.get_data_manager()
            race_info = dm.get_race_info()
            
            if race_info:
                duration = race_info.get('duration_seconds', 0)
                preview_time = duration * progress
                self.lbl_current_time.setText(self._format_time(preview_time))
    
    # ===========================================
    # DataManager 信號處理
    # ===========================================
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """賽事載入完成"""
        print(f"[CONTROL_PANEL] Race loaded: {race_info}")
        
        total_snapshots = race_info.get('total_snapshots', 0)
        duration = race_info.get('duration_seconds', 0)
        
        self.lbl_total_time.setText(f"/ {self._format_time(duration)}")
        self.lbl_snapshot_count.setText(f"0 / {total_snapshots}")
        self.slider_timeline.setMaximum(1000)
        self.slider_timeline.setValue(0)
        
        self._set_controls_enabled(True)
    
    def _on_race_unloaded(self):
        """賽事卸載"""
        print("[CONTROL_PANEL] Race unloaded")
        
        self.lbl_current_time.setText("00:00:00")
        self.lbl_total_time.setText("/ 00:00:00")
        self.lbl_snapshot_count.setText("0 / 0")
        self.slider_timeline.setValue(0)
        
        self._set_controls_enabled(False)
        self._update_play_button('stopped')
    
    def _on_playback_state_changed(self, state: str):
        """播放狀態改變"""
        print(f"[CONTROL_PANEL] Playback state: {state}")
        self._update_play_button(state)
        
        if state == 'playing':
            self.lbl_status.setText(tr("Playing"))
            self.lbl_status.setStyleSheet("color: #4CAF50;")
        elif state == 'paused':
            self.lbl_status.setText(tr("Paused"))
            self.lbl_status.setStyleSheet("color: #FF9800;")
        else:
            self.lbl_status.setText(tr("Stopped"))
            self.lbl_status.setStyleSheet("color: #888;")
    
    def _on_time_changed(self, time_seconds: float):
        """時間改變"""
        self.lbl_current_time.setText(self._format_time(time_seconds))
    
    def _on_progress_changed(self, progress: float):
        """進度改變"""
        if not self._slider_dragging:
            self.slider_timeline.setValue(int(progress * 1000))
        
        # 更新快照計數
        dm = self.get_data_manager()
        current_idx = dm.get_current_index()
        total = dm.get_total_snapshots()
        self.lbl_snapshot_count.setText(f"{current_idx} / {total}")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """快照更新"""
        # 控制面板不需要處理快照內容
        pass
    
    # ===========================================
    # 工具方法
    # ===========================================
    def _update_play_button(self, state: str):
        """更新播放按鈕狀態"""
        if state == 'playing':
            self.btn_play_pause.setText("⏸")
            self.btn_play_pause.setToolTip(tr("Pause"))
            self.btn_play_pause.setStyleSheet(
                "font-size: 18px; background-color: #FF9800; color: white;"
            )
        else:
            self.btn_play_pause.setText("▶")
            self.btn_play_pause.setToolTip(tr("Play"))
            self.btn_play_pause.setStyleSheet(
                "font-size: 18px; background-color: #2196F3; color: white;"
            )
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """格式化時間"""
        if seconds is None or seconds < 0:
            return "00:00:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
