"""
Live Timing Ranking Tower MDI
=============================

即時排名塔 MDI 模組，顯示車手排名、圈速、輪胎策略等資訊。

Extracted from: demo_live_position_tracking.py lines 6214-6779

Author: F1T Team
Date: 2025-12-04
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QMenu, QHeaderView, QStyledItemDelegate, QStyle
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont, QPen

from typing import Dict, List, Any, Optional
import json
import os

from core.gui_i18n import tr
from ..core.base_live_mdi import BaseLiveTimingMDI

from core.logger import get_logger
logger = get_logger(__name__)

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    # fallback to default colors; log once
    get_logger("live_timing.ranking_tower", component="gui").warning(
        "[RANKING_TOWER] color_palette_provider not available"
    )


logger = get_logger("live_timing.ranking_tower", component="gui")


# ===========================================
# 輪胎常數
# ===========================================
TYRE_ABBREV = {
    'SOFT': 'S',
    'MEDIUM': 'M',
    'HARD': 'H',
    'INTERMEDIATE': 'I',
    'WET': 'W',
    'UNKNOWN': '?'
}

# 輪胎背景顏色 (用於儲存格背景)
TYRE_COLORS = {
    'SOFT': '#FF0000',
    'MEDIUM': '#FFFF00',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#00FF00',
    'WET': '#0099FF',
    'UNKNOWN': '#888888'
}

# 輪胎文字顏色 (深色模式下在表格中顯示)
TYRE_TEXT_COLORS = {
    'SOFT': '#FF4444',      # 亮紅色
    'MEDIUM': '#FFFF00',    # 黃色
    'HARD': '#FFFFFF',      # 白色
    'INTERMEDIATE': '#00FF00',  # 綠色
    'WET': '#66CCFF',       # 淡藍色
    'UNKNOWN': '#888888'    # 灰色
}


class RankingTableWidget(QWidget):
    """
    即時排名表 Widget
    
    顯示欄位：
    - P (排名)
    - +/- (名次變動)
    - No (車號)
    - Tyre (輪胎)
    - Age (輪胎壽命)
    - Pit (進站次數)
    - Driver (車手)
    - S1/S2/S3 (區間時間)
    - Last (上圈時間)
    - Best (最佳時間)
    - Delta (與最佳差距)
    - Gap (與領先者)
    - Int (與前車間隔)
    - Trend (間距趨勢: >> 追近, << 拉開, - 維持)
    - Lap (圈數)
    - P1%/P2%/P3% (勝率)
    - OT% (超車機率)
    - DRS
    
    採用深色主題設計。
    """
    
    # 信號
    driver_selected = pyqtSignal(str)  # 車手被選中
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ 優化：預先創建常用顏色對象緩存，避免重複創建
        self._color_cache = {
            'default_text': QColor('#E0E0E0'),
            'white': QColor('#FFFFFF'),
            'black': QColor('#000000'),
            'green': QColor('#00FF00'),
            'dark_green': QColor('#00DD00'),
            'purple': QColor('#FF00FF'),
            'yellow': QColor('#FFFF00'),
            'orange': QColor('#FFA500'),
            'light_blue': QColor('#4A90E2'),
            'pit_yellow': QColor('#FFD700'),
            'red': QColor('#FF0000'),
            'grey': QColor('#888888'),
            'light_green': QColor('#66FF66'),
            'deep_green': QColor('#00CC00'),
            'light_blue': QColor('#6699FF'),
            'blue': QColor('#0066FF'),
            'deep_blue': QColor('#0044CC'),
        }
        
        # 進站策略資料庫（輪胎建議圈數）
        self._pit_strategy_db: Dict[str, Any] = {}
        self._current_circuit: str = ""
        self._circuit_pit_windows: Dict[str, Dict] = {}  # {compound: {max_stint_laps, optimal_pit_lap, ...}}
        self._load_pit_strategy_database()
        
        # 設置深色背景
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # 設定 Live Timing 識別屬性 (供 force_white_background 排除使用)
        self.setProperty("is_live_timing_widget", True)
        
        self._current_snapshot: Optional[Dict] = None
        self._grid_positions: Dict[str, int] = {}
        self._grid_initialized = False
        self._driver_stints: Dict[str, List[Dict[str, Any]]] = {}
        self._pit_events: List[Dict[str, Any]] = []
        self._current_tyre_state: Dict[str, Dict[str, Any]] = {}
        self._current_car_data: Dict[str, Dict[str, Any]] = {}
        
        # 名次變更追蹤 (用於紅框顯示)
        self._previous_positions: Dict[str, int] = {}  # {driver_num: position}
        self._position_changed_drivers: Dict[str, float] = {}  # {driver_num: race_time_seconds}
        self._position_change_duration = 30.0  # 紅框顯示時間 (播放秒數)
        self._current_race_time_seconds: float = 0.0  # 當前播放時間
        
        # 進站 (PIT) 狀態追蹤
        self._drivers_in_pit: Dict[str, float] = {}  # {driver_num: pit_start_race_time}
        self._previous_pit_states: Dict[str, bool] = {}  # {driver_num: was_in_pit}
        
        # 最快圈速追蹤 (用於深紫色背景顯示)
        self._fastest_best_lap: Optional[str] = None  # 全場最快的 best_lap 時間字串
        
        # 紅框更新計時器
        self._highlight_timer = QTimer(self)
        self._highlight_timer.timeout.connect(self._check_highlight_expiry)
        self._highlight_timer.start(1000)  # 每秒檢查一次
        
        # F87 省胎分數查詢 (DataManager 引用)
        self._data_manager = None
        
        self._init_ui()
    
    def set_data_manager(self, data_manager):
        """設定 DataManager 引用 (用於查詢省胎分數)"""
        self._data_manager = data_manager
    
    def _load_pit_strategy_database(self):
        """載入輪胎衰退資料庫 - 僅使用 API，禁止本地回退"""
        # 僅通過 API 獲取
        if self._load_pit_strategy_via_api():
            return
        
        # API 失敗，顯示錯誤（禁止本地回退）
        logger.warning("[RANKING_TOWER] API 獲取配置失敗，請確認 API 服務器已啟動")
    
    def _load_pit_strategy_via_api(self) -> bool:
        """通過 API 獲取輪胎衰退數據庫"""
        try:
            from modules.gui.live_timing.core.api_client import get_api_client
            
            api_client = get_api_client()
            tire_data = api_client.get_tire_degradation()
            
            if tire_data:
                self._pit_strategy_db = tire_data
                logger.info(
                    "[RANKING_TOWER] 載入輪胎衰退數據庫 (API): %s circuits",
                    len(tire_data.get('circuits', {})),
                )
                return True
            
            return False
            
        except Exception as e:
            logger.exception("[RANKING_TOWER] API 獲取輪胎衰退數據庫失敗: %s", e)
            return False
    
    def set_circuit(self, circuit_name: str):
        """
        設置當前賽道，載入對應的輪胎建議數據
        
        Args:
            circuit_name: 賽道名稱 (例如: "Qatar", "Lusail", "Japanese")
        """
        if not circuit_name:
            return
        
        # 標準化賽道名稱 (移除 "_Race" 等後綴)
        circuit_key = circuit_name.replace("_Race", "").replace("_", " ").strip()
        
        # LiveF1 → tire_degradation_database 名稱映射
        name_map = {
            "Japanese": "Suzuka",
            "Qatar": "Lusail",
            "Qatari": "Lusail",
            "Chinese": "Shanghai",
            "Australian": "Melbourne",
            "Saudi Arabian": "Jeddah",
            "Saudi": "Jeddah",
            "British": "Silverstone",
            "Austrian": "Spielberg",
            "Hungarian": "Budapest",
            "Belgian": "Spa",
            "Dutch": "Zandvoort",
            "Italian": "Monza",
            "Emilia Romagna": "Imola",
            "Spanish": "Barcelona",
            "Canadian": "Montreal",
            "United States": "Austin",
            "American": "Austin",
            "Mexican": "Mexico",
            "Brazilian": "Interlagos",
            "Sao Paulo": "Interlagos",
            "Las Vegas": "Las_Vegas",
            "Abu Dhabi": "Yas_Marina",
            "Azerbaijan": "Baku",
        }
        
        # 查找對應的 key
        db_key = name_map.get(circuit_key, circuit_key)
        
        circuits = self._pit_strategy_db.get('circuits', {})
        if db_key in circuits:
            circuit_data = circuits[db_key]
            self._current_circuit = db_key
            # 使用 optimal_stint_length 作為建議圈數
            self._circuit_pit_windows = circuit_data.get('optimal_stint_length', {})
            logger.info(
                "[RANKING_TOWER] Circuit set: %s, optimal stint: %s",
                db_key,
                self._circuit_pit_windows,
            )
        else:
            # 嘗試模糊匹配
            for key in circuits.keys():
                if key.lower() in circuit_key.lower() or circuit_key.lower() in key.lower():
                    circuit_data = circuits[key]
                    self._current_circuit = key
                    self._circuit_pit_windows = circuit_data.get('optimal_stint_length', {})
                    logger.info(
                        "[RANKING_TOWER] Circuit fuzzy match: %s, optimal stint: %s",
                        key,
                        self._circuit_pit_windows,
                    )
                    return
            
            logger.warning(
                "[RANKING_TOWER] Circuit not found in database: %s (tried: %s)",
                circuit_key,
                db_key,
            )
            self._circuit_pit_windows = {}

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 表格設置
        self.table = QTableWidget()
        self.table.setProperty("is_live_timing_widget", True)  # 標記為 Live Timing widget
        self.table.setColumnCount(24)  # 增加 CC% 欄位
        self.table.setHorizontalHeaderLabels([
            "P", tr("driver"), "+/-", "No", tr("tyre"), tr("age"), "Pit", tr("tyre_hist"),
            "S1", "S2", "S3",
            tr("last_lap"), tr("best_lap"), tr("delta"), tr("gap_leader"), tr("gap_ahead"), "Trend", tr("fuel_save"),
            "P1%", "P2%", "P3%", "OT%", "CC%",  # ❌ OT% 和 CC% 已禁用（性能優化）
            "DRS"
        ])
        
        # 啟用排序
        self.table.setSortingEnabled(True)
        
        # 表格屬性
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.NoSelection)
        self.table.setAlternatingRowColors(False)  # 關閉交替行顏色，避免繼承主 GUI 的白色調色板
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 與 Demo 一致：不設定 QTableWidget 的 QSS 樣式表
        # 讓 setBackground() 和 setForeground() 能正常工作
        # Demo 也沒有為表格設定任何 stylesheet
        
        # 欄位寬度
        self._set_column_widths()
        
        # 表頭設置
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        
        # 行高
        self.table.verticalHeader().setDefaultSectionSize(22)
        self.table.verticalHeader().setVisible(False)
        
        # 右鍵選單
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # 確保 viewport 也被標記為 Live Timing widget
        if self.table.viewport():
            self.table.viewport().setProperty("is_live_timing_widget", True)
        
        layout.addWidget(self.table)
    
    def _set_column_widths(self):
        """設置欄位寬度"""
        widths = [
            22,   # P
            45,   # 車手
            33,   # +/-
            26,   # No (隱藏)
            22,   # 胎
            26,   # 齡
            26,   # Pit
            70,   # 換胎 (隱藏)
            58,   # S1
            58,   # S2
            58,   # S3
            70,   # 上圈
            70,   # 最佳
            60,   # 差距
            75,   # 領先
            75,   # 前車
            36,   # Trend (趨勢)
            38,   # 省油% (原為圈)
            41,   # P1%
            41,   # P2%
            41,   # P3%
            41,   # OT% (超車機率)
            41,   # CC% (近距離接觸機率)
            32    # DRS
        ]
        
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)
        
        # 隱藏欄位
        self.table.hideColumn(3)   # No
        self.table.hideColumn(7)   # 換胎
        self.table.hideColumn(17)  # SF% (暫時隱藏)
        self.table.hideColumn(21)  # ❌ OT% (超車機率 - 已禁用以提升性能)
        self.table.hideColumn(22)  # ❌ CC% (近距離接觸 - 已禁用以提升性能)
    
    def _show_context_menu(self, pos):
        """顯示右鍵選單"""
        item = self.table.itemAt(pos)
        if item is None:
            # 點擊空白區域不顯示選單
            return
        
        row = item.row()
        driver_item = self.table.item(row, 1)
        if driver_item is None:
            return
        
        driver_data = driver_item.data(Qt.UserRole)
        if not driver_data:
            return
        
        driver_num = driver_data.get('driver_num', '')
        driver_tla = driver_data.get('driver_tla', driver_num)
        
        menu = QMenu(self.table)
        
        # 選擇車手
        select_action = menu.addAction(tr("select_driver_action").format(driver_tla))
        select_action.triggered.connect(lambda: self.driver_selected.emit(driver_num))
        
        menu.exec_(self.table.viewport().mapToGlobal(pos))
    
    def _add_pit_windows_menu(self, menu: QMenu):
        """添加 Pit Windows 修改選單"""
        # 設置深色主題樣式 (覆蓋主 GUI 的白色主題)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2D2D2D;
                border: 1px solid #555555;
                color: #FFFFFF;
                padding: 2px;
            }
            QMenu::item {
                padding: 4px 20px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
            QMenu::item:disabled {
                color: #888888;
            }
            QMenu::separator {
                height: 1px;
                background-color: #555555;
                margin: 2px 5px;
            }
        """)
        pit_menu = menu.addMenu(tr("modify_pit_windows"))
        
        # 顯示當前賽道資訊
        circuit_name = self._current_circuit or "Unknown"
        info_action = pit_menu.addAction(f"Circuit: {circuit_name}")
        info_action.setEnabled(False)
        pit_menu.addSeparator()
        
        # 無論是否有賽道數據都顯示可編輯的選項
        for compound in ["SOFT", "MEDIUM", "HARD"]:
            current_value = self._circuit_pit_windows.get(compound, 25)
            # 使用 i18n 翻譯
            label_key = f"optimal_stint_{compound.lower()}"
            label = tr(label_key).format(current_value)
            action = pit_menu.addAction(label)
            action.triggered.connect(lambda checked, c=compound: self._modify_optimal_stint(c))
    
    def _modify_optimal_stint(self, compound: str):
        """修改指定輪胎的最佳 stint 長度"""
        from PyQt5.QtWidgets import QInputDialog
        
        current_value = self._circuit_pit_windows.get(compound, 25)
        
        new_value, ok = QInputDialog.getInt(
            self.table,
            tr("modify_optimal_stint_title").format(compound),
            tr("modify_optimal_stint_prompt").format(compound),
            current_value,  # 預設值
            5,              # 最小值
            60,             # 最大值
            1               # 步進值
        )
        
        if ok:
            self._circuit_pit_windows[compound] = new_value
            logger.info(
                "[RANKING_TOWER] Updated %s optimal stint to %s laps",
                compound,
                new_value,
            )
            
            # 強制刷新顯示（重新計算輪胎老化顏色）
            if self._current_snapshot and self._current_tyre_state:
                self.update_display(self._current_snapshot, self._current_tyre_state)
    
    def set_tyre_state(self, tyre_state: Dict[str, Dict[str, Any]]):
        """設置即時輪胎狀態"""
        self._current_tyre_state = tyre_state
    
    def set_car_data(self, car_data: Dict[str, Dict[str, Any]]):
        """設置車輛遙測資料"""
        self._current_car_data = car_data
    
    def update_display(self, snapshot: Dict, tyre_state: Dict[str, Dict[str, Any]] = None):
        """
        更新顯示（✅ 高頻優化版本）
        
        優化策略：
        1. 使用 blockSignals 減少信號觸發
        2. 批次更新所有行後才重新啟用信號
        3. 只在必要時才 setRowCount（車手數量變化）
        
        Args:
            snapshot: 當前時間快照
            tyre_state: 即時輪胎狀態
        """
        # ✅ 優化 1: 阻止所有信號觸發，批次更新完成後再恢復
        self.table.blockSignals(True)
        
        self._current_snapshot = snapshot
        if tyre_state:
            self._current_tyre_state = tyre_state
        
        # 更新當前播放時間
        self._current_race_time_seconds = snapshot.get('race_time_seconds', 0.0)
        
        drivers = snapshot.get('drivers', {})
        
        # 初始化發車位置
        if not self._grid_initialized:
            for driver_num, driver_data in drivers.items():
                pos = driver_data.get('position')
                if pos is not None:
                    self._grid_positions[driver_num] = pos
            self._grid_initialized = True
        
        # 按排名排序
        def get_sort_key(item):
            pos = item[1].get('position')
            if pos is None:
                return 999
            try:
                return int(pos)
            except (ValueError, TypeError):
                return 999
        
        sorted_drivers = sorted(drivers.items(), key=get_sort_key)
        
        # 檢測名次變更並記錄 (使用播放時間)
        current_race_time = self._current_race_time_seconds
        
        for driver_num, driver_data in drivers.items():
            current_pos = driver_data.get('position')
            if current_pos is None:
                continue
            
            try:
                current_pos = int(current_pos)
            except (ValueError, TypeError):
                continue
            
            previous_pos = self._previous_positions.get(driver_num)
            
            if previous_pos is not None and previous_pos != current_pos:
                # 名次變更！記錄這個車手 (使用播放時間)
                self._position_changed_drivers[driver_num] = current_race_time
            
            # 更新上一次排名記錄
            self._previous_positions[driver_num] = current_pos
            
            # 檢測進站狀態變化
            is_in_pit = driver_data.get('in_pit', False)
            was_in_pit = self._previous_pit_states.get(driver_num, False)
            
            if is_in_pit and not was_in_pit:
                # 剛進站，記錄進站開始時間
                self._drivers_in_pit[driver_num] = current_race_time
            elif not is_in_pit and was_in_pit:
                # 出站，移除進站記錄
                if driver_num in self._drivers_in_pit:
                    del self._drivers_in_pit[driver_num]
            
            self._previous_pit_states[driver_num] = is_in_pit
        
        # ✅ 優化 2: 只在車手數量變化時才 setRowCount
        current_row_count = self.table.rowCount()
        needed_row_count = len(sorted_drivers)
        
        if current_row_count != needed_row_count:
            self.table.setSortingEnabled(False)
            self.table.setRowCount(needed_row_count)
        
        # ✅ 計算全場最快的 best_lap (用於紫色背景顯示)
        fastest_best_lap_time = None
        fastest_best_lap_seconds = float('inf')
        
        for driver_num, driver_data in drivers.items():
            best_lap_time = driver_data.get('best_lap_time', '')
            if best_lap_time and best_lap_time.strip():
                # 轉換為秒數進行比較 (格式: "1:23.456")
                try:
                    if ':' in best_lap_time:
                        parts = best_lap_time.split(':')
                        minutes = int(parts[0])
                        seconds = float(parts[1])
                        total_seconds = minutes * 60 + seconds
                    else:
                        total_seconds = float(best_lap_time)
                    
                    if total_seconds < fastest_best_lap_seconds:
                        fastest_best_lap_seconds = total_seconds
                        fastest_best_lap_time = best_lap_time
                except (ValueError, IndexError):
                    pass
        
        # 儲存最快圈速供 _set_lap_times 使用
        self._fastest_best_lap = fastest_best_lap_time
        
        # ✅ 優化 3: 批次更新所有行
        for row, (driver_num, driver_data) in enumerate(sorted_drivers):
            self._update_row(row, driver_num, driver_data)
        
        # ✅ 優化 4: 恢復信號觸發
        self.table.blockSignals(False)
    
    def update_fast_columns(self, snapshot: Dict):
        """
        快速更新關鍵欄位（Gap Leader, Gap Ahead, DRS）
        
        這些欄位變化頻繁，需要較高的更新率 (30 FPS)
        其他欄位由 update_display() 以較低頻率更新 (10 FPS)
        """
        self.table.blockSignals(True)
        
        self._current_snapshot = snapshot
        self._current_race_time_seconds = snapshot.get('race_time_seconds', 0.0)
        
        drivers = snapshot.get('drivers', {})
        
        # 按排名排序
        def get_sort_key(item):
            pos = item[1].get('position')
            if pos is None:
                return 999
            try:
                return int(pos)
            except (ValueError, TypeError):
                return 999
        
        sorted_drivers = sorted(drivers.items(), key=get_sort_key)
        
        # 快速更新每行的 Gap 和 DRS 欄位
        for row, (driver_num, driver_data) in enumerate(sorted_drivers):
            if row >= self.table.rowCount():
                break
            
            # Gap to Leader (欄位 14) - P1 永遠不顯示
            position = driver_data.get('position')
            if position == 1 or position == '1':
                gap_leader_text = ""
            else:
                gap_leader_text = driver_data.get('gap_to_leader_display', '')
                if not gap_leader_text:
                    # fallback 嘗試其他可能的欄位名
                    gap_leader_text = driver_data.get('gap_leader', driver_data.get('gap_to_leader', ''))
            gap_item = self.table.item(row, 14)
            if gap_item:
                gap_item.setText(str(gap_leader_text) if gap_leader_text else '')
            
            # Gap to Ahead (欄位 15) - 使用與完整更新相同的欄位名
            if driver_data.get('position') == 1:
                gap_ahead_text = ""
            else:
                gap_ahead_text = driver_data.get('gap_to_ahead_display', '')
                if not gap_ahead_text:
                    # fallback 嘗試其他可能的欄位名
                    gap_ahead_text = driver_data.get('gap_ahead', driver_data.get('interval', ''))
            interval_item = self.table.item(row, 15)
            if interval_item:
                interval_item.setText(str(gap_ahead_text) if gap_ahead_text else '')
            
            # DRS (欄位 23)
            self._set_telemetry(row, driver_num)
        
        self.table.blockSignals(False)

    def _update_row(self, row: int, driver_num: str, driver_data: Dict):
        """
        更新單行數據（✅ 高頻優化版本）
        
        優化策略：
        1. 使用緩存的顏色對象
        2. 減少臨時對象創建
        3. 複用 QTableWidgetItem（如果可能）
        """
        # ✅ 使用緩存的顏色
        default_text_color = self._color_cache['default_text']
        
        # P - 排名 (欄位 0)
        pos_item = self.table.item(row, 0)
        if not pos_item:
            pos_item = QTableWidgetItem()
            self.table.setItem(row, 0, pos_item)
        
        pos_item.setText(str(driver_data.get('position', 'N/A')))
        pos_item.setTextAlignment(Qt.AlignCenter)
        pos_item.setForeground(default_text_color)
        font = pos_item.font()
        font.setBold(True)
        pos_item.setFont(font)
        
        # 車手 (欄位 1)
        self._set_driver_info(row, driver_num, driver_data)
        
        # +/- 名次變動 (欄位 2)
        self._set_position_change(row, driver_num, driver_data)
        
        # No - 車號 (欄位 3)
        num_item = self.table.item(row, 3)
        if not num_item:
            num_item = QTableWidgetItem()
            self.table.setItem(row, 3, num_item)
        
        num_item.setText(driver_num)
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setForeground(default_text_color)
        
        # 輪胎相關欄位 (欄位 4-7)
        self._set_tyre_info(row, driver_num)
        
        # 區間時間 (欄位 8-10)
        self._set_sector_times(row, driver_data)
        
        # 圈時相關 (欄位 11-17)
        self._set_lap_times(row, driver_num, driver_data)
        
        # 勝率 (欄位 18-20)
        self._set_probabilities(row, driver_data)
        
        # 遙測資料 (欄位 23)
        self._set_telemetry(row, driver_num)
        
        # 檢查是否需要顯示紅框 (名次變更)
        self._apply_position_change_highlight(row, driver_num)
        
        # 檢查並應用進站 (PIT) 黃色高亮
        self._apply_pit_highlight(row, driver_num, driver_data)
    
    def _apply_position_change_highlight(self, row: int, driver_num: str):
        """為名次變更的行設置紅色邊框 (使用播放時間)"""
        current_race_time = self._current_race_time_seconds
        
        if driver_num in self._position_changed_drivers:
            change_time = self._position_changed_drivers[driver_num]
            elapsed = current_race_time - change_time
            
            if elapsed >= 0 and elapsed < self._position_change_duration:
                # 仍在紅框顯示時間內 - 為該行所有儲存格設置紅色邊框
                red_border_color = QColor('#FF0000')
                
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        # 使用 UserRole+1 儲存原始背景色（如果尚未儲存）
                        if item.data(Qt.UserRole + 1) is None:
                            original_bg = item.background().color()
                            item.setData(Qt.UserRole + 1, original_bg.name())
                        
                        # 設置紅色邊框樣式 - 通過深紅色背景模擬邊框效果
                        # 因為 QTableWidgetItem 不支持直接設置邊框，使用微妙的背景色變化
                        current_bg = item.background().color()
                        # 添加紅色調
                        new_r = min(255, current_bg.red() + 60)
                        new_g = max(0, current_bg.green() - 20)
                        new_b = max(0, current_bg.blue() - 20)
                        item.setBackground(QColor(new_r, new_g, new_b))
            else:
                # ✅ 時間已過 - 恢復原始背景色
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        # 恢復原始背景色
                        original_bg_name = item.data(Qt.UserRole + 1)
                        if original_bg_name:
                            item.setBackground(QColor(original_bg_name))
                            # 清除儲存的原始顏色標記
                            item.setData(Qt.UserRole + 1, None)
                
                # 從追蹤字典中移除（避免重複處理）
                del self._position_changed_drivers[driver_num]
    
    def _apply_pit_highlight(self, row: int, driver_num: str, driver_data: Dict):
        """
        為進站中的車手設置黃色背景高亮，並用 PIT + 計時覆蓋整行（除 P 和 Driver）
        
        Args:
            row: 表格行號
            driver_num: 車手號碼
            driver_data: 車手數據
        """
        is_in_pit = driver_data.get('in_pit', False)
        
        if not is_in_pit:
            # 如果不在 PIT，確保移除之前的 span
            # 檢查是否有之前設置的 span 需要清除
            if hasattr(self, '_pit_span_rows') and row in self._pit_span_rows:
                # 重置 span（恢復為單一儲存格）
                self.table.setSpan(row, 2, 1, 1)
                self._pit_span_rows.discard(row)
            return
        
        # 初始化 pit span 追蹤集合
        if not hasattr(self, '_pit_span_rows'):
            self._pit_span_rows = set()
        
        # 計算進站時間
        pit_start_time = self._drivers_in_pit.get(driver_num)
        current_race_time = self._current_race_time_seconds
        
        if pit_start_time is not None:
            pit_duration = current_race_time - pit_start_time
            pit_duration_str = f"{pit_duration:.1f}s"
        else:
            pit_duration_str = "0.0s"
        
        # 黃色背景顏色
        pit_yellow_bg = QColor('#FFD700')  # 金黃色
        pit_text_color = QColor('#000000')  # 黑色文字
        
        # P (欄位 0) 和 Driver (欄位 1) 保持原樣，不修改
        # 從欄位 2 開始到最後全部設為黃色並清空
        
        # 欄位 2 開始的所有欄位設為黃色背景
        for col in range(2, self.table.columnCount()):
            item = self.table.item(row, col)
            if item:
                item.setBackground(pit_yellow_bg)
                item.setForeground(pit_text_color)
                item.setText("")  # 清空內容
        
        # 在欄位 2 (+/-) 設置合併儲存格來顯示 PIT 資訊
        # 合併從欄位 2 到欄位 21 (共 20 個欄位)
        span_cols = self.table.columnCount() - 2  # 從欄位2到最後
        self.table.setSpan(row, 2, 1, span_cols)
        self._pit_span_rows.add(row)
        
        # 設置 PIT 顯示文字
        pit_item = self.table.item(row, 2)
        if pit_item:
            pit_display_text = f"PIT  {pit_duration_str}"
            pit_item.setText(pit_display_text)
            pit_item.setBackground(pit_yellow_bg)
            pit_item.setForeground(pit_text_color)
            pit_item.setTextAlignment(Qt.AlignCenter)
            font = pit_item.font()
            font.setBold(True)
            font.setPointSize(12)  # 較大字體
            pit_item.setFont(font)
    
    def _check_highlight_expiry(self):
        """檢查並移除過期的紅框高亮 (使用播放時間)"""
        current_race_time = self._current_race_time_seconds
        
        expired_drivers = []
        for driver_num, change_time in self._position_changed_drivers.items():
            if current_race_time - change_time >= self._position_change_duration:
                expired_drivers.append(driver_num)
        
        if expired_drivers:
            for driver_num in expired_drivers:
                del self._position_changed_drivers[driver_num]
            
            # 刷新顯示以移除紅框
            if self._current_snapshot:
                self.update_display(self._current_snapshot, self._current_tyre_state)
    
    def _set_position_change(self, row: int, driver_num: str, driver_data: Dict):
        """設置名次變動欄位"""
        current_pos = driver_data.get('position')
        grid_pos = self._grid_positions.get(driver_num)
        
        if current_pos is not None and grid_pos is not None:
            change = grid_pos - current_pos
            if change > 0:
                change_text = f"+{change}"
                change_color = QColor(80, 220, 80)   # 深色模式：亮綠色
            elif change < 0:
                change_text = f"{change}"
                change_color = QColor(255, 80, 80)   # 深色模式：亮紅色
            else:
                change_text = "-"
                change_color = QColor(180, 180, 180)  # 深色模式：亮灰色
        else:
            change_text = "-"
            change_color = QColor(180, 180, 180)
        
        change_item = QTableWidgetItem(change_text)
        change_item.setTextAlignment(Qt.AlignCenter)
        change_item.setForeground(change_color)
        font = change_item.font()
        font.setBold(True)
        change_item.setFont(font)
        self.table.setItem(row, 2, change_item)
    
    def _set_tyre_info(self, row: int, driver_num: str):
        """設置輪胎資訊欄位 - 與 Demo 一致"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        tyre_info = self._current_tyre_state.get(driver_num, {})
        compound = tyre_info.get('compound', 'UNKNOWN')
        tyre_abbrev = TYRE_ABBREV.get(compound, '?')
        tyre_text_color = TYRE_TEXT_COLORS.get(compound, TYRE_TEXT_COLORS['UNKNOWN'])
        
        # 調試：顯示讀取的 tyre_info
        driver_data = None
        if hasattr(self, '_current_snapshot'):
            driver_data = self._current_snapshot.get('drivers', {}).get(driver_num, {})
        driver_tla = driver_data.get('tla', '???') if driver_data else '???'
        logger.debug(
            "[RANKING_TOWER]  _set_tyre_info for Driver %s (%s): tyre_info=%s, tyre_age_key=%s",
            driver_num,
            driver_tla,
            tyre_info,
            tyre_info.get('tyre_age', 'KEY_NOT_FOUND'),
        )
        
        # 胎 (欄位 4) - 黑底 + 對應顏色字體
        tyre_item = QTableWidgetItem(tyre_abbrev)
        tyre_item.setTextAlignment(Qt.AlignCenter)
        tyre_item.setBackground(QColor('#1A1A1A'))  # 黑色背景
        tyre_item.setForeground(QColor(tyre_text_color))  # 輪胎對應顏色
        font = tyre_item.font()
        font.setBold(True)
        tyre_item.setFont(font)
        self.table.setItem(row, 4, tyre_item)
        
        # 齡 (欄位 5)
        tyre_age = tyre_info.get('tyre_age', tyre_info.get('stint_length', ''))
        logger.debug("   Final tyre_age for display: %s", tyre_age)
        age_item = QTableWidgetItem(str(tyre_age) if tyre_age else '')
        age_item.setTextAlignment(Qt.AlignCenter)
        age_item.setForeground(default_text_color)  # 預設顏色，_set_age_color 會覆蓋
        self._set_age_color(age_item, tyre_age, compound)  # 傳入輪胎類型
        self.table.setItem(row, 5, age_item)
        
        # Pit (欄位 6)
        stint_count = tyre_info.get('stint_count', 0)
        pit_count = max(0, stint_count - 1) if stint_count else 0
        pit_item = QTableWidgetItem(str(pit_count) if pit_count > 0 else '0')
        pit_item.setTextAlignment(Qt.AlignCenter)
        pit_item.setForeground(default_text_color)
        self.table.setItem(row, 6, pit_item)
        
        # 換胎 (欄位 7)
        stints = tyre_info.get('stints', [])
        if stints:
            tyre_hist = '→'.join([TYRE_ABBREV.get(s.get('compound', 'UNKNOWN'), '?') for s in stints])
        else:
            tyre_hist = tyre_abbrev
        hist_item = QTableWidgetItem(tyre_hist)
        hist_item.setTextAlignment(Qt.AlignCenter)
        hist_item.setForeground(default_text_color)
        self.table.setItem(row, 7, hist_item)
    
    def _set_age_color(self, item: QTableWidgetItem, tyre_age, compound: str = 'UNKNOWN'):
        """
        設置輪胎壽命顏色
        
        根據 tire_degradation_database.json 的 optimal_stint_length：
        - 超過 optimal_stint * 1.2: 紅色 (輪胎嚴重超限，懸崖效應風險)
        - 超過 optimal_stint: 黃色 (已超過建議圈數，應進站)
        - 未達建議: 無顏色
        
        例如 Lusail SOFT optimal=16:
        - 16圈以下: 正常
        - 16-19圈: 黃色 (超過建議)
        - 20圈以上: 紅色 (嚴重超限)
        """
        if not tyre_age:
            return
            
        try:
            age_val = int(tyre_age)
        except (ValueError, TypeError):
            return
        
        # 取得該輪胎的建議圈數 (optimal_stint_length)
        optimal_stint = 25  # 預設值
        
        compound_upper = compound.upper() if compound else 'UNKNOWN'
        if compound_upper in self._circuit_pit_windows:
            optimal_stint = self._circuit_pit_windows[compound_upper]
        
        # 根據建議值設置顏色
        if age_val >= int(optimal_stint * 1.2):
            # 超過 120% 建議圈數 - 紅色 (懸崖效應風險)
            item.setBackground(QColor('#FF4444'))
            item.setForeground(QColor('#FFFFFF'))
        elif age_val >= optimal_stint:
            # 超過建議圈數 - 黃色 (應進站)
            item.setBackground(QColor('#FFFF00'))
            item.setForeground(QColor('#000000'))
    
    def _set_driver_info(self, row: int, driver_num: str, driver_data: Dict):
        """設置車手資訊欄位 - 使用車隊顏色"""
        driver_display = driver_data.get('driver_tla', driver_num)
        driver_item = QTableWidgetItem(driver_display)
        driver_item.setTextAlignment(Qt.AlignCenter)
        
        # 獲取車隊顏色 (優先使用 color_palette_provider)
        team_color = None
        if COLOR_PALETTE_AVAILABLE:
            try:
                # 使用通用顏色系統獲取車手顏色
                team_color_qcolor = color_palette_provider.get_driver_color(driver_display, fallback=True)
                if team_color_qcolor:
                    team_color = team_color_qcolor.name()
            except Exception:
                pass
        
        # 備選：使用 snapshot 中的 team_color
        if not team_color:
            team_color = driver_data.get('team_color', 'CCCCCC')
            if team_color and not team_color.startswith('#'):
                team_color = f'#{team_color}'
        
        driver_item.setBackground(QColor(team_color))
        
        # 文字顏色：根據背景亮度自動選擇
        bg_color = QColor(team_color)
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue()) / 255
        if luminance < 0.5:
            driver_item.setForeground(QColor('#FFFFFF'))
        else:
            driver_item.setForeground(QColor('#000000'))
        
        font = driver_item.font()
        font.setBold(True)
        driver_item.setFont(font)
        driver_item.setData(Qt.UserRole, {'driver_num': driver_num, 'driver_tla': driver_display})
        self.table.setItem(row, 1, driver_item)
    
    def _set_sector_times(self, row: int, driver_data: Dict):
        """設置區間時間欄位（✅ 優化版本）"""
        # ✅ 使用緩存的顏色
        default_text_color = self._color_cache['default_text']
        green = self._color_cache['green']
        dark_green = self._color_cache['dark_green']
        purple = self._color_cache['purple']
        white = self._color_cache['white']
        black = self._color_cache['black']
        
        for sector_idx in range(3):
            sector_name = f's{sector_idx + 1}'
            sector_time = driver_data.get(f'{sector_name}_time', '')
            sector_personal = driver_data.get(f'{sector_name}_personal_fastest', False)
            sector_overall = driver_data.get(f'{sector_name}_overall_fastest', False)
            
            sector_item = QTableWidgetItem(sector_time if sector_time else '')
            sector_item.setTextAlignment(Qt.AlignCenter)
            
            if sector_overall:
                sector_item.setBackground(QColor('#FF00FF'))
                sector_item.setForeground(QColor('#FFFFFF'))  # 紫色背景用白字
                font = sector_item.font()
                font.setBold(True)
                sector_item.setFont(font)
            elif sector_personal:
                sector_item.setBackground(QColor('#00DD00'))  # 稍暗的綠色
                sector_item.setForeground(QColor('#000000'))
                font = sector_item.font()
                font.setBold(True)
                sector_item.setFont(font)
            else:
                sector_item.setForeground(default_text_color)
            
            self.table.setItem(row, 8 + sector_idx, sector_item)
    
    def _set_lap_times(self, row: int, driver_num: str, driver_data: Dict):
        """設置圈時相關欄位（✅ 優化版本）"""
        # ✅ 使用緩存的顏色
        default_text_color = self._color_cache['default_text']
        white = self._color_cache['white']
        dark_green = self._color_cache['dark_green']
        purple = self._color_cache['purple']
        black = self._color_cache['black']
        
        # 上圈 (欄位 11)
        last_lap_time = driver_data.get('last_lap_time', '')
        last_lap_personal = driver_data.get('last_lap_personal_fastest', False)
        last_lap_overall = driver_data.get('last_lap_overall_fastest', False)
        
        last_lap_item = QTableWidgetItem(last_lap_time if last_lap_time else '')
        last_lap_item.setTextAlignment(Qt.AlignCenter)
        
        if last_lap_overall:
            last_lap_item.setBackground(QColor('#FF00FF'))
            last_lap_item.setForeground(QColor('#FFFFFF'))  # 紫色背景用白字
            font = last_lap_item.font()
            font.setBold(True)
            last_lap_item.setFont(font)
        elif last_lap_personal:
            last_lap_item.setBackground(QColor('#00DD00'))  # 稍暗的綠色
            last_lap_item.setForeground(QColor('#000000'))
            font = last_lap_item.font()
            font.setBold(True)
            last_lap_item.setFont(font)
        else:
            last_lap_item.setForeground(default_text_color)
        
        self.table.setItem(row, 11, last_lap_item)
        
        # 最佳 (欄位 12)
        best_lap_time = driver_data.get('best_lap_time', '')
        best_lap_item = QTableWidgetItem(best_lap_time if best_lap_time else '')
        best_lap_item.setTextAlignment(Qt.AlignCenter)
        
        # ✅ 檢查是否為全場最快圈速 - 顯示深紫色背景
        is_fastest_overall = (
            best_lap_time 
            and best_lap_time.strip() 
            and hasattr(self, '_fastest_best_lap') 
            and best_lap_time == self._fastest_best_lap
        )
        
        if is_fastest_overall:
            # 深紫色背景 (類似深紅色的色調)
            best_lap_item.setBackground(QColor('#663399'))  # 深紫色 (Rebecca Purple)
            best_lap_item.setForeground(QColor('#FFFFFF'))  # 白色文字
            font = best_lap_item.font()
            font.setBold(True)
            best_lap_item.setFont(font)
        else:
            best_lap_item.setForeground(QColor('#FFFFFF'))  # 白色
        
        self.table.setItem(row, 12, best_lap_item)
        
        # 差距 (欄位 13)
        self._set_delta(row, last_lap_time, best_lap_time)
        
        # 領先 (欄位 14) - P1 永遠不顯示
        position = driver_data.get('position')
        if position == 1 or position == '1':
            gap_leader_text = ""
        else:
            gap_leader_text = driver_data.get('gap_to_leader_display', '')
        gap_leader_item = QTableWidgetItem(gap_leader_text)
        gap_leader_item.setTextAlignment(Qt.AlignCenter)
        gap_leader_item.setForeground(default_text_color)
        self.table.setItem(row, 14, gap_leader_item)
        
        # 前車 (欄位 15)
        self._set_gap_ahead(row, driver_data)
        
        # Trend 趨勢 (欄位 16)
        self._set_gap_trend(row, driver_data, default_text_color)
        
        # SF% 省胎分數 (欄位 17) - 暫時隱藏
        # self._set_fuel_saving(row, driver_num, driver_data, default_text_color)
    
    def _set_delta(self, row: int, last_lap_time: str, best_lap_time: str):
        """
        設置差距欄位 (Delta = Last Lap - Best Lap)
        
        顏色邏輯：
        - < +2.0 秒：無背景（正常範圍）
        - +2.0 ~ +5.0 秒：橙色漸變背景（越慢越橘）
        - >= +5.0 秒：最深橙色背景
        """
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        delta_text = ''
        delta_value = None
        
        if last_lap_time and best_lap_time:
            try:
                last_secs = self._parse_lap_time(last_lap_time)
                best_secs = self._parse_lap_time(best_lap_time)
                if last_secs is not None and best_secs is not None:
                    delta_value = last_secs - best_secs
                    if delta_value > 0:
                        delta_text = f"+{delta_value:.3f}"
                    elif delta_value < 0:
                        delta_text = f"{delta_value:.3f}"
                    else:
                        delta_text = "0.000"
            except:
                pass
        
        delta_item = QTableWidgetItem(delta_text)
        delta_item.setTextAlignment(Qt.AlignCenter)
        
        # 顏色邏輯：只有 +2 秒以上才顯示橙色
        if delta_value is not None and delta_value >= 2.0:
            # +2.0 ~ +5.0 秒漸變，>=5.0 秒最深
            if delta_value >= 5.0:
                # 最深橙色
                delta_item.setBackground(QColor('#FF6600'))
                delta_item.setForeground(QColor('#FFFFFF'))
            else:
                # 漸變：從淺橙 (#FFAA00) 到深橙 (#FF6600)
                # intensity: 0.0 (at 2s) to 1.0 (at 5s)
                intensity = (delta_value - 2.0) / 3.0
                
                # 計算漸變顏色
                r = 255
                g = int(170 - (170 - 102) * intensity)  # 170 -> 102
                b = 0
                
                delta_item.setBackground(QColor(r, g, b))
                delta_item.setForeground(QColor('#FFFFFF') if intensity > 0.3 else QColor('#000000'))
        else:
            # < +2 秒或等於個人最佳：無背景
            delta_item.setForeground(default_text_color)
        
        self.table.setItem(row, 13, delta_item)
    
    def _set_gap_ahead(self, row: int, driver_data: Dict):
        """
        設置前車間隔欄位
        
        顏色邏輯（簡化版）：
        - 0~1秒：綠色背景 (DRS 範圍 / 攻擊距離)
        - 1~2.5秒：黃色背景 (追趕距離)
        - >2.5秒：黑色背景 (安全間距)
        """
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        # P1 沒有前車，強制設為空字串
        if driver_data.get('position') == 1:
            gap_ahead_text = ""
        else:
            gap_ahead_text = driver_data.get('gap_to_ahead_display', '')
        
        gap_ahead_item = QTableWidgetItem(gap_ahead_text)
        gap_ahead_item.setTextAlignment(Qt.AlignCenter)
        gap_ahead_item.setForeground(default_text_color)  # 預設顏色
        
        # 顏色編碼 - 簡化版
        if gap_ahead_text and gap_ahead_text not in ('', '-', 'LAP'):
            try:
                gap_str = gap_ahead_text.replace('+', '').replace('s', '').strip()
                gap_seconds = float(gap_str)
                
                if gap_seconds <= 1.0:
                    # 0~1秒：淺綠色背景 (DRS 範圍 / 攻擊距離)
                    gap_ahead_item.setBackground(QColor('#90EE90'))
                    gap_ahead_item.setForeground(QColor('#000000'))
                elif gap_seconds <= 2.5:
                    # 1~2.5秒：黃色文字 (追趕距離) - 無背景
                    gap_ahead_item.setForeground(QColor('#FFFF00'))  # 黃色文字
                    # 不設置背景，使用預設深色背景
                else:
                    # >2.5秒：黑色背景 (安全間距)
                    gap_ahead_item.setBackground(QColor('#1A1A1A'))
                    gap_ahead_item.setForeground(QColor('#FFFFFF'))
            except (ValueError, AttributeError):
                pass
        
        self.table.setItem(row, 15, gap_ahead_item)
    
    def _set_gap_trend(self, row: int, driver_data: Dict, default_text_color: QColor):
        """
        設置間距趨勢欄位 (Trend) - 改進版：階段式顯示
        
        新邏輯（單圈 gap 變化）：
        - 追近（負值）：
          * 0.0 ~ -0.3秒：  >   (淺綠 #66FF66)
          * -0.3 ~ -0.5秒： >>  (綠色 #00FF00)
          * -0.5秒以上：   >>> (深綠 #00CC00)
          * ≥1.0秒：      >>> (黃色底 #FFFF00 - 劇烈追近警報)
        - 拉開（正值）：
          * 0.0 ~ +0.3秒：  <   (淺藍 #6699FF)
          * +0.3 ~ +0.5秒： <<  (藍色 #0066FF)
          * +0.5秒以上：   <<< (深藍 #0044CC)
        - 維持：±0.1秒內：-   (灰色 #888888)
        
        Args:
            row: 表格行索引
            driver_data: 車手數據字典
            default_text_color: 預設文字顏色
        """
        position = driver_data.get('position', 99)
        
        # P1 沒有前車，顯示 '-'
        if position == 1:
            item = QTableWidgetItem('-')
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(default_text_color)
            self.table.setItem(row, 16, item)
            return
        
        # 獲取單圈 gap 變化量（秒）
        gap_trend = driver_data.get('gap_trend', 0.0)
        
        # 確保是數值
        if not isinstance(gap_trend, (int, float)):
            gap_trend = 0.0
        
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        
        # 判斷是否劇烈變化（≥1.0秒）
        is_extreme = abs(gap_trend) >= 1.0
        
        # 維持狀態（±0.1秒內）
        if abs(gap_trend) <= 0.1:
            item.setText('-')
            item.setForeground(QColor('#888888'))
        
        # 追近（負值）
        elif gap_trend < 0:
            abs_change = abs(gap_trend)
            
            if abs_change >= 0.5:
                # 強烈追近：>>>
                item.setText('>>>')
                if is_extreme:
                    # 劇烈變化：黃底
                    item.setBackground(QColor('#FFFF00'))
                    item.setForeground(QColor('#000000'))
                else:
                    # 正常強烈：深綠背景
                    item.setBackground(QColor('#00CC00'))
                    item.setForeground(QColor('#000000'))
            elif abs_change >= 0.3:
                # 中等追近：>>
                item.setText('>>')
                item.setBackground(QColor('#00FF00'))
                item.setForeground(QColor('#000000'))
            else:
                # 輕微追近：>
                item.setText('>')
                item.setForeground(QColor('#66FF66'))
        
        # 拉開（正值）
        else:
            abs_change = abs(gap_trend)
            
            if abs_change >= 0.5:
                # 強烈拉開：<<<
                item.setText('<<<')
                # 拉開不使用黃色警報，統一使用深藍背景
                item.setBackground(QColor('#0044CC'))
                item.setForeground(QColor('#FFFFFF'))
            elif abs_change >= 0.3:
                # 中等拉開：<<
                item.setText('<<')
                item.setBackground(QColor('#0066FF'))
                item.setForeground(QColor('#FFFFFF'))
            else:
                # 輕微拉開：<
                item.setText('<')
                item.setForeground(QColor('#6699FF'))
        
        self.table.setItem(row, 16, item)
    
    def _set_fuel_saving(self, row: int, driver_num: str, driver_data: Dict, default_text_color: QColor):
        """
        設置省胎分數欄位 SF% (欄位 17)
        
        從 driver_data 讀取 F87 計算的省胎分數 (與 P1% 相同模式)。
        DataManager 會在 _update_win_probabilities 中合併 SF% 到 drivers 字典。
        
        顏色邏輯：
        - 0-10%: 白字（無背景）
        - 10-30%: 綠色漸變到藍色
        - 30%+: 藍色
        """
        item = QTableWidgetItem()
        item.setTextAlignment(Qt.AlignCenter)
        
        # 從 driver_data 讀取 SF% (與 P1% 相同模式)
        saving_pct = int(driver_data.get('tire_saving_score', 0))
        
        if saving_pct == 0:
            item.setText('-')
            item.setForeground(default_text_color)
        else:
            # 顯示整數百分比
            item.setText(f"{saving_pct}%")
            
            # 顏色邏輯：0-10% 白字，10-30% 綠→藍漸變，30%+ 藍色
            if saving_pct < 10:
                # 0-10%: 白字無背景
                item.setForeground(default_text_color)
            elif saving_pct >= 30:
                # 30%+: 藍色
                item.setForeground(QColor('#0088FF'))
            else:
                # 10-30%: 綠色漸變到藍色
                ratio = (saving_pct - 10) / 20.0
                r = 0
                g = int(200 * (1 - ratio))
                b = int(136 + (255 - 136) * ratio)
                item.setForeground(QColor(r, g, b))
        
        self.table.setItem(row, 17, item)
    
    def _set_probabilities(self, row: int, driver_data: Dict):
        """設置勝率欄位（✅ 優化版本）"""
        # ✅ 使用緩存的顏色
        default_text_color = self._color_cache['default_text']
        green = self._color_cache['green']
        yellow = self._color_cache['yellow']
        orange = self._color_cache['orange']
        black = self._color_cache['black']
        
        probs = [
            ('win_probability', 18, [70, 35]),   # P1%: ≥70% 綠, 35-69% 橙
            ('p2_probability', 19, [70, 40]),    # P2%: ≥70% 綠, 40-69% 橙
            ('p3_probability', 20, [80, 50])     # P3%: ≥80% 綠, 50-79% 橙
        ]
        
        for key, col, thresholds in probs:
            prob = driver_data.get(key, '')
            if isinstance(prob, (int, float)):
                text = f"{int(round(prob))}%"
            else:
                text = str(prob) if prob else '-'
            
            item = QTableWidgetItem(text)
            item.setTextAlignment(Qt.AlignCenter)
            
            if isinstance(prob, (int, float)):
                # 統一使用兩層邏輯（綠色/橙色）
                if prob >= thresholds[0]:
                    item.setBackground(QColor('#00FF00'))  # 高機率：綠色
                    item.setForeground(QColor('#000000'))
                elif prob >= thresholds[1]:
                    item.setBackground(QColor('#FFA500'))  # 中機率：橙色
                    item.setForeground(QColor('#000000'))
                else:
                    # 低機率：無背景
                    item.setForeground(default_text_color)
            else:
                item.setForeground(default_text_color)
            
            self.table.setItem(row, col, item)
        
        # F83: 超車機率 OT% (欄位 21)
        self._set_overtake_probability(row, driver_data, default_text_color)
        
        # F85: 近距離接觸機率 CC% (欄位 22)
        self._set_close_combat_probability(row, driver_data, default_text_color)
    
    def _set_overtake_probability(self, row: int, driver_data: Dict, default_text_color: QColor):
        """
        F83: 設置超車機率欄位
        
        顏色編碼：
        - >= 80%: 橙色背景 - 極高超車機會
        - < 80%: 黑底白字 - 一般顯示
        - P1: 顯示 '-' (沒有前車)
        """
        position = driver_data.get('position', 99)
        
        # P1 沒有前車，顯示 '-'
        if position == 1:
            item = QTableWidgetItem('-')
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(default_text_color)
            self.table.setItem(row, 21, item)
            return
        
        prob = driver_data.get('overtake_probability', '')
        
        if isinstance(prob, (int, float)):
            text = f"{int(round(prob))}%"
        else:
            text = str(prob) if prob else '-'
        
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        
        if isinstance(prob, (int, float)) and prob >= 80:
            # >= 80%：橙色背景 - 極高超車機會
            item.setBackground(QColor('#FFA500'))
            item.setForeground(QColor('#000000'))
        else:
            # 其餘：黑底白字
            item.setForeground(default_text_color)
        
        self.table.setItem(row, 21, item)
    
    def _set_close_combat_probability(self, row: int, driver_data: Dict, default_text_color: QColor):
        """
        F85: 設置近距離接觸機率欄位
        
        顏色編碼：
        - >= 70%: 淺藍色背景 - 高機率追近
        - < 70%: 黑底白字 - 一般顯示
        - P1: 顯示 '-' (沒有前車)
        """
        position = driver_data.get('position', 99)
        
        # P1 沒有前車，顯示 '-'
        if position == 1:
            item = QTableWidgetItem('-')
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(default_text_color)
            self.table.setItem(row, 22, item)
            return
        
        prob = driver_data.get('close_combat_probability', '')
        
        if isinstance(prob, (int, float)):
            text = f"{int(round(prob))}%"
        else:
            text = str(prob) if prob else '-'
        
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        
        if isinstance(prob, (int, float)) and prob >= 70:
            # >= 70%：淺藍色背景 - 高機率追近
            item.setBackground(QColor('#4A90E2'))
            item.setForeground(QColor('#FFFFFF'))
        else:
            # 其餘：黑底白字
            item.setForeground(default_text_color)
        
        self.table.setItem(row, 22, item)
    
    def _set_telemetry(self, row: int, driver_num: str):
        """設置遙測資料欄位（DRS）"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        car_data = self._current_car_data.get(driver_num, {})
        
        # DRS (欄位 23)
        # DRS 值說明 (來源: F1 Live Timing API):
        # - 0 = Off
        # - 1 = DRS Disabled (禁用 - 76% of the time)
        # - 2 = DRS Eligible/Available (可用但未開 - rare)
        # - 3 = DRS Disabled (禁用變體)
        # - 8 = DRS Available/Ready (在DRS區內可用 - 10%)
        # - 10 = DRS Enabled (啟用中 - rare)
        # - 12 = DRS Active/Open (實際開啟 - 13%)
        # - 14 = DRS Enabled variant (啟用變體)
        drs = car_data.get('drs', '')
        drs_text = ''
        if drs:
            try:
                drs_val = int(drs)
                if drs_val >= 10 and drs_val % 2 == 0:
                    # 偶數且 >= 10: DRS 實際開啟
                    drs_text = 'ON'
                elif drs_val >= 2 and drs_val % 2 == 0:
                    # 偶數且 2-8: DRS 可用但未開
                    drs_text = 'RDY'
                # 奇數或 0: 保持空白 (DRS 禁用/關閉)
            except (ValueError, TypeError):
                pass
        
        drs_item = QTableWidgetItem(drs_text)
        drs_item.setTextAlignment(Qt.AlignCenter)
        if drs_text == 'ON':
            drs_item.setBackground(QColor('#00FF00'))  # 綠色背景
            drs_item.setForeground(QColor('#000000'))  # 黑色字體
            font = drs_item.font()
            font.setBold(True)
            drs_item.setFont(font)
        elif drs_text == 'RDY':
            drs_item.setBackground(QColor('#1A1A1A'))  # 黑色背景
            drs_item.setForeground(QColor('#FFFF00'))  # 黃色字體
        else:
            drs_item.setForeground(default_text_color)
        
        self.table.setItem(row, 23, drs_item)
    
    def _parse_lap_time(self, lap_time_str: str) -> Optional[float]:
        """解析圈時字串為秒數"""
        if not lap_time_str:
            return None
        try:
            if ':' in lap_time_str:
                parts = lap_time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except (ValueError, IndexError):
            return None
    
    def clear(self):
        """清除表格"""
        self.table.setRowCount(0)
        self._grid_positions.clear()
        self._grid_initialized = False
        self._current_snapshot = None
        self._current_tyre_state.clear()
        self._current_car_data.clear()
        # 清除名次變更追蹤
        self._previous_positions.clear()
        self._position_changed_drivers.clear()


class LiveTimingRankingTower(BaseLiveTimingMDI):
    """
    即時排名塔 MDI 視窗
    
    整合 RankingTableWidget 到 MDI 框架中。
    深色主題設計，適合長時間觀看。
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        self.setWindowTitle(tr("live_ranking_tower"))
        self.resize(900, 500)
        
        # 性能優化: 分層更新間隔
        # 快速欄位 (Gap, DRS): 每 2 幀 (~30 FPS @ 60 FPS)
        # 標準欄位 (其他所有): 每 6 幀 (~10 FPS @ 60 FPS)
        self._fast_update_interval = 2    # Gap, DRS - 30 FPS
        self._full_update_interval = 6    # 其他欄位 - 10 FPS
        
        # 設置深色背景
        self.setStyleSheet("""
            LiveTimingRankingTower {
                background-color: #1a1a1a;
            }
        """)
    
    def _setup_ui(self):
        """設置 UI"""
        self._ranking_widget = RankingTableWidget()
        self._main_layout.addWidget(self._ranking_widget)
        
        # 傳遞 DataManager 給 widget (用於查詢 F87 省胎分數)
        if self._data_manager:
            self._ranking_widget.set_data_manager(self._data_manager)
            logger.debug("[F87_DEBUG] LiveTimingRankingTower: DataManager passed to widget")
        else:
            logger.warning(
                "[F87_DEBUG] LiveTimingRankingTower: _data_manager is None in _setup_ui!"
            )
        
        # 連接信號
        self._ranking_widget.driver_selected.connect(self._on_driver_selected)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        處理快照更新 - 分層更新策略
        
        快速欄位 (每 3 幀): 位置、名次變動、區間時間、Gap
        完整更新 (每 10 幀): 所有欄位（輪胎、圈速、DRS 等）
        """
        # 調試輸出 - 每個快照都輸出
        if not hasattr(self, '_snapshot_count'):
            self._snapshot_count = 0
        self._snapshot_count += 1
        
        frame_counter = snapshot.get('frame_counter', 0)
        
        # 分層更新策略
        is_fast_update = (frame_counter == 0 or frame_counter % self._fast_update_interval == 0)
        is_full_update = (frame_counter == 0 or frame_counter % self._full_update_interval == 0)
        
        # 如果不是任何更新時機，跳過
        if not is_fast_update and not is_full_update:
            return
        
        drivers = snapshot.get('drivers', {})
        current_lap = snapshot.get('current_lap', 0)
        total_laps = snapshot.get('total_laps', 0)
        
        # 每個快照都輸出調試
        if self._snapshot_count <= 5 or self._snapshot_count % 20 == 0:
            logger.debug(
                "[RANKING_TOWER] Snapshot #%d: %d drivers, lap %s/%s",
                self._snapshot_count,
                len(drivers),
                current_lap,
                total_laps,
            )
            if drivers:
                sample_num = next(iter(drivers.keys()))
                sample = drivers[sample_num]
                logger.debug(
                    "[RANKING_TOWER] Sample driver %s: pos=%s, tla=%s, compound=%s, tyre_age=%s",
                    sample_num,
                    sample.get('position'),
                    sample.get('tla'),
                    sample.get('compound'),
                    sample.get('tyre_age'),
                )
        
        # 快速更新：只更新位置、Gap、區間時間，跳過輪胎和遙測數據處理
        if is_fast_update and not is_full_update:
            self._ranking_widget.update_fast_columns(snapshot)
            return
        
        # === 以下為完整更新邏輯 ===
        
        # 獲取輪胎狀態
        # 1. 即時模式：直接從 snapshot drivers 中提取 tyre 數據
        # 2. 歷史模式：從 DataManager 獲取
        tyre_state = {}
        drivers = snapshot.get('drivers', {})
        
        # 優先從 snapshot 的 drivers 中提取（即時模式）
        logger.debug(
            "[RANKING_TOWER]  Extracting tyre data from snapshot.drivers: %d drivers",
            len(drivers),
        )
        for driver_num, driver_data in drivers.items():
            compound = driver_data.get('compound')
            tyre_age_raw = driver_data.get('tyre_age')
            driver_tla = driver_data.get('tla', driver_data.get('driver_tla', '???'))
            
            if compound or tyre_age_raw is not None:
                tyre_state[driver_num] = {
                    'compound': compound or 'UNKNOWN',
                    'tyre_age': tyre_age_raw if tyre_age_raw is not None else 0,
                    'tyre_new': driver_data.get('tyre_new', False),
                    'stint_count': driver_data.get('pit_count', 0) + 1,  # stint_count = pit_count + 1
                    'stints': driver_data.get('stints', []),
                }
                logger.debug(
                    "[RANKING_TOWER]  Driver %s (%s): compound=%s, tyre_age=%s → stored as tyre_age=%s",
                    driver_num,
                    driver_tla,
                    compound,
                    tyre_age_raw,
                    tyre_state[driver_num]['tyre_age'],
                )
            else:
                logger.debug(
                    "[RANKING_TOWER]  Driver %s (%s): NO tyre data (compound=%s, tyre_age=%s)",
                    driver_num,
                    driver_tla,
                    compound,
                    tyre_age_raw,
                )
        
        # 如果 snapshot 沒有輪胎數據，嘗試從 DataManager 獲取（歷史模式）
        if not tyre_state:
            if hasattr(self._data_manager, 'get_tyre_state'):
                tyre_state = self._data_manager.get_tyre_state()
            elif hasattr(self._data_manager, 'get_tyre_state_at_time'):
                timestamp = snapshot.get('race_time', '')
                if timestamp:
                    tyre_state = self._data_manager.get_tyre_state_at_time(timestamp)
        
        # 調試：輪胎狀態
        if self._snapshot_count % 100 == 0:
            logger.debug("[RANKING_TOWER] Tyre state: %d drivers", len(tyre_state))
            if tyre_state:
                sample_driver = next(iter(tyre_state.keys()))
                logger.debug(
                    "[RANKING_TOWER] Sample tyre (%s): %s",
                    sample_driver,
                    tyre_state.get(sample_driver, {}),
                )
        
        # 從 drivers 中提取車輛遙測數據
        car_data = {}
        drivers = snapshot.get('drivers', {})
        for driver_num, driver_data in drivers.items():
            car_data[driver_num] = {
                'speed': driver_data.get('speed'),
                'rpm': driver_data.get('rpm'),
                'gear': driver_data.get('gear'),
                'throttle': driver_data.get('throttle'),
                'brake': driver_data.get('brake'),
                'drs': driver_data.get('drs'),
            }
        
        if car_data:
            self._ranking_widget.set_car_data(car_data)
        
        # 設置輪胎狀態
        if tyre_state:
            self._ranking_widget.set_tyre_state(tyre_state)
        
        # 完整更新：所有欄位
        self._ranking_widget.update_display(snapshot, tyre_state)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入"""
        race_name = race_info.get('race', '')
        logger.info(
            "[LiveTimingRankingTower] Race loaded: %s %s",
            race_info.get('year'),
            race_name,
        )
        
        # 設置賽道，載入對應的輪胎建議數據
        self._ranking_widget.set_circuit(race_name)
        self._ranking_widget.clear()
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        self._ranking_widget.clear()
    
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇 - 透過 DataManager 廣播給其他模組"""
        logger.debug("[LiveTimingRankingTower] Driver selected: %s", driver_num)
        # 透過 DataManager 廣播車手選擇信號
        if self._data_manager:
            self._data_manager.driver_selected.emit(driver_num)
            logger.debug(
                "[LiveTimingRankingTower] Emitted driver_selected signal via DataManager: %s",
                driver_num,
            )
    
    def _cleanup(self):
        """清理資源"""
        self._ranking_widget.clear()
