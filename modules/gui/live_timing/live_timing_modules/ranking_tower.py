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

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    print("[RANKING_TOWER] color_palette_provider not available")


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
    - Lap (圈數)
    - P1%/P2%/P3% (勝率)
    - SPD (速度)
    - DRS
    
    採用深色主題設計。
    """
    
    # 信號
    driver_selected = pyqtSignal(str)  # 車手被選中
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
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
        self._position_changed_drivers: Dict[str, float] = {}  # {driver_num: timestamp}
        self._position_change_duration = 10.0  # 紅框顯示時間 (秒)
        
        # 紅框更新計時器
        self._highlight_timer = QTimer(self)
        self._highlight_timer.timeout.connect(self._check_highlight_expiry)
        self._highlight_timer.start(1000)  # 每秒檢查一次
        
        self._init_ui()
    
    def _load_pit_strategy_database(self):
        """載入輪胎衰退資料庫 (tire_degradation_database.json)"""
        try:
            # 尋找 config 目錄
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
            
            # 優先使用 tire_degradation_database.json (原始數據，更準確)
            db_path = os.path.join(project_root, 'config', 'tire_degradation_database.json')
            
            if os.path.exists(db_path):
                with open(db_path, 'r', encoding='utf-8') as f:
                    self._pit_strategy_db = json.load(f)
                print(f"[RANKING_TOWER] Loaded tire degradation database: {len(self._pit_strategy_db.get('circuits', {}))} circuits")
            else:
                print(f"[RANKING_TOWER] Tire degradation database not found: {db_path}")
        except Exception as e:
            print(f"[RANKING_TOWER] Failed to load tire degradation database: {e}")
    
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
            print(f"[RANKING_TOWER] Circuit set: {db_key}, optimal stint: {self._circuit_pit_windows}")
        else:
            # 嘗試模糊匹配
            for key in circuits.keys():
                if key.lower() in circuit_key.lower() or circuit_key.lower() in key.lower():
                    circuit_data = circuits[key]
                    self._current_circuit = key
                    self._circuit_pit_windows = circuit_data.get('optimal_stint_length', {})
                    print(f"[RANKING_TOWER] Circuit fuzzy match: {key}, optimal stint: {self._circuit_pit_windows}")
                    return
            
            print(f"[RANKING_TOWER] Circuit not found in database: {circuit_key} (tried: {db_key})")
            self._circuit_pit_windows = {}

    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        
        # 表格設置
        self.table = QTableWidget()
        self.table.setProperty("is_live_timing_widget", True)  # 標記為 Live Timing widget
        self.table.setColumnCount(22)
        self.table.setHorizontalHeaderLabels([
            "P", tr("driver"), "+/-", "No", tr("tyre"), tr("age"), "Pit", tr("tyre_hist"),
            "S1", "S2", "S3",
            tr("last_lap"), tr("best_lap"), tr("delta"), tr("gap_leader"), tr("gap_ahead"), tr("lap"),
            "P1%", "P2%", "P3%",
            "SPD", "DRS"
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
            28,   # 圈
            41,   # P1%
            41,   # P2%
            41,   # P3%
            36,   # SPD
            32    # DRS
        ]
        
        for i, width in enumerate(widths):
            self.table.setColumnWidth(i, width)
        
        # 隱藏欄位
        self.table.hideColumn(3)   # No
        self.table.hideColumn(7)   # 換胎
    
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
            print(f"[RANKING_TOWER] Updated {compound} optimal stint to {new_value} laps")
            
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
        更新顯示
        
        Args:
            snapshot: 當前時間快照
            tyre_state: 即時輪胎狀態
        """
        self._current_snapshot = snapshot
        if tyre_state:
            self._current_tyre_state = tyre_state
        
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
        
        # 檢測名次變更並記錄
        import time
        current_time = time.time()
        
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
                # 名次變更！記錄這個車手
                self._position_changed_drivers[driver_num] = current_time
                print(f"[RANKING_TOWER] Position change: {driver_data.get('driver_tla', driver_num)} P{previous_pos} -> P{current_pos}")
            
            # 更新上一次排名記錄
            self._previous_positions[driver_num] = current_pos
        
        # 暫停排序
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(sorted_drivers))
        
        for row, (driver_num, driver_data) in enumerate(sorted_drivers):
            self._update_row(row, driver_num, driver_data)
    
    def _update_row(self, row: int, driver_num: str, driver_data: Dict):
        """更新單行數據"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        # P - 排名 (欄位 0)
        pos_item = QTableWidgetItem(str(driver_data.get('position', 'N/A')))
        pos_item.setTextAlignment(Qt.AlignCenter)
        pos_item.setForeground(default_text_color)
        font = pos_item.font()
        font.setBold(True)
        pos_item.setFont(font)
        self.table.setItem(row, 0, pos_item)
        
        # 車手 (欄位 1)
        self._set_driver_info(row, driver_num, driver_data)
        
        # +/- 名次變動 (欄位 2)
        self._set_position_change(row, driver_num, driver_data)
        
        # No - 車號 (欄位 3)
        num_item = QTableWidgetItem(driver_num)
        num_item.setTextAlignment(Qt.AlignCenter)
        num_item.setForeground(default_text_color)
        self.table.setItem(row, 3, num_item)
        
        # 輪胎相關欄位 (欄位 4-7)
        self._set_tyre_info(row, driver_num)
        
        # 區間時間 (欄位 8-10)
        self._set_sector_times(row, driver_data)
        
        # 圈時相關 (欄位 11-16)
        self._set_lap_times(row, driver_data)
        
        # 勝率 (欄位 17-19)
        self._set_probabilities(row, driver_data)
        
        # 遙測資料 (欄位 20-21)
        self._set_telemetry(row, driver_num)
        
        # 檢查是否需要顯示紅框 (名次變更)
        self._apply_position_change_highlight(row, driver_num)
    
    def _apply_position_change_highlight(self, row: int, driver_num: str):
        """為名次變更的行設置紅色邊框"""
        import time
        current_time = time.time()
        
        if driver_num in self._position_changed_drivers:
            change_time = self._position_changed_drivers[driver_num]
            elapsed = current_time - change_time
            
            if elapsed < self._position_change_duration:
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
    
    def _check_highlight_expiry(self):
        """檢查並移除過期的紅框高亮"""
        import time
        current_time = time.time()
        
        expired_drivers = []
        for driver_num, change_time in self._position_changed_drivers.items():
            if current_time - change_time >= self._position_change_duration:
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
        """設置區間時間欄位"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
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
    
    def _set_lap_times(self, row: int, driver_data: Dict):
        """設置圈時相關欄位"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
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
        best_lap_item.setForeground(QColor('#FFFFFF'))  # 白色
        self.table.setItem(row, 12, best_lap_item)
        
        # 差距 (欄位 13)
        self._set_delta(row, last_lap_time, best_lap_time)
        
        # 領先 (欄位 14)
        gap_leader_text = driver_data.get('gap_to_leader_display', '')
        if not gap_leader_text and driver_data.get('position') == 1:
            gap_leader_text = ""
        gap_leader_item = QTableWidgetItem(gap_leader_text)
        gap_leader_item.setTextAlignment(Qt.AlignCenter)
        gap_leader_item.setForeground(default_text_color)
        self.table.setItem(row, 14, gap_leader_item)
        
        # 前車 (欄位 15)
        self._set_gap_ahead(row, driver_data)
        
        # 圈 (欄位 16)
        lap_item = QTableWidgetItem(str(driver_data.get('lap') or ''))
        lap_item.setTextAlignment(Qt.AlignCenter)
        lap_item.setForeground(default_text_color)
        self.table.setItem(row, 16, lap_item)
    
    def _set_delta(self, row: int, last_lap_time: str, best_lap_time: str):
        """設置差距欄位"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        delta_text = ''
        if last_lap_time and best_lap_time:
            try:
                last_secs = self._parse_lap_time(last_lap_time)
                best_secs = self._parse_lap_time(best_lap_time)
                if last_secs is not None and best_secs is not None:
                    delta = last_secs - best_secs
                    if delta > 0:
                        delta_text = f"+{delta:.3f}"
                    elif delta < 0:
                        delta_text = f"{delta:.3f}"
                    else:
                        delta_text = "0.000"
            except:
                pass
        
        delta_item = QTableWidgetItem(delta_text)
        delta_item.setTextAlignment(Qt.AlignCenter)
        
        if delta_text.startswith('+') and delta_text != '+0.000':
            delta_item.setBackground(QColor('#CC8800'))  # 較暗的橙色
            delta_item.setForeground(QColor('#FFFFFF'))
        elif delta_text == '0.000':
            delta_item.setBackground(QColor('#00DD00'))
            delta_item.setForeground(QColor('#000000'))
        else:
            delta_item.setForeground(default_text_color)
        
        self.table.setItem(row, 13, delta_item)
    
    def _set_gap_ahead(self, row: int, driver_data: Dict):
        """
        設置前車間隔欄位 - 與 Demo Live 邏輯一致
        
        顏色邏輯（深色模式優化）：
        - ≤ 0秒：綠色背景 (DRS 範圍)
        - 0-2.5秒：綠→黃漸變背景
        - 2.5-5秒：黃→紅漸變背景
        - ≥ 5秒：無背景，白色文字 (安全間距)
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
        
        # 顏色編碼 - 與 Demo Live 一致，深色模式優化
        if gap_ahead_text and gap_ahead_text not in ('', '-', 'LAP'):
            try:
                gap_str = gap_ahead_text.replace('+', '').replace('s', '').strip()
                gap_seconds = float(gap_str)
                
                if gap_seconds >= 5.0:
                    # ≥5秒：黑色背景 + 白色字（安全間距）
                    gap_ahead_item.setBackground(QColor('#1A1A1A'))
                    gap_ahead_item.setForeground(QColor('#FFFFFF'))
                elif gap_seconds <= 0.0:
                    # ≤0秒：綠色背景 (DRS 範圍)
                    gap_ahead_item.setBackground(QColor('#00FF00'))
                    gap_ahead_item.setForeground(QColor('#000000'))
                else:
                    # 0~5秒：漸變 (綠色 → 黃色 → 紅色)
                    ratio = gap_seconds / 5.0  # 0.0 ~ 1.0
                    if ratio < 0.5:
                        # 0~2.5秒：綠色 → 黃色
                        r = int(255 * (ratio * 2))
                        g = 255
                        b = 0
                    else:
                        # 2.5~5秒：黃色 → 紅色
                        r = 255
                        g = int(255 * (1 - (ratio - 0.5) * 2))
                        b = 0
                    gap_ahead_item.setBackground(QColor(r, g, b))
                    gap_ahead_item.setForeground(QColor('#000000'))
            except (ValueError, AttributeError):
                pass
        
        self.table.setItem(row, 15, gap_ahead_item)
    
    def _set_probabilities(self, row: int, driver_data: Dict):
        """設置勝率欄位"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        probs = [
            ('win_probability', 17, [50, 20, 5]),
            ('p2_probability', 18, [70, 40, 15]),
            ('p3_probability', 19, [80, 50, 20])
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
                if prob >= thresholds[0]:
                    item.setBackground(QColor('#00FF00'))  # 高機率：綠色（與 Demo 同步）
                    item.setForeground(QColor('#000000'))
                elif prob >= thresholds[1]:
                    item.setBackground(QColor('#FFFF00'))  # 中機率：黃色（與 Demo 同步）
                    item.setForeground(QColor('#000000'))
                elif prob >= thresholds[2]:
                    item.setBackground(QColor('#FFA500'))  # 低機率：橙色（與 Demo 一致）
                    item.setForeground(QColor('#000000'))
                else:
                    # 極低機率：使用預設文字顏色
                    item.setForeground(default_text_color)
            else:
                item.setForeground(default_text_color)
            
            self.table.setItem(row, col, item)
    
    def _set_telemetry(self, row: int, driver_num: str):
        """設置遙測資料欄位"""
        # 深色模式預設文字顏色
        default_text_color = QColor('#E0E0E0')
        
        car_data = self._current_car_data.get(driver_num, {})
        
        # Speed (欄位 20) - 與 Demo 一致：無特殊顏色
        speed = car_data.get('speed', '')
        speed_item = QTableWidgetItem(str(speed) if speed else '')
        speed_item.setTextAlignment(Qt.AlignCenter)
        # Demo 沒有為 SPD 設置顏色，使用預設文字顏色
        speed_item.setForeground(default_text_color)
        self.table.setItem(row, 20, speed_item)
        
        # DRS (欄位 21)
        # DRS 值說明 (來源: FastF1 文檔):
        # - 0 = Off
        # - 奇數 (1,3,5,...) = DRS Disabled (禁用)
        # - 偶數且 >= 10 (10,12,14) = DRS ON (實際開啟)
        # - 偶數且 2-8 = DRS Eligible (可用但未開)
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
        
        self.table.setItem(row, 21, drs_item)
    
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
        
        # 連接信號
        self._ranking_widget.driver_selected.connect(self._on_driver_selected)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """處理快照更新"""
        # 調試輸出
        if not hasattr(self, '_snapshot_count'):
            self._snapshot_count = 0
        self._snapshot_count += 1
        if self._snapshot_count % 10 == 0:
            print(f"[RANKING_TOWER] 收到第 {self._snapshot_count} 個快照更新")
        
        # 獲取輪胎狀態（使用當前時間戳）
        tyre_state = {}
        if hasattr(self._data_manager, 'get_tyre_state'):
            tyre_state = self._data_manager.get_tyre_state()
        elif hasattr(self._data_manager, 'get_tyre_state_at_time'):
            timestamp = snapshot.get('race_time', '')
            if timestamp:
                tyre_state = self._data_manager.get_tyre_state_at_time(timestamp)
        
        # 調試：輪胎狀態
        if self._snapshot_count % 100 == 0:
            print(f"[RANKING_TOWER] 輪胎狀態: {len(tyre_state)} 車手, 範例: {list(tyre_state.keys())[:3] if tyre_state else 'Empty'}")
            if tyre_state:
                sample_driver = next(iter(tyre_state.keys()))
                print(f"[RANKING_TOWER] 範例輪胎資料 ({sample_driver}): {tyre_state.get(sample_driver, {})}")
        
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
        
        # 更新顯示
        self._ranking_widget.update_display(snapshot, tyre_state)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入"""
        race_name = race_info.get('race', '')
        print(f"[LiveTimingRankingTower] Race loaded: {race_info.get('year')} {race_name}")
        
        # 設置賽道，載入對應的輪胎建議數據
        self._ranking_widget.set_circuit(race_name)
        self._ranking_widget.clear()
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        self._ranking_widget.clear()
    
    def _on_driver_selected(self, driver_num: str):
        """處理車手選擇 - 透過 DataManager 廣播給其他模組"""
        print(f"[LiveTimingRankingTower] Driver selected: {driver_num}")
        # 透過 DataManager 廣播車手選擇信號
        if self._data_manager:
            self._data_manager.driver_selected.emit(driver_num)
            print(f"[LiveTimingRankingTower] Emitted driver_selected signal via DataManager: {driver_num}")
    
    def _cleanup(self):
        """清理資源"""
        self._ranking_widget.clear()
