"""
Live Timing Lap History
=======================

圈速歷史記錄表模組，顯示每個車手每一圈的圈速/S1/S2/S3。

四個獨立模組：
- Lap History - Lap Time: 圈速表
- Lap History - S1: 第一區間表  
- Lap History - S2: 第二區間表
- Lap History - S3: 第三區間表

顏色標註：
- 紫色: 全場最快 (Overall Best)
- 綠色: 個人最快 (Personal Best)
- 深紅色: 進站圈 (PIT)
- 橘色: Safety Car 圈
- 白色: 普通時間

Author: F1T Team
Date: 2025-12-04
"""

from typing import Dict, List, Any, Optional
import time

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

# 嘗試導入通用顏色系統
COLOR_PALETTE_AVAILABLE = False
color_palette_provider = None
try:
    from modules.gui.themes import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    pass


logger = get_logger("live_timing.lap_history", component="gui")


# ===========================================
# 顏色常數
# ===========================================
COLOR_OVERALL_BEST_BG = '#FF00FF'  # 紫色背景
COLOR_OVERALL_BEST_FG = '#FFFFFF'  # 白色文字
COLOR_PERSONAL_BEST_BG = '#00DD00'  # 綠色背景
COLOR_PERSONAL_BEST_FG = '#000000'  # 黑色文字
COLOR_PIT_LAP_BG = '#8B0000'  # 深紅色背景
COLOR_PIT_LAP_FG = '#FFFFFF'  # 白色文字
COLOR_SC_LAP_BG = '#FF8C00'  # 橘色背景
COLOR_SC_LAP_FG = '#000000'  # 黑色文字
COLOR_NORMAL_FG = '#E0E0E0'  # 淺灰色文字


