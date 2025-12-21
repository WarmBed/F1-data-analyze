# -*- coding: utf-8 -*-
"""
DialogSeasonHelper - 對話框季節日曆輔助類別

從 WindowSettingsDialog 提取的季節日曆相關邏輯。
處理賽事列表填充、賽段更新等功能。

Phase 5.4.2: WindowSettingsDialog 拆分
"""

import logging
from typing import TYPE_CHECKING, Optional, Dict, List, Any

from PyQt5.QtWidgets import QComboBox

from core.gui_i18n import tr
from core.logger import get_logger
from typing import Dict
from typing import List
from typing import Optional
from modules.gui.shared.season_calendar_provider import SeasonEvent
from typing import Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QDialog
    from core.season_calendar import SeasonEvent

logger = logging.getLogger(__name__)


class DialogSeasonHelper:
    """
    對話框季節日曆輔助類別
    
    處理 WindowSettingsDialog 中的季節日曆相關邏輯：
    - 獲取指定年份的賽事列表
    - 填充賽事下拉選單
    - 更新賽段下拉選單
    - 賽事選擇和顯示格式化
    """
    
    def __init__(self, dialog: 'QDialog', main_window):
        """
        初始化季節日曆輔助類別
        
        Args:
            dialog: 父對話框 (WindowSettingsDialog)
            main_window: 主視窗 (StyleHMainWindow)
        """
        self.dialog = dialog
        self.main_window = main_window
        
        # 內部映射表
        self._season_event_lookup: Dict[str, 'SeasonEvent'] = {}
        self._display_to_race_key: Dict[str, str] = {}
        
        # 控制項引用（由 setup 方法設置）
        self.year_combo: Optional[QComboBox] = None
        self.race_combo: Optional[QComboBox] = None
        self.session_combo: Optional[QComboBox] = None
    
    def set_controls(self, year_combo: QComboBox, race_combo: QComboBox, session_combo: QComboBox) -> None:
        """
        設置控制項引用
        
        Args:
            year_combo: 年份下拉選單
            race_combo: 賽事下拉選單
            session_combo: 賽段下拉選單
        """
        self.year_combo = year_combo
        self.race_combo = race_combo
        self.session_combo = session_combo
    
    def get_calendar_events_for_year(self, year: int) -> List['SeasonEvent']:
        """
        獲取指定年份的賽事列表
        
        Args:
            year: 年份
            
        Returns:
            List[SeasonEvent]: 賽事列表
        """
        if self.main_window and hasattr(self.main_window, "_get_calendar_events"):
            return self.main_window._get_calendar_events(year)
        if self.main_window and hasattr(self.main_window, "_season_provider"):
            try:
                from core.season_calendar import SeasonCalendarError
                return self.main_window._season_provider.get_completed_events(year)
            except Exception as exc:
                logger.debug(f"[DIALOG_SEASON] Get calendar events failed: {exc}")
        return []
    
    def format_race_display(self, event: 'SeasonEvent') -> str:
        """
        格式化賽事顯示文字
        
        Args:
            event: 賽事物件
            
        Returns:
            str: 格式化後的顯示文字
        """
        if self.main_window and hasattr(self.main_window, "_format_race_display"):
            return self.main_window._format_race_display(event)
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[Upcoming]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label
    
    def rebuild_race_mapping(self, events: List['SeasonEvent']) -> None:
        """
        重建賽事映射表
        
        Args:
            events: 賽事列表
        """
        self._season_event_lookup.clear()
        self._display_to_race_key.clear()
        
        for event in events:
            self._season_event_lookup[event.race_key] = event
            formatted_label = self.format_race_display(event)
            candidate_labels = {event.display_label, formatted_label}
            for label in candidate_labels:
                self._display_to_race_key[label] = event.race_key
                if self.main_window:
                    plain = self.main_window._strip_race_display(label) if hasattr(self.main_window, '_strip_race_display') else label
                else:
                    plain = label
                if plain and plain not in self._display_to_race_key:
                    self._display_to_race_key[plain] = event.race_key
    
    def select_race_by_key(self, race_key: Optional[str]) -> None:
        """
        根據賽事鍵值選擇賽事
        
        Args:
            race_key: 賽事鍵值 (如 "Japan", "Monaco")
        """
        if race_key is None or self.race_combo is None:
            return
        
        # 使用 SeasonEvent 驗證
        from core.season_calendar import SeasonEvent
        
        for index in range(self.race_combo.count()):
            data = self.race_combo.itemData(index)
            if isinstance(data, SeasonEvent) and data.race_key == race_key:
                self.race_combo.setCurrentIndex(index)
                return
    
    def get_selected_event(self) -> Optional['SeasonEvent']:
        """
        獲取當前選擇的賽事
        
        Returns:
            Optional[SeasonEvent]: 選擇的賽事，或 None
        """
        from core.season_calendar import SeasonEvent
        
        if self.race_combo is None:
            return None
            
        data = self.race_combo.currentData()
        if isinstance(data, SeasonEvent):
            return data
        
        display_text = self.race_combo.currentText()
        race_key = self._display_to_race_key.get(display_text)
        
        if not race_key and self.main_window and hasattr(self.main_window, '_strip_race_display'):
            race_key = self.main_window._strip_race_display(display_text)
            race_key = self._display_to_race_key.get(race_key, race_key)
        
        return self._season_event_lookup.get(race_key)
    
    def get_selected_race_key(self) -> str:
        """
        獲取當前選擇的賽事鍵值
        
        Returns:
            str: 賽事鍵值
        """
        event = self.get_selected_event()
        if event:
            return event.race_key
        
        display_text = self.race_combo.currentText() if self.race_combo else ""
        race_key = self._display_to_race_key.get(display_text)
        
        if not race_key and self.main_window and hasattr(self.main_window, '_strip_race_display'):
            race_key = self.main_window._strip_race_display(display_text)
        
        return race_key or "Unknown"
    
    def get_selected_session_code(self) -> str:
        """
        獲取當前選擇的賽段代碼
        
        Returns:
            str: 賽段代碼 (如 "R", "Q", "FP1")
        """
        if self.session_combo is None:
            return "R"
            
        data = self.session_combo.currentData()
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        
        text = self.session_combo.currentText()
        return text or "R"
    
    def update_session_combo(self, preserve_session_code: Optional[str] = None) -> None:
        """
        更新賽段下拉選單
        
        Args:
            preserve_session_code: 要保留的賽段代碼
        """
        from core.season_calendar import SeasonEvent
        
        logger.debug(f"[DIALOG_SEASON] update_session_combo called, session_combo: {self.session_combo}")
        
        # 使用 None 檢查（避免 PyQt5 boolean 陷阱）
        if not hasattr(self, 'session_combo') or self.session_combo is None:
            logger.warning(f"[DIALOG_SEASON] session_combo is None, returning early")
            return

        event = self.get_selected_event()
        current_code = preserve_session_code or self.get_selected_session_code()
        
        logger.debug(f"[DIALOG_SEASON] preserve_session_code: {preserve_session_code}")
        logger.debug(f"[DIALOG_SEASON] current_code: {current_code}")
        logger.debug(f"[DIALOG_SEASON] event: {event}")
        
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
    
    def get_races_for_year(self, year: str) -> List['SeasonEvent']:
        """
        獲取指定年份的賽事列表（供對話框使用）
        
        Args:
            year: 年份字串
            
        Returns:
            List[SeasonEvent]: 賽事列表
        """
        try:
            year_int = int(year)
            events = self.get_calendar_events_for_year(year_int)
            self.rebuild_race_mapping(events)
            logger.debug(f"[DIALOG_SEASON] Loaded {year_int} races: {len(events)} events")
            return events
        except Exception as e:
            logger.debug(f"[DIALOG_SEASON] Get races error: {e}")
            return []
    
    def populate_races_for_year(self, year: str) -> None:
        """
        為指定年份填充賽事列表
        
        Args:
            year: 年份字串
        """
        if self.race_combo is None:
            return
            
        events = self.get_races_for_year(year)
        self.race_combo.clear()
        
        if events:
            # 分離已完成和未開賽的賽事
            completed_events = [event for event in events if event.is_completed]
            upcoming_events = [event for event in events if not event.is_completed]

            def add_event(event) -> None:
                label = self.format_race_display(event)
                self._display_to_race_key[label] = event.race_key
                self.race_combo.addItem(label, event)

            for event in completed_events:
                add_event(event)

            if completed_events and upcoming_events:
                self.race_combo.insertSeparator(self.race_combo.count())

            for event in upcoming_events:
                add_event(event)

            if self.race_combo.currentIndex() < 0:
                # 選擇偏好賽事
                preferred_event = self._select_preferred_event(completed_events, upcoming_events)
                if preferred_event is not None:
                    self.select_race_by_key(preferred_event.race_key)
            
            if self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
                self.race_combo.setCurrentIndex(0)
        else:
            placeholder = tr("season_calendar_placeholder", "[No completed events]")
            self.race_combo.addItem(placeholder, None)
    
    def _select_preferred_event(
        self, 
        completed_events: List['SeasonEvent'], 
        upcoming_events: List['SeasonEvent']
    ) -> Optional['SeasonEvent']:
        """
        選擇偏好賽事（最近完成的賽事）
        
        Args:
            completed_events: 已完成的賽事列表
            upcoming_events: 未開賽的賽事列表
            
        Returns:
            Optional[SeasonEvent]: 偏好的賽事
        """
        # 嘗試使用主視窗的 select_preferred_event 函數
        try:
            # 動態導入以避免循環引用
            from core.season_calendar import select_preferred_event
            return select_preferred_event(completed_events, upcoming_events)
        except ImportError:
            pass
        
        # 備用邏輯：選擇最後一個已完成的賽事
        if completed_events:
            return completed_events[-1]
        if upcoming_events:
            return upcoming_events[0]
        return None
    
    def on_year_changed(self, year: str) -> None:
        """
        處理年份變更事件
        
        Args:
            year: 新年份
        """
        logger.debug(f"[DIALOG_SEASON] Year changed to: {year}")
        
        # 記住當前選擇的賽事
        current_event = self.get_selected_event()
        current_race_key = current_event.race_key if current_event else None
        
        # 更新賽事列表
        self.populate_races_for_year(year)
        
        # 嘗試恢復之前選擇的賽事
        if current_race_key:
            self.select_race_by_key(current_race_key)
        
        if self.race_combo and self.race_combo.currentIndex() < 0 and self.race_combo.count() > 0:
            self.race_combo.setCurrentIndex(0)

        # 更新賽段列表
        self.update_session_combo()
    
    def on_race_combo_changed(self) -> None:
        """處理賽事選擇變更事件"""
        self.update_session_combo()
