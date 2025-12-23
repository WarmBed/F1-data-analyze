# -*- coding: utf-8 -*-
"""
DriverLapSettingsHelper - 車手與圈數設定輔助類別

從 WindowSettingsDialog 提取的車手與圈數控制邏輯。
支援跨賽事比較功能。

Phase 5.4.1: WindowSettingsDialog 拆分
"""

import logging
from typing import TYPE_CHECKING, Optional, Dict, Any

from PyQt5.QtWidgets import (
    QGroupBox, QVBoxLayout, QGridLayout, QWidget,
    QCheckBox, QComboBox, QLineEdit, QLabel, QFrame
)
from PyQt5.QtGui import QIntValidator

from core.gui_i18n import tr
from core.logger import get_logger
from typing import Dict
from typing import Optional
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QGridLayout
from typing import Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QDialog

logger = logging.getLogger(__name__)


class DriverLapSettingsHelper:
    """
    車手與圈數設定輔助類別
    
    處理遙測模組的車手/圈數/年份/賽事/賽段控制。
    支援跨賽事比較功能。
    """
    
    def __init__(self, dialog: 'QDialog', parent_window, main_window):
        """
        初始化車手與圈數設定輔助類別
        
        Args:
            dialog: 父對話框 (WindowSettingsDialog)
            parent_window: 父視窗 (PopoutSubWindow)
            main_window: 主視窗 (StyleHMainWindow)
        """
        self.dialog = dialog
        self.parent_window = parent_window
        self.main_window = main_window
        
        # 控制項引用（由 setup_controls 設置）
        self.sync_driver_lap_checkbox: Optional[QCheckBox] = None
        self.use_time_axis_checkbox: Optional[QCheckBox] = None
        
        # 車手 1 控制項
        self.driver1_year_combo: Optional[QComboBox] = None
        self.driver1_race_combo: Optional[QComboBox] = None
        self.driver1_session_combo: Optional[QComboBox] = None
        self.driver1_combo: Optional[QComboBox] = None
        self.lap1_input: Optional[QLineEdit] = None
        self.fastest_lap1_checkbox: Optional[QCheckBox] = None
        
        # 車手 2 控制項
        self.driver2_year_combo: Optional[QComboBox] = None
        self.driver2_race_combo: Optional[QComboBox] = None
        self.driver2_session_combo: Optional[QComboBox] = None
        self.driver2_combo: Optional[QComboBox] = None
        self.lap2_input: Optional[QLineEdit] = None
        self.fastest_lap2_checkbox: Optional[QCheckBox] = None
    
    def setup_controls(self, parent_layout: QVBoxLayout) -> None:
        """
        設置車手與圈數控制（僅遙測模組） - 支援跨賽事比較
        
        Args:
            parent_layout: 父佈局
        """
        try:
            # 車手與圈數同步控制分組
            driver_lap_group = QGroupBox(tr("driver_lap_sync_control", "Driver & Lap Sync Control"))
            driver_lap_group.setObjectName("SettingsGroup")
            driver_lap_layout = QVBoxLayout(driver_lap_group)
            
            # 同步控制勾選框
            self.sync_driver_lap_checkbox = QCheckBox(
                tr("sync_driver_lap_checkbox", "[LINK] Sync Driver & Lap with Main Window")
            )
            self.sync_driver_lap_checkbox.setObjectName("SyncDriverLapCheckbox")
            
            # 從分析模組讀取同步狀態（如果存在）
            if hasattr(self.parent_window, 'analysis_module'):
                analysis_module = self.parent_window.analysis_module
                current_sync_state = getattr(analysis_module, 'sync_driver_lap_enabled', True)
                self.sync_driver_lap_checkbox.setChecked(current_sync_state)
                logger.info(f"[DRIVER_LAP_HELPER] Loaded sync state from module: {current_sync_state}")
            else:
                self.sync_driver_lap_checkbox.setChecked(True)  # 預設啟用同步
            
            self.sync_driver_lap_checkbox.setToolTip(
                tr("sync_driver_lap_tooltip", "When checked, driver & lap controlled by main window")
            )
            self.sync_driver_lap_checkbox.toggled.connect(self._on_sync_toggled)
            driver_lap_layout.addWidget(self.sync_driver_lap_checkbox)
            
            # 車手與圈數控制區域
            controls_widget = QWidget()
            controls_layout = QGridLayout(controls_widget)
            controls_layout.setContentsMargins(10, 10, 10, 10)
            controls_layout.setSpacing(6)
            
            # === 車手 1 控制 ===
            self._setup_driver1_controls(controls_layout)
            
            # === 分隔線 ===
            row = 3
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            controls_layout.addWidget(separator, row, 0, 1, 6)
            
            # === 車手 2 控制 ===
            self._setup_driver2_controls(controls_layout)
            
            driver_lap_layout.addWidget(controls_widget)
            
            # === 時間軸控制 ===
            self._setup_time_axis_control(driver_lap_layout)
            
            parent_layout.addWidget(driver_lap_group)
            
            # 從父視窗的分析模組獲取當前車手和圈數
            self._load_current_settings()
            
            # 初始化控制項的可編輯性
            self._update_controls_editability()
            
            logger.debug(f"[OK] [DRIVER_LAP_HELPER] Controls setup complete (cross-event support)")
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Setup failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _setup_driver1_controls(self, layout: QGridLayout) -> None:
        """設置車手 1 控制項"""
        row = 0
        layout.addWidget(QLabel(tr("driver1_section", "Driver 1:")), row, 0, 1, 5)
        
        row += 1
        # 年份
        layout.addWidget(QLabel(tr("year_label", "Year:")), row, 0)
        self.driver1_year_combo = QComboBox()
        self.driver1_year_combo.setObjectName("YearComboBox")
        self.driver1_year_combo.addItems([str(y) for y in range(2020, 2027)])
        self.driver1_year_combo.setMinimumWidth(70)
        self.driver1_year_combo.currentTextChanged.connect(self._on_driver1_year_changed)
        layout.addWidget(self.driver1_year_combo, row, 1)
        
        # 賽事
        layout.addWidget(QLabel(tr("race_label", "Race:")), row, 2)
        self.driver1_race_combo = QComboBox()
        self.driver1_race_combo.setObjectName("RaceComboBox")
        self.driver1_race_combo.setMinimumWidth(120)
        self.driver1_race_combo.currentIndexChanged.connect(self._on_driver1_race_changed)
        layout.addWidget(self.driver1_race_combo, row, 3)
        
        # 賽段
        layout.addWidget(QLabel(tr("session_label", "Session:")), row, 4)
        self.driver1_session_combo = QComboBox()
        self.driver1_session_combo.setObjectName("SessionComboBox")
        self.driver1_session_combo.setMinimumWidth(50)
        layout.addWidget(self.driver1_session_combo, row, 5)
        
        row += 1
        # 車手
        layout.addWidget(QLabel(tr("driver_label", "Driver:")), row, 0)
        self.driver1_combo = QComboBox()
        self.driver1_combo.setObjectName("DriverComboBox")
        self.driver1_combo.setMinimumWidth(80)
        self._populate_driver_combo(self.driver1_combo)
        layout.addWidget(self.driver1_combo, row, 1)
        
        # 圈數
        layout.addWidget(QLabel(tr("lap_label", "Lap:")), row, 2)
        self.lap1_input = QLineEdit()
        self.lap1_input.setObjectName("LapInput")
        self.lap1_input.setText("1")
        self.lap1_input.setMaximumWidth(50)
        self.lap1_input.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.lap1_input, row, 3)
        
        # 最速圈
        self.fastest_lap1_checkbox = QCheckBox(tr("fastest_lap_label", "Fastest Lap"))
        self.fastest_lap1_checkbox.setObjectName("FastestLapCheckbox")
        self.fastest_lap1_checkbox.stateChanged.connect(lambda state: self._on_fastest_lap_changed(state, 1))
        layout.addWidget(self.fastest_lap1_checkbox, row, 4, 1, 2)
    
    def _setup_driver2_controls(self, layout: QGridLayout) -> None:
        """設置車手 2 控制項"""
        row = 4
        layout.addWidget(QLabel(tr("driver2_section", "Driver 2:")), row, 0, 1, 5)
        
        row += 1
        # 年份
        layout.addWidget(QLabel(tr("year_label", "Year:")), row, 0)
        self.driver2_year_combo = QComboBox()
        self.driver2_year_combo.setObjectName("YearComboBox")
        self.driver2_year_combo.addItems([str(y) for y in range(2020, 2027)])
        self.driver2_year_combo.setMinimumWidth(70)
        self.driver2_year_combo.currentTextChanged.connect(self._on_driver2_year_changed)
        layout.addWidget(self.driver2_year_combo, row, 1)
        
        # 賽事（自動同步車手 1，灰色不可編輯）
        layout.addWidget(QLabel(tr("race_label", "Race:")), row, 2)
        self.driver2_race_combo = QComboBox()
        self.driver2_race_combo.setObjectName("RaceComboBox")
        self.driver2_race_combo.setMinimumWidth(120)
        self.driver2_race_combo.setEnabled(False)  # 強制灰色
        layout.addWidget(self.driver2_race_combo, row, 3)
        
        # 賽段
        layout.addWidget(QLabel(tr("session_label", "Session:")), row, 4)
        self.driver2_session_combo = QComboBox()
        self.driver2_session_combo.setObjectName("SessionComboBox")
        self.driver2_session_combo.setMinimumWidth(50)
        layout.addWidget(self.driver2_session_combo, row, 5)
        
        row += 1
        # 車手
        layout.addWidget(QLabel(tr("driver_label", "Driver:")), row, 0)
        self.driver2_combo = QComboBox()
        self.driver2_combo.setObjectName("DriverComboBox")
        self.driver2_combo.setMinimumWidth(80)
        self._populate_driver_combo(self.driver2_combo)
        layout.addWidget(self.driver2_combo, row, 1)
        
        # 圈數
        layout.addWidget(QLabel(tr("lap_label", "Lap:")), row, 2)
        self.lap2_input = QLineEdit()
        self.lap2_input.setObjectName("LapInput")
        self.lap2_input.setText("1")
        self.lap2_input.setMaximumWidth(50)
        self.lap2_input.setValidator(QIntValidator(1, 999))
        layout.addWidget(self.lap2_input, row, 3)
        
        # 最速圈
        self.fastest_lap2_checkbox = QCheckBox(tr("fastest_lap_label", "Fastest Lap"))
        self.fastest_lap2_checkbox.setObjectName("FastestLapCheckbox")
        self.fastest_lap2_checkbox.stateChanged.connect(lambda state: self._on_fastest_lap_changed(state, 2))
        layout.addWidget(self.fastest_lap2_checkbox, row, 4, 1, 2)
    
    def _setup_time_axis_control(self, layout: QVBoxLayout) -> None:
        """設置時間軸控制"""
        self.use_time_axis_checkbox = QCheckBox(tr("use_time_axis_checkbox", "Use Time Axis"))
        self.use_time_axis_checkbox.setObjectName("UseTimeAxisCheckbox")
        
        # 從主視窗或分析模組載入時間軸狀態（加入 try-except 保護）
        try:
            if hasattr(self.main_window, 'use_time_axis_checkbox') and self.main_window.use_time_axis_checkbox:
                current_time_axis_state = self.main_window.use_time_axis_checkbox.isChecked()
                self.use_time_axis_checkbox.setChecked(current_time_axis_state)
                logger.debug(f"[DRIVER_LAP_HELPER] Loaded time axis state from main: {current_time_axis_state}")
            elif hasattr(self.parent_window, 'analysis_module'):
                analysis_module = self.parent_window.analysis_module
                current_time_axis_state = getattr(analysis_module, 'use_time_axis', False)
                self.use_time_axis_checkbox.setChecked(current_time_axis_state)
                logger.debug(f"[DRIVER_LAP_HELPER] Loaded time axis state from module: {current_time_axis_state}")
            else:
                self.use_time_axis_checkbox.setChecked(False)
        except (AttributeError, RuntimeError) as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Load time axis state failed: {e}")
            self.use_time_axis_checkbox.setChecked(False)
        
        self.use_time_axis_checkbox.setToolTip(
            tr("use_time_axis_tooltip", "Toggle horizontal axis between time (sec) and distance (m)")
        )
        layout.addWidget(self.use_time_axis_checkbox)
    
    def _populate_driver_combo(self, combo: QComboBox) -> None:
        """填充車手下拉選單"""
        try:
            # 從主視窗獲取車手列表（加入 try-except 保護）
            try:
                if hasattr(self.main_window, 'driver1_combo') and self.main_window.driver1_combo:
                    # 複製主視窗的車手列表
                    for i in range(self.main_window.driver1_combo.count()):
                        driver_text = self.main_window.driver1_combo.itemText(i)
                        driver_data = self.main_window.driver1_combo.itemData(i)
                        combo.addItem(driver_text, driver_data)
                else:
                    # 預設車手列表
                    default_drivers = ["VER", "LEC", "HAM", "PER", "SAI", "RUS", "NOR", "PIA", "ALO", "STR"]
                    combo.addItems(default_drivers)
            except (AttributeError, RuntimeError) as e:
                logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Get drivers from main failed: {e}")
                # 預設車手列表
                default_drivers = ["VER", "LEC", "HAM", "PER", "SAI", "RUS", "NOR", "PIA", "ALO", "STR"]
                combo.addItems(default_drivers)
                
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Populate driver combo failed: {e}")
            # 使用最小預設列表
            combo.addItems(["VER", "LEC", "HAM"])
    
    def _load_current_settings(self) -> None:
        """從分析模組載入當前的車手和圈數設定"""
        try:
            # 判斷是否勾選同步
            sync_enabled = self.sync_driver_lap_checkbox.isChecked() if self.sync_driver_lap_checkbox else True
            
            # 決定資料來源：同步時從主視窗，否則從分析模組
            if sync_enabled:
                try:
                    # 從主視窗載入（加入 try-except 保護）
                    source_year = str(self.main_window.year_combo.currentText()) if hasattr(self.main_window, 'year_combo') else "2024"
                    source_race = self.main_window.race_combo.currentText() if hasattr(self.main_window, 'race_combo') else ""
                    source_session = self.main_window.session_combo.currentText() if hasattr(self.main_window, 'session_combo') else "R"
                    source_driver1 = self.main_window.driver1_combo.currentText() if hasattr(self.main_window, 'driver1_combo') else "VER"
                    source_driver2 = self.main_window.driver2_combo.currentText() if hasattr(self.main_window, 'driver2_combo') else "NOR"
                    
                    # 同步模式：兩個車手使用相同的 Year/Race/Session
                    year1, race1, session1 = source_year, source_race, source_session
                    year2, race2, session2 = source_year, source_race, source_session
                    lap1, lap2 = 1, 1  # 預設值
                    
                except AttributeError as e:
                    logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Cannot load from main: {e}")
                    # 使用預設值
                    year1 = year2 = "2024"
                    race1 = race2 = ""
                    session1 = session2 = "R"
                    source_driver1, source_driver2 = "VER", "NOR"
                    lap1, lap2 = 1, 1
            else:
                # 從分析模組載入（如果存在）
                if not hasattr(self.parent_window, 'analysis_module'):
                    year1 = year2 = "2024"
                    race1 = race2 = ""
                    session1 = session2 = "R"
                    source_driver1, source_driver2 = "VER", "NOR"
                    lap1, lap2 = 1, 1
                else:
                    analysis_module = self.parent_window.analysis_module
                    
                    # 從分析模組載入車手 1 的參數
                    year1 = str(getattr(analysis_module, 'driver1_year', getattr(analysis_module, 'current_year', '2025')))
                    race1 = getattr(analysis_module, 'driver1_race', getattr(analysis_module, 'current_race', ''))
                    session1 = getattr(analysis_module, 'driver1_session', getattr(analysis_module, 'current_session', 'R'))
                    source_driver1 = getattr(analysis_module, 'driver1', 'VER')
                    lap1 = getattr(analysis_module, 'lap1', 1)
                    
                    # 從分析模組載入車手 2 的參數
                    year2 = str(getattr(analysis_module, 'driver2_year', year1))
                    race2 = getattr(analysis_module, 'driver2_race', race1)
                    session2 = getattr(analysis_module, 'driver2_session', session1)
                    source_driver2 = getattr(analysis_module, 'driver2', 'NOR')
                    lap2 = getattr(analysis_module, 'lap2', 1)
            
            # === 填充車手 1 的年份/賽事/賽段 ===
            if self.driver1_year_combo:
                self.driver1_year_combo.setCurrentText(year1)
            self._populate_race_combo_for_driver(1, year1, race1)
            self._populate_session_combo_for_driver(1, race1, session1)
            
            # === 填充車手 2 的年份/賽事/賽段 ===
            if self.driver2_year_combo:
                self.driver2_year_combo.setCurrentText(year2)
            # 賽事強制同步車手 1（灰色）
            self._populate_race_combo_for_driver(2, year2, race2)
            self._populate_session_combo_for_driver(2, race2, session2)
            
            # === 載入車手設定 ===
            if self.driver1_combo:
                index = self.driver1_combo.findText(source_driver1)
                if index >= 0:
                    self.driver1_combo.setCurrentIndex(index)
            
            if self.driver2_combo:
                index = self.driver2_combo.findText(source_driver2)
                if index >= 0:
                    self.driver2_combo.setCurrentIndex(index)
            
            # === 載入圈數設定 ===
            if lap1 == 99:
                if self.fastest_lap1_checkbox:
                    self.fastest_lap1_checkbox.setChecked(True)
                if self.lap1_input:
                    self.lap1_input.setText("99")
            else:
                if self.lap1_input:
                    self.lap1_input.setText(str(lap1))
            
            if lap2 == 99:
                if self.fastest_lap2_checkbox:
                    self.fastest_lap2_checkbox.setChecked(True)
                if self.lap2_input:
                    self.lap2_input.setText("99")
            else:
                if self.lap2_input:
                    self.lap2_input.setText(str(lap2))
            
            logger.debug(f"[DRIVER_LAP_HELPER] Settings loaded:")
            logger.debug(f"  Driver 1: {year1} {race1} {session1} {source_driver1} Lap{lap1}")
            logger.debug(f"  Driver 2: {year2} {race2} {session2} {source_driver2} Lap{lap2}")
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Load settings failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_race_combo_for_driver(self, driver_num: int, year: str, current_race: str = "") -> None:
        """為指定車手填充賽事下拉選單"""
        try:
            combo = self.driver1_race_combo if driver_num == 1 else self.driver2_race_combo
            if combo is None:
                return
                
            combo.blockSignals(True)
            combo.clear()
            
            # 獲取該年份的賽事列表（使用與主視窗相同的邏輯）
            year_int = int(year)
            events = []
            
            if hasattr(self.main_window, '_get_calendar_events'):
                events = self.main_window._get_calendar_events(year_int)
            elif hasattr(self.main_window, '_season_provider'):
                try:
                    events = self.main_window._season_provider.get_completed_events(year_int)
                except Exception as exc:
                    logger.debug(f"[DRIVER_LAP_HELPER] Get events failed: {exc}")
            
            if events:
                for event in events:
                    if event.is_completed:  # 只顯示已完成的賽事
                        display_name = event.race_key  # 使用賽事名稱（如 "Brazil"）
                        combo.addItem(display_name, event)
            else:
                # 無賽事時使用預設列表
                combo.addItems(["Brazil", "Japan", "Singapore", "Monaco", "Bahrain"])
            
            # 設定當前賽事
            if current_race:
                index = combo.findText(current_race)
                if index >= 0:
                    combo.setCurrentIndex(index)
                elif combo.count() > 0:
                    combo.setCurrentIndex(0)
            elif combo.count() > 0:
                combo.setCurrentIndex(0)
            
            combo.blockSignals(False)
            logger.debug(f"[DRIVER_LAP_HELPER] Driver {driver_num} race combo populated: {combo.count()} events")
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Populate race combo for driver {driver_num} failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_session_combo_for_driver(self, driver_num: int, race: str, current_session: str = "R") -> None:
        """為指定車手填充賽段下拉選單"""
        try:
            combo = self.driver1_session_combo if driver_num == 1 else self.driver2_session_combo
            if combo is None:
                return
                
            combo.blockSignals(True)
            combo.clear()
            
            # 預設 Session 列表
            default_sessions = ["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"]
            combo.addItems(default_sessions)
            
            # 設定當前賽段
            if current_session:
                index = combo.findText(current_session)
                if index >= 0:
                    combo.setCurrentIndex(index)
                else:
                    # 預設選擇 R（正賽）
                    index = combo.findText("R")
                    if index >= 0:
                        combo.setCurrentIndex(index)
            
            combo.blockSignals(False)
            logger.debug(f"[DRIVER_LAP_HELPER] Driver {driver_num} session combo populated")
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Populate session combo for driver {driver_num} failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_driver1_year_changed(self, year: str) -> None:
        """處理車手 1 年份變更 → 動態更新賽事列表"""
        try:
            logger.debug(f"[DRIVER_LAP_HELPER] Driver 1 year changed: {year} -> reload race list")
            
            # 保留當前選擇的賽事（如果存在）
            current_race = self.driver1_race_combo.currentText() if self.driver1_race_combo else ""
            
            # 重新填充車手 1 的賽事列表
            self._populate_race_combo_for_driver(1, year, current_race)
            
            # 同步更新車手 2 的賽事列表（因為賽事必須同步）
            year2 = self.driver2_year_combo.currentText() if self.driver2_year_combo else year
            self._populate_race_combo_for_driver(2, year2, current_race)
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Driver 1 year change handler failed: {e}")
    
    def _on_driver2_year_changed(self, year: str) -> None:
        """處理車手 2 年份變更 → 動態更新賽事列表"""
        try:
            logger.debug(f"[DRIVER_LAP_HELPER] Driver 2 year changed: {year} -> reload race list")
            
            # 保留當前選擇的賽事（必須與車手 1 同步）
            current_race = self.driver1_race_combo.currentText() if self.driver1_race_combo else ""
            
            # 重新填充車手 2 的賽事列表（賽事與車手 1 同步）
            self._populate_race_combo_for_driver(2, year, current_race)
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Driver 2 year change handler failed: {e}")
    
    def _on_driver1_race_changed(self, index: int) -> None:
        """處理車手 1 賽事變更 → 自動同步車手 2 賽事"""
        try:
            if index < 0:
                return
            selected_race = self.driver1_race_combo.currentText() if self.driver1_race_combo else ""
            logger.debug(f"[DRIVER_LAP_HELPER] Driver 1 race changed: {selected_race} -> sync driver 2")
            
            # 強制同步車手 2 賽事（防止選錯賽道）
            if self.driver2_race_combo:
                self.driver2_race_combo.blockSignals(True)
                self.driver2_race_combo.setCurrentText(selected_race)
                self.driver2_race_combo.blockSignals(False)
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Driver 1 race change handler failed: {e}")
    
    def _on_sync_toggled(self, checked: bool) -> None:
        """處理車手與圈數同步勾選框變更"""
        logger.info(f"[SYNC_TOGGLED] Driver lap sync: {'enabled' if checked else 'disabled'}")
        
        # 步驟 1: 同步更新標題欄按鈕狀態
        if hasattr(self.parent_window, 'title_bar'):
            if hasattr(self.parent_window.title_bar, 'driver_lap_sync_btn'):
                # 阻止信號避免遞迴
                self.parent_window.title_bar.driver_lap_sync_btn.blockSignals(True)
                self.parent_window.title_bar.driver_lap_sync_btn.setChecked(checked)
                # 手動更新按鈕外觀
                if checked:
                    self.parent_window.title_bar.driver_lap_sync_btn.setText("D")
                else:
                    self.parent_window.title_bar.driver_lap_sync_btn.setText("X")
                self.parent_window.title_bar.driver_lap_sync_btn.blockSignals(False)
        
        # 步驟 2: 更新分析模組的同步狀態
        if hasattr(self.parent_window, 'analysis_module'):
            analysis_module = self.parent_window.analysis_module
            if hasattr(analysis_module, 'sync_driver_lap_enabled'):
                analysis_module.sync_driver_lap_enabled = checked
        
        # 步驟 3: 更新控制項的可編輯性
        self._update_controls_editability()
        
        # 步驟 4: 如果停用同步，載入全域參數池的值
        if not checked:
            self._load_shared_params_to_ui()
    
    def _load_shared_params_to_ui(self) -> None:
        """從全域參數池載入參數到 UI 控制項"""
        try:
            # 驗證物件存在
            if not hasattr(self.main_window, 'shared_independent_params'):
                logger.debug(f"[LOAD_SHARED] Main window has no shared_independent_params")
                return
            
            try:
                shared_params = self.main_window.shared_independent_params
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"[LOAD_SHARED] Cannot access shared_independent_params: {e}")
                return
            
            if not isinstance(shared_params, dict):
                logger.debug(f"[LOAD_SHARED] shared_independent_params is not dict: {type(shared_params)}")
                return
            
            # 檢查是否為空（所有值都是 None）
            if all(v is None for k, v in shared_params.items() if k != 'use_time_axis'):
                logger.debug(f"[LOAD_SHARED] Shared params pool is empty, skip loading")
                return
            
            # 載入車手 1 參數
            year1 = shared_params.get('year1')
            race1 = shared_params.get('race1')
            session1 = shared_params.get('session1')
            driver1 = shared_params.get('driver1')
            lap1 = shared_params.get('lap1')
            
            # 載入車手 2 參數
            year2 = shared_params.get('year2')
            race2 = shared_params.get('race2')
            session2 = shared_params.get('session2')
            driver2 = shared_params.get('driver2')
            lap2 = shared_params.get('lap2')
            
            # 載入時間軸參數
            use_time_axis = shared_params.get('use_time_axis', False)
            
            # === 更新車手 1 UI ===
            if year1 and self.driver1_year_combo:
                self.driver1_year_combo.setCurrentText(str(year1))
            
            if race1:
                self._populate_race_combo_for_driver(1, str(year1) if year1 else "2025", race1)
            
            if session1:
                self._populate_session_combo_for_driver(1, race1 if race1 else "", session1)
            
            if driver1 and self.driver1_combo:
                index = self.driver1_combo.findText(driver1)
                if index >= 0:
                    self.driver1_combo.setCurrentIndex(index)
            
            if lap1 is not None and self.lap1_input:
                if lap1 == 99:
                    if self.fastest_lap1_checkbox:
                        self.fastest_lap1_checkbox.setChecked(True)
                    self.lap1_input.setText("99")
                else:
                    if self.fastest_lap1_checkbox:
                        self.fastest_lap1_checkbox.setChecked(False)
                    self.lap1_input.setText(str(lap1))
            
            # === 更新車手 2 UI ===
            if year2 and self.driver2_year_combo:
                self.driver2_year_combo.setCurrentText(str(year2))
            
            if race2:
                self._populate_race_combo_for_driver(2, str(year2) if year2 else "2025", race2)
            
            if session2:
                self._populate_session_combo_for_driver(2, race2 if race2 else "", session2)
            
            if driver2 and self.driver2_combo:
                index = self.driver2_combo.findText(driver2)
                if index >= 0:
                    self.driver2_combo.setCurrentIndex(index)
            
            if lap2 is not None and self.lap2_input:
                if lap2 == 99:
                    if self.fastest_lap2_checkbox:
                        self.fastest_lap2_checkbox.setChecked(True)
                    self.lap2_input.setText("99")
                else:
                    if self.fastest_lap2_checkbox:
                        self.fastest_lap2_checkbox.setChecked(False)
                    self.lap2_input.setText(str(lap2))
            
            # === 更新時間軸 checkbox ===
            if self.use_time_axis_checkbox:
                self.use_time_axis_checkbox.setChecked(use_time_axis)
            
            logger.debug(f"[LOAD_SHARED] Shared params loaded to UI")
            
        except Exception as e:
            logger.debug(f"[LOAD_SHARED] Load failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_controls_editability(self) -> None:
        """根據同步狀態更新車手與圈數控制項的可編輯性"""
        if not self.sync_driver_lap_checkbox:
            return
        
        is_sync_enabled = self.sync_driver_lap_checkbox.isChecked()
        
        # === 設置 Year/Race/Session 控制項的可編輯性 ===
        if self.driver1_year_combo:
            self.driver1_year_combo.setEnabled(not is_sync_enabled)
        if self.driver1_race_combo:
            self.driver1_race_combo.setEnabled(not is_sync_enabled)
        if self.driver1_session_combo:
            self.driver1_session_combo.setEnabled(not is_sync_enabled)
        
        if self.driver2_year_combo:
            self.driver2_year_combo.setEnabled(not is_sync_enabled)
        # 車手 2 的 Race **始終灰色**（強制與車手 1 同步）
        if self.driver2_race_combo:
            self.driver2_race_combo.setEnabled(False)
        if self.driver2_session_combo:
            self.driver2_session_combo.setEnabled(not is_sync_enabled)
        
        # === 設置車手與圈數控制項的可編輯性 ===
        if self.driver1_combo:
            self.driver1_combo.setEnabled(not is_sync_enabled)
        if self.driver2_combo:
            self.driver2_combo.setEnabled(not is_sync_enabled)
        
        fastest1_checked = self.fastest_lap1_checkbox.isChecked() if self.fastest_lap1_checkbox else False
        fastest2_checked = self.fastest_lap2_checkbox.isChecked() if self.fastest_lap2_checkbox else False
        
        if self.lap1_input:
            self.lap1_input.setEnabled(not is_sync_enabled and not fastest1_checked)
        if self.lap2_input:
            self.lap2_input.setEnabled(not is_sync_enabled and not fastest2_checked)
        if self.fastest_lap1_checkbox:
            self.fastest_lap1_checkbox.setEnabled(not is_sync_enabled)
        if self.fastest_lap2_checkbox:
            self.fastest_lap2_checkbox.setEnabled(not is_sync_enabled)
        
        # === 更新提示文字 ===
        if is_sync_enabled:
            tooltip = tr("sync_driver_lap_enabled_tooltip", "Sync enabled, params controlled by main window")
            for widget in [self.driver1_year_combo, self.driver1_race_combo, self.driver1_session_combo,
                          self.driver2_year_combo, self.driver2_session_combo,
                          self.driver1_combo, self.driver2_combo, self.lap1_input, self.lap2_input]:
                if widget:
                    widget.setToolTip(tooltip)
            if self.driver2_race_combo:
                self.driver2_race_combo.setToolTip(tr("race_sync_tooltip", "Race auto-syncs with Driver 1"))
            logger.debug(f"[LOCK] [DRIVER_LAP_HELPER] All controls locked (sync mode)")
        else:
            if self.driver1_year_combo:
                self.driver1_year_combo.setToolTip(tr("year1_tooltip", "Set Driver 1 year"))
            if self.driver1_race_combo:
                self.driver1_race_combo.setToolTip(tr("race1_tooltip", "Set Driver 1 race"))
            if self.driver1_session_combo:
                self.driver1_session_combo.setToolTip(tr("session1_tooltip", "Set Driver 1 session"))
            if self.driver2_year_combo:
                self.driver2_year_combo.setToolTip(tr("year2_tooltip", "Set Driver 2 year"))
            if self.driver2_race_combo:
                self.driver2_race_combo.setToolTip(tr("race_sync_tooltip", "Race auto-syncs with Driver 1"))
            if self.driver2_session_combo:
                self.driver2_session_combo.setToolTip(tr("session2_tooltip", "Set Driver 2 session"))
            if self.driver1_combo:
                self.driver1_combo.setToolTip(tr("driver1_tooltip", "Select Driver 1"))
            if self.driver2_combo:
                self.driver2_combo.setToolTip(tr("driver2_tooltip", "Select Driver 2"))
            if self.lap1_input:
                self.lap1_input.setToolTip(tr("lap1_tooltip", "Set Lap 1"))
            if self.lap2_input:
                self.lap2_input.setToolTip(tr("lap2_tooltip", "Set Lap 2"))
            logger.debug(f"[UNLOCK] [DRIVER_LAP_HELPER] All controls unlocked (manual mode)")
    
    def _on_fastest_lap_changed(self, state: int, driver_num: int) -> None:
        """處理最速圈勾選框變更"""
        is_checked = (state == 2)  # Qt.Checked
        
        if driver_num == 1:
            if self.lap1_input:
                if is_checked:
                    self.lap1_input.setText("99")
                    self.lap1_input.setEnabled(False)
                    self.lap1_input.setStyleSheet("color: #666666;")
                    logger.debug(f"[DRIVER_LAP_HELPER] Driver 1 fastest lap enabled (lap=99)")
                else:
                    self.lap1_input.setText("1")
                    sync_enabled = self.sync_driver_lap_checkbox.isChecked() if self.sync_driver_lap_checkbox else False
                    self.lap1_input.setEnabled(not sync_enabled)
                    self.lap1_input.setStyleSheet("")
                    logger.debug(f"[DRIVER_LAP_HELPER] Driver 1 fastest lap disabled")
        elif driver_num == 2:
            if self.lap2_input:
                if is_checked:
                    self.lap2_input.setText("99")
                    self.lap2_input.setEnabled(False)
                    self.lap2_input.setStyleSheet("color: #666666;")
                    logger.debug(f"[DRIVER_LAP_HELPER] Driver 2 fastest lap enabled (lap=99)")
                else:
                    self.lap2_input.setText("1")
                    sync_enabled = self.sync_driver_lap_checkbox.isChecked() if self.sync_driver_lap_checkbox else False
                    self.lap2_input.setEnabled(not sync_enabled)
                    self.lap2_input.setStyleSheet("")
                    logger.debug(f"[DRIVER_LAP_HELPER] Driver 2 fastest lap disabled")
    
    def get_settings(self) -> Dict[str, Any]:
        """獲取當前設定"""
        return {
            'sync_enabled': self.sync_driver_lap_checkbox.isChecked() if self.sync_driver_lap_checkbox else True,
            'use_time_axis': self.use_time_axis_checkbox.isChecked() if self.use_time_axis_checkbox else False,
            'year1': self.driver1_year_combo.currentText() if self.driver1_year_combo else "2025",
            'race1': self.driver1_race_combo.currentText() if self.driver1_race_combo else "",
            'session1': self.driver1_session_combo.currentText() if self.driver1_session_combo else "R",
            'driver1': self.driver1_combo.currentText() if self.driver1_combo else "VER",
            'lap1': int(self.lap1_input.text()) if self.lap1_input and self.lap1_input.text().isdigit() else 1,
            'year2': self.driver2_year_combo.currentText() if self.driver2_year_combo else "2025",
            'race2': self.driver2_race_combo.currentText() if self.driver2_race_combo else "",
            'session2': self.driver2_session_combo.currentText() if self.driver2_session_combo else "R",
            'driver2': self.driver2_combo.currentText() if self.driver2_combo else "NOR",
            'lap2': int(self.lap2_input.text()) if self.lap2_input and self.lap2_input.text().isdigit() else 1,
            'is_fastest_lap': (
                (self.fastest_lap1_checkbox.isChecked() if self.fastest_lap1_checkbox else False) or
                (self.fastest_lap2_checkbox.isChecked() if self.fastest_lap2_checkbox else False)
            )
        }
    
    def apply_settings(self) -> bool:
        """
        應用車手與圈數設定到分析模組（支援跨賽事比較）
        
        Returns:
            bool: 是否成功應用設定
        """
        settings = self.get_settings()
        
        logger.debug(f"\n{'='*80}")
        logger.debug(f"[APPLY_SETTINGS] Starting apply")
        logger.debug(f"[APPLY_SETTINGS] Settings: {settings}")
        logger.debug(f"{'='*80}\n")
        
        try:
            if not hasattr(self.parent_window, 'analysis_module'):
                logger.warning(f"[WARNING] [DRIVER_LAP_HELPER] Parent window has no analysis_module")
                return False
            
            analysis_module = self.parent_window.analysis_module
            
            # === 保存同步狀態到分析模組 ===
            analysis_module.sync_driver_lap_enabled = settings['sync_enabled']
            
            # === 保存時間軸設定到分析模組 ===
            analysis_module.use_time_axis = settings['use_time_axis']
            
            # === 保存所有參數到分析模組 ===
            analysis_module.driver1_year = settings['year1']
            analysis_module.driver1_race = settings['race1']
            analysis_module.driver1_session = settings['session1']
            analysis_module.driver1 = settings['driver1']
            analysis_module.lap1 = settings['lap1']
            
            analysis_module.driver2_year = settings['year2']
            analysis_module.driver2_race = settings['race2']
            analysis_module.driver2_session = settings['session2']
            analysis_module.driver2 = settings['driver2']
            analysis_module.lap2 = settings['lap2']
            
            # === 檢測是否為跨賽事比較 ===
            is_cross_event = (
                settings['year1'] != settings['year2'] or
                settings['session1'] != settings['session2']
            )
            
            if settings['sync_enabled']:
                # 同步模式強制為單賽事
                is_cross_event = False
                logger.debug(f"[APPLY_SETTINGS] Sync enabled, force single event mode")
            
            if is_cross_event:
                logger.debug(f"[CROSS-EVENT] Detected cross-event comparison")
                if hasattr(analysis_module, 'update_cross_event_comparison'):
                    success = analysis_module.update_cross_event_comparison(
                        year1=settings['year1'], race1=settings['race1'], session1=settings['session1'],
                        driver1=settings['driver1'], lap1=settings['lap1'],
                        year2=settings['year2'], race2=settings['race2'], session2=settings['session2'],
                        driver2=settings['driver2'], lap2=settings['lap2'],
                        is_fastest=settings['is_fastest_lap'],
                        use_time_axis=settings['use_time_axis']
                    )
                    return success
            else:
                # === 標準模式（同一賽事比較）===
                if hasattr(analysis_module, 'update_lap_parameters'):
                    success = analysis_module.update_lap_parameters(
                        year=settings['year1'],
                        race=settings['race1'],
                        session=settings['session1'],
                        driver1=settings['driver1'],
                        driver2=settings['driver2'],
                        lap1=settings['lap1'],
                        lap2=settings['lap2'],
                        is_fastest=settings['is_fastest_lap'],
                        use_time_axis=settings['use_time_axis']
                    )
                    return success
                else:
                    # 舊版模組：直接設定屬性
                    analysis_module.driver1 = settings['driver1']
                    analysis_module.driver2 = settings['driver2']
                    analysis_module.lap1 = settings['lap1']
                    analysis_module.lap2 = settings['lap2']
                    return True
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] [DRIVER_LAP_HELPER] Apply settings failed: {e}")
            import traceback
            traceback.print_exc()
            return False
