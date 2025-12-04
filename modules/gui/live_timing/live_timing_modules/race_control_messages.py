"""
Live Timing Race Control Messages
=================================

顯示比賽控制訊息面板 - 黃旗、處罰、調查等訊息。

完全複製自: Live_timing_test/demo_live_position_tracking.py RaceControlMessagesWidget

Author: F1T Team
Date: 2025-12-04
"""

from typing import Dict, List, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView
)
from PyQt5.QtGui import QColor

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr


class RaceControlMessagesWidget(QWidget):
    """
    比賽控制訊息面板 - 顯示黃旗、處罰、調查等訊息
    
    完全複製自 demo_live_position_tracking.py
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._all_messages: List[Dict[str, Any]] = []
        self._current_lap = 0
        
        self._init_ui()
        
        print("[RaceControlMessagesWidget] initialized")
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 訊息列表
        self.message_list = QTableWidget()
        self.message_list.setColumnCount(3)
        self.message_list.setHorizontalHeaderLabels([
            tr("lap", "Lap"),
            tr("type", "Type"),
            tr("message", "Message")
        ])
        self.message_list.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.message_list.setSelectionMode(QAbstractItemView.NoSelection)
        self.message_list.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.message_list.setColumnWidth(0, 35)
        self.message_list.setColumnWidth(1, 70)
        self.message_list.horizontalHeader().setStretchLastSection(True)
        
        # 啟用自動換行
        self.message_list.setWordWrap(True)
        self.message_list.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # 深色主題樣式
        self.message_list.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #E0E0E0;
                gridline-color: #333333;
                border: none;
            }
            QTableWidget::item {
                padding: 2px;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #E0E0E0;
                padding: 4px;
                border: 1px solid #333333;
            }
        """)
        
        print("[RaceControlMessagesWidget] Column widths: 0:Lap=35, 1:Type=70, 2:Message=stretch")
        
        layout.addWidget(self.message_list)
    
    def set_messages(self, messages: List[Dict[str, Any]]):
        """設置所有訊息"""
        self._all_messages = messages
        print(f"[RaceControlMessagesWidget] Loaded {len(messages)} messages")
    
    def _get_message_type_and_color(self, msg: Dict) -> tuple:
        """
        根據訊息內容判斷類型和顏色
        
        Returns:
            (type_text, bg_color, fg_color)
        """
        flag = msg.get('Flag', '')
        category = msg.get('Category', '')
        message = msg.get('Message', '').upper()
        
        # 優先檢查訊息內容關鍵字
        if 'SAFETY CAR' in message or 'SC ' in message or category == 'SafetyCar':
            return ('SC', '#FF8C00', '#FFFFFF')  # 橘色 - Safety Car
        elif 'DRS' in message:
            return ('DRS', '#00FF00', '#000000')  # 綠色 - DRS
        elif 'PENALTY' in message or category == 'Penalty':
            return ('Penalty', '#1E90FF', '#FFFFFF')  # 藍色 - Penalty
        elif 'DOUBLE YELLOW' in message:
            return ('YELLOW', '#FFFF00', '#000000')  # 黃色 - Double Yellow
        elif 'VSC' in message:
            return ('VSC', '#FFD700', '#000000')  # 金黃色 - VSC
        
        # 根據 Flag 設置顏色
        if flag == 'GREEN':
            return ('GREEN', '#00FF00', '#000000')
        elif flag == 'YELLOW':
            return ('YELLOW', '#FFFF00', '#000000')
        elif flag == 'RED':
            return ('RED', '#FF0000', '#FFFFFF')
        elif flag == 'BLUE':
            return ('BLUE', '#0000FF', '#FFFFFF')
        elif flag == 'CHEQUERED':
            return ('FINISH', '#000000', '#FFFFFF')
        elif flag:
            return (flag, '#888888', '#FFFFFF')
        
        # 使用 Category
        return (category if category else 'Other', '#555555', '#FFFFFF')
    
    def update_for_lap(self, current_lap: int):
        """根據當前圈數更新顯示"""
        self._current_lap = current_lap
        
        # 過濾只顯示當前圈數之前的訊息
        visible_messages = [
            msg for msg in self._all_messages 
            if msg.get('Lap', 0) <= current_lap
        ]
        
        # 分離重要訊息 (SC/Penalty) 和一般訊息
        priority_messages = []
        normal_messages = []
        
        for msg in visible_messages:
            message_text = msg.get('Message', '').upper()
            category = msg.get('Category', '').upper()
            
            # SC 和 Penalty 為高優先級
            is_priority = (
                'SAFETY CAR' in message_text or 
                'SC ' in message_text or 
                category == 'SAFETYCAR' or
                'PENALTY' in message_text or 
                category == 'PENALTY'
            )
            
            if is_priority:
                priority_messages.append(msg)
            else:
                normal_messages.append(msg)
        
        # 分別按圈數倒序排列
        priority_messages = sorted(priority_messages, key=lambda m: m.get('Lap', 0), reverse=True)
        normal_messages = sorted(normal_messages, key=lambda m: m.get('Lap', 0), reverse=True)
        
        # 合併: 優先訊息在前
        all_sorted = priority_messages + normal_messages
        
        # 限制顯示數量
        visible_messages = all_sorted[:20]
        
        self.message_list.setRowCount(len(visible_messages))
        
        for row, msg in enumerate(visible_messages):
            lap = msg.get('Lap', '?')
            message = msg.get('Message', '')
            
            # 獲取類型和顏色
            type_text, bg_color, fg_color = self._get_message_type_and_color(msg)
            
            # 設置圈數
            lap_item = QTableWidgetItem(str(lap))
            lap_item.setTextAlignment(Qt.AlignCenter)
            self.message_list.setItem(row, 0, lap_item)
            
            # 設置類型（帶顏色）
            type_item = QTableWidgetItem(type_text)
            type_item.setTextAlignment(Qt.AlignCenter)
            type_item.setBackground(QColor(bg_color))
            type_item.setForeground(QColor(fg_color))
            self.message_list.setItem(row, 1, type_item)
            
            # 設置訊息
            msg_item = QTableWidgetItem(message)
            self.message_list.setItem(row, 2, msg_item)


