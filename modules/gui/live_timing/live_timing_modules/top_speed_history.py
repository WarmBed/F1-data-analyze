"""
Live Timing Top Speed History
=============================

每圈最高速歷史記錄表模組，顯示每個車手每一圈的最高速度 (km/h)。

顏色標註：
- 紫色: 該車手的個人最高速圈
- 白色: 正常

Author: F1T Team
Date: 2025-12-29
"""

from typing import Dict, List, Any, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

from core.logger import get_logger
logger = get_logger(__name__)


# ===========================================
# 顏色常數
# ===========================================
COLOR_PERSONAL_BEST_FG = '#DA70D6'     # 淺紫色文字 (個人最高速)
COLOR_NORMAL_FG = '#E0E0E0'            # 淺灰色文字 (正常)
COLOR_PIT_LAP_BG = '#BA68C8'           # 淺紫色背景 (進站)
COLOR_PIT_LAP_FG = '#FFFFFF'


class TopSpeedHistoryTableWidget(QWidget):
    """
    Top Speed 歷史表格 Widget
    
    顯示格式：
    | Lap | VER | LEC | NOR | SAI | ... |
    |-----|-----|-----|-----|-----|-----|
    | 1   | 325 | 322 | 318 | ... |
    | 2   | 338 | 324 | 320 | ... |
    
    欄位按當前名次排序 (P1 在最左邊)
    紫色文字表示該車手的個人最高速
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設置深色背景
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setProperty("is_live_timing_widget", True)
        
        # 資料儲存
        # {driver_num: {lap_num: {'top_speed': float, 'is_pit': bool}}}
        self._lap_data: Dict[str, Dict[int, Dict[str, Any]]] = {}
        
        # 車手資訊 {driver_num: {'tla': str, 'position': int, 'team_color': str}}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 進站圈追蹤 {driver_num: set of lap numbers}
        self._pit_laps: Dict[str, set] = {}
        
        # 每位車手的個人最高速 {driver_num: max_speed}
        self._personal_best_speeds: Dict[str, float] = {}
        
        # 上一次記錄的圈數 {driver_num: lap_num}
        self._last_lap_recorded: Dict[str, int] = {}
        
        # 當前圈的速度樣本追蹤 {driver_num: max_speed_this_lap}
        self._current_lap_max_speed: Dict[str, float] = {}
        
        self._init_ui()
        
        logger.info("[TOP_SPEED_HISTORY] TopSpeedHistoryTableWidget initialized")
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 表格
        self.table = QTableWidget()
        self.table.setProperty("is_live_timing_widget", True)
        
        # 表格屬性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 表頭設置
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setDefaultSectionSize(70)
        
        # 行高
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.verticalHeader().setVisible(True)
        
        # 確保 viewport 也被標記
        if self.table.viewport():
            self.table.viewport().setProperty("is_live_timing_widget", True)
        
        layout.addWidget(self.table)
    
    def update_driver_info(self, driver_info: Dict[str, Dict[str, Any]]):
        """更新車手資訊"""
        for driver_num, info in driver_info.items():
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            self._driver_info[driver_num].update(info)
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """從 snapshot 更新資料"""
        drivers = snapshot.get('drivers', {})
        
        for driver_num, driver_data in drivers.items():
            # 獲取當前圈數
            lap_num = driver_data.get('lap')
            if lap_num is None:
                continue
            
            try:
                lap_num = int(lap_num)
            except (ValueError, TypeError):
                continue
            
            # 獲取當前速度
            current_speed = driver_data.get('speed', 0)
            if current_speed is None:
                current_speed = 0
            
            try:
                current_speed = float(current_speed)
            except (ValueError, TypeError):
                current_speed = 0
            
            # 追蹤當前圈的最高速度
            last_recorded = self._last_lap_recorded.get(driver_num, 0)
            
            if lap_num == last_recorded or (last_recorded == 0 and lap_num >= 1):
                # 同一圈內，更新最高速度
                current_max = self._current_lap_max_speed.get(driver_num, 0)
                if current_speed > current_max:
                    self._current_lap_max_speed[driver_num] = current_speed
            
            # 圈數變化：儲存上一圈的最高速度
            if lap_num > last_recorded and last_recorded > 0:
                # 儲存上一圈的資料
                completed_lap = last_recorded
                top_speed = self._current_lap_max_speed.get(driver_num, 0)
                
                if top_speed > 0:
                    # 檢測進站狀態
                    is_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
                    
                    # 儲存進站圈
                    if is_pit:
                        if driver_num not in self._pit_laps:
                            self._pit_laps[driver_num] = set()
                        self._pit_laps[driver_num].add(completed_lap)
                        if completed_lap > 1:
                            self._pit_laps[driver_num].add(completed_lap - 1)
                        self._pit_laps[driver_num].add(completed_lap + 1)
                    
                    # 儲存資料
                    if driver_num not in self._lap_data:
                        self._lap_data[driver_num] = {}
                    
                    self._lap_data[driver_num][completed_lap] = {
                        'top_speed': top_speed,
                        'is_pit': is_pit,
                    }
                    
                    # 更新個人最高速
                    current_best = self._personal_best_speeds.get(driver_num, 0)
                    if top_speed > current_best:
                        self._personal_best_speeds[driver_num] = top_speed
                
                # 重置當前圈追蹤
                self._current_lap_max_speed[driver_num] = current_speed
            
            # 初始化第一圈
            if last_recorded == 0:
                self._current_lap_max_speed[driver_num] = current_speed
            
            # 更新車手資訊
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            
            self._driver_info[driver_num]['tla'] = driver_data.get('driver_tla', driver_num)
            self._driver_info[driver_num]['position'] = driver_data.get('position', 99)
            self._driver_info[driver_num]['team_color'] = driver_data.get('team_color', 'CCCCCC')
            
            # 記錄已處理的圈數
            self._last_lap_recorded[driver_num] = lap_num
        
        # 刷新表格
        self._refresh_table()
    
    def _refresh_table(self):
        """刷新表格顯示"""
        if not self._lap_data:
            return
        
        # 獲取所有車手並按當前名次排序
        sorted_drivers = sorted(
            self._driver_info.items(),
            key=lambda x: x[1].get('position', 99)
        )
        
        driver_nums = [d[0] for d in sorted_drivers]
        driver_tlas = [self._driver_info.get(d, {}).get('tla', d) for d in driver_nums]
        
        # 獲取所有圈數
        all_laps = set()
        for driver_laps in self._lap_data.values():
            all_laps.update(driver_laps.keys())
        
        if not all_laps:
            return
        
        # 圈數由大到小排序 (最新的圈在最上面)
        sorted_laps = sorted(all_laps, reverse=True)
        
        # 設置表格大小
        self.table.setColumnCount(len(driver_nums))
        self.table.setRowCount(len(sorted_laps))
        
        # 設置表頭 (車手代碼)
        self.table.setHorizontalHeaderLabels(driver_tlas)
        
        # 設置表頭車隊顏色和欄寬
        for col, driver_num in enumerate(driver_nums):
            header_item = self.table.horizontalHeaderItem(col)
            if header_item:
                team_color = self._driver_info.get(driver_num, {}).get('team_color', 'CCCCCC')
                # 確保顏色格式正確 (加上 # 前綴)
                if not team_color.startswith('#'):
                    team_color = f'#{team_color}'
                header_item.setForeground(QColor(team_color))  # 車隊顏色文字
            self.table.setColumnWidth(col, 70)
        
        # 設置行標籤 (圈數)
        self.table.setVerticalHeaderLabels([str(lap) for lap in sorted_laps])
        
        # 填充資料
        for row, lap_num in enumerate(sorted_laps):
            for col, driver_num in enumerate(driver_nums):
                lap_info = self._lap_data.get(driver_num, {}).get(lap_num)
                
                if lap_info:
                    top_speed = lap_info.get('top_speed', 0)
                    is_pit = lap_info.get('is_pit', False)
                    
                    # 檢查是否為進站相關圈
                    pit_set = self._pit_laps.get(driver_num, set())
                    is_pit_related = lap_num in pit_set
                    
                    # 檢查是否為個人最高速
                    personal_best = self._personal_best_speeds.get(driver_num, 0)
                    is_personal_best = (top_speed > 0 and abs(top_speed - personal_best) < 0.1)
                    
                    # 格式化顯示
                    item = QTableWidgetItem(f"{top_speed:.0f}")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # 設置顏色
                    self._apply_cell_color(
                        item,
                        top_speed,
                        is_pit_related,
                        is_personal_best
                    )
                    
                    self.table.setItem(row, col, item)
                else:
                    # 空儲存格
                    item = QTableWidgetItem('')
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setForeground(QColor(COLOR_NORMAL_FG))
                    self.table.setItem(row, col, item)
    
    def _apply_cell_color(
        self,
        item: QTableWidgetItem,
        top_speed: float,
        is_pit_related: bool,
        is_personal_best: bool
    ):
        """設置儲存格顏色"""
        if is_pit_related:
            # 進站圈：紫色背景
            item.setBackground(QColor(COLOR_PIT_LAP_BG))
            item.setForeground(QColor(COLOR_PIT_LAP_FG))
        elif is_personal_best:
            # 個人最高速：淺紫色文字
            item.setForeground(QColor(COLOR_PERSONAL_BEST_FG))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        else:
            # 正常：淺灰文字
            item.setForeground(QColor(COLOR_NORMAL_FG))
    
    def clear(self):
        """清除所有資料"""
        self._lap_data.clear()
        self._driver_info.clear()
        self._pit_laps.clear()
        self._personal_best_speeds.clear()
        self._last_lap_recorded.clear()
        self._current_lap_max_speed.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


class LiveTimingTopSpeedHistory(BaseLiveTimingMDI):
    """
    Top Speed History MDI 模組
    
    顯示每個車手每一圈的最高速度。
    紫色文字標示該車手的個人最高速圈。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr('top_speed_history', 'Top Speed History'))
        self.setMinimumSize(600, 200)
        self.resize(900, 300)
        
        logger.info("[TOP_SPEED_HISTORY_MDI] LiveTimingTopSpeedHistory initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.history_widget = TopSpeedHistoryTableWidget()
        self._main_layout.addWidget(self.history_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        driver_info = race_info.get('driver_info', {})
        self.history_widget.update_driver_info(driver_info)
        logger.info("[TOP_SPEED_HISTORY_MDI] Race loaded: %s %s", race_info.get('year'), race_info.get('race'))
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        self.history_widget.clear()
        logger.info("[TOP_SPEED_HISTORY_MDI] Race unloaded")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated"""
        self.history_widget.update_from_snapshot(snapshot)
    
    def _cleanup(self):
        """清理資源"""
        self.history_widget.clear()
