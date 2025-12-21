# -*- coding: utf-8 -*-
"""
PopoutSubWindow - MDI 子視窗類別
================================

從 f1t_gui_main.py 提取的 MDI 子視窗實現。
支援彈出功能、調整大小、參數同步等功能。
"""

import json
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QMdiSubWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QLabel, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor

from core.logger import get_logger
from core.gui_i18n import tr
from modules.gui.shared.season_calendar_provider import SeasonCalendarError, SeasonEvent
from windows.widgets import DraggableTitleBar, ResizableStandaloneWindow
from windows.workers import MainWindowParameterProvider
from windows.dialogs import WindowSettingsDialog

logger = get_logger(__name__)


def select_preferred_event(
    completed_events: List[SeasonEvent],
    upcoming_events: List[SeasonEvent],
) -> Optional[SeasonEvent]:
    """Return the preferred event for default selection."""
    if completed_events:
        return completed_events[-1]
    if upcoming_events:
        return upcoming_events[0]
    return None


class PopoutSubWindow(QMdiSubWindow):
    """支援彈出功能和調整大小的MDI子視窗 - 升級為通用模組容器"""
    
    # 添加自定義信號
    resized = pyqtSignal()  # 尺寸調整信號
    window_closed = pyqtSignal()  # 視窗關閉信號
    
    def __init__(self, title="", parent_mdi=None, analysis_module=None, 
                 sync_enabled=True, parameter_provider=None, global_signal_manager=None, **kwargs):
        super().__init__()
        #print(f"[START] DEBUG: Creating PopoutSubWindow '{title}'")
        self.parent_mdi = parent_mdi
        self.is_popped_out = False
        self.original_widget = None
        self.content_widget = None
        
        # [TOOL] 新增：模組支援
        self.analysis_module = analysis_module
        self._parameter_provider = parameter_provider
        
        # [DEBUG] 方案A調試：驗證 analysis_module 保存
        logger.debug(f"[POPOUT_INIT] Title: '{title}'")
        logger.debug(f"[POPOUT_INIT] analysis_module parameter: {type(analysis_module).__name__ if analysis_module else None}")
        logger.debug(f"[POPOUT_INIT] analysis_module id: {id(analysis_module) if analysis_module else 'None'}")
        if analysis_module and hasattr(analysis_module, 'analysis_type'):
            logger.debug(f"[POPOUT_INIT] analysis_module.analysis_type: {analysis_module.analysis_type}")
        logger.debug(f"[POPOUT_INIT] self.analysis_module stored: {type(self.analysis_module).__name__ if self.analysis_module else None}")
        logger.info(f"[POPOUT_INIT] PopoutSubWindow created: title='{title}', module={type(analysis_module).__name__ if analysis_module else None}")

        # 確保關閉後釋放資源並從父層列表移除
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        
        # [TOOL] 新增：本地參數存儲 (用於非同步狀態)
        self.local_year = "2025"
        self.local_race = "Japan"
        self.local_session = "R"
        self._season_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        
        # [TOOL] 修正：正確提取模組名稱
        self.module_name = self._extract_module_name_from_title(title)
        
        self.setWindowTitle(title)
        self.setObjectName("ProfessionalSubWindow")
        
        # 初始化同步設定狀態
        self.sync_enabled = sync_enabled  # 使用傳入的同步設定
        
        # 嘗試獲取主視窗引用
        self.main_window = None
        if parent_mdi:
            # 向上查找主視窗
            current_parent = parent_mdi.parent()
            while current_parent:
                if hasattr(current_parent, 'year_combo') and hasattr(current_parent, 'race_combo'):
                    self.main_window = current_parent
                    # [TOOL] 新增：設置參數提供者（如果沒有傳入的話）
                    if not self._parameter_provider:
                        self._parameter_provider = MainWindowParameterProvider(current_parent)
                    logger.debug(f"[LINK] [INIT] {title} 已找到主視窗引用")
                    break
                current_parent = current_parent.parent()
        
        # [TOOL] 新增：如果有模組，進行初始化
        if self.analysis_module and self._parameter_provider:
            self.analysis_module.parameter_provider = self._parameter_provider
            # 連接模組信號 - 修正：信號直接在模組上，不在 signals 屬性下
            if hasattr(self.analysis_module, 'module_error'):
                self.analysis_module.module_error.connect(self._handle_module_error)
            if hasattr(self.analysis_module, 'parameters_updated'):
                self.analysis_module.parameters_updated.connect(self._handle_parameters_updated)
                
            logger.debug(f"[SYNC] [INIT] {title} 已連接模組同步信號")
            
            # [FIX] 立即進行一次初始同步，確保模組獲得當前參數
            try:
                if hasattr(self.analysis_module, 'update_parameters'):
                    year = int(self._parameter_provider.get_current_year())
                    race = self._parameter_provider.get_current_race()
                    session = self._parameter_provider.get_current_session()
                    logger.debug(f"[SYNC] [INIT] 進行初始參數同步: {year} {race} {session}")
                    self.analysis_module.update_parameters(year, race, session)
            except Exception as e:
                logger.warning(f"[WARNING] [INIT] 初始同步失敗: {e}")
        
        # 初始化最小化狀態
        self.is_minimized = False
        self.original_geometry = None
        
        # [TOOL] [FIX] 確保調整大小相關屬性被初始化
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        # [TOOL] [FIX] 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
        # 🆕 初始化圖表更新處理器 (Phase 5.1 重構)
        from windows.managers import PopoutChartUpdater, PopoutCliHandler, PopoutResizeHandler
        self._chart_updater = PopoutChartUpdater(self)
        
        # 🆕 初始化 CLI 分析處理器 (Phase 5.2 重構)
        self._cli_handler = PopoutCliHandler(self)
        
        # 🆕 初始化調整大小處理器 (Phase 5.3 重構)
        self._resize_handler = PopoutResizeHandler(self, self.resize_detection_margin)
        
        logger.debug(f"[OK] [INIT] PopoutSubWindow '{title}' 初始化完成 - 包含調整大小支援")
    
    def _extract_module_name_from_title(self, title):
        """從標題中提取模組名稱"""
        try:
            # 處理各種可能的標題格式
            if title.startswith("[RAIN]"):
                return "Rain Analysis"
            elif title.startswith("[LAP]"):
                return "Lap Analysis" 
            elif title.startswith("[COMPARE]"):
                return "Comparison Analysis"
            elif title.startswith("[TELEMETRY]"):
                return "Race Overview"
            elif "_" in title:
                # 新格式：模組名稱_年份_賽事_賽段
                module_part = title.split('_')[0]
                # 處理帶圖標的模組名稱，如 "⚡ 速度分析" -> "速度分析"
                if " " in module_part and not module_part.startswith("["):
                    parts = module_part.split(" ")
                    if len(parts) >= 2:
                        return " ".join(parts[1:])  # 移除圖標，保留模組名稱
                return module_part
            elif " - " in title:
                # 舊格式：[TAG] 模組名稱 - 詳細資訊
                if "]" in title:
                    # 移除標籤部分
                    without_tag = title.split("]", 1)[1].strip()
                    # 取 " - " 之前的部分
                    return without_tag.split(" - ")[0].strip()
                else:
                    return title.split(" - ")[0].strip()
            else:
                # 純模組名稱
                return title.strip()
                
        except Exception as e:
            logger.warning(f"[WARNING] [TITLE] 提取模組名稱失敗: {e}, 使用原標題: {title}")
            return title
        
    def _handle_module_error(self, error_message):
        """處理模組錯誤"""
        logger.error(f"[ERROR] [MODULE] {self.windowTitle()} 模組錯誤: {error_message}")
    
    def _handle_parameters_updated(self, params):
        """處理模組參數更新"""
        logger.debug(f"[REFRESH] [MODULE] {self.windowTitle()} 參數已更新: {params}")
    
    def update_current_window(self):
        """更新當前視窗 - 委託給模組處理"""
        logger.debug(f"[UPDATE_DEBUG] ========== 視窗更新請求 ==========")
        logger.debug(f"[UPDATE_DEBUG] 視窗標題: {self.windowTitle()}")
        logger.debug(f"[UPDATE_DEBUG] 是否有 analysis_module: {self.analysis_module is not None}")
        logger.debug(f"🚨 [SYNC_DEBUG] sync_enabled 值: {getattr(self, 'sync_enabled', 'N/A')}")
        logger.debug(f"🚨 [SYNC_DEBUG] _parameter_provider 存在: {hasattr(self, '_parameter_provider') and self._parameter_provider is not None}")
        
        if self.analysis_module:
            logger.debug(f"[UPDATE_DEBUG] 🎯 使用新版模組更新邏輯")
            # 如果有模組，委託給模組處理
            try:
                params = {}
                if self.sync_enabled and self._parameter_provider:
                    # 同步模式：使用主視窗參數
                    logger.debug(f"🟢 [SYNC_DEBUG] 同步模式啟用 - 使用主視窗參數")
                    params = {
                        'year': int(self._parameter_provider.get_current_year()),  # 轉換為int
                        'race': self._parameter_provider.get_current_race(),
                        'session': self._parameter_provider.get_current_session()
                    }
                    logger.debug(f"🟢 [SYNC_DEBUG] 主視窗參數: {params}")
                    # 更新本地參數
                    self.local_year = str(params['year'])  # 本地參數保持字符串
                    self.local_race = params['race'] 
                    self.local_session = params['session']
                else:
                    # 非同步模式：使用本地參數
                    logger.debug(f"🔴 [SYNC_DEBUG] 同步模式停用 - 使用本地參數")
                    logger.debug(f"🔴 [SYNC_DEBUG] 本地參數: year={self.local_year}, race={self.local_race}, session={self.local_session}")
                    params = {
                        'year': int(self.local_year),  # 轉換為int
                        'race': self.local_race,
                        'session': self.local_session
                    }
                
                # 更新標題
                self.update_window_title()
                
                logger.debug(f"[REFRESH] [{self.windowTitle()}] 更新視窗數據: {params['year']} {params['race']} {params['session']}")
                
                # [TOOL] 重新載入模組而不是委託更新
                success = self.analysis_module.update_parameters(**params)
                if success:
                    logger.debug(f"[OK] [MODULE] {self.windowTitle()} 模組更新成功")
                else:
                    logger.warning(f"[WARNING] [MODULE] {self.windowTitle()} 模組更新失敗")
                return success
                
            except Exception as e:
                logger.error(f"[ERROR] [MODULE] {self.windowTitle()} 更新異常: {e}")
                return False
        else:
            # 舊版模式：直接調用原有邏輯
            logger.debug(f"[UPDATE_DEBUG] ⚠️ 使用舊版更新邏輯")
            logger.debug(f"[UPDATE_DEBUG] 原因: analysis_module 為 None")
            logger.warning(f"[WARNING] [LEGACY] {self.windowTitle()} 使用舊版更新模式")
            return self._legacy_update_current_window()
    
    def update_window_title(self):
        """更新視窗標題 - 確保使用模組的當前參數"""
        try:
            # 如果有 analysis_module，使用模組的 get_window_title 方法
            if self.analysis_module and hasattr(self.analysis_module, 'get_window_title'):
                # ✅ [FIX] 優先從模組獲取當前參數（確保同步）
                if hasattr(self.analysis_module, 'current_year'):
                    year = self.analysis_module.current_year
                    race = self.analysis_module.current_race
                    session = self.analysis_module.current_session
                else:
                    # 備選：使用本地參數
                    year = str(self.local_year)
                    race = self.local_race
                    session = self.local_session
                
                # 傳遞當前參數給模組的 get_window_title 方法
                new_title = self.analysis_module.get_window_title(year, race, session)
                logger.debug(f"[TITLE] [MODULE] 使用模組標題: {new_title}")
                logger.debug(f"[TITLE] [MODULE] 參數: {year} {race} {session}")
            else:
                # 舊版邏輯：保持原始格式，只更新參數部分
                if hasattr(self, 'original_title') and self.original_title:
                    # 保持原始標題格式，只添加參數後綴
                    new_title = f"{self.original_title}_{self.local_year}_{self.local_race}_{self.local_session}"
                else:
                    # 最後備選方案
                    new_title = f"{self.module_name}_{self.local_year}_{self.local_race}_{self.local_session}"
                logger.debug(f"[TITLE] [LEGACY] 使用舊版標題格式: {new_title}")
            
            self.setWindowTitle(new_title)
            
            # 同時更新自定義標題欄
            if hasattr(self, 'title_bar') and self.title_bar:
                self.title_bar.update_title(new_title)
                
            logger.debug(f"[LABEL] [TITLE] 標題已更新: {new_title}")
            
        except Exception as e:
            logger.error(f"[ERROR] [TITLE] 標題更新失敗: {e}")
    
    def toggle_x_sync(self, enabled: Optional[bool] = None) -> bool:
        """切換或設定 X 軸同步狀態，支援還原快照時直接指定狀態。"""
        if not hasattr(self, 'title_bar') or not self.title_bar:
            if enabled is None:
                self.sync_enabled = not getattr(self, 'sync_enabled', True)
            else:
                self.sync_enabled = bool(enabled)
            return self.sync_enabled

        if enabled is None:
            self.title_bar.sync_btn.toggle()
        else:
            desired_state = bool(enabled)
            if self.title_bar.sync_btn.isChecked() != desired_state:
                self.title_bar.sync_btn.setChecked(desired_state)
            self.title_bar.toggle_x_sync()

        if hasattr(self.title_bar, 'get_sync_status'):
            self.sync_enabled = self.title_bar.get_sync_status()
        else:
            self.sync_enabled = getattr(self, 'sync_enabled', True)
        return self.sync_enabled

    def update_local_parameters(self, year=None, race=None, session=None):
        """更新本地參數（用於非同步模式）"""
        if year is not None:
            self.local_year = year
        if race is not None:
            self.local_race = race
        if session is not None:
            self.local_session = session
            
        # 立即更新標題
        self.update_window_title()
        
        logger.debug(f"[REFRESH] [LOCAL] {self.windowTitle()} 本地參數已更新: {self.local_year} {self.local_race} {self.local_session}")
    
    def _get_calendar_events_for_year(self, year: int) -> List[SeasonEvent]:
        if self.main_window and hasattr(self.main_window, "_get_calendar_events"):
            return self.main_window._get_calendar_events(year)
        if self.main_window and hasattr(self.main_window, "_season_provider"):
            try:
                return self.main_window._season_provider.get_completed_events(year)
            except SeasonCalendarError as exc:
                logger.debug(f"[CALENDAR] 子視窗取得日曆失敗: {exc}")
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
                plain_label = self.main_window._strip_race_display(label) if self.main_window else label
                if plain_label and plain_label not in self._display_to_race_key:
                    self._display_to_race_key[plain_label] = event.race_key

    def _select_race_by_key(self, race_key: Optional[str]) -> None:
        if not hasattr(self, 'race_combo') or not self.race_combo or race_key is None:
            return
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == race_key:
                self.race_combo.setCurrentIndex(index)
                return

    def get_selected_event(self) -> Optional[SeasonEvent]:
        if not hasattr(self, 'race_combo') or not self.race_combo:
            return None
        data = self.race_combo.currentData()
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText()
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
            race_key = self._display_to_race_key.get(race_key, race_key)
        return self._season_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText() if hasattr(self, 'race_combo') else ''
        race_key = self._display_to_race_key.get(display_text)
        if not race_key and self.main_window:
            race_key = self.main_window._strip_race_display(display_text)
        return race_key or self.local_race or "Unknown"

    def get_selected_session_code(self) -> str:
        if not hasattr(self, 'session_combo') or not self.session_combo:
            return self.local_session or "R"
        data = self.session_combo.currentData()
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText()
        return text if text else (self.local_session or "R")

    def _update_session_combo(self, event: Optional[SeasonEvent] = None, preserve_session_code: Optional[str] = None) -> None:
        if not hasattr(self, 'session_combo') or not self.session_combo:
            return

        event = event or self.get_selected_event()
        self.session_combo.blockSignals(True)
        self.session_combo.clear()

        if isinstance(event, SeasonEvent) and event.sessions:
            codes = []
            for session in event.sessions:
                self.session_combo.addItem(session.code, session)
                codes.append(session.code)

            target_code = preserve_session_code or self.local_session or ("R" if "R" in codes else (codes[0] if codes else None))
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
            target_code = preserve_session_code or self.local_session
            if target_code:
                index = self.session_combo.findText(target_code)
                if index >= 0:
                    self.session_combo.setCurrentIndex(index)

        self.session_combo.blockSignals(False)



    def get_current_parameters(self):
        """獲取當前參數"""
        if self.sync_enabled and self._parameter_provider:
            # 同步模式：返回主視窗參數
            return {
                'year': self._parameter_provider.get_current_year(),
                'race': self._parameter_provider.get_current_race(), 
                'session': self._parameter_provider.get_current_session()
            }
        else:
            # 非同步模式：返回本地參數
            return {
                'year': self.local_year,
                'race': self.local_race,
                'session': self.local_session
            }
    
    def _legacy_update_current_window(self):
        """舊版視窗更新邏輯 - 保持向後相容性"""
        try:
            # 嘗試從主視窗獲取參數（舊版方式）
            year = "2025"
            race = "Japan" 
            session = "R"
            
            if self._parameter_provider:
                year = self._parameter_provider.get_current_year()
                race = self._parameter_provider.get_current_race()
                session = self._parameter_provider.get_current_session()
            
            logger.debug(f"[REFRESH] [LEGACY] {self.windowTitle()} 舊版更新: {year} {race} {session}")
            
            # 如果內容widget有更新方法，調用它
            if self.content_widget and hasattr(self.content_widget, 'update'):
                self.content_widget.update()
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] [LEGACY] 舊版更新失敗: {e}")
            return False
        
        # [TEST][HOT] 設置最小尺寸防止縮小到無法使用 - 已取消限制
        # self.setMinimumSize(250, 150)  # 移除最小尺寸限制
        #print(f"[LOCK] 最小尺寸限制已取消")
        
        # [HOT] 隱藏所有 MDI 子窗口的標題列
        # [修改] 保留邊框，只隱藏標題列
        # 使用自定義方式隱藏標題列但保留邊框
        self.setWindowFlags(Qt.SubWindow)  # 移除 FramelessWindowHint 以保留邊框
        #print(f"[LABEL] MDI子窗口 - 保留邊框，隱藏標題列")
        
        # 設置邊距以適應邊框
        self.setContentsMargins(2, 2, 2, 2)  # 為邊框留出空間
        
        # [HOT] 強化邊框樣式設置 - 確保邊框可見
        subwindow_qss = """
            PopoutSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 加粗邊框以確保可見 */
                border-radius: 2px;
            }
            QMdiSubWindow {
                background-color: #FFFFFF;
                border: 2px solid #666666;
                margin: 0px;
                padding: 2px;
                border-radius: 2px;
            }
            QMdiSubWindow[objectName="ProfessionalSubWindow"] {
                background-color: #FFFFFF;
                border: 2px solid #666666;  /* 強化邊框 */
                border-radius: 2px;
            }
            
            /* 隱藏標題列但保留邊框 */
            QMdiSubWindow::title {
                height: 0px;
                margin: 0px;
                padding: 0px;
                background: transparent;
                border: none;
            }
            
            /* 接收同步按鈕 - 紅綠狀態指示 (子窗口專用) */
            #SyncButton {
                background-color: #FF4444;  /* 預設紅色 - 獨立模式 */
                color: #FFFFFF;
                border: 1px solid #CC0000;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SyncButton:hover {
                background-color: #FF6666;  /* 紅色懸停 */
            }
            #SyncButton:pressed {
                background-color: #CC0000;  /* 紅色按下 */
            }
            #SyncButton:checked {
                background-color: #00CC00;  /* 綠色 - 接收同步 */
                border: 1px solid #009900;
            }
            #SyncButton:checked:hover {
                background-color: #00FF00;  /* 綠色懸停 */
            }
            
            /* 個別連動按鈕 - 藍色主題 */
            #LinkageButton {
                background-color: #2196F3;  /* 藍色 - 連動啟用 */
                color: white;
                border: 1px solid #1976D2;
                border-radius: 3px;
                font-size: 8px;
                font-weight: bold;
                text-align: center;
            }
            #LinkageButton:hover {
                background-color: #42A5F5;  /* 藍色懸停 */
            }
            #LinkageButton:pressed {
                background-color: #1565C0;  /* 藍色按下 */
            }
            #LinkageButton:!checked {
                background-color: #9E9E9E;  /* 灰色 - 連動停用 */
                border: 1px solid #757575;
            }
            #LinkageButton:!checked:hover {
                background-color: #BDBDBD;  /* 灰色懸停 */
            }
            
            /* 車手與圈數同步按鈕 - 紫色主題（遙測模組專用） */
            #DriverLapSyncButton {
                background-color: #9C27B0;  /* 紫色 - 同步啟用 */
                color: white;
                border: 1px solid #7B1FA2;
                border-radius: 3px;
                font-size: 8px;
                font-weight: bold;
                text-align: center;
            }
            #DriverLapSyncButton:hover {
                background-color: #AB47BC;  /* 紫色懸停 */
            }
            #DriverLapSyncButton:pressed {
                background-color: #6A1B9A;  /* 紫色按下 */
            }
            #DriverLapSyncButton:!checked {
                background-color: #9E9E9E;  /* 灰色 - 同步停用 */
                border: 1px solid #757575;
            }
            #DriverLapSyncButton:!checked:hover {
                background-color: #BDBDBD;  /* 灰色懸停 */
            }
            
            /* 視窗控制按鈕 - 與主視窗保持一致 */
            #WindowControlButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #D0D0D0;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #WindowControlButton:hover {
                background-color: #E0E0E0;
            }
            #WindowControlButton:pressed {
                background-color: #D0D0D0;
            }
            
            /* 設定按鈕 */
            #SettingsButton {
                background-color: #F0F0F0;
                color: #333333;
                border: 1px solid #CCCCCC;
                border-radius: 0px;
                font-size: 8pt;
                font-weight: bold;
            }
            #SettingsButton:hover {
                background-color: #E8E8E8;
            }
            #SettingsButton:pressed {
                background-color: #D8D8D8;
            }
        """
        self.setStyleSheet(subwindow_qss)
        #print(f"[OK] Direct QSS applied to subwindow: {len(subwindow_qss)} characters")
        #print(f"[DESIGN] QSS content: {subwindow_qss[:100]}...")
        
        # 調整大小相關屬性
        self.resize_margin = 3  # 視覺邊框寬度 (3像素，與QSS邊框一致)
        self.resize_detection_margin = 10  # 實際可操作區域 (10像素)
        self.resizing = False
        self.resize_direction = None
        
        # 🔧 修復洩漏: 預創建靜態游標對象，避免重複創建
        self._cursor_arrow = Qt.ArrowCursor
        self._cursor_size_ver = Qt.SizeVerCursor
        self._cursor_size_hor = Qt.SizeHorCursor
        self._cursor_size_fdiag = Qt.SizeFDiagCursor
        self._cursor_size_bdiag = Qt.SizeBDiagCursor
        self._current_cursor = None  # 追蹤當前游標，避免重複設置
        
        #print(f"📏 Resize margins - Visual: {self.resize_margin}px, Detection: {self.resize_detection_margin}px")
        
        # 強制啟用滑鼠追蹤
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_Hover, True)
        self.setAttribute(Qt.WA_MouseTracking, True)
        
    def mousePressEvent(self, event):
        """滑鼠按下事件 - 處理調整大小"""
        if event.button() == Qt.LeftButton:
            self.resize_direction = self.get_resize_direction(event.pos())
            if self.resize_direction:
                self.resizing = True
                self.resize_start_pos = event.globalPos()
                self.resize_start_geometry = self.geometry()
                event.accept()
                return
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        """滑鼠移動事件 - 處理調整大小和游標"""
        if self.resizing and self.resize_direction:
            self.perform_resize(event.globalPos())
            event.accept()
            return
        
        # 🔧 防禦性檢查: 確保游標屬性已初始化
        if not hasattr(self, '_current_cursor'):
            super().mouseMoveEvent(event)
            return
            
        # 更新游標 - 即使沒有在調整也要檢查
        direction = self.get_resize_direction(event.pos())
        
        # 🔧 修復洩漏: 只在游標真正改變時才設置，避免重複創建游標對象
        new_cursor = None
        if direction:
            # 取消上方調整大小功能，移除 'top' 相關游標
            if direction in ['bottom']:  # 只保留 bottom，移除 top
                new_cursor = self._cursor_size_ver
            elif direction in ['left', 'right']:
                new_cursor = self._cursor_size_hor
            elif direction in ['bottom-right']:  # 移除 top-left
                new_cursor = self._cursor_size_fdiag
            elif direction in ['bottom-left']:  # 移除 top-right
                new_cursor = self._cursor_size_bdiag
            event.accept()  # 接受事件，防止被覆蓋
        else:
            new_cursor = self._cursor_arrow
        
        # 🔧 只在游標改變時才設置，減少 setCursor 調用次數
        if new_cursor != self._current_cursor:
            self.setCursor(new_cursor)
            self._current_cursor = new_cursor
            
        # [HOT] 重要：讓事件傳遞給父類以保持拖動功能
        super().mouseMoveEvent(event)
        
    def enterEvent(self, event):
        """滑鼠進入事件"""
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """滑鼠離開事件 - 恢復箭頭游標"""
        # 🔧 修復洩漏: 只在需要時設置游標（防禦性檢查）
        if hasattr(self, '_current_cursor') and hasattr(self, '_cursor_arrow'):
            if self._current_cursor != self._cursor_arrow:
                self.setCursor(self._cursor_arrow)
                self._current_cursor = self._cursor_arrow
        else:
            # 如果屬性未初始化（極少數情況），使用標準游標
            self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)
        
    def mouseReleaseEvent(self, event):
        """滑鼠釋放事件 - 結束調整大小"""
        if event.button() == Qt.LeftButton:
            self.resizing = False
            self.resize_direction = None
            # 🔧 修復洩漏: 只在需要時設置游標（防禦性檢查）
            if hasattr(self, '_current_cursor') and hasattr(self, '_cursor_arrow'):
                if self._current_cursor != self._cursor_arrow:
                    self.setCursor(self._cursor_arrow)
                    self._current_cursor = self._cursor_arrow
            else:
                # 如果屬性未初始化（極少數情況），使用標準游標
                self.setCursor(Qt.ArrowCursor)
            event.accept()
            return
        super().mouseReleaseEvent(event)
        
    def get_resize_direction(self, pos):
        """判斷調整方向 - 使用10像素檢測區域（取消上方調整大小）"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        detection_margin = self.resize_detection_margin  # 10像素檢測區域
        
        # 角落區域 (優先判斷) - 取消上方相關的角落調整
        # if x <= detection_margin and y <= detection_margin:
        #     return 'top-left'
        # elif x >= w - detection_margin and y <= detection_margin:
        #     return 'top-right'
        if x <= detection_margin and y >= h - detection_margin:
            return 'bottom-left'
        elif x >= w - detection_margin and y >= h - detection_margin:
            return 'bottom-right'
        # 邊緣區域 - 取消上方調整，保留左、右、下
        # elif y <= detection_margin:
        #     return 'top'
        elif y >= h - detection_margin:
            return 'bottom'
        elif x <= detection_margin:
            return 'left'
        elif x >= w - detection_margin:
            return 'right'
        
        return None
        
    def perform_resize(self, global_pos):
        """執行調整大小"""
        if not self.resize_direction:
            return
            
        delta = global_pos - self.resize_start_pos
        old_geometry = self.resize_start_geometry
        
        new_x = old_geometry.x()
        new_y = old_geometry.y()
        new_width = old_geometry.width()
        new_height = old_geometry.height()
        
        # 根據方向調整
        if 'left' in self.resize_direction:
            new_x = old_geometry.x() + delta.x()
            new_width = old_geometry.width() - delta.x()
        elif 'right' in self.resize_direction:
            new_width = old_geometry.width() + delta.x()
            
        # 取消 top 調整，只保留 bottom
        # if 'top' in self.resize_direction:
        #     new_y = old_geometry.y() + delta.y()
        #     new_height = old_geometry.height() - delta.y()
        if 'bottom' in self.resize_direction:
            new_height = old_geometry.height() + delta.y()
            
        # 限制最小大小
        min_width, min_height = 200, 150
        if new_width < min_width:
            if 'left' in self.resize_direction:
                new_x = old_geometry.x() + old_geometry.width() - min_width
            new_width = min_width
            
        if new_height < min_height:
            # 取消 top 調整功能
            # if 'top' in self.resize_direction:
            #     new_y = old_geometry.y() + old_geometry.height() - min_height
            new_height = min_height
            
        # 限制在MDI區域內
        if self.parent_mdi:
            mdi_rect = self.parent_mdi.rect()
            if new_x < 0:
                new_x = 0
            if new_y < 0:
                new_y = 0
            if new_x + new_width > mdi_rect.width():
                if 'right' in self.resize_direction:
                    new_width = mdi_rect.width() - new_x
                else:
                    new_x = mdi_rect.width() - new_width
            if new_y + new_height > mdi_rect.height():
                if 'bottom' in self.resize_direction:
                    new_height = mdi_rect.height() - new_y
                else:
                    new_y = mdi_rect.height() - new_height
            
        # 應用新的幾何形狀
        self.setGeometry(new_x, new_y, new_width, new_height)
        
    def paintEvent(self, event):
        """繪製事件 - 使用QSS邊框，只繪製右下角提示"""
        #print(f"[DESIGN] DEBUG: PopoutSubWindow paintEvent called for {self.windowTitle()}")
        #print(f"📐 Window size: {self.width()}x{self.height()}")
        #print(f"[PIN] Window position: ({self.x()}, {self.y()})")
        #print(f"🔲 Window rect: {self.rect()}")
        #print(f"[THEATER] Window frameless: {self.windowFlags() & Qt.FramelessWindowHint}")
        #print(f"[DESIGN] Self QSS length: {len(self.styleSheet())}")
        #print(f"🏠 Parent QSS length: {len(self.parent().styleSheet()) if self.parent() else 'No parent'}")
        
        # 調用父類方法繪製基本內容
        super().paintEvent(event)
        
        # 只繪製右下角調整提示
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        w, h = self.width(), self.height()
        
        # 右下角調整提示 (白色)
        corner_size = 8
        corner_color = QColor(255, 255, 255, 120)
        painter.fillRect(
            w - corner_size, 
            h - corner_size, 
            corner_size, 
            corner_size, 
            corner_color
        )
        
        # 繪製右下角調整線條 (白色)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        for i in range(3):
            offset = 2 + i * 2
            painter.drawLine(
                w - offset, h - 2,
                w - 2, h - offset
            )
            
        # 在四個角落添加小的調整提示 (2像素白色方塊)
        corner_indicator_size = 2
        corner_indicator_color = QColor(255, 255, 255, 150)
        
        # 左上角
        painter.fillRect(0, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右上角  
        painter.fillRect(w - corner_indicator_size, 0, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 左下角
        painter.fillRect(0, h - corner_indicator_size, corner_indicator_size, corner_indicator_size, corner_indicator_color)
        # 右下角已經有了更明顯的提示
        
    def setWidget(self, widget):
        """設置內容小部件並添加彈出按鈕"""
        #print(f"[TOOL] DEBUG: PopoutSubWindow.setWidget called for {self.windowTitle()}")
        
        # 創建包裝容器
        wrapper = QWidget()
        wrapper.setObjectName("SubWindowWrapper")
        wrapper_layout = QVBoxLayout(wrapper)
        
        # 標題欄不需要邊距，應該延伸到邊緣
        wrapper_layout.setContentsMargins(0, 0, 0, 0)  # 移除所有邊距
        wrapper_layout.setSpacing(0)
        
        # 確保wrapper本身也沒有邊距
        wrapper.setStyleSheet("""
            #SubWindowWrapper {
                margin: 0px;
                padding: 0px;
                border: none;
                background-color: transparent;
            }
        """)
        
        #print(f"[PACKAGE] Wrapper margins set to: 0px (標題欄延伸到邊緣)")
        #print(f"[DESIGN] Wrapper ObjectName: {wrapper.objectName()}")
        
        # 創建可拖拽的自定義標題欄
        self.title_bar = DraggableTitleBar(self, self.windowTitle())
        wrapper_layout.addWidget(self.title_bar)
        
        # [DRIVER_LAP_SYNC] 檢查是否為遙測模組，顯示車手與圈數同步按鈕
        if self.analysis_module and hasattr(self.analysis_module, 'sync_driver_lap_enabled'):
            # 這是遙測模組（速度/RPM/煞車/油門），顯示專用按鈕
            self.title_bar.driver_lap_sync_btn.setVisible(True)
            # 從模組讀取初始同步狀態
            initial_sync_state = getattr(self.analysis_module, 'sync_driver_lap_enabled', True)
            self.title_bar.driver_lap_sync_btn.setChecked(initial_sync_state)
            logger.debug(f"[DRIVER_LAP_SYNC] 遙測模組檢測到，顯示車手與圈數同步按鈕，初始狀態: {initial_sync_state}")
        
        # 確保標題欄使用正確的 QSS
        self.title_bar.setStyleSheet(self.styleSheet())
        #print(f"[DESIGN] DEBUG: Applied QSS to CustomTitleBar: {len(self.styleSheet())} characters")
        
        # 創建內容容器，為內容添加邊距
        content_container = QWidget()
        content_layout = QVBoxLayout(content_container)
        margin = getattr(self, 'resize_margin', 3)  # 安全訪問，預設3像素
        content_layout.setContentsMargins(margin, margin, margin, margin)
        content_layout.setSpacing(0)
        content_layout.addWidget(widget)
        
        # 添加內容容器到主layout
        wrapper_layout.addWidget(content_container)
        
        # 保存內容widget引用
        self.content_widget = widget
        
        # 確保包裝器不攔截滑鼠事件
        wrapper.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        wrapper.setMouseTracking(True)
        
        # 設置包裝器為主widget
        super().setWidget(wrapper)
        
        # [移除] 不再設置最小尺寸限制，允許完全自由縮放
        # self.setMinimumSize(250, 150) - 已移除
        #print(f"[LOCK] 移除尺寸限制，允許自由縮放")
        
        # [移除] 不再計算標題欄最小高度限制
        # title_height = self.title_bar.height() if hasattr(self, 'title_bar') else 20
        # min_height = max(150, title_height + 100) - 已移除
        #print(f"[LOCK] 無尺寸限制")
        
    def setMinimumSize(self, *args):
        """覆寫 setMinimumSize 來追蹤誰在修改最小尺寸"""
        if len(args) == 1:  # QSize 參數
            size = args[0]
            #print(f"[ALERT] setMinimumSize 被調用: {size.width()}x{size.height()}")
        elif len(args) == 2:  # width, height 參數
            width, height = args
            #print(f"[ALERT] setMinimumSize 被調用: {width}x{height}")
            
        # 強制確保最小尺寸不小於我們的限制
        if len(args) == 2:
            width, height = args
            width = max(width, 250)
            height = max(height, 150)
            args = (width, height)
            #print(f"[LOCK] 強制調整最小尺寸至: {width}x{height}")
        elif len(args) == 1:
            size = args[0]
            width = max(size.width(), 250)
            height = max(size.height(), 150)
            from PyQt5.QtCore import QSize
            args = (QSize(width, height),)
            #print(f"[LOCK] 強制調整最小尺寸至: {width}x{height}")
            
        super().setMinimumSize(*args)
        
    def minimumSize(self):
        """移除強制最小尺寸，返回系統預設"""
        # 不再強制返回固定尺寸，讓系統自然處理
        return super().minimumSize()
        
    def minimumSizeHint(self):
        """移除強制最小尺寸提示，返回系統預設"""
        # 不再強制返回固定尺寸提示，讓系統自然處理
        return super().minimumSizeHint()
        
    def resizeEvent(self, event):
        """處理窗口縮放事件，確保不會小於最小尺寸"""
        #print(f"[TOOL] PopoutSubWindow: resizeEvent 被調用，新尺寸: {event.size().width()}x{event.size().height()}")
        super().resizeEvent(event)
        
        # [HOT] 強制檢查最小尺寸限制（不依賴 minimumSize()）
        MIN_WIDTH = 250
        MIN_HEIGHT = 150
        
        current_size = self.size()
        
        #print(f"[LOCK] PopoutSubWindow: 強制最小尺寸: {MIN_WIDTH}x{MIN_HEIGHT}")
        #print(f"[LOCK] PopoutSubWindow: 當前尺寸: {current_size.width()}x{current_size.height()}")
        
        needs_resize = False
        new_width = current_size.width()
        new_height = current_size.height()
        
        if current_size.width() < MIN_WIDTH:
            new_width = MIN_WIDTH
            needs_resize = True
            #print(f"[WARNING] 寬度低於最小值，調整: {current_size.width()} -> {new_width}")
            
        if current_size.height() < MIN_HEIGHT:
            new_height = MIN_HEIGHT
            needs_resize = True
            #print(f"[WARNING] 高度低於最小值，調整: {current_size.height()} -> {new_height}")
        
        if needs_resize:
            #print(f"[LOCK] 即將強制調整至最小尺寸: {new_width}x{new_height}")
            # 使用 QTimer 延遲調整，避免與Qt內部的調整衝突
            QTimer.singleShot(0, lambda: self._force_resize(new_width, new_height))
        
        # 發射調整大小信號
        self.resized.emit()
        #print(f"📡 PopoutSubWindow: 發射 resized 信號")
        
    def _force_resize(self, width, height):
        """強制調整尺寸"""
        #print(f"💥 強制調整視窗尺寸至: {width}x{height}")
        self.resize(width, height)
        # 也嘗試更新幾何形狀
        current_pos = self.pos()
        self.setGeometry(current_pos.x(), current_pos.y(), width, height)
    
    def showEvent(self, event):
        """窗口顯示時確保最小尺寸"""
        super().showEvent(event)
        min_size = self.minimumSize()
        if self.size().width() < min_size.width() or self.size().height() < min_size.height():
            self.resize(min_size)
            #print(f"[LOCK] showEvent 強制調整至最小尺寸: {min_size.width()}x{min_size.height()}")

    def create_window_control_panel(self):
        """創建視窗控制面板"""
        control_panel = QWidget()
        control_panel.setObjectName("WindowControlPanel")
        control_panel.setFixedHeight(35)
        control_layout = QHBoxLayout(control_panel)
        control_layout.setContentsMargins(5, 3, 5, 3)
        control_layout.setSpacing(10)
        
        # 視窗同步名稱勾選框
        self.sync_windows_checkbox = QCheckBox(tr("sync_other_windows", "[LINK] Sync Other Windows"))
        self.sync_windows_checkbox.setObjectName("SyncWindowsCheckbox")
        self.sync_windows_checkbox.setChecked(True)
        self.sync_windows_checkbox.setToolTip(tr("sync_windows_tooltip", "Sync other windows (Race/Session/Year sync)"))
        self.sync_windows_checkbox.toggled.connect(self.on_sync_windows_toggled)
        control_layout.addWidget(self.sync_windows_checkbox)
        
        control_layout.addStretch()
        
        # 年份選擇器
        year_label = QLabel(tr("year"))
        year_label.setObjectName("ControlLabel")
        control_layout.addWidget(year_label)
        
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("AnalysisComboBox")
        self.year_combo.addItems([str(year) for year in range(2020, 2027)])
        self.year_combo.setCurrentText("2025")
        self.year_combo.setFixedWidth(70)
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        control_layout.addWidget(self.year_combo)
        
        # 賽事選擇器
        race_label = QLabel(tr("race"))
        race_label.setObjectName("ControlLabel")
        control_layout.addWidget(race_label)
        
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("AnalysisComboBox")
        # [TOOL] 修復: 使用動態賽事列表而非硬編碼
        current_year = self.year_combo.currentText()
        self.update_races_for_year(current_year)
        self._select_race_by_key(self.local_race)
        self.race_combo.setFixedWidth(250)
        self.race_combo.currentTextChanged.connect(self.on_race_changed)
        control_layout.addWidget(self.race_combo)
        
        # 賽段選擇器
        session_label = QLabel(tr("session"))
        session_label.setObjectName("ControlLabel")
        control_layout.addWidget(session_label)
        
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("AnalysisComboBox")
        self._update_session_combo(preserve_session_code=self.local_session)
        self.session_combo.setFixedWidth(70)
        self.session_combo.currentTextChanged.connect(self.on_session_changed)
        control_layout.addWidget(self.session_combo)
        
        # 重新分析按鈕
        reanalyze_btn = QPushButton("R")
        reanalyze_btn.setObjectName("ReanalyzeButton")
        reanalyze_btn.setFixedSize(25, 25)
        reanalyze_btn.setToolTip("Reanalyze")
        reanalyze_btn.clicked.connect(self.perform_reanalysis)
        control_layout.addWidget(reanalyze_btn)
        
        return control_panel
        
    def on_sync_windows_toggled(self, checked):
        """處理視窗連動開關
        
        同時控制：
        1. sync_enabled - 是否接受來自主程式的批次參數更新
        2. sync_to_other_windows - 是否主動同步到其他視窗
        """
        window_title = self.windowTitle()
        status = "enabled" if checked else "disabled"
        
        # 🔒 [SYNC_FIX] 關鍵修復：更新 sync_enabled 屬性
        # 這會讓批次更新邏輯 (lap_analysis_updater.py) 能正確跳過此視窗
        self.sync_enabled = checked
        logger.debug(f"[SYNC] [{window_title}] sync_enabled = {checked}, sync {status}")
        
        # 如果啟用連動，同步當前參數到其他視窗
        if checked:
            self.sync_to_other_windows()
        
    def on_year_changed(self, year):
        """處理年份變更"""
        window_title = self.windowTitle()
        #print(f"[CALENDAR] [{window_title}] 年份變更為: {year}")
        
        # [TOOL] 新增: 動態更新賽事列表
        self.update_races_for_year(year)

        self.local_year = str(year)
        
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
        
        # Debounce telemetry refresh instead of issuing immediate updates.
        self._schedule_parameter_broadcast("year_changed")
            
    def on_race_changed(self, race):
        """處理賽事變更"""
        # ✅ 調試點 1: 方法入口
        logger.info(f"🔵 [DEBUG]    on_race_changed 被調用: race={race}")
        logger.debug(f"🔵 [DEBUG]    on_race_changed 被調用: race={race}")
        
        window_title = self.windowTitle()
        #print(f"[FINISH] [{window_title}] 賽事變更為: {race}")
        
        event = self.get_selected_event()
        if event:
            self.local_race = event.race_key
        else:
            canonical = self._display_to_race_key.get(race)
            if canonical:
                self.local_race = canonical

        self._update_session_combo()

        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
        
        # Debounced parameter broadcast for race change
        logger.info("🔵 [DEBUG]    on_race_changed - scheduling parameter broadcast")
        logger.debug("🔵 [DEBUG]    on_race_changed - scheduling parameter broadcast")
        self._schedule_parameter_broadcast("race_changed")

            
    def on_session_changed(self, session):
        """處理賽段變更"""
        # ✅ 調試點 1: 方法入口
        logger.info(f"🔵 [DEBUG]    on_session_changed 被調用: session={session}")
        logger.debug(f"🔵 [DEBUG]    on_session_changed 被調用: session={session}")
        
        window_title = self.windowTitle()
        #print(f"[F1] [{window_title}] 賽段變更為: {session}")
        
        self.local_session = self.get_selected_session_code()

        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
        else:
            self.update_current_window()
        
        # Debounced parameter broadcast for session change
        logger.info("🔵 [DEBUG]    on_session_changed - scheduling parameter broadcast")
        logger.debug("🔵 [DEBUG]    on_session_changed - scheduling parameter broadcast")
        self._schedule_parameter_broadcast("session_changed")

            
    def perform_reanalysis(self):
        """執行重新分析 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        #print(f"[REFRESH] [{window_title}] 開始重新分析")
        #print(f"   參數: {year} {race} {session}")
        #print(f"   視窗連動: {'是' if self.sync_windows_checkbox.isChecked() else '否'}")
        
        # 重新分析當前視窗
        self.update_current_window()
        
        # 如果啟用連動，也更新其他視窗
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox.isChecked():
            self.sync_to_other_windows()
            
    def sync_to_other_windows(self):
        """同步參數到其他視窗 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        logger.debug(f"[REFRESH] [{window_title}] 同步參數到其他視窗: {year} {race} {session}")
        
        # 同步到同一MDI區域中的其他子視窗
        synced_count = 0
        if self.parent_mdi:
            for subwindow in self.parent_mdi.subWindowList():
                if subwindow != self and hasattr(subwindow, 'set_analysis_parameters'):
                    # 檢查其他子視窗是否啟用同步
                    if hasattr(subwindow, 'sync_windows_checkbox') and \
                       subwindow.sync_windows_checkbox.isChecked():
                        
                        params = {
                            'year': year,
                            'race': race,
                            'session': session
                        }
                        subwindow.set_analysis_parameters(params, skip_sync=True)
                        synced_count += 1
                        logger.debug(f"[REFRESH] 同步到子視窗: {subwindow.windowTitle()}")
        
        logger.debug(f"[OK] 完成子視窗同步，共更新 {synced_count} 個視窗")
            
    def _legacy_update_current_window(self):
        """舊版更新當前視窗的分析數據 - 使用安全的參數獲取"""
        window_title = self.windowTitle()
        
        # [TOOL] 使用安全的參數獲取方法
        year = getattr(self, 'local_year', None) or self.get_current_year_from_main_window()
        race = getattr(self, 'local_race', None) or self.get_current_race_from_main_window()
        session = getattr(self, 'local_session', None) or self.get_current_session_from_main_window()
        
        logger.debug(f"[REFRESH] [{window_title}] 舊版更新視窗數據: {year} {race} {session}")
        
        # 啟動資料載入流程
        self.load_race_data(year, race, session)
    
    def load_race_data(self, year, race, session):
        """載入比賽資料 - 完整的JSON載入流程"""
        # Step 1: 載入JSON
        json_data = self.try_load_json(year, race, session)
        
        if json_data:
            # JSON存在，直接使用
            logger.debug(f"[OK] 找到JSON檔案，直接載入資料")
            self.update_charts_and_analysis(json_data)
        else:
            # Step 2: 無JSON則進行CLI參數呼叫
            logger.error(f"[ERROR] 未找到JSON檔案，啟動CLI分析...")
            self.call_cli_analysis(year, race, session)
            # 注意：JSON監控已在 call_cli_analysis 中啟動
    
    def try_load_json(self, year, race, session):
        """嘗試載入JSON檔案 - 與RainAnalysisCache保持一致"""
        import glob
        import os
        
        # 嘗試與 RainAnalysisCache 相同的搜尋邏輯
        # 1. 先嘗試降雨分析的標準格式
        rain_analysis_file = f"json/rain_analysis_{year}_{race}_{session}.json"
        if os.path.exists(rain_analysis_file):
            try:
                with open(rain_analysis_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[ERROR] JSON載入錯誤: {e}")
        
        # 2. 備用搜尋 - 構建JSON檔案搜尋模式
        json_patterns = [
            f"json/*{year}*{race}*{session}*.json",
            f"json_exports/*{year}*{race}*{session}*.json", 
            f"cache/*{year}*{race}*{session}*.json"
        ]
        
        for pattern in json_patterns:
            json_files = glob.glob(pattern)
            if json_files:
                # 過濾掉非JSON檔案
                json_files = [f for f in json_files if f.lower().endswith('.json')]
                if json_files:
                    json_file = json_files[0]  # 取第一個符合的檔案
                    logger.debug(f"[FILES] 找到JSON檔案: {json_file}")
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            return json.load(f)
                    except Exception as e:
                        logger.error(f"[ERROR] JSON載入錯誤: {e}")
                        continue
        
        logger.warning(f"[WARNING] 未找到適合的JSON檔案: {year}/{race}/{session}")
        return None
    
    def get_races_for_year_in_subwindow(self, year):
        """子視窗中根據年份獲取賽事列表（與主視窗保持一致）"""
        try:
            year_int = int(year)
            events = self._get_calendar_events_for_year(year_int)
            self._rebuild_race_mapping(events)
            race_labels = [self._format_race_display(event) for event in events]
            logger.debug(f"[SUBWINDOW] 載入 {year_int} 年的賽事列表: {len(race_labels)} 個賽事")
            return race_labels
        except Exception as e:
            logger.debug(f"[SUBWINDOW ERROR] 獲取賽事列表時出錯: {e}")
            return ["Japan", "Great Britain", "Monaco"]  # 回退列表
    
    def update_races_for_year(self, year):
        """為指定年份更新賽事列表"""
        if not hasattr(self, 'race_combo') or not self.race_combo:
            return

        try:
            year_int = int(year)
        except Exception:
            year_int = int(self.local_year) if self.local_year else 2025

        previous_race_key = self.get_selected_race_key()
        if not previous_race_key or previous_race_key == "Unknown":
            previous_race_key = self.local_race

        events = self._get_calendar_events_for_year(year_int)
        self._rebuild_race_mapping(events)

        self.race_combo.blockSignals(True)
        self.race_combo.clear()

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

        if previous_race_key:
            self._select_race_by_key(previous_race_key)

        if self.race_combo.currentIndex() < 0:
            preferred_event = select_preferred_event(completed_events, upcoming_events)
            if preferred_event is not None:
                self._select_race_by_key(preferred_event.race_key)
        if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
            self.race_combo.setCurrentIndex(0)

        self.race_combo.blockSignals(False)

        selected_event = self.get_selected_event()
        if selected_event:
            self.local_race = selected_event.race_key

        self._update_session_combo(preserve_session_code=self.local_session)

        logger.debug(f"[SUBWINDOW] 已更新賽事列表，當前選擇: {self.get_selected_race_key()}")
    
    def call_cli_analysis(self, year, race, session):
        """呼叫 CLI 進行分析 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.call_cli_analysis(year, race, session)
        else:
            logger.warning("[WARNING] cli_handler 未初始化，無法執行 CLI 分析")
    
    def stop_cli_analysis(self):
        """停止 CLI 分析 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.stop_cli_analysis()
    
    def show_analysis_progress(self):
        """顯示分析進度 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.show_analysis_progress()
    
    def hide_analysis_progress(self):
        """隱藏分析進度 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.hide_analysis_progress()
    
    def on_analysis_progress(self, message):
        """處理分析進度更新 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.on_analysis_progress(message)
    
    def on_analysis_output(self, output):
        """處理分析輸出 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.on_analysis_output(output)
    
    def on_analysis_completed(self, success, message):
        """處理分析完成 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.on_analysis_completed(success, message)
    
    def start_json_monitoring(self, year, race, session):
        """開始監控 JSON 檔案產生 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.start_json_monitoring(year, race, session)
    
    def stop_json_monitoring(self):
        """停止 JSON 監控 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.stop_json_monitoring()
    
    def check_json_ready(self, year, race, session):
        """檢查 JSON 是否已準備好 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.check_json_ready(year, race, session)
    
    def on_json_wait_timeout(self):
        """JSON 等待超時處理 - 委派給 PopoutCliHandler"""
        if hasattr(self, '_cli_handler') and self._cli_handler:
            self._cli_handler.on_json_wait_timeout()
    
    def update_charts_and_analysis(self, json_data):
        """更新圖表和分析結果 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater.update_charts_and_analysis(json_data)
        else:
            logger.warning("[WARNING] chart_updater 未初始化，無法更新圖表")
    
    def _update_speed_analysis_chart(self, json_data):
        """更新速度分析圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater._update_speed_analysis_chart(json_data)
    
    def _update_throttle_analysis_chart(self, json_data):
        """更新油門分析圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater._update_throttle_analysis_chart(json_data)
    
    def _update_rpm_analysis_chart(self, json_data):
        """更新RPM分析圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater._update_rpm_analysis_chart(json_data)
    
    def _update_gear_analysis_chart(self, json_data):
        """更新檔位分析圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater._update_gear_analysis_chart(json_data)

    def _update_acceleration_analysis_chart(self, json_data):
        """更新加速度分析圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater._update_acceleration_analysis_chart(json_data)

    def update_telemetry_chart(self, telemetry_data):
        """更新遙測圖表 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater.update_telemetry_chart(telemetry_data)
    
    def update_track_map(self, track_data):
        """更新軌道地圖 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater.update_track_map(track_data)
    
    def update_analysis_data(self, analysis_data):
        """更新分析數據 - 委派給 PopoutChartUpdater"""
        if hasattr(self, '_chart_updater') and self._chart_updater:
            self._chart_updater.update_analysis_data(analysis_data)
        # 實現具體的分析數據更新邏輯
        pass
        
    def get_analysis_parameters(self):
        """獲取當前分析參數"""
        if hasattr(self, 'year_combo'):
            return {
                'year': self.year_combo.currentText(),
                'race': self.race_combo.currentText(),
                'session': self.session_combo.currentText(),
                'sync_windows': self.sync_windows_checkbox.isChecked()
            }
        return None
        
    def set_analysis_parameters(self, params, skip_sync=False):
        """設置分析參數，支援跳過同步"""
        if hasattr(self, 'year_combo') and params:
            # 暫時斷開信號連接避免循環同步
            self.year_combo.blockSignals(True)
            self.race_combo.blockSignals(True)
            self.session_combo.blockSignals(True)
            
            # 更新參數
            self.year_combo.setCurrentText(params.get('year', '2025'))
            self.race_combo.setCurrentText(params.get('race', 'Japan'))
            self.session_combo.setCurrentText(params.get('session', 'R'))
            
            # 恢復信號連接
            self.year_combo.blockSignals(False)
            self.race_combo.blockSignals(False)
            self.session_combo.blockSignals(False)
            
            # 更新資料（如果不是跳過同步）
            if not skip_sync:
                self.update_current_window()
            
            # 注意：不同步連動和遙測設定，保持各視窗獨立
        
    def toggle_maximize(self):
        """切換最大化狀態"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
        # 🔄 [FIX] 狀態切換後強制重繪圖表（修復最大化/還原後顯示異常）
        QTimer.singleShot(50, self._force_redraw_chart)
    
    def custom_minimize(self):
        """自定義最小化：隱藏內容，只保留標題欄，移動到底部"""
        if hasattr(self, 'is_minimized') and self.is_minimized:
            # 如果已經最小化，則恢復
            self.restore_from_minimize()
        else:
            # 執行最小化
            self.minimize_to_bottom()
    
    def minimize_to_bottom(self):
        """最小化到底部，只顯示標題欄"""
        #print(f"🔽 最小化視窗 '{self.windowTitle()}' 到底部")
        
        # 保存當前狀態
        if self.original_geometry is None:
            self.original_geometry = self.geometry()
        
        # 隱藏內容區域
        if self.content_widget:
            self.content_widget.hide()
            #print(f"[PACKAGE] 隱藏內容區域")
        
        # 設置最小化狀態
        self.is_minimized = True
        
        # 調整視窗大小為只有標題欄高度
        title_height = 25  # 標題欄高度
        current_width = self.width()
        
        # 獲取MDI區域大小
        if self.parent():
            mdi_area = self.parent()
            mdi_height = mdi_area.height()
            mdi_width = mdi_area.width()
            
            # 移動到底部
            bottom_y = mdi_height - title_height - 5
            new_x = max(0, min(self.x(), mdi_width - current_width))
            
            # 設置新的幾何形狀
            self.setGeometry(new_x, bottom_y, current_width, title_height)
            #print(f"[PIN] 移動到底部位置: ({new_x}, {bottom_y}, {current_width}, {title_height})")
        else:
            # 如果沒有父視窗，只調整高度
            self.resize(current_width, title_height)
            #print(f"📏 調整大小為: {current_width}x{title_height}")
    
    def restore_from_minimize(self):
        """從最小化狀態恢復"""
        #print(f"🔼 恢復視窗 '{self.windowTitle()}' 從最小化狀態")
        
        # 恢復幾何形狀
        if self.original_geometry is not None:
            self.setGeometry(self.original_geometry)
            #print(f"[PIN] 恢復到原始位置: {self.original_geometry}")
        else:
            #print(f"[WARNING] 無法恢復：原始幾何形狀未保存")
            pass
        
        # 顯示內容區域
        if self.content_widget:
            self.content_widget.show()
            #print(f"[PACKAGE] 顯示內容區域")
        
        # 清除最小化狀態
        self.is_minimized = False
        
        # 🔄 [FIX] 強制重繪圖表內容（修復最小化恢復後顯示異常）
        QTimer.singleShot(50, self._force_redraw_chart)
    
    def _force_redraw_chart(self):
        """強制重繪圖表組件"""
        try:
            # 嘗試找到並重繪 Matplotlib 圖表
            if self.analysis_module:
                # 方法 1: 直接調用 chart_widget 的重繪
                if hasattr(self.analysis_module, 'chart_widget') and self.analysis_module.chart_widget:
                    chart = self.analysis_module.chart_widget
                    if hasattr(chart, 'figure') and chart.figure:
                        chart.figure.canvas.draw_idle()
                        logger.debug(f"[REDRAW] 已重繪圖表: {self.windowTitle()}")
                    # 如果是包裝類，嘗試內部 chart_widget
                    if hasattr(chart, 'chart_widget') and chart.chart_widget:
                        inner_chart = chart.chart_widget
                        if hasattr(inner_chart, 'figure') and inner_chart.figure:
                            inner_chart.figure.canvas.draw_idle()
                
                # 方法 2: 調用 update() 強制重繪
                if hasattr(self.analysis_module, 'update'):
                    self.analysis_module.update()
            
            # 對內容區域也調用 update
            if self.content_widget:
                self.content_widget.update()
                
        except Exception as e:
            logger.warning(f"[REDRAW] 重繪圖表時發生警告: {e}")
        
    def toggle_popout(self):
        """切換彈出狀態"""
        if not self.is_popped_out:
            self.pop_out()
        else:
            self.pop_back_in()
            
    def pop_out(self):
        """彈出為獨立視窗"""
        if self.parent_mdi and not self.is_popped_out and self.content_widget:
            # 保存原始widget
            self.original_widget = self.content_widget
            
            # 創建可調整大小的獨立視窗
            self.standalone_window = ResizableStandaloneWindow()
            self.standalone_window.setWindowTitle(f"[Standalone] {self.windowTitle()}")
            self.standalone_window.setObjectName("StandaloneWindow")
            self.standalone_window.setCentralWidget(self.original_widget)
            self.standalone_window.resize(800, 600)  # 調整預設大小更大
            
            # 設置視窗最小大小
            # self.standalone_window.setMinimumSize(400, 300) - 尺寸限制已移除
            
            # 添加返回按鈕
            toolbar = self.standalone_window.addToolBar(tr("controls", "Controls"))
            toolbar.setObjectName("StandaloneToolbar")
            return_action = toolbar.addAction(tr("return_to_main", "Return to Main"))
            return_action.triggered.connect(self.pop_back_in)
            
            self.standalone_window.show()
            
            # 在MDI中隱藏
            self.hide()
            self.is_popped_out = True
            self.title_bar.popout_btn.setText("⌂")
            self.title_bar.popout_btn.setToolTip(tr("return_to_main", "Return to Main"))
            
    def pop_back_in(self):
        """返回主畫面"""
        if self.is_popped_out and self.content_widget:
            # 重新包裝widget
            wrapper = QWidget()
            wrapper.setObjectName("SubWindowWrapper")
            wrapper_layout = QVBoxLayout(wrapper)
            wrapper_layout.setContentsMargins(0, 0, 0, 0)
            wrapper_layout.setSpacing(0)
            
            # 重新創建可拖拽標題欄
            self.title_bar = DraggableTitleBar(self, self.windowTitle())
            wrapper_layout.addWidget(self.title_bar)
            wrapper_layout.addWidget(self.content_widget)
            
            # 恢復到MDI
            super().setWidget(wrapper)
            
            if hasattr(self, 'standalone_window'):
                self.standalone_window.close()
                delattr(self, 'standalone_window')
            
            # 在MDI中顯示
            self.show()
            self.is_popped_out = False
            self.title_bar.popout_btn.setText("⧉")
            self.title_bar.popout_btn.setToolTip(tr('popout_tooltip'))
            
    def resizeEvent(self, event):
        """處理視窗大小調整事件 - 簡化版本，避免重複處理"""
        super().resizeEvent(event)
        
        # 只處理內容組件的基本更新，避免多重縮放處理
        if hasattr(self, 'content_widget') and self.content_widget:
            try:
                # 簡化處理：只調用基本的update，讓Qt的佈局系統自動處理
                self.content_widget.update()
                #print(f"[RESIZE] 子視窗內容已更新: {event.size().width()}x{event.size().height()}")
            except Exception as e:
                #print(f"[RESIZE_ERROR] 內容更新失敗: {e}")
                pass


        # 發射resize信號
        self.resized.emit()
            
    def show_settings_dialog(self):
        """顯示設定對話框"""
        # 保存對話框引用以便實時同步
        if not hasattr(self, 'settings_dialog') or self.settings_dialog is None:
            self.settings_dialog = WindowSettingsDialog(self)
        
        # 顯示對話框
        result = self.settings_dialog.exec_()
        
        # 對話框關閉後清理引用（避免內存洩漏）
        if result == QDialog.Rejected:
            self.settings_dialog = None

    def set_linkage_enabled(self, enabled: bool):
        """設置個別連動狀態 (L 按鈕) - 轉發給分析模組
        
        此方法由 DraggableTitleBar 的 L 按鈕調用，
        需要將連動狀態傳遞給內部的 analysis_module
        """
        logger.debug(f"[LINKAGE] PopoutSubWindow.set_linkage_enabled({enabled}) 被調用")
        
        if hasattr(self, 'analysis_module') and self.analysis_module:
            # 優先調用分析模組的 set_linkage_enabled
            if hasattr(self.analysis_module, 'set_linkage_enabled'):
                self.analysis_module.set_linkage_enabled(enabled)
                logger.debug(f"[LINKAGE] 已轉發給 analysis_module.set_linkage_enabled({enabled})")
            
            # 🔧 [FIX] 檢查所有可能的圖表組件屬性名稱
            chart_widget_names = ['chart_widget', 'speed_chart_widget', 'brake_chart_widget', 
                                  'throttle_chart_widget', 'rpm_chart_widget', 'gear_chart_widget',
                                  'acceleration_chart_widget', 'telemetry_chart_widget']
            
            for attr_name in chart_widget_names:
                if hasattr(self.analysis_module, attr_name):
                    chart_widget = getattr(self.analysis_module, attr_name)
                    if chart_widget and hasattr(chart_widget, 'set_linkage_enabled'):
                        chart_widget.set_linkage_enabled(enabled)
                        logger.debug(f"[LINKAGE] 已轉發給 {attr_name}.set_linkage_enabled({enabled})")
                        break  # 找到一個就夠了

    def set_master_linkage_enabled(self, enabled: bool):
        """設置主視窗連動總開關狀態 - 轉發給分析模組
        
        此方法由 LinkageManager 的主開關調用
        """
        logger.debug(f"[LINKAGE] PopoutSubWindow.set_master_linkage_enabled({enabled}) 被調用")
        
        if hasattr(self, 'analysis_module') and self.analysis_module:
            if hasattr(self.analysis_module, 'set_master_linkage_enabled'):
                self.analysis_module.set_master_linkage_enabled(enabled)
                logger.debug(f"[LINKAGE] 已轉發給 analysis_module.set_master_linkage_enabled({enabled})")

    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數變更通知"""
        window_title = self.windowTitle()
        logger.debug(f"[ANNOUNCE] [NOTIFICATION] {window_title} 收到主視窗更新通知: {param_type}={value}")
        
        # 檢查同步狀態 - 支援多種同步狀態檢查方式
        sync_enabled = False
        
        # 方法1: 檢查 sync_windows_checkbox (用於有控制面板的子視窗)
        if hasattr(self, 'sync_windows_checkbox') and self.sync_windows_checkbox:
            sync_enabled = self.sync_windows_checkbox.isChecked()
            logger.debug(f"[SEARCH] [NOTIFICATION] {window_title} 使用 checkbox 檢查同步狀態: {sync_enabled}")
        
        # 方法2: 檢查 sync_enabled 屬性 (用於 PopoutSubWindow 等)
        elif hasattr(self, 'sync_enabled'):
            sync_enabled = self.sync_enabled
            logger.debug(f"[SEARCH] [NOTIFICATION] {window_title} 使用屬性檢查同步狀態: {sync_enabled}")
        
        # 如果未啟用同步，直接返回
        if not sync_enabled:
            logger.debug(f"🔴 [NOTIFICATION] {window_title} 同步已停用，忽略更新通知")
            return
        
        logger.debug(f"[GREEN] [NOTIFICATION] {window_title} 同步已啟用，處理參數更新")
        
        # [TOOL] 更新本地參數（同步模式）
        if param_type == 'year':
            self.local_year = value
        elif param_type == 'race':
            self.local_race = value
        elif param_type == 'session':
            self.local_session = value
        
        # [TOOL] 立即更新標題
        self.update_window_title()
        
        # 使用統一的方法更新視窗內容
        try:
            success = self.update_current_window()
            if success:
                logger.debug(f"[OK] [NOTIFICATION] {window_title} 內容更新成功")
            else:
                logger.warning(f"[WARNING] [NOTIFICATION] {window_title} 內容更新完成但可能有問題")
        except Exception as e:
            logger.error(f"[ERROR] [NOTIFICATION] {window_title} 內容更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def get_current_year_from_main_window(self):
        """從主視窗獲取當前年份 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_year') and self.local_year:
                return self.local_year
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_year'):
                    return str(self.main_window.get_selected_year())
                if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                    return self.main_window.year_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            logger.warning(f"[WARNING] [GET_YEAR] 獲取主視窗年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race_from_main_window(self):
        """從主視窗獲取當前賽事 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_race') and self.local_race:
                return self.local_race
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_race_key'):
                    return self.main_window.get_selected_race_key()
                if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                    return self.main_window.race_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            logger.warning(f"[WARNING] [GET_RACE] 獲取主視窗賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session_from_main_window(self):
        """從主視窗獲取當前賽段 - 安全版本"""
        try:
            # 優先使用本地參數
            if hasattr(self, 'local_session') and self.local_session:
                return self.local_session
                
            # 如果有main_window引用
            if hasattr(self, 'main_window') and self.main_window:
                if hasattr(self.main_window, 'get_selected_session_code'):
                    return self.main_window.get_selected_session_code()
                if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                    return self.main_window.session_combo.currentText()
            
            # [TOOL] 移除不安全的parent遍歷邏輯，避免AttributeError
                    
        except Exception as e:
            logger.warning(f"[WARNING] [GET_SESSION] 獲取主視窗賽段失敗: {e}")
        return "R"  # 預設值
    
    def closeEvent(self, event):
        """子視窗關閉事件處理"""
        try:
            window_title = self.windowTitle()
            
            # 🔧 修復洩漏1: 調用模組的 cleanup() 方法（最優先！）
            if hasattr(self, 'analysis_module') and self.analysis_module:
                try:
                    # ✅ 調用模組的 cleanup() 方法清理所有資源
                    if hasattr(self.analysis_module, 'cleanup'):
                        logger.debug(f"[CLEANUP] {window_title} 正在調用模組 cleanup()...")
                        self.analysis_module.cleanup()
                        logger.debug(f"[CLEANUP] {window_title} ✅ 模組 cleanup() 完成")
                    else:
                        logger.warning(f"[WARNING] {window_title} 模組沒有 cleanup() 方法")
                    
                    # 斷開模組信號
                    if hasattr(self.analysis_module, 'module_error'):
                        try:
                            self.analysis_module.module_error.disconnect()
                        except:
                            pass
                    if hasattr(self.analysis_module, 'parameters_updated'):
                        try:
                            self.analysis_module.parameters_updated.disconnect()
                        except:
                            pass
                    logger.debug(f"[CLEANUP] {window_title} 已斷開模組信號連接")
                except Exception as e:
                    logger.error(f"[ERROR] {window_title} 模組清理時出錯: {e}")
                    import traceback
                    traceback.print_exc()
            
            # 🔧 修復洩漏2: 清理 DraggableTitleBar 資源（7個按鈕信號）
            if hasattr(self, 'title_bar') and self.title_bar:
                try:
                    self.title_bar.cleanup()
                    self.title_bar = None
                    logger.debug(f"[CLEANUP] {window_title} 已清理 TitleBar 資源")
                except Exception as e:
                    logger.warning(f"[WARNING] {window_title} TitleBar 清理失敗: {e}")
            
            # 發出關閉信號
            self.window_closed.emit()
            
            # 停止任何正在執行的 CLI 分析
            if hasattr(self, 'stop_cli_analysis'):
                self.stop_cli_analysis()
            
            # 如果內容widget有 CLI 分析功能，也要停止
            if self.content_widget and hasattr(self.content_widget, 'stop_cli_analysis'):
                self.content_widget.stop_cli_analysis()
            
            # 🔧 修復洩漏3: 清理所有對象引用
            self.analysis_module = None
            self._parameter_provider = None
            self.content_widget = None
            self.main_window = None
            
            # 🔧 修復洩漏4: 清理事件處理狀態
            self.resizing = False
            self.resize_direction = None
            self.resize_start_pos = None
            self.resize_start_geometry = None
            self._current_cursor = None

            # 從父層 MDI 區域移除子視窗，避免殘留在 subWindowList()
            if self.parent_mdi and hasattr(self.parent_mdi, 'removeSubWindow'):
                try:
                    logger.debug(f"[CLEANUP] {window_title} 正在從 MDI 區域移除子視窗...")
                    self.parent_mdi.removeSubWindow(self)
                    logger.debug(f"[CLEANUP] {window_title} ✅ 已從 MDI 區域移除")
                except Exception as e:
                    logger.error(f"[ERROR] {window_title} 從 MDI 移除失敗: {e}")
            else:
                logger.warning(f"[WARNING] {window_title} 無法移除（parent_mdi={self.parent_mdi}, hasRemove={hasattr(self.parent_mdi, 'removeSubWindow') if self.parent_mdi else False}）")
            
            # 🔧 修復洩漏5: 明確調用 deleteLater() 確保 Qt 釋放資源
            logger.debug(f"[CLEANUP] {window_title} 正在調用 deleteLater()...")
            self.deleteLater()
            logger.debug(f"[CLEANUP] {window_title} ✅ deleteLater() 已調用")
            
            logger.debug(f"[CLEANUP] {window_title} 資源已清理完成")
            
            # 接受關閉事件，讓 PyQt 自動處理移除
            event.accept()
            
        except Exception as e:
            logger.error(f"[ERROR] closeEvent 異常: {e}")
            event.accept()  # 即使出錯也要關閉


# ========== ContextMenuTreeWidget 已移至 windows/widgets/context_menu_tree_widget.py ==========
# ========== ResizableStandaloneWindow, TabStandaloneWindow 已移至 windows/widgets/standalone_windows.py ==========