class LiveTimingRaceControlMessages(BaseLiveTimingMDI):
    """
    Live Timing Race Control Messages MDI Window
    
    顯示比賽控制訊息 - 黃旗、處罰、調查等。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr("race_control_messages", "Race Control Messages"))
        self.setMinimumSize(300, 200)
        self.resize(400, 300)
        
        self._messages_loaded = False
        
        print("[RACE_CONTROL_MDI] LiveTimingRaceControlMessages initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.messages_widget = RaceControlMessagesWidget()
        self._main_layout.addWidget(self.messages_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded - 載入比賽控制訊息"""
        print(f"[RACE_CONTROL_MDI] Race loaded: {race_info.get('year')} {race_info.get('race')}")
        
        # 從 DataManager 獲取比賽控制訊息
        if self._data_manager:
            raw_messages = self._data_manager.get_race_control_messages()
            if raw_messages:
                # 格式化訊息 - 從原始格式轉換為扁平格式
                # 原始: {timestamp, data: {Messages: {id: {Lap, Message, ...}}}}
                # 目標: [{Lap, Message, Category, Flag, ...}, ...]
                formatted_messages = self._format_messages(raw_messages)
                self.messages_widget.set_messages(formatted_messages)
                self._messages_loaded = True
                print(f"[RACE_CONTROL_MDI] Loaded {len(formatted_messages)} race control messages (from {len(raw_messages)} raw records)")
            else:
                print("[RACE_CONTROL_MDI] No race control messages available")
    
    def _format_messages(self, raw_messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        格式化訊息 - 從原始 JSON 格式轉換為 Widget 期望的扁平格式
        
        原始格式 (來自 RaceControlMessages.json):
        {
            "timestamp": "01:00:35.266",
            "data": {
                "Messages": {
                    "6": {"Lap": 2, "Category": "Drs", "Message": "DRS ENABLED", ...}
                }
            }
        }
        
        目標格式 (Widget 期望):
        {"Lap": 2, "Category": "Drs", "Message": "DRS ENABLED", "Flag": "", ...}
        """
        formatted = []
        
        for record in raw_messages:
            data = record.get('data', {})
            messages_raw = data.get('Messages', {})
            
            # Messages 可能是 list 或 dict
            if isinstance(messages_raw, list):
                for msg in messages_raw:
                    if isinstance(msg, dict):
                        formatted.append(msg)
            elif isinstance(messages_raw, dict):
                for key, msg in messages_raw.items():
                    if isinstance(msg, dict):
                        formatted.append(msg)
        
        return formatted
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        print("[RACE_CONTROL_MDI] Race unloaded")
        self.messages_widget._all_messages = []
        self.messages_widget.message_list.setRowCount(0)
        self._messages_loaded = False
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated - 根據當前圈數更新顯示"""
        if not self._messages_loaded:
            return
        
        # 獲取當前圈數
        current_lap = 0
        drivers = snapshot.get('drivers', {})
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # 更新顯示
        if current_lap > 0:
            self.messages_widget.update_for_lap(current_lap)
