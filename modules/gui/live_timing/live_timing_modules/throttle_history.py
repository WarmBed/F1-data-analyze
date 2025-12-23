"""
Live Timing Throttle 95% History
================================

油門 95% 歷史記錄表模組，顯示每個車手每一圈的油門使用率 (>=95% 的比率)。

顏色標註：
- 紅色: 省油 (偏離基線 < -5%)
- 黃色: 可疑 (偏離基線 -3% ~ -5%)
- 紫色: 進站圈
- 白色: 正常

Author: F1T Team
Date: 2025-12-15
"""

from typing import Dict, List, Any, Optional
import statistics

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
COLOR_FUEL_SAVING_HIGH_BG = '#FF6B6B'  # 淺紅色背景 (省油)
COLOR_FUEL_SAVING_HIGH_FG = '#FFFFFF'
COLOR_FUEL_SAVING_MED_BG = '#FFEB7A'   # 淺黃色背景 (可疑)
COLOR_FUEL_SAVING_MED_FG = '#000000'
COLOR_PIT_LAP_BG = '#BA68C8'           # 淺紫色背景 (進站)
COLOR_PIT_LAP_FG = '#FFFFFF'
COLOR_NORMAL_FG = '#E0E0E0'            # 淺灰色文字


class ThrottleHistoryTableWidget(QWidget):
    """
    油門 95% 歷史表格 Widget
    
    顯示格式：
    | Lap | VER | LEC | NOR | SAI | ... |
    |-----|-----|-----|-----|-----|-----|
    | 1   | 55.2 | 54.8 | 53.1 | ... |
    | 2   | 56.1 | 55.3 | 54.2 | ... |
    
    欄位按當前名次排序 (P1 在最左邊)
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設置深色背景
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setProperty("is_live_timing_widget", True)
        
        # 資料儲存
        # {driver_num: {lap_num: {'throttle_pct': float, 'is_pit': bool, 'lamp': str}}}
        self._lap_data: Dict[str, Dict[int, Dict[str, Any]]] = {}
        
        # 車手資訊 {driver_num: {'tla': str, 'position': int, 'team_color': str}}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        
        # 進站圈追蹤 {driver_num: set of lap numbers}
        self._pit_laps: Dict[str, set] = {}
        
        # 動態基線追蹤 {driver_num: [throttle_pct list for rolling median]}
        self._rolling_history: Dict[str, List[float]] = {}
        
        # 上一次記錄的圈數 {driver_num: lap_num}
        self._last_lap_recorded: Dict[str, int] = {}
        
        self._init_ui()
        
        logger.info("[THROTTLE_HISTORY] ThrottleHistoryTableWidget initialized")
    
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
        header.setDefaultSectionSize(55)
        
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
            
            # 檢查是否已記錄過這一圈
            last_recorded = self._last_lap_recorded.get(driver_num, 0)
            if lap_num <= last_recorded:
                continue
            
            # 獲取油門百分比
            throttle_pct = driver_data.get('throttle_95_pct', 0)
            if throttle_pct <= 0:
                continue
            
            # 檢測進站狀態
            is_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
            lamp = driver_data.get('fuel_saving_lamp', '')
            
            # 更新車手資訊
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            
            self._driver_info[driver_num]['tla'] = driver_data.get('driver_tla', driver_num)
            self._driver_info[driver_num]['position'] = driver_data.get('position', 99)
            self._driver_info[driver_num]['team_color'] = driver_data.get('team_color', 'CCCCCC')
            
            # 儲存進站圈
            if is_pit:
                if driver_num not in self._pit_laps:
                    self._pit_laps[driver_num] = set()
                self._pit_laps[driver_num].add(lap_num)
                if lap_num > 1:
                    self._pit_laps[driver_num].add(lap_num - 1)
                self._pit_laps[driver_num].add(lap_num + 1)
            
            # 儲存資料
            if driver_num not in self._lap_data:
                self._lap_data[driver_num] = {}
            
            self._lap_data[driver_num][lap_num] = {
                'throttle_pct': throttle_pct,
                'is_pit': is_pit,
                'lamp': lamp,
            }
            
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
        
        # 計算每個車手的動態基線（用於顏色判斷）
        driver_baselines: Dict[str, float] = {}
        for driver_num in driver_nums:
            laps_data = self._lap_data.get(driver_num, {})
            pit_set = self._pit_laps.get(driver_num, set())
            
            # 過濾進站圈
            valid_values = [
                data['throttle_pct']
                for lap, data in laps_data.items()
                if lap not in pit_set and data['throttle_pct'] > 0
            ]
            
            if len(valid_values) >= 3:
                # 取最近 10 圈計算中位數
                recent_values = valid_values[-10:]
                median_val = statistics.median(recent_values)
                # 過濾異常值
                filtered = [v for v in recent_values if v > median_val * 0.7]
                if len(filtered) >= 3:
                    driver_baselines[driver_num] = statistics.median(filtered)
                else:
                    driver_baselines[driver_num] = median_val
        
        # 設置表格大小
        self.table.setColumnCount(len(driver_nums))
        self.table.setRowCount(len(sorted_laps))
        
        # 設置表頭 (車手代碼)
        self.table.setHorizontalHeaderLabels(driver_tlas)
        
        # 設置行標籤 (圈數)
        self.table.setVerticalHeaderLabels([str(lap) for lap in sorted_laps])
        
        # 填充資料
        for row, lap_num in enumerate(sorted_laps):
            for col, driver_num in enumerate(driver_nums):
                lap_info = self._lap_data.get(driver_num, {}).get(lap_num)
                
                if lap_info:
                    throttle_pct = lap_info.get('throttle_pct', 0)
                    is_pit = lap_info.get('is_pit', False)
                    lamp = lap_info.get('lamp', '')
                    
                    # 檢查是否為進站相關圈
                    pit_set = self._pit_laps.get(driver_num, set())
                    is_pit_related = lap_num in pit_set
                    
                    # 格式化顯示
                    item = QTableWidgetItem(f"{throttle_pct:.1f}")
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # 設置顏色
                    self._apply_cell_color(
                        item,
                        throttle_pct,
                        lamp,
                        is_pit_related,
                        driver_baselines.get(driver_num)
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
        throttle_pct: float,
        lamp: str,
        is_pit_related: bool,
        baseline: Optional[float]
    ):
        """設置儲存格顏色"""
        if is_pit_related:
            # 進站圈：紫色
            item.setBackground(QColor(COLOR_PIT_LAP_BG))
            item.setForeground(QColor(COLOR_PIT_LAP_FG))
        elif lamp == 'R':
            # 紅燈：省油
            item.setBackground(QColor(COLOR_FUEL_SAVING_HIGH_BG))
            item.setForeground(QColor(COLOR_FUEL_SAVING_HIGH_FG))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        elif lamp == 'Y':
            # 黃燈：可疑
            item.setBackground(QColor(COLOR_FUEL_SAVING_MED_BG))
            item.setForeground(QColor(COLOR_FUEL_SAVING_MED_FG))
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
        self._rolling_history.clear()
        self._last_lap_recorded.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


class LiveTimingThrottleHistory(BaseLiveTimingMDI):
    """
    Throttle 95% History MDI 模組
    
    顯示每個車手每一圈的油門 95% 使用率。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr('throttle_history', 'Throttle 95% History'))
        self.setMinimumSize(600, 200)
        self.resize(900, 300)
        
        logger.info("[THROTTLE_HISTORY_MDI] LiveTimingThrottleHistory initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.history_widget = ThrottleHistoryTableWidget()
        self._main_layout.addWidget(self.history_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        driver_info = race_info.get('driver_info', {})
        self.history_widget.update_driver_info(driver_info)
        logger.info("[THROTTLE_HISTORY_MDI] Race loaded: %s %s", race_info.get('year'), race_info.get('race'))
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        self.history_widget.clear()
        logger.info("[THROTTLE_HISTORY_MDI] Race unloaded")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated"""
        self.history_widget.update_from_snapshot(snapshot)
    
    def _cleanup(self):
        """清理資源"""
        self.history_widget.clear()
