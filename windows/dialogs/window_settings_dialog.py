# -*- coding: utf-8 -*-
"""
WindowSettingsDialog - 視窗設定對話框
=====================================

從 f1t_gui_main.py 提取的視窗設定對話框實現。
提供年份、賽事、賽段選擇及同步控制功能。
"""

from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QComboBox, QCheckBox, QPushButton, QLabel, QGroupBox,
    QListWidget, QListWidgetItem, QSpinBox, QDialogButtonBox,
    QLineEdit, QFrame
)
from PyQt5.QtCore import Qt

from core.logger import get_logger
from core.gui_i18n import tr
from modules.gui.shared.season_calendar_provider import SeasonCalendarError, SeasonEvent

logger = get_logger(__name__)


class WindowSettingsDialog(QDialog):
    """視窗設定對話框"""
    
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.main_window = parent_window.main_window if hasattr(parent_window, 'main_window') else parent_window
        self._season_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        self.setWindowTitle(tr("window_settings_title", "Window Settings"))
        self.setObjectName("SettingsDialog")
        
        # 判斷是否為遙測模組（需要車手/圈數控制）
        self.is_telemetry_module = self._check_if_telemetry_module()
        
        # 根據模組類型調整對話框尺寸
        if self.is_telemetry_module:
            self.setFixedSize(500, 750)  # 遙測模組需要更大的對話框（支援跨賽事比較）
        else:
            self.setFixedSize(400, 300)  # 其他模組維持原尺寸
        
        self.setModal(True)
        
        # 設置對話框佈局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 標題
        title_label = QLabel(tr("window_settings_dialog_title", "[TOOL] Window Analysis Settings"))
        title_label.setObjectName("DialogTitle")
        layout.addWidget(title_label)
        
        # 連動控制區域
        sync_group = QGroupBox(tr("window_sync_control_group", "Window Sync Control"))
        sync_group.setObjectName("SettingsGroup")
        sync_layout = QVBoxLayout(sync_group)
        
        # 連動控制勾選框
        self.sync_windows_checkbox = QCheckBox(tr("sync_checkbox_main", "[LINK] Receive Main Window Sync (Year/Race/Session)"))
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        # [TOOL] 修復: 從父視窗獲取當前同步狀態
        current_sync_state = getattr(parent_window, 'sync_enabled', True)
        self.sync_windows_checkbox.setChecked(current_sync_state)
        self.sync_windows_checkbox.setToolTip(tr("sync_checkbox_tooltip_main", "When checked, receive parameters from main window and lock analysis controls"))
        # [TOOL] 新增: 當同步狀態改變時，切換分析參數的可編輯性
        self.sync_windows_checkbox.toggled.connect(self.on_sync_checkbox_toggled)
        sync_layout.addWidget(self.sync_windows_checkbox)
        
        layout.addWidget(sync_group)
        
        # 分析參數區域
        params_group = QGroupBox(tr("analysis_params_group", "Analysis Parameters"))
        params_group.setObjectName("SettingsGroup")
        params_layout = QGridLayout(params_group)
        
        # 年份選擇器
        params_layout.addWidget(QLabel(tr("year_label", "Year:")), 0, 0)
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems([str(year) for year in range(2020, 2027)])
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_year') and parent_window.local_year:
            current_year = parent_window.local_year
        else:
            current_year = self.get_current_year_from_main_window()
        self.year_combo.setCurrentText(current_year)
        # [TOOL] 新增: 年份變更時動態更新賽事列表
        self.year_combo.currentTextChanged.connect(self.on_year_changed_in_dialog)
        params_layout.addWidget(self.year_combo, 0, 1)
        
        # 賽事選擇器
        params_layout.addWidget(QLabel(tr("race_label", "Race:")), 1, 0)
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 使用動態賽事列表而非硬編碼
        self.populate_races_for_year(current_year)
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_race') and parent_window.local_race:
            current_race = parent_window.local_race
        else:
            current_race = self.get_current_race_from_main_window()
        self._select_race_by_key(current_race)
        self.race_combo.currentIndexChanged.connect(self._on_race_combo_changed)
        params_layout.addWidget(self.race_combo, 1, 1)
        
        # 賽段選擇器
        params_layout.addWidget(QLabel(tr("session_label", "Session:")), 2, 0)
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 優先從子視窗本地參數獲取，其次從主視窗獲取
        if hasattr(parent_window, 'local_session') and parent_window.local_session:
            current_session = parent_window.local_session
        else:
            current_session = self.get_current_session_from_main_window()
        
        # [DEBUG] 調用前確認點
        logger.info(f"🔍 [SESSION_CALL] 即將調用 _update_session_combo，current_session={current_session}")
        logger.debug(f"🔍 [SESSION_CALL] 即將調用 _update_session_combo，current_session={current_session}")
        
        try:
            self._update_session_combo(preserve_session_code=current_session)
            logger.info(f"✅ [SESSION_CALL] _update_session_combo 調用完成")
            logger.debug(f"✅ [SESSION_CALL] _update_session_combo 調用完成")
        except Exception as e:
            logger.error(f"❌ [SESSION_CALL] _update_session_combo 調用失敗: {e}")
            logger.debug(f"❌ [SESSION_CALL] _update_session_combo 調用失敗: {e}")
            import traceback
            traceback.print_exc()
        
        params_layout.addWidget(self.session_combo, 2, 1)
        
        layout.addWidget(params_group)
        
        # [TOOL] 新增: 遙測模組專用 - 車手與圈數同步控制
        if self.is_telemetry_module:
            self._setup_driver_lap_controls(layout)
        
        # [TOOL] 新增: 根據同步狀態設置分析參數的可編輯性
        self.update_analysis_params_editability()
        
        layout.addStretch()
        
        # 對話框按鈕
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.setObjectName("DialogButtonBox")
        button_box.accepted.connect(self.accept_settings)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def on_sync_checkbox_toggled(self, checked):
        """處理同步勾選框狀態變化"""
        logger.debug(f"[LINK] [SETTING] 同步接收狀態變更為: {'啟用' if checked else '停用'}")
        self.update_analysis_params_editability()
        
        # [TOOL] 移除錯誤的同步調用 - 不需要從主程式同步，保持當前設定
        # if checked:
        #     self.sync_params_from_main_window()  # 這個調用會產生錯誤
    
    def update_analysis_params_editability(self):
        """根據同步狀態更新分析參數的可編輯性"""
        is_sync_enabled = self.sync_windows_checkbox.isChecked()
        
        # 設置分析參數控件的可編輯性（同步時不可編輯）
        self.year_combo.setEnabled(not is_sync_enabled)
        self.race_combo.setEnabled(not is_sync_enabled)
        self.session_combo.setEnabled(not is_sync_enabled)
        
        # 更新提示文字
        if is_sync_enabled:
            self.year_combo.setToolTip(tr("params_locked_tooltip", "Sync enabled, parameters controlled by main window"))
            self.race_combo.setToolTip(tr("params_locked_tooltip", "Sync enabled, parameters controlled by main window"))
            self.session_combo.setToolTip(tr("params_locked_tooltip", "Sync enabled, parameters controlled by main window"))
            logger.debug(f"[LOCK] [SETTING] 分析參數已鎖定 - 接收主程式同步")
        else:
            self.year_combo.setToolTip(tr("year_tooltip", "Set year manually"))
            self.race_combo.setToolTip(tr("race_tooltip", "Set race manually"))
            self.session_combo.setToolTip(tr("session_tooltip", "Set session manually"))
            logger.debug(f"🔓 [SETTING] 分析參數已解鎖 - 可手動編輯")
    
    def sync_params_from_main_window(self):
        """從主程式同步參數到設定對話框"""
        try:
            current_year = self.get_current_year_from_main_window()
            current_race = self.get_current_race_from_main_window()
            current_session = self.get_current_session_from_main_window()
            
            logger.debug(f"📥 [SETTING] 從主程式同步參數: {current_year} {current_race} {current_session}")
            
            # 更新對話框中的參數
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            self.year_combo.setCurrentText(current_year)
            # 需要先更新賽事列表
            self.populate_races_for_year(current_year)
            self._select_race_by_key(current_race)
            self._update_session_combo(preserve_session_code=current_session)
            
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            logger.debug(f"[OK] [SETTING] 參數同步完成")
            
        except Exception as e:
            logger.error(f"[ERROR] [SETTING] 從主程式同步參數失敗: {e}")
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'year_combo') and main_window.year_combo:
                    return main_window.year_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'year_combo') and self.parent_window.year_combo:
            #     return self.parent_window.year_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [SETTING] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'race_combo') and main_window.race_combo:
                    return main_window.race_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'race_combo') and self.parent_window.race_combo:
            #     return self.parent_window.race_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [SETTING] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段"""
        try:
            # 如果父視窗有main_window屬性（子視窗情況）
            if hasattr(self.parent_window, 'main_window'):
                main_window = self.parent_window.main_window
                if hasattr(main_window, 'get_selected_session_code'):
                    return main_window.get_selected_session_code()
                if hasattr(main_window, 'session_combo') and main_window.session_combo:
                    return main_window.session_combo.currentText()
            # [TOOL] 移除不安全的直接訪問，避免 AttributeError
            # elif hasattr(self.parent_window, 'session_combo') and self.parent_window.session_combo:
            #     return self.parent_window.session_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [SETTING] 獲取賽段失敗: {e}")
        return "R"  # 預設值

    # --- Season calendar helpers ---

    def _get_calendar_events_for_year(self, year: int) -> List[SeasonEvent]:
        if self.main_window and hasattr(self.main_window, "_get_calendar_events"):
            return self.main_window._get_calendar_events(year)
        if self.main_window and hasattr(self.main_window, "_season_provider"):
            try:
                return self.main_window._season_provider.get_completed_events(year)
            except SeasonCalendarError as exc:
                logger.debug(f"[DIALOG] 取得賽事日曆失敗: {exc}")
        return []

    def _format_race_display(self, event: SeasonEvent) -> str:
        if self.main_window and hasattr(self.main_window, "_format_race_display"):
            return self.main_window._format_race_display(event)
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label

    def _rebuild_race_mapping(self, events: List[SeasonEvent]) -> None:
        self._season_event_lookup.clear()
        self._display_to_race_key.clear()
        for event in events:
            self._season_event_lookup[event.race_key] = event
            formatted_label = self._format_race_display(event)
            candidate_labels = {event.display_label, formatted_label}
            for label in candidate_labels:
                self._display_to_race_key[label] = event.race_key
                if self.main_window:
                    plain = self.main_window._strip_race_display(label)
                else:
                    plain = label
                if plain and plain not in self._display_to_race_key:
                    self._display_to_race_key[plain] = event.race_key

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        if race_key is None or not self.race_combo:
            return
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == race_key:
                self.race_combo.setCurrentIndex(index)
                return

    def get_selected_event(self) -> Optional[SeasonEvent]:
        data = self.race_combo.currentData() if self.race_combo else None
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText() if self.race_combo else ""
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
            race_key = self._display_to_race_key.get(race_key, race_key)
        return self._season_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText() if self.race_combo else ""
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
        return race_key or "Unknown"

    def get_selected_session_code(self) -> str:
        data = self.session_combo.currentData() if self.session_combo else None
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText() if self.session_combo else ""
        return text or "R"

    def _update_session_combo(self, preserve_session_code: Optional[str] = None) -> None:
        logger.info(f"🔍 [SESSION_DEBUG] _update_session_combo 入口，session_combo: {self.session_combo}")
        logger.debug(f"🔍 [SESSION_DEBUG] _update_session_combo 入口，session_combo: {self.session_combo}")
        
        # ✅ 修復：不使用布爾檢查（PyQt5 已刪除的 widget 會返回 False）
        # 改用 hasattr 和 None 檢查
        if not hasattr(self, 'session_combo') or self.session_combo is None:
            logger.warning(f"🔍 [SESSION_DEBUG] session_combo 不存在或為 None，提早返回！")
            logger.debug(f"🔍 [SESSION_DEBUG] session_combo 不存在或為 None，提早返回！")
            return

        event = self.get_selected_event()
        current_code = preserve_session_code or self.get_selected_session_code()
        
        # 🔍 [SESSION_DEBUG] 調試輸出
        logger.info(f"🔍 [SESSION_DEBUG] _update_session_combo 被調用")
        logger.info(f"🔍 [SESSION_DEBUG] preserve_session_code: {preserve_session_code}")
        logger.info(f"🔍 [SESSION_DEBUG] current_code: {current_code}")
        logger.info(f"🔍 [SESSION_DEBUG] event: {event}")
        logger.debug(f"🔍 [SESSION_DEBUG] _update_session_combo 被調用")
        logger.debug(f"🔍 [SESSION_DEBUG] preserve_session_code: {preserve_session_code}")
        logger.debug(f"🔍 [SESSION_DEBUG] current_code: {current_code}")
        logger.debug(f"🔍 [SESSION_DEBUG] event: {event}")
        if event:
            logger.info(f"🔍 [SESSION_DEBUG] event.race_key: {event.race_key}")
            logger.info(f"🔍 [SESSION_DEBUG] event.sessions: {event.sessions}")
            logger.debug(f"🔍 [SESSION_DEBUG] event.race_key: {event.race_key}")
            logger.debug(f"🔍 [SESSION_DEBUG] event.sessions: {event.sessions}")
            if event.sessions:
                logger.info(f"🔍 [SESSION_DEBUG] sessions 數量: {len(event.sessions)}")
                logger.debug(f"🔍 [SESSION_DEBUG] sessions 數量: {len(event.sessions)}")
                for session in event.sessions:
                    logger.info(f"🔍 [SESSION_DEBUG]   - {session.code}")
                    logger.debug(f"🔍 [SESSION_DEBUG]   - {session.code}")
        
        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes = []
            for session in event.sessions:
                self.session_combo.addItem(session.code, session)
                codes.append(session.code)

            target_code = current_code or ("R" if "R" in codes else (codes[0] if codes else None))
            if target_code:
                index = self.session_combo.findText(target_code)
                if index < 0:
                    index = self.session_combo.findText(target_code.upper())
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)
                elif self.session_combo.count() > 0:
                    self.session_combo.setCurrentIndex(0)
        else:
            for code in ["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"]:
                self.session_combo.addItem(code)
            if current_code:
                index = self.session_combo.findText(current_code)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)

        self.session_combo.blockSignals(False)

    def _on_race_combo_changed(self):
        self._update_session_combo()

    
    def get_races_for_year_in_dialog(self, year):
        """在設定對話框中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            year_int = int(year)
            events = self._get_calendar_events_for_year(year_int)
            self._rebuild_race_mapping(events)
            logger.debug(f"[DIALOG] 載入 {year_int} 年的賽事列表: {len(events)} 個賽事")
            return events
        except Exception as e:
            logger.debug(f"[DIALOG ERROR] 獲取賽事列表時出錯: {e}")
            return []
    
    def populate_races_for_year(self, year):
        """為指定年份填充賽事列表"""
        events = self.get_races_for_year_in_dialog(year)
        self.race_combo.clear()
        if events:
            completed_events = [event for event in events if event.is_completed]
            upcoming_events = [event for event in events if not event.is_completed]

            def add_event(event: SeasonEvent) -> None:
                label = self._format_race_display(event)
                self._display_to_race_key[label] = event.race_key
                self.race_combo.addItem(label, event)

            for event in completed_events:
                add_event(event)

            if completed_events and upcoming_events:
                self.race_combo.insertSeparator(self.race_combo.count())

            for event in upcoming_events:
                add_event(event)

            if self.race_combo.currentIndex() < 0:
                preferred_event = select_preferred_event(completed_events, upcoming_events)
                if preferred_event is not None:
                    logger.debug(
                        "[RACE_DEFAULT][MAIN] preferred=%s %s %s",
                        preferred_event.race_key,
                        preferred_event.round,
                        preferred_event.is_completed,
                    )
                    before_index = self.race_combo.currentIndex()
                    self._select_race_by_key(preferred_event.race_key)
                    after_index = self.race_combo.currentIndex()
                    logger.debug(
                        "[RACE_DEFAULT][MAIN] index from %s to %s text=%s",
                        before_index,
                        after_index,
                        self.race_combo.currentText(),
                    )
            if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
                logger.debug(
                    "[RACE_DEFAULT][MAIN] fallback index=0 text=%s",
                    self.race_combo.currentText(),
                )
        else:
            placeholder = tr("season_calendar_placeholder", "[無已完成賽事]")
            self.race_combo.addItem(placeholder, None)
        
    def on_year_changed_in_dialog(self, year):
        """處理設定對話框中的年份變更"""
        logger.debug(f"[DIALOG] 年份變更為: {year}")
        
        # 記住當前選擇的賽事
        current_event = self.get_selected_event()
        current_race_key = current_event.race_key if current_event else None
        
        # 更新賽事列表
        self.populate_races_for_year(year)
        
        if current_race_key:
            self._select_race_by_key(current_race_key)
        if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
            self.race_combo.setCurrentIndex(0)

        self._update_session_combo()
    
    def _check_if_telemetry_module(self) -> bool:
        """檢查當前模組是否為遙測分析模組（需要車手/圈數控制）"""
        try:
            # 方法1: 檢查父視窗的分析模組
            if hasattr(self.parent_window, 'analysis_module'):
                analysis_module = self.parent_window.analysis_module
                if hasattr(analysis_module, 'analysis_type'):
                    analysis_type = analysis_module.analysis_type
                    # 定義遙測模組類型列表（支援大小寫變體以兼容 Workspace 序列化）
                    telemetry_types = [
                        'speed', 'rpm', 'throttle', 'gear', 
                        'acceleration', 'speeddiff', 'Speeddiff',  # 同時支援小寫和大寫S
                        'timediff', 'Timediff',  # 🆕 添加 Time Diff 支援
                        'distancediff', 'brake', 'steering', 'drs'
                    ]
                    is_telemetry = analysis_type in telemetry_types
                    logger.debug(f"[WINDOW_SETTINGS] 模組類型: {analysis_type}, 是否為遙測模組: {is_telemetry}")
                    return is_telemetry
            
            # 方法2: 檢查父視窗的 _analysis_type 屬性
            if hasattr(self.parent_window, '_analysis_type'):
                analysis_type = self.parent_window._analysis_type
                telemetry_types = [
                    'speed', 'rpm', 'throttle', 'gear',
                    'acceleration', 'speeddiff', 'Speeddiff',  # 同時支援小寫和大寫S
                    'timediff', 'Timediff',  # 🆕 添加 Time Diff 支援
                    'distancediff', 'brake', 'steering', 'drs'
                ]
                is_telemetry = analysis_type in telemetry_types
                logger.debug(f"[WINDOW_SETTINGS] 模組類型 (_analysis_type): {analysis_type}, 是否為遙測模組: {is_telemetry}")
                return is_telemetry
            
            logger.debug(f"[WINDOW_SETTINGS] 無法判斷模組類型，預設為非遙測模組")
            return False
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 檢查模組類型失敗: {e}")
            return False
    
    def _setup_driver_lap_controls(self, parent_layout):
        """設置車手與圈數控制（僅遙測模組） - 支援跨賽事比較"""
        try:
            from PyQt5.QtGui import QIntValidator
            
            # 車手與圈數同步控制分組
            driver_lap_group = QGroupBox(tr("driver_lap_sync_control", "車手與圈數同步控制"))
            driver_lap_group.setObjectName("SettingsGroup")
            driver_lap_layout = QVBoxLayout(driver_lap_group)
            
            # 同步控制勾選框
            self.sync_driver_lap_checkbox = QCheckBox(tr("sync_driver_lap_checkbox", "[LINK] 與主視窗同步車手與圈數"))
            self.sync_driver_lap_checkbox.setObjectName("SyncDriverLapCheckbox")
            
            # 從分析模組讀取同步狀態（如果存在）
            if hasattr(self.parent_window, 'analysis_module'):
                analysis_module = self.parent_window.analysis_module
                current_sync_state = getattr(analysis_module, 'sync_driver_lap_enabled', True)
                self.sync_driver_lap_checkbox.setChecked(current_sync_state)
                logger.info(f"[WINDOW_SETTINGS] 從分析模組載入同步狀態: {current_sync_state}")
            else:
                self.sync_driver_lap_checkbox.setChecked(True)  # 預設啟用同步
            
            self.sync_driver_lap_checkbox.setToolTip(tr("sync_driver_lap_tooltip", "勾選時車手與圈數由主視窗控制，取消勾選可手動設定"))
            self.sync_driver_lap_checkbox.toggled.connect(self._on_sync_driver_lap_toggled)
            logger.info(f"[WINDOW_SETTINGS] 車手與圈數同步 checkbox 信號已連接到 _on_sync_driver_lap_toggled")
            driver_lap_layout.addWidget(self.sync_driver_lap_checkbox)
            
            # 車手與圈數控制區域
            controls_widget = QWidget()
            controls_layout = QGridLayout(controls_widget)
            controls_layout.setContentsMargins(10, 10, 10, 10)
            controls_layout.setSpacing(6)
            
            # === 車手 1 控制 ===
            row = 0
            controls_layout.addWidget(QLabel(tr("driver1_section", "車手 1:")), row, 0, 1, 5)
            
            row += 1
            # 年份
            controls_layout.addWidget(QLabel(tr("year_label", "年份:")), row, 0)
            self.driver1_year_combo = QComboBox()
            self.driver1_year_combo.setObjectName("YearComboBox")
            self.driver1_year_combo.addItems([str(y) for y in range(2020, 2027)])
            self.driver1_year_combo.setMinimumWidth(70)
            self.driver1_year_combo.currentTextChanged.connect(self._on_driver1_year_changed)
            controls_layout.addWidget(self.driver1_year_combo, row, 1)
            
            # 賽事
            controls_layout.addWidget(QLabel(tr("race_label", "賽事:")), row, 2)
            self.driver1_race_combo = QComboBox()
            self.driver1_race_combo.setObjectName("RaceComboBox")
            self.driver1_race_combo.setMinimumWidth(120)
            self.driver1_race_combo.currentIndexChanged.connect(self._on_driver1_race_changed)
            controls_layout.addWidget(self.driver1_race_combo, row, 3)
            
            # 賽段
            controls_layout.addWidget(QLabel(tr("session_label", "賽段:")), row, 4)
            self.driver1_session_combo = QComboBox()
            self.driver1_session_combo.setObjectName("SessionComboBox")
            self.driver1_session_combo.setMinimumWidth(50)
            controls_layout.addWidget(self.driver1_session_combo, row, 5)
            
            row += 1
            # 車手
            controls_layout.addWidget(QLabel(tr("driver_label", "車手:")), row, 0)
            self.driver1_combo = QComboBox()
            self.driver1_combo.setObjectName("DriverComboBox")
            self.driver1_combo.setMinimumWidth(80)
            self._populate_driver_combo(self.driver1_combo)
            controls_layout.addWidget(self.driver1_combo, row, 1)
            
            # 圈數
            controls_layout.addWidget(QLabel(tr("lap_label", "圈數:")), row, 2)
            self.lap1_input = QLineEdit()
            self.lap1_input.setObjectName("LapInput")
            self.lap1_input.setText("1")
            self.lap1_input.setMaximumWidth(50)
            self.lap1_input.setValidator(QIntValidator(1, 999))
            controls_layout.addWidget(self.lap1_input, row, 3)
            
            # 最速圈
            self.fastest_lap1_checkbox = QCheckBox(tr("fastest_lap_label", "最速圈"))
            self.fastest_lap1_checkbox.setObjectName("FastestLapCheckbox")
            self.fastest_lap1_checkbox.stateChanged.connect(lambda state: self._on_fastest_lap_changed(state, 1))
            controls_layout.addWidget(self.fastest_lap1_checkbox, row, 4, 1, 2)
            
            # === 分隔線 ===
            row += 1
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            controls_layout.addWidget(separator, row, 0, 1, 6)
            
            # === 車手 2 控制 ===
            row += 1
            controls_layout.addWidget(QLabel(tr("driver2_section", "車手 2:")), row, 0, 1, 5)
            
            row += 1
            # 年份
            controls_layout.addWidget(QLabel(tr("year_label", "年份:")), row, 0)
            self.driver2_year_combo = QComboBox()
            self.driver2_year_combo.setObjectName("YearComboBox")
            self.driver2_year_combo.addItems([str(y) for y in range(2020, 2027)])
            self.driver2_year_combo.setMinimumWidth(70)
            self.driver2_year_combo.currentTextChanged.connect(self._on_driver2_year_changed)
            controls_layout.addWidget(self.driver2_year_combo, row, 1)
            
            # 賽事（自動同步車手 1，灰色不可編輯）
            controls_layout.addWidget(QLabel(tr("race_label", "賽事:")), row, 2)
            self.driver2_race_combo = QComboBox()
            self.driver2_race_combo.setObjectName("RaceComboBox")
            self.driver2_race_combo.setMinimumWidth(120)
            self.driver2_race_combo.setEnabled(False)  # 強制灰色
            controls_layout.addWidget(self.driver2_race_combo, row, 3)
            
            # 賽段
            controls_layout.addWidget(QLabel(tr("session_label", "賽段:")), row, 4)
            self.driver2_session_combo = QComboBox()
            self.driver2_session_combo.setObjectName("SessionComboBox")
            self.driver2_session_combo.setMinimumWidth(50)
            controls_layout.addWidget(self.driver2_session_combo, row, 5)
            
            row += 1
            # 車手
            controls_layout.addWidget(QLabel(tr("driver_label", "車手:")), row, 0)
            self.driver2_combo = QComboBox()
            self.driver2_combo.setObjectName("DriverComboBox")
            self.driver2_combo.setMinimumWidth(80)
            self._populate_driver_combo(self.driver2_combo)
            controls_layout.addWidget(self.driver2_combo, row, 1)
            
            # 圈數
            controls_layout.addWidget(QLabel(tr("lap_label", "圈數:")), row, 2)
            self.lap2_input = QLineEdit()
            self.lap2_input.setObjectName("LapInput")
            self.lap2_input.setText("1")
            self.lap2_input.setMaximumWidth(50)
            self.lap2_input.setValidator(QIntValidator(1, 999))
            controls_layout.addWidget(self.lap2_input, row, 3)
            
            # 最速圈
            self.fastest_lap2_checkbox = QCheckBox(tr("fastest_lap_label", "最速圈"))
            self.fastest_lap2_checkbox.setObjectName("FastestLapCheckbox")
            self.fastest_lap2_checkbox.stateChanged.connect(lambda state: self._on_fastest_lap_changed(state, 2))
            controls_layout.addWidget(self.fastest_lap2_checkbox, row, 4, 1, 2)
            
            driver_lap_layout.addWidget(controls_widget)
            
            # === 時間軸控制 ===
            self.use_time_axis_checkbox = QCheckBox(tr("use_time_axis_checkbox", "使用時間軸 (Use Time Axis)"))
            self.use_time_axis_checkbox.setObjectName("UseTimeAxisCheckbox")
            
            # 從主視窗或分析模組載入時間軸狀態（加入 try-except 保護）
            try:
                if hasattr(self.main_window, 'use_time_axis_checkbox') and self.main_window.use_time_axis_checkbox:
                    current_time_axis_state = self.main_window.use_time_axis_checkbox.isChecked()
                    self.use_time_axis_checkbox.setChecked(current_time_axis_state)
                    logger.debug(f"[WINDOW_SETTINGS] 從主視窗載入時間軸狀態: {current_time_axis_state}")
                elif hasattr(self.parent_window, 'analysis_module'):
                    analysis_module = self.parent_window.analysis_module
                    current_time_axis_state = getattr(analysis_module, 'use_time_axis', False)
                    self.use_time_axis_checkbox.setChecked(current_time_axis_state)
                    logger.debug(f"[WINDOW_SETTINGS] 從分析模組載入時間軸狀態: {current_time_axis_state}")
                else:
                    self.use_time_axis_checkbox.setChecked(False)  # 預設不使用時間軸
            except (AttributeError, RuntimeError) as e:
                logger.error(f"[ERROR] [WINDOW_SETTINGS] 載入時間軸狀態失敗: {e}")
                self.use_time_axis_checkbox.setChecked(False)  # 預設不使用時間軸
            
            self.use_time_axis_checkbox.setToolTip(tr("use_time_axis_tooltip", "切換橫軸為時間軸（秒）或距離軸（米）"))
            driver_lap_layout.addWidget(self.use_time_axis_checkbox)
            
            parent_layout.addWidget(driver_lap_group)
            
            # 從父視窗的分析模組獲取當前車手和圈數
            self._load_current_driver_lap_settings()
            
            # 初始化控制項的可編輯性
            self._update_driver_lap_controls_editability()
            
            logger.debug(f"[OK] [WINDOW_SETTINGS] 車手與圈數控制已設置（支援跨賽事比較）")
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 設置車手與圈數控制失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_driver_combo(self, combo: QComboBox):
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
                logger.error(f"[ERROR] [WINDOW_SETTINGS] 從主視窗獲取車手列表失敗: {e}")
                # 預設車手列表
                default_drivers = ["VER", "LEC", "HAM", "PER", "SAI", "RUS", "NOR", "PIA", "ALO", "STR"]
                combo.addItems(default_drivers)
                
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 填充車手列表失敗: {e}")
            # 使用最小預設列表
            combo.addItems(["VER", "LEC", "HAM"])
    
    def _load_current_driver_lap_settings(self):
        """從分析模組載入當前的車手和圈數設定"""
        try:
            # 判斷是否勾選同步
            sync_enabled = self.sync_driver_lap_checkbox.isChecked()
            
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
                    logger.error(f"[ERROR] [WINDOW_SETTINGS] 無法從主視窗載入參數: {e}")
                    # 使用預設值
                    source_year, source_race, source_session = "2024", "", "R"
                    source_driver1, source_driver2 = "VER", "NOR"
                    year1, race1, session1 = source_year, source_race, source_session
                    year2, race2, session2 = source_year, source_race, source_session
                    lap1, lap2 = 1, 1
            else:
                # 從分析模組載入（如果存在）
                if not hasattr(self.parent_window, 'analysis_module'):
                    source_year = "2024"
                    source_race = ""
                    source_session = "R"
                    source_driver1 = "VER"
                    source_driver2 = "NOR"
                    year1, race1, session1 = source_year, source_race, source_session
                    year2, race2, session2 = source_year, source_race, source_session
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
                    year2 = str(getattr(analysis_module, 'driver2_year', year1))  # 預設與車手 1 相同
                    race2 = getattr(analysis_module, 'driver2_race', race1)  # 預設與車手 1 相同
                    session2 = getattr(analysis_module, 'driver2_session', session1)  # 預設與車手 1 相同
                    source_driver2 = getattr(analysis_module, 'driver2', 'NOR')
                    lap2 = getattr(analysis_module, 'lap2', 1)
            
            # === 填充車手 1 的年份/賽事/賽段 ===
            self.driver1_year_combo.setCurrentText(year1)
            self._populate_race_combo_for_driver(1, year1, race1)
            self._populate_session_combo_for_driver(1, race1, session1)
            
            # === 填充車手 2 的年份/賽事/賽段 ===
            self.driver2_year_combo.setCurrentText(year2)
            # 賽事強制同步車手 1（灰色）
            self._populate_race_combo_for_driver(2, year2, race2)
            self._populate_session_combo_for_driver(2, race2, session2)
            
            # === 載入車手設定 ===
            index = self.driver1_combo.findText(source_driver1)
            if index >= 0:
                self.driver1_combo.setCurrentIndex(index)
            
            index = self.driver2_combo.findText(source_driver2)
            if index >= 0:
                self.driver2_combo.setCurrentIndex(index)
            
            # === 載入圈數設定 ===
            if lap1 == 99:
                self.fastest_lap1_checkbox.setChecked(True)
                self.lap1_input.setText("99")
            else:
                self.lap1_input.setText(str(lap1))
            
            if lap2 == 99:
                self.fastest_lap2_checkbox.setChecked(True)
                self.lap2_input.setText("99")
            else:
                self.lap2_input.setText(str(lap2))
            
            logger.debug(f"[WINDOW_SETTINGS] 已載入設定:")
            logger.debug(f"  車手 1: {year1} {race1} {session1} {source_driver1} 第{lap1}圈")
            logger.debug(f"  車手 2: {year2} {race2} {session2} {source_driver2} 第{lap2}圈")
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 載入車手與圈數設定失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_race_combo_for_driver(self, driver_num: int, year: str, current_race: str = ""):
        """為指定車手填充賽事下拉選單"""
        try:
            combo = self.driver1_race_combo if driver_num == 1 else self.driver2_race_combo
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
                    logger.debug(f"[WINDOW_SETTINGS] 獲取賽事列表失敗: {exc}")
            
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
            logger.debug(f"[WINDOW_SETTINGS] 車手 {driver_num} 賽事列表已填充: {combo.count()} 個賽事")
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 填充車手 {driver_num} 賽事列表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _populate_session_combo_for_driver(self, driver_num: int, race: str, current_session: str = "R"):
        """為指定車手填充賽段下拉選單"""
        try:
            combo = self.driver1_session_combo if driver_num == 1 else self.driver2_session_combo
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
            logger.debug(f"[WINDOW_SETTINGS] 車手 {driver_num} 賽段列表已填充")
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 填充車手 {driver_num} 賽段列表失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_driver1_year_changed(self, year: str):
        """處理車手 1 年份變更 → 動態更新賽事列表"""
        try:
            logger.debug(f"[WINDOW_SETTINGS] 車手 1 年份變更: {year} → 重新載入賽事列表")
            
            # 保留當前選擇的賽事（如果存在）
            current_race = self.driver1_race_combo.currentText()
            
            # 重新填充車手 1 的賽事列表
            self._populate_race_combo_for_driver(1, year, current_race)
            
            # 同步更新車手 2 的賽事列表（因為賽事必須同步）
            self._populate_race_combo_for_driver(2, self.driver2_year_combo.currentText(), current_race)
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 處理車手 1 年份變更失敗: {e}")
    
    def _on_driver2_year_changed(self, year: str):
        """處理車手 2 年份變更 → 動態更新賽事列表"""
        try:
            logger.debug(f"[WINDOW_SETTINGS] 車手 2 年份變更: {year} → 重新載入賽事列表")
            
            # 保留當前選擇的賽事（必須與車手 1 同步）
            current_race = self.driver1_race_combo.currentText()
            
            # 重新填充車手 2 的賽事列表（賽事與車手 1 同步）
            self._populate_race_combo_for_driver(2, year, current_race)
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 處理車手 2 年份變更失敗: {e}")
    
    def _on_driver1_race_changed(self, index: int):
        """處理車手 1 賽事變更 → 自動同步車手 2 賽事"""
        try:
            if index < 0:
                return
            selected_race = self.driver1_race_combo.currentText()
            logger.debug(f"[WINDOW_SETTINGS] 車手 1 賽事變更: {selected_race} → 同步車手 2")
            
            # 強制同步車手 2 賽事（防止選錯賽道）
            self.driver2_race_combo.blockSignals(True)  # 避免觸發遞迴
            self.driver2_race_combo.setCurrentText(selected_race)
            self.driver2_race_combo.blockSignals(False)
            
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 處理車手 1 賽事變更失敗: {e}")
    
    def _on_sync_driver_lap_toggled(self, checked: bool):
        """處理車手與圈數同步勾選框變更"""
        logger.info(f"🔔 [SYNC_TOGGLED] 方法被調用! checked={checked}")
        logger.info(f"{'='*80}")
        logger.info(f"[SYNC_TOGGLED] 車手與圈數同步: {'啟用' if checked else '停用'}")
        logger.info(f"[SYNC_TOGGLED] parent_window 類型: {type(self.parent_window).__name__}")
        logger.info(f"{'='*80}")
        
        # 步驟 1: 同步更新標題欄按鈕狀態
        if hasattr(self.parent_window, 'title_bar'):
            logger.info(f"[SYNC_TOGGLED] ✅ parent_window 有 title_bar 屬性")
            if hasattr(self.parent_window.title_bar, 'driver_lap_sync_btn'):
                logger.info(f"[SYNC_TOGGLED] ✅ title_bar 有 driver_lap_sync_btn 按鈕")
                # 阻止信號避免遞迴
                self.parent_window.title_bar.driver_lap_sync_btn.blockSignals(True)
                self.parent_window.title_bar.driver_lap_sync_btn.setChecked(checked)
                # 手動更新按鈕外觀
                if checked:
                    self.parent_window.title_bar.driver_lap_sync_btn.setText("D")
                    logger.info(f"[SYNC_TOGGLED] 標題欄按鈕已更新為 D (啟用)")
                else:
                    self.parent_window.title_bar.driver_lap_sync_btn.setText("X")
                    logger.info(f"[SYNC_TOGGLED] 標題欄按鈕已更新為 X (停用)")
                self.parent_window.title_bar.driver_lap_sync_btn.blockSignals(False)
            else:
                logger.warning(f"[SYNC_TOGGLED] ❌ title_bar 沒有 driver_lap_sync_btn 按鈕")
        else:
            logger.warning(f"[SYNC_TOGGLED] ❌ parent_window 沒有 title_bar 屬性")
        
        # 步驟 2: 更新分析模組的同步狀態
        if hasattr(self.parent_window, 'analysis_module'):
            analysis_module = self.parent_window.analysis_module
            if hasattr(analysis_module, 'sync_driver_lap_enabled'):
                analysis_module.sync_driver_lap_enabled = checked
                logger.info(f"[SYNC_TOGGLED] 分析模組同步狀態已更新: {checked}")
        
        # 步驟 3: 更新控制項的可編輯性
        self._update_driver_lap_controls_editability()
        
        # 步驟 4: 如果停用同步，載入全域參數池的值
        if not checked:
            logger.info(f"[SYNC_TOGGLED] 同步已停用，準備載入全域參數池")
            self._load_shared_params_to_ui()
        else:
            logger.info(f"[SYNC_TOGGLED] 同步已啟用，使用主視窗參數")
    
    def _load_shared_params_to_ui(self):
        """從全域參數池載入參數到 UI 控制項"""
        try:
            # ✅ 原則 0-1：驗證物件存在
            if not hasattr(self.main_window, 'shared_independent_params'):
                logger.debug(f"[LOAD_SHARED] ⚠️  主視窗沒有 shared_independent_params")
                return
            
            # ✅ 原則 0-1：在 try-except 內訪問物件（防止 EXE 中的 RuntimeError）
            try:
                shared_params = self.main_window.shared_independent_params
            except (AttributeError, RuntimeError) as e:
                logger.debug(f"[LOAD_SHARED] ❌ 無法訪問 shared_independent_params: {e}")
                logger.debug(f"[LOAD_SHARED] 這通常發生在 EXE 中物件已被釋放")
                return
            
            # ✅ 原則 0-1：驗證獲取的物件是字典
            if not isinstance(shared_params, dict):
                logger.debug(f"[LOAD_SHARED] ⚠️  shared_independent_params 不是字典類型: {type(shared_params)}")
                return
            
            logger.debug(f"[LOAD_SHARED] 全域參數池內容:")
            for key, value in shared_params.items():
                logger.debug(f"   {key}: {value}")
            
            # 檢查是否為空（所有值都是 None）
            if all(v is None for k, v in shared_params.items() if k != 'use_time_axis'):
                logger.debug(f"[LOAD_SHARED] ⚠️  全域參數池為空，跳過載入")
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
            
            logger.debug(f"[LOAD_SHARED] 🔄 開始更新 UI 控制項...")
            
            # === 更新車手 1 UI ===
            if year1:
                self.driver1_year_combo.setCurrentText(str(year1))
                logger.debug(f"[LOAD_SHARED] ✅ 車手 1 年份: {year1}")
            
            if race1:
                # 需要先載入賽事列表
                self._populate_race_combo_for_driver(1, str(year1) if year1 else "2025", race1)
                logger.debug(f"[LOAD_SHARED] ✅ 車手 1 賽事: {race1}")
            
            if session1:
                # 需要先載入賽段列表
                self._populate_session_combo_for_driver(1, race1 if race1 else "", session1)
                logger.debug(f"[LOAD_SHARED] ✅ 車手 1 賽段: {session1}")
            
            if driver1:
                index = self.driver1_combo.findText(driver1)
                if index >= 0:
                    self.driver1_combo.setCurrentIndex(index)
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 1: {driver1}")
            
            if lap1 is not None:
                if lap1 == 99:
                    self.fastest_lap1_checkbox.setChecked(True)
                    self.lap1_input.setText("99")
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 1 圈數: 99 (最速圈)")
                else:
                    self.fastest_lap1_checkbox.setChecked(False)
                    self.lap1_input.setText(str(lap1))
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 1 圈數: {lap1}")
            
            # === 更新車手 2 UI ===
            if year2:
                self.driver2_year_combo.setCurrentText(str(year2))
                logger.debug(f"[LOAD_SHARED] ✅ 車手 2 年份: {year2}")
            
            if race2:
                # 車手 2 的賽事自動同步車手 1
                self._populate_race_combo_for_driver(2, str(year2) if year2 else "2025", race2)
                logger.debug(f"[LOAD_SHARED] ✅ 車手 2 賽事: {race2}")
            
            if session2:
                self._populate_session_combo_for_driver(2, race2 if race2 else "", session2)
                logger.debug(f"[LOAD_SHARED] ✅ 車手 2 賽段: {session2}")
            
            if driver2:
                index = self.driver2_combo.findText(driver2)
                if index >= 0:
                    self.driver2_combo.setCurrentIndex(index)
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 2: {driver2}")
            
            if lap2 is not None:
                if lap2 == 99:
                    self.fastest_lap2_checkbox.setChecked(True)
                    self.lap2_input.setText("99")
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 2 圈數: 99 (最速圈)")
                else:
                    self.fastest_lap2_checkbox.setChecked(False)
                    self.lap2_input.setText(str(lap2))
                    logger.debug(f"[LOAD_SHARED] ✅ 車手 2 圈數: {lap2}")
            
            # === 更新時間軸 checkbox ===
            if hasattr(self, 'use_time_axis_checkbox'):
                self.use_time_axis_checkbox.setChecked(use_time_axis)
                logger.debug(f"[LOAD_SHARED] ✅ 時間軸模式: {use_time_axis}")
            
            logger.debug(f"\n{'='*80}")
            logger.debug(f"[LOAD_SHARED] ✅ 全域參數池已載入到 UI")
            logger.debug(f"{'='*80}\n")
            
        except Exception as e:
            logger.debug(f"[LOAD_SHARED] ❌ 載入失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_driver_lap_controls_editability(self):
        """根據同步狀態更新車手與圈數控制項的可編輯性"""
        if not hasattr(self, 'sync_driver_lap_checkbox'):
            return
        
        is_sync_enabled = self.sync_driver_lap_checkbox.isChecked()
        
        # === 設置 Year/Race/Session 控制項的可編輯性 ===
        # 車手 1 的 Year/Race/Session（同步時不可編輯）
        self.driver1_year_combo.setEnabled(not is_sync_enabled)
        self.driver1_race_combo.setEnabled(not is_sync_enabled)
        self.driver1_session_combo.setEnabled(not is_sync_enabled)
        
        # 車手 2 的 Year/Session（同步時不可編輯）
        self.driver2_year_combo.setEnabled(not is_sync_enabled)
        # 車手 2 的 Race **始終灰色**（強制與車手 1 同步）
        self.driver2_race_combo.setEnabled(False)  # 永遠不可編輯
        self.driver2_session_combo.setEnabled(not is_sync_enabled)
        
        # === 設置車手與圈數控制項的可編輯性 ===
        self.driver1_combo.setEnabled(not is_sync_enabled)
        self.driver2_combo.setEnabled(not is_sync_enabled)
        self.lap1_input.setEnabled(not is_sync_enabled and not self.fastest_lap1_checkbox.isChecked())
        self.lap2_input.setEnabled(not is_sync_enabled and not self.fastest_lap2_checkbox.isChecked())
        self.fastest_lap1_checkbox.setEnabled(not is_sync_enabled)
        self.fastest_lap2_checkbox.setEnabled(not is_sync_enabled)
        
        # === 更新提示文字 ===
        if is_sync_enabled:
            tooltip = tr("sync_driver_lap_enabled_tooltip", "已啟用同步，參數由主視窗控制")
            self.driver1_year_combo.setToolTip(tooltip)
            self.driver1_race_combo.setToolTip(tooltip)
            self.driver1_session_combo.setToolTip(tooltip)
            self.driver2_year_combo.setToolTip(tooltip)
            self.driver2_race_combo.setToolTip(tr("race_sync_tooltip", "賽事自動同步車手 1（防止選錯賽道）"))
            self.driver2_session_combo.setToolTip(tooltip)
            self.driver1_combo.setToolTip(tooltip)
            self.driver2_combo.setToolTip(tooltip)
            self.lap1_input.setToolTip(tooltip)
            self.lap2_input.setToolTip(tooltip)
            logger.debug(f"[LOCK] [WINDOW_SETTINGS] 所有控制已鎖定（同步模式）")
        else:
            self.driver1_year_combo.setToolTip(tr("year1_tooltip", "設定車手 1 的年份"))
            self.driver1_race_combo.setToolTip(tr("race1_tooltip", "設定車手 1 的賽事"))
            self.driver1_session_combo.setToolTip(tr("session1_tooltip", "設定車手 1 的賽段"))
            self.driver2_year_combo.setToolTip(tr("year2_tooltip", "設定車手 2 的年份"))
            self.driver2_race_combo.setToolTip(tr("race_sync_tooltip", "賽事自動同步車手 1（防止選錯賽道）"))
            self.driver2_session_combo.setToolTip(tr("session2_tooltip", "設定車手 2 的賽段"))
            self.driver1_combo.setToolTip(tr("driver1_tooltip", "選擇車手 1"))
            self.driver2_combo.setToolTip(tr("driver2_tooltip", "選擇車手 2"))
            self.lap1_input.setToolTip(tr("lap1_tooltip", "設定圈數 1"))
            self.lap2_input.setToolTip(tr("lap2_tooltip", "設定圈數 2"))
            logger.debug(f"🔓 [WINDOW_SETTINGS] 所有控制已解鎖（手動模式）")
    
    def _on_fastest_lap_changed(self, state, driver_num: int):
        """處理最速圈勾選框變更"""
        is_checked = (state == 2)  # Qt.Checked
        
        if driver_num == 1:
            if is_checked:
                self.lap1_input.setText("99")
                self.lap1_input.setEnabled(False)
                self.lap1_input.setStyleSheet("color: #666666;")
                logger.debug(f"[WINDOW_SETTINGS] 車手 1 最速圈已啟用（圈數=99）")
            else:
                self.lap1_input.setText("1")
                self.lap1_input.setEnabled(not self.sync_driver_lap_checkbox.isChecked())
                self.lap1_input.setStyleSheet("")
                logger.debug(f"[WINDOW_SETTINGS] 車手 1 最速圈已停用")
        elif driver_num == 2:
            if is_checked:
                self.lap2_input.setText("99")
                self.lap2_input.setEnabled(False)
                self.lap2_input.setStyleSheet("color: #666666;")
                logger.debug(f"[WINDOW_SETTINGS] 車手 2 最速圈已啟用（圈數=99）")
            else:
                self.lap2_input.setText("1")
                self.lap2_input.setEnabled(not self.sync_driver_lap_checkbox.isChecked())
                self.lap2_input.setStyleSheet("")
                logger.debug(f"[WINDOW_SETTINGS] 車手 2 最速圈已停用")
        
    def accept_settings(self):
        """確認設定"""
        window_title = self.parent_window.windowTitle()
        year = self.year_combo.currentText()
        race = self.get_selected_race_key()
        session = self.get_selected_session_code()
        sync_windows = self.sync_windows_checkbox.isChecked()
        
        logger.debug(f"\n{'='*80}")
        logger.debug(f"[ACCEPT_SETTINGS] 設定對話框 OK 按鈕被點擊")
        logger.debug(f"[ACCEPT_SETTINGS] 視窗: {window_title}")
        logger.debug(f"[ACCEPT_SETTINGS] 參數: {year} {race} {session}")
        logger.debug(f"[ACCEPT_SETTINGS] 同步接收狀態: {'啟用' if sync_windows else '停用'}")
        logger.debug(f"[ACCEPT_SETTINGS] 是否為遙測模組: {self.is_telemetry_module}")
        logger.debug(f"{'='*80}\n")
        
        # 保存同步狀態到父視窗
        self.parent_window.sync_enabled = sync_windows
        
        # [TOOL] 新增: 處理遙測模組的車手與圈數設定
        if self.is_telemetry_module and hasattr(self, 'sync_driver_lap_checkbox') and self.sync_driver_lap_checkbox:
            try:
                sync_driver_lap = self.sync_driver_lap_checkbox.isChecked()
            except RuntimeError:
                # QCheckBox 已被刪除，使用預設值
                logger.warning("[ACCEPT_SETTINGS] sync_driver_lap_checkbox 已被刪除，使用預設值 True")
                sync_driver_lap = True
            logger.debug(f"\n[TELEMETRY_MODULE_DETECTED]")
            logger.debug(f"   車手與圈數同步: {'啟用' if sync_driver_lap else '停用'}")
            
            if not sync_driver_lap:
                logger.debug(f"[MANUAL_MODE] 車手與圈數同步已停用，進入手動模式")
                # 手動模式：獲取車手和圈數設定
                driver1 = self.driver1_combo.currentText()
                driver2 = self.driver2_combo.currentText()
                
                try:
                    lap1 = int(self.lap1_input.text())
                except ValueError:
                    lap1 = 1
                
                try:
                    lap2 = int(self.lap2_input.text())
                except ValueError:
                    lap2 = 1
                
                is_fastest_lap = (lap1 == 99 or lap2 == 99)
                
                logger.debug(f"   車手設定: {driver1} vs {driver2}")
                logger.debug(f"   圈數設定: 第{lap1}圈 vs 第{lap2}圈")
                logger.debug(f"   最速圈: {is_fastest_lap}")
                
                # 應用車手與圈數設定到分析模組
                logger.debug(f"[CALLING] _apply_driver_lap_settings()")
                self._apply_driver_lap_settings(driver1, driver2, lap1, lap2, is_fastest_lap)
                logger.debug(f"[RETURNED] _apply_driver_lap_settings()")
            else:
                # 啟用同步：從主視窗讀取參數並應用
                logger.debug(f"[SYNC_MODE] 車手與圈數同步已啟用，從主視窗讀取參數")
                
                try:
                    # ✅ 從主視窗讀取所有參數（加入 try-except 保護）
                    main_driver1 = self.main_window.driver1_combo.currentText() if hasattr(self.main_window, 'driver1_combo') else "VER"
                    
                    if hasattr(self.main_window, 'driver2_combo'):
                        main_driver2_data = self.main_window.driver2_combo.currentData()
                        main_driver2 = self.main_window.driver2_combo.currentText() if main_driver2_data is not None else None
                    else:
                        main_driver2 = None
                    
                    main_lap1 = self.main_window.lap1_spinbox.value() if hasattr(self.main_window, 'lap1_spinbox') else 1
                    main_lap2 = self.main_window.lap2_spinbox.value() if hasattr(self.main_window, 'lap2_spinbox') else 1
                    main_is_fastest = self.main_window.fastest_lap_checkbox.isChecked() if hasattr(self.main_window, 'fastest_lap_checkbox') else False
                    
                    logger.debug(f"[SYNC_MODE] 主視窗參數:")
                    logger.debug(f"   車手 1: {main_driver1}")
                    logger.debug(f"   車手 2: {main_driver2}")
                    logger.debug(f"   圈數 1: {main_lap1}")
                    logger.debug(f"   圈數 2: {main_lap2}")
                    logger.debug(f"   最速圈: {main_is_fastest}")
                    
                    # ✅ 調用 _apply_driver_lap_settings 實際套用主視窗參數
                    logger.debug(f"[CALLING] _apply_driver_lap_settings() with main window params")
                    self._apply_driver_lap_settings(main_driver1, main_driver2, main_lap1, main_lap2, main_is_fastest)
                    logger.debug(f"[RETURNED] _apply_driver_lap_settings()")
                    logger.debug(f"[SYNC_MODE] ✅ 主視窗參數已套用到當前視窗")
                    
                except AttributeError as e:
                    logger.error(f"[ERROR] [SYNC_MODE] 無法從主視窗讀取參數: {e}")
                    logger.error(f"[ERROR] 這通常發生在 EXE 中物件引用失效")
                    # 使用預設值繼續
                    self._apply_driver_lap_settings("VER", None, 1, 1, False)
                except Exception as e:
                    logger.error(f"[ERROR] [SYNC_MODE] 讀取主視窗參數時發生未預期錯誤: {e}")
                    import traceback
                    traceback.print_exc()
        
        # [TOOL] 修改邏輯：根據同步狀態決定行為
        # ⚠️ 關鍵修復：檢查 sync_driver_lap_enabled，如果停用則跳過主視窗同步
        if sync_windows:
            # ✅ 車手與圈數同步已在上面的 if-else 處理完畢
            # 不需要再調用 update_current_window_only()
            logger.debug(f"[REFRESH] [SETTING] [{window_title}] ✅ 車手與圈數已同步完成")
            logger.debug(f"[REFRESH] [SETTING] [{window_title}] sync_driver_lap = {sync_driver_lap}")
        else:
            # 當停用同步時，允許手動設定並應用到當前視窗
            logger.debug(f"[TOOL] [SETTING] [{window_title}] 手動設定模式 - 應用自定義參數")
            self.apply_manual_settings(year, race, session)
        
        self.accept()
    
    def _apply_driver_lap_settings(self, driver1: str, driver2: str, lap1: int, lap2: int, is_fastest_lap: bool):
        """應用車手與圈數設定到分析模組（支援跨賽事比較）"""
        logger.debug(f"\n{'='*80}")
        logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 方法開始執行")
        logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 參數: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
        logger.debug(f"{'='*80}\n")
        
        try:
            if not hasattr(self.parent_window, 'analysis_module'):
                logger.warning(f"[WARNING] [WINDOW_SETTINGS] 父視窗沒有 analysis_module 屬性")
                return
            
            analysis_module = self.parent_window.analysis_module
            logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 獲取到 analysis_module: {type(analysis_module).__name__}")
            
            # === 保存同步狀態到分析模組 ===
            try:
                if hasattr(self, 'sync_driver_lap_checkbox') and self.sync_driver_lap_checkbox:
                    sync_enabled = self.sync_driver_lap_checkbox.isChecked()
                else:
                    sync_enabled = True  # 預設啓用同步
            except RuntimeError:
                # QCheckBox 已被刪除，使用預設值
                logger.warning("[_APPLY_DRIVER_LAP_SETTINGS] sync_driver_lap_checkbox 已被刪除，使用預設值 True")
                sync_enabled = True
            analysis_module.sync_driver_lap_enabled = sync_enabled
            logger.debug(f"[WINDOW_SETTINGS] 同步狀態已保存: {sync_enabled}")
            
            # === 保存時間軸設定到分析模組 ===
            try:
                if hasattr(self, 'use_time_axis_checkbox') and self.use_time_axis_checkbox:
                    use_time_axis = self.use_time_axis_checkbox.isChecked()
                else:
                    use_time_axis = False  # 預設使用距離軸
            except RuntimeError:
                logger.warning("[_APPLY_DRIVER_LAP_SETTINGS] use_time_axis_checkbox 已被刪除，使用預設值 False")
                use_time_axis = False
            analysis_module.use_time_axis = use_time_axis
            logger.debug(f"[WINDOW_SETTINGS] 時間軸設定已保存: {use_time_axis}")
            logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 時間軸 checkbox 狀態: {use_time_axis}")
            
            # === 獲取車手 1 和車手 2 的 Year/Race/Session ===
            year1 = self.driver1_year_combo.currentText()
            race1 = self.driver1_race_combo.currentText()
            session1 = self.driver1_session_combo.currentText()
            
            year2 = self.driver2_year_combo.currentText()
            race2 = self.driver2_race_combo.currentText()  # 應該與 race1 相同（灰色同步）
            session2 = self.driver2_session_combo.currentText()
            
            logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 車手 1: {year1} {race1} {session1} {driver1} Lap{lap1}")
            logger.debug(f"[_APPLY_DRIVER_LAP_SETTINGS] 車手 2: {year2} {race2} {session2} {driver2} Lap{lap2}")
            
            # === 保存所有參數到分析模組（用於下次開啟時載入）===
            analysis_module.driver1_year = year1
            analysis_module.driver1_race = race1
            analysis_module.driver1_session = session1
            analysis_module.driver1 = driver1
            analysis_module.lap1 = lap1
            
            analysis_module.driver2_year = year2
            analysis_module.driver2_race = race2
            analysis_module.driver2_session = session2
            analysis_module.driver2 = driver2
            analysis_module.lap2 = lap2
            
            logger.debug(f"[WINDOW_SETTINGS] 所有參數已保存到分析模組")
            
            # === 檢測是否為跨賽事比較 ===
            # ⚠️ 關鍵修復：如果啟用同步，強制使用主視窗參數（單賽事模式）
            if sync_enabled:
                logger.debug(f"[SYNC_FIX] 🔒 已啟用同步，強制使用主視窗參數（單賽事模式）")
                try:
                    # 從主視窗獲取當前參數（使用 combo box）- 加入 try-except 保護
                    year1 = self.main_window.year_combo.currentText() if hasattr(self.main_window, 'year_combo') else year1
                    
                    if hasattr(self.main_window, 'race_combo'):
                        race1_display = self.main_window.race_combo.currentText()
                        # 檢查方法是否存在
                        if hasattr(self.main_window, '_get_race_key_from_display'):
                            race1 = self.main_window._get_race_key_from_display(race1_display)
                        else:
                            race1 = race1  # 保持原值
                    
                    session1 = self.main_window.session_combo.currentText() if hasattr(self.main_window, 'session_combo') else session1
                    year2 = year1  # 強制相同
                    race2 = race1  # 強制相同
                    session2 = session1  # 強制相同
                    
                    logger.debug(f"[SYNC_FIX] 主視窗參數: {year1} {race1} {session1}")
                    logger.debug(f"[SYNC_FIX] 強制設定: year2={year2}, session2={session2}")
                    
                    # 更新分析模組的跨賽事參數為主視窗值
                    analysis_module.driver1_year = year1
                    analysis_module.driver1_race = race1
                    analysis_module.driver1_session = session1
                    analysis_module.driver2_year = year2
                    analysis_module.driver2_race = race2
                    analysis_module.driver2_session = session2
                    
                    is_cross_event = False  # 強制設為 False
                    logger.debug(f"[SYNC_FIX] ✅ 已強制切換為單賽事模式（is_cross_event = False）")
                    
                except AttributeError as e:
                    logger.error(f"[ERROR] [SYNC_FIX] 無法從主視窗獲取參數: {e}")
                    logger.error(f"[ERROR] 使用對話框設定的參數作為備用")
                    is_cross_event = (year1 != year2) or (session1 != session2)
                except Exception as e:
                    logger.error(f"[ERROR] [SYNC_FIX] 獲取主視窗參數時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    is_cross_event = (year1 != year2) or (session1 != session2)
            else:
                is_cross_event = (year1 != year2) or (session1 != session2)
            
            if is_cross_event:
                logger.debug(f"[CROSS-EVENT] 檢測到跨賽事比較:")
                logger.debug(f"   車手 1: {year1} {race1} {session1} {driver1} 第{lap1}圈")
                logger.debug(f"   車手 2: {year2} {race2} {session2} {driver2} 第{lap2}圈")
                
                # 檢查分析模組是否支援跨賽事比較
                if hasattr(analysis_module, 'update_cross_event_comparison'):
                    logger.debug(f"[CROSS-EVENT] 調用 update_cross_event_comparison 方法")
                    
                    success = analysis_module.update_cross_event_comparison(
                        year1=year1, race1=race1, session1=session1, driver1=driver1, lap1=lap1,
                        year2=year2, race2=race2, session2=session2, driver2=driver2, lap2=lap2,
                        is_fastest=is_fastest_lap,
                        use_time_axis=use_time_axis  # 傳遞時間軸設定
                    )
                    
                    if success:
                        logger.debug(f"[OK] [CROSS-EVENT] 跨賽事比較設定已套用")
                    else:
                        logger.debug(f"[INFO] [CROSS-EVENT] 跨賽事比較功能開發中")
                else:
                    logger.debug(f"[INFO] [CROSS-EVENT] 分析模組不支援跨賽事比較")
            else:
                # === 標準模式（同一賽事比較）===
                logger.debug(f"[STANDARD] 標準比較模式:")
                logger.debug(f"   賽事: {year1} {race1} {session1}")
                logger.debug(f"   車手: {driver1} vs {driver2}")
                logger.debug(f"   圈數: 第{lap1}圈 vs 第{lap2}圈")
                
                # 檢查分析模組是否有 update_lap_parameters 方法
                if hasattr(analysis_module, 'update_lap_parameters'):
                    logger.debug(f"[STANDARD] 調用 update_lap_parameters 更新車手與圈數")
                    
                    success = analysis_module.update_lap_parameters(
                        year=year1,
                        race=race1,
                        session=session1,
                        driver1=driver1,
                        driver2=driver2,
                        lap1=lap1,
                        lap2=lap2,
                        is_fastest=is_fastest_lap,
                        use_time_axis=use_time_axis  # 傳遞時間軸設定
                    )
                    
                    if success:
                        logger.debug(f"[OK] [STANDARD] 車手與圈數設定已套用，視窗標題應已更新")
                    else:
                        logger.warning(f"[WARNING] [STANDARD] 車手與圈數設定套用失敗")
                else:
                    # 舊版模組：直接設定屬性
                    logger.debug(f"[STANDARD] 使用直接屬性設定方式（舊版相容）")
                    analysis_module.driver1 = driver1
                    analysis_module.driver2 = driver2
                    analysis_module.lap1 = lap1
                    analysis_module.lap2 = lap2
                    
                    # 手動更新視窗標題
                    if hasattr(self.parent_window, 'setWindowTitle'):
                        new_title = f"Speed Analysis - {year1} {race1} {session1}"
                        self.parent_window.setWindowTitle(new_title)
                        logger.debug(f"[OK] [STANDARD] 車手與圈數屬性已設定，視窗標題已更新: {new_title}")
            
            # ⚠️ [全域共享參數池] 新增：同步所有停用同步的視窗
            if not sync_enabled:
                logger.debug(f"\n{'='*80}")
                logger.debug(f"[SHARED_PARAMS] 當前視窗已停用同步，準備更新全域參數池")
                logger.debug(f"{'='*80}\n")
                
                # 構建參數字典
                updated_params = {
                    'year1': year1,
                    'race1': race1,
                    'session1': session1,
                    'driver1': driver1,
                    'lap1': lap1,
                    'year2': year2,
                    'race2': race2,
                    'session2': session2,
                    'driver2': driver2,
                    'lap2': lap2,
                    'use_time_axis': use_time_axis
                }
                
                logger.debug(f"[SHARED_PARAMS] 構建的參數字典:")
                for key, value in updated_params.items():
                    logger.debug(f"   {key}: {value}")
                
                # 檢查全域參數池是否為空（首次停用同步）
                if all(v is None for k, v in self.main_window.shared_independent_params.items() if k != 'use_time_axis'):
                    logger.debug(f"[SHARED_PARAMS] 全域參數池為空，複製當前參數到全域池")
                    self.main_window.shared_independent_params.update(updated_params)
                    logger.debug(f"[SHARED_PARAMS] ✅ 全域參數池已初始化")
                else:
                    logger.debug(f"[SHARED_PARAMS] 全域參數池已有值，更新全域池並同步所有停用同步的視窗")
                
                # 通知主 GUI 同步所有停用同步的視窗
                if hasattr(self.main_window, 'sync_all_independent_windows'):
                    logger.debug(f"[SHARED_PARAMS] ✅ 找到 sync_all_independent_windows() 方法")
                    logger.debug(f"[SHARED_PARAMS] 🚀 準備調用 sync_all_independent_windows()")
                    self.main_window.sync_all_independent_windows(updated_params)
                    logger.debug(f"[SHARED_PARAMS] ✅ sync_all_independent_windows() 調用完成")
                    logger.debug(f"[SHARED_PARAMS] ✅ 所有停用同步的視窗已同步")
                else:
                    logger.debug(f"[SHARED_PARAMS] ⚠️  主視窗沒有 sync_all_independent_windows() 方法")
                
                logger.debug(f"\n{'='*80}")
                logger.debug(f"[SHARED_PARAMS] 全域參數池同步流程結束")
                logger.debug(f"{'='*80}\n")
            else:
                logger.debug(f"[SHARED_PARAMS] ⚠️  當前視窗啟用了同步，跳過全域參數池更新")
                
        except Exception as e:
            logger.error(f"[ERROR] [WINDOW_SETTINGS] 套用車手與圈數設定失敗: {e}")
            import traceback
            traceback.print_exc()
        
    def update_current_window_only(self):
        """僅更新當前視窗（同步接收模式）"""
        window_title = self.parent_window.windowTitle()
        logger.debug(f"[REFRESH] [SETTING] [{window_title}] 更新視窗數據（同步模式）")
        
        try:
            # 如果當前視窗有update_current_window方法，調用它
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                logger.debug(f"[OK] [SETTING] 當前視窗數據更新完成（同步模式）")
        except Exception as e:
            logger.error(f"[ERROR] [SETTING] 更新當前視窗失敗: {e}")
    
    def apply_manual_settings(self, year, race, session):
        """應用手動設定（獨立模式）"""
        window_title = self.parent_window.windowTitle()
        logger.debug(f"[TOOL] [SETTING] [{window_title}] 應用手動設定: {year} {race} {session}")
        
        try:
            # 更新當前視窗的內容（使用手動設定的參數）
            self.update_current_window_with_params(year, race, session)
            logger.debug(f"[OK] [SETTING] 手動設定應用完成")
        except Exception as e:
            logger.error(f"[ERROR] [SETTING] 應用手動設定失敗: {e}")
    
    def update_current_window_with_params(self, year, race, session):
        """使用指定參數更新當前視窗"""
        window_title = self.parent_window.windowTitle()
        logger.debug(f"[REFRESH] [SETTING] [{window_title}] 使用參數更新視窗: {year} {race} {session}")
        
        try:
            # [TOOL] 新方法：直接更新子視窗的本地參數
            if hasattr(self.parent_window, 'update_local_parameters'):
                # 更新本地參數（這會自動更新標題）
                self.parent_window.update_local_parameters(year, race, session)
                
                # 調用視窗更新
                if hasattr(self.parent_window, 'update_current_window'):
                    self.parent_window.update_current_window()
                    
                logger.debug(f"[OK] [SETTING] 參數更新完成（新方法）: {year} {race} {session}")
                return
            
            # [TOOL] 舊方法向後兼容：直接調用更新
            logger.warning(f"[WARNING] [SETTING] 使用舊方法向後兼容模式")
            if hasattr(self.parent_window, 'update_current_window'):
                self.parent_window.update_current_window()
                logger.debug(f"[OK] [SETTING] 當前視窗數據更新完成（向後兼容模式）")
            else:
                logger.warning(f"[WARNING] [SETTING] 視窗沒有 update_current_window 方法")
                
        except Exception as e:
            logger.error(f"[ERROR] [SETTING] 更新當前視窗失敗: {e}")
            logger.debug(f"[INFO] [SETTING] 錯誤詳情: {type(e).__name__}: {str(e)}")
    
    def apply_settings(self, year, race, session, sync_windows):
        """應用設定到父視窗（已棄用，由新方法取代）"""
        # [TOOL] 此方法已被 update_current_window_only 和 apply_manual_settings 取代
        logger.warning(f"[WARNING] [SETTING] apply_settings 方法已棄用")
        pass
        
    def sync_to_other_windows(self, year, race, session):
        """同步參數到其他視窗（已棄用，避免命令混亂）"""
        # [TOOL] 移除此功能，避免MDI子視窗向主程式發送控制命令
        logger.warning(f"[WARNING] [SETTING] sync_to_other_windows 方法已停用 - 避免多視窗命令混亂")
        logger.debug(f"[TEST] [SETTING] 子視窗應僅接收主程式同步，不應發送控制命令")
        pass
        
    def update_current_window(self, year, race, session):
        """更新當前視窗的分析數據（已棄用，由新方法取代）"""
        # [TOOL] 此方法已被 update_current_window_only 取代
        logger.warning(f"[WARNING] [SETTING] update_current_window 方法已棄用")
        pass



# ========== ApiHealthWorker, ApiRuntimeWorker 已移至 windows/workers/api_workers.py ==========