class LapHistoryTableWidget(QWidget):
    """
    圈速歷史表格 Widget
    
    顯示格式：
    | Lap | VER | LEC | NOR | SAI | ... |
    |-----|-----|-----|-----|-----|-----|
    | 1   | 1:35.123 | 1:35.456 | ... |
    | 2   | 1:33.456 | 1:33.789 | ... |
    
    欄位按當前名次排序 (P1 在最左邊)
    """
    
    def __init__(self, data_type: str = 'lap_time', parent=None):
        """
        初始化表格
        
        Args:
            data_type: 資料類型 ('lap_time', 's1', 's2', 's3')
            parent: 父視窗
        """
        super().__init__(parent)
        
        self._data_type = data_type  # 'lap_time', 's1', 's2', 's3'
        
        # 設置深色背景
        self.setStyleSheet("background-color: #1a1a1a;")
        self.setProperty("is_live_timing_widget", True)
        
        # 資料儲存
        # {driver_num: {lap_num: {'time': str, 'time_seconds': float, 'is_pit': bool, 'is_sc': bool}}}
        # 注意: personal_best 和 overall_best 在 _refresh_table 中動態計算
        self._lap_data: Dict[str, Dict[int, Dict[str, Any]]] = {}
        
        # 車手資訊 {driver_num: {'tla': str, 'position': int, 'team_color': str}}
        self._driver_info: Dict[str, Dict[str, Any]] = {}
        
        # SC 圈數追蹤
        self._sc_laps: set = set()
        
        # 上一次更新的圈數 {driver_num: lap_num}
        self._last_lap_recorded: Dict[str, int] = {}
        
        self._init_ui()
        
        logger.info("[LAP_HISTORY] LapHistoryTableWidget initialized (type=%s)", data_type)
    
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
        header.setDefaultSectionSize(65)
        
        # 行高
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.verticalHeader().setVisible(True)  # 顯示行號 (圈數)
        
        # 確保 viewport 也被標記
        if self.table.viewport():
            self.table.viewport().setProperty("is_live_timing_widget", True)
        
        layout.addWidget(self.table)
    
    def set_sc_laps(self, sc_laps: set):
        """設置 Safety Car 圈數"""
        self._sc_laps = sc_laps
    
    def add_sc_lap(self, lap_num: int):
        """添加 SC 圈"""
        self._sc_laps.add(lap_num)
    
    def update_driver_info(self, driver_info: Dict[str, Dict[str, Any]]):
        """
        更新車手資訊
        
        Args:
            driver_info: {driver_num: {'tla': str, 'team': str, ...}}
        """
        for driver_num, info in driver_info.items():
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            self._driver_info[driver_num].update(info)
    
    def update_from_snapshot(self, snapshot: Dict[str, Any]):
        """
        從 snapshot 更新資料
        
        Args:
            snapshot: DataManager 發送的快照
        """
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
            
            # 獲取時間值
            time_value = self._get_time_value(driver_data)
            if not time_value:
                continue
            
            # 更新車手資訊
            if driver_num not in self._driver_info:
                self._driver_info[driver_num] = {}
            
            self._driver_info[driver_num]['tla'] = driver_data.get('driver_tla', driver_num)
            self._driver_info[driver_num]['position'] = driver_data.get('position', 99)
            self._driver_info[driver_num]['team_color'] = driver_data.get('team_color', 'CCCCCC')
            
            # 解析時間為秒數 (用於比較)
            time_seconds = self._parse_time_to_seconds(time_value)
            
            # 檢查是否進站圈
            is_pit = driver_data.get('in_pit', False) or driver_data.get('pit_out', False)
            
            # 檢查是否 SC 圈
            is_sc = lap_num in self._sc_laps
            
            # 儲存資料 (personal_best 和 overall_best 在 _refresh_table 中動態計算)
            if driver_num not in self._lap_data:
                self._lap_data[driver_num] = {}
            
            self._lap_data[driver_num][lap_num] = {
                'time': time_value,
                'time_seconds': time_seconds,
                'is_pit': is_pit,
                'is_sc': is_sc,
            }
            
            # 記錄已處理的圈數
            self._last_lap_recorded[driver_num] = lap_num
        
        # 刷新表格
        self._refresh_table()
    
    def _get_time_value(self, driver_data: Dict) -> Optional[str]:
        """根據資料類型獲取對應的時間值"""
        if self._data_type == 'lap_time':
            return driver_data.get('last_lap_time', '')
        elif self._data_type == 's1':
            return driver_data.get('s1_time', '')
        elif self._data_type == 's2':
            return driver_data.get('s2_time', '')
        elif self._data_type == 's3':
            return driver_data.get('s3_time', '')
        return None
    
    def _parse_time_to_seconds(self, time_str: str) -> Optional[float]:
        """將時間字串解析為秒數"""
        if not time_str:
            return None
        
        try:
            # 格式: "1:23.456" 或 "23.456"
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, IndexError):
            return None
    
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
        
        # ========== 動態計算最佳圈 ==========
        # 計算每位車手的個人最佳圈 (排除 PIT 圈和 SC 圈)
        personal_best_laps = {}  # {driver_num: lap_num}
        for driver_num, laps in self._lap_data.items():
            best_time = None
            best_lap = None
            for lap_num, lap_info in laps.items():
                # 排除 PIT 圈和 SC 圈
                if lap_info.get('is_pit', False) or lap_info.get('is_sc', False):
                    continue
                time_seconds = lap_info.get('time_seconds')
                if time_seconds is not None and time_seconds > 0:
                    if best_time is None or time_seconds < best_time:
                        best_time = time_seconds
                        best_lap = lap_num
            if best_lap is not None:
                personal_best_laps[driver_num] = best_lap
        
        # 計算全場最佳圈 (所有車手中最快的)
        overall_best_driver = None
        overall_best_lap = None
        overall_best_time = None
        for driver_num, best_lap in personal_best_laps.items():
            lap_info = self._lap_data.get(driver_num, {}).get(best_lap)
            if lap_info:
                time_seconds = lap_info.get('time_seconds')
                if time_seconds is not None:
                    if overall_best_time is None or time_seconds < overall_best_time:
                        overall_best_time = time_seconds
                        overall_best_driver = driver_num
                        overall_best_lap = best_lap
        # ========================================
        
        # 設置表格大小
        self.table.setColumnCount(len(driver_nums))
        self.table.setRowCount(len(sorted_laps))
        
        # 設置表頭 (車手代碼)
        self.table.setHorizontalHeaderLabels(driver_tlas)
        
        # 設置表頭車隊顏色 (文字顏色)
        for col, driver_num in enumerate(driver_nums):
            header_item = self.table.horizontalHeaderItem(col)
            if header_item:
                team_color = self._driver_info.get(driver_num, {}).get('team_color', 'CCCCCC')
                # 確保顏色格式正確 (加上 # 前綴)
                if not team_color.startswith('#'):
                    team_color = f'#{team_color}'
                header_item.setForeground(QColor(team_color))  # 車隊顏色文字
        
        # 設置行標籤 (圈數)
        self.table.setVerticalHeaderLabels([str(lap) for lap in sorted_laps])
        
        # 填充資料
        for row, lap_num in enumerate(sorted_laps):
            for col, driver_num in enumerate(driver_nums):
                lap_info = self._lap_data.get(driver_num, {}).get(lap_num)
                
                if lap_info:
                    time_value = lap_info.get('time', '')
                    item = QTableWidgetItem(time_value)
                    item.setTextAlignment(Qt.AlignCenter)
                    
                    # 動態判斷顏色
                    is_overall_best = (driver_num == overall_best_driver and lap_num == overall_best_lap)
                    is_personal_best = (personal_best_laps.get(driver_num) == lap_num)
                    
                    # 設置顏色
                    self._apply_cell_color_dynamic(
                        item, lap_info, 
                        is_overall_best=is_overall_best,
                        is_personal_best=is_personal_best
                    )
                    
                    self.table.setItem(row, col, item)
                else:
                    # 空儲存格
                    item = QTableWidgetItem('')
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setForeground(QColor(COLOR_NORMAL_FG))
                    self.table.setItem(row, col, item)
        
        # 設置欄寬
        for col in range(len(driver_nums)):
            self.table.setColumnWidth(col, 70)
    
    def _apply_cell_color_dynamic(self, item: QTableWidgetItem, lap_info: Dict, 
                                   is_overall_best: bool, is_personal_best: bool):
        """應用儲存格顏色 (動態計算版本)
        
        Args:
            item: 表格項目
            lap_info: 圈速資訊
            is_overall_best: 是否為全場最佳圈
            is_personal_best: 是否為個人最佳圈
        """
        is_pit = lap_info.get('is_pit', False)
        is_sc = lap_info.get('is_sc', False)
        
        # 優先級: 全場最佳 > 個人最佳 > 進站圈 > SC圈 > 普通
        # 注意: 全場最佳不會同時顯示個人最佳綠色，只顯示紫色
        if is_overall_best:
            item.setBackground(QColor(COLOR_OVERALL_BEST_BG))
            item.setForeground(QColor(COLOR_OVERALL_BEST_FG))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        elif is_personal_best:
            # 只有非全場最佳的個人最佳才顯示綠色
            item.setBackground(QColor(COLOR_PERSONAL_BEST_BG))
            item.setForeground(QColor(COLOR_PERSONAL_BEST_FG))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        elif is_pit:
            item.setBackground(QColor(COLOR_PIT_LAP_BG))
            item.setForeground(QColor(COLOR_PIT_LAP_FG))
        elif is_sc:
            item.setBackground(QColor(COLOR_SC_LAP_BG))
            item.setForeground(QColor(COLOR_SC_LAP_FG))
        else:
            item.setForeground(QColor(COLOR_NORMAL_FG))
    
    def clear(self):
        """清除所有資料"""
        self._lap_data.clear()
        self._driver_info.clear()
        self._sc_laps.clear()
        self._last_lap_recorded.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)


class LiveTimingLapHistoryBase(BaseLiveTimingMDI):
    """
    Lap History MDI 基類
    
    子類只需指定 _data_type 即可
    """
    
    _data_type = 'lap_time'  # 子類覆寫
    _window_title_key = 'lap_history_lap_time'  # 子類覆寫
    _default_title = 'Lap History - Lap Time'  # 子類覆寫
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr(self._window_title_key, self._default_title))
        self.setMinimumSize(600, 200)
        self.resize(800, 250)
        
        logger.info("[LAP_HISTORY_MDI] %s initialized", self.__class__.__name__)
    
    def _setup_ui(self):
        """Setup UI components"""
        self.history_widget = LapHistoryTableWidget(data_type=self._data_type)
        self._main_layout.addWidget(self.history_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        driver_info = race_info.get('driver_info', {})
        self.history_widget.update_driver_info(driver_info)
        logger.info("[LAP_HISTORY_MDI] Race loaded: %s %s", race_info.get('year'), race_info.get('race'))
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        self.history_widget.clear()
        logger.info("[LAP_HISTORY_MDI] Race unloaded")
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """Snapshot updated"""
        self.history_widget.update_from_snapshot(snapshot)
    
    def _cleanup(self):
        """清理資源"""
        self.history_widget.clear()


class LiveTimingLapHistoryLapTime(LiveTimingLapHistoryBase):
    """Lap History - Lap Time 模組"""
    _data_type = 'lap_time'
    _window_title_key = 'lap_history_lap_time'
    _default_title = 'Lap History - Lap Time'


class LiveTimingLapHistoryS1(LiveTimingLapHistoryBase):
    """Lap History - S1 模組"""
    _data_type = 's1'
    _window_title_key = 'lap_history_s1'
    _default_title = 'Lap History - S1'


class LiveTimingLapHistoryS2(LiveTimingLapHistoryBase):
    """Lap History - S2 模組"""
    _data_type = 's2'
    _window_title_key = 'lap_history_s2'
    _default_title = 'Lap History - S2'


class LiveTimingLapHistoryS3(LiveTimingLapHistoryBase):
    """Lap History - S3 模組"""
    _data_type = 's3'
    _window_title_key = 'lap_history_s3'
    _default_title = 'Lap History - S3'
