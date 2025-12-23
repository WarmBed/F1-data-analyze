#!/usr/bin/env python3
"""
FIA Parts Changes Classification - Widget
==========================================

FIA 部件變更分類表格元件 - 完全基於 API

功能特點：
- 頂部過濾工具列（賽事/車隊/車手/主分類/子分類/類型 + 搜尋）
- 統計摘要列
- 完整變更記錄表格（所有欄位）
- 支援排序、搜尋、顏色標記
- 完全基於 API，無本地 JSON 讀取

表格欄位：
- 序號 | 賽事 | 車隊 | 車手 | 主分類 | 子分類 | 變更類型 | 信心度 | 描述 | 部件 | 日期

Author: F1T Team  
Date: 2025-11-08
Version: 1.0.0 (API-ONLY)
"""

import sys
import os

# 添加專案根目錄到 Python 路徑（用於獨立執行）
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from typing import Dict, List, Any, Optional, Set, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox, QLineEdit,
    QPushButton, QFrame, QHeaderView, QApplication, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QBrush  # ✨ 添加 QBrush（用於顏色應用）

from core.gui_i18n import tr, get_team_name_text  # ✨ 添加車隊名稱翻譯函數

from core.logger import get_logger
logger = get_logger(__name__)


logger = get_logger(component="parts_analysis_widget")

# ✨ 導入通用顏色系統（與 Ideal Lap Ranking 保持一致）
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    logger.info("[PARTS_WIDGET] ✅ 已導入通用顏色系統 (color_palette_provider)")
except ImportError:
    logger.warning("[PARTS_WIDGET] ⚠️ 無法導入 color_palette_provider，使用預設配色")
    color_palette_provider = None

# 🗺️ 車手全名到代碼的映射（2025 賽季）
DRIVER_NAME_TO_CODE = {
    # Red Bull Racing
    "Max Verstappen": "VER",
    "Liam Lawson": "LAW",
    "Sergio Perez": "PER",
    # Ferrari
    "Charles Leclerc": "LEC",
    "Lewis Hamilton": "HAM",
    # Mercedes
    "George Russell": "RUS",
    "Andrea Kimi Antonelli": "ANT",
    "Kimi Antonelli": "ANT",  # FastF1 使用的簡稱
    # McLaren
    "Lando Norris": "NOR",
    "Oscar Piastri": "PIA",
    # Aston Martin
    "Fernando Alonso": "ALO",
    "Lance Stroll": "STR",
    # Alpine
    "Pierre Gasly": "GAS",
    "Franco Colapinto": "COL",
    "Jack Doohan": "DOO",
    # Haas
    "Esteban Ocon": "OCO",
    "Oliver Bearman": "BEA",
    "Kevin Magnussen": "MAG",
    # RB (Racing Bulls)
    "Yuki Tsunoda": "TSU",
    "Isack Hadjar": "HAD",
    "Daniel Ricciardo": "RIC",
    # Kick Sauber
    "Gabriel Bortoleto": "BOR",
    "Nico Hülkenberg": "HUL",
    "Nico Hulkenberg": "HUL",  # 變體拼寫
    "Valtteri Bottas": "BOT",
    "Zhou Guanyu": "ZHO",
    # Williams
    "Alexander Albon": "ALB",
    "Carlos Sainz": "SAI",
    "Logan Sargeant": "SAR",
    # 未知車手（PDF 解析失敗或缺少車手資訊時的預設值）
    "Unknown": "UNK",
}

# 🌐 JSON 數據內容翻譯映射（中文 → 翻譯鍵）
# JSON 中的變更類型、分類等是中文，需要映射到多國語言鍵
CHANGE_TYPE_TRANSLATION_MAP = {
    "維修 (Repair)": "repair",
    "重大更新 (Major Update)": "major_update",
    "變更 (Change)": "change",
    "參數調整 (Parameter Adjustment)": "param_adjustment",
    "安全/標準件 (Safety/Standard Parts)": "safety_standard",
    "未分類 (Unclassified)": "unclassified",
    "噪音 (Noise)": "noise",
}

# 類型說明翻譯映射（中文 → 翻譯鍵）
DESCRIPTION_TRANSLATION_MAP = {
    "損壞後更換舊件/備件、小零件維護、冷卻系統管路": "desc_repair",
    "結構性改動、觸發 FIA 重新檢驗、非全新套件": "desc_major_update",
    "Parc Fermé 內合法調整、空力/配置切換、摩擦材料、懸吊": "desc_change",
    "純軟體參數變更，無硬體更換": "desc_param_adjustment",
    "FIA 標準安全設備、駕駛介面": "desc_safety_standard",
    "無法根據現有規則分類（信心度低於 0.60）": "desc_unclassified",
}

# 主分類翻譯映射（英文 → 翻譯鍵）
MAIN_CATEGORY_TRANSLATION_MAP = {
    "Aerodynamics": "aerodynamics",
    "Cooling": "cooling",
    "Suspension": "suspension",
    "Powertrain": "powertrain",
    "Brakes": "brakes",
    "Transmission": "transmission",
    "Chassis": "chassis",
    "Bodywork": "bodywork",
    "Electronics": "electronics",
    "Fuel System": "fuel_system",
    "Hydraulics": "hydraulics",
    "Safety": "safety",
    "Miscellaneous": "miscellaneous",
    "Other": "other",
}

# 子分類翻譯映射（英文 → 翻譯鍵）
SUB_CATEGORY_TRANSLATION_MAP = {
    # Aerodynamics
    "Front Wing": "front_wing",
    "Rear Wing": "rear_wing",
    "Floor": "floor",
    "Diffuser": "diffuser",
    "Sidepods": "sidepods",
    "Bargeboards": "bargeboards",
    
    # Cooling
    "Radiators": "radiators",
    "Cooling Ducts": "cooling_ducts",
    "Pumps": "pumps",
    
    # Suspension
    "Front Suspension": "front_suspension",
    "Rear Suspension": "rear_suspension",
    "Wishbones": "wishbones",
    
    # Powertrain
    "ICE": "ice",
    "Turbocharger": "turbocharger",
    "MGU-K": "mgu_k",
    "MGU-H": "mgu_h",
    
    # Brakes
    "Brake Discs": "brake_discs",
    "Brake Calipers": "brake_calipers",
    "Brake Ducts": "brake_ducts",
    
    # Transmission
    "Gearbox": "gearbox",
    "Clutch": "clutch",
    
    # Chassis
    "Monocoque": "monocoque",
    "Plank": "plank",
    
    # 其他常見子分類
    "T-Tray": "t_tray",
    "Fuel Tank": "fuel_tank",
    "Seat Belts": "seat_belts",
    "Fire Extinguisher": "fire_extinguisher",
    "Wheel Rims": "wheel_rims",
    "Other": "other",
}


class PartsAnalysisWidget(QWidget):
    """FIA Parts Classification 詳細記錄表格 Widget - API-ONLY 版本"""
    
    def __init__(self, api_base_url: str, year: int = 2025, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.year = year
        self._api_base_url = api_base_url
        self._is_initializing = False  # 防止初始化時重複觸發篩選
        
        # 數據
        self.records_data = []
        self.filtered_data = []
        self.current_filters = {}
        self._last_record_path = ""
        
        # 建立欄位映射：API中文欄位 -> 顯示欄位
        self.field_mapping = {
            "序號": tr('sequence_number', 'No.'),
            "比賽": tr('race', 'Race'),
            "車隊": tr('team', 'Team'),
            "車手": tr('driver', 'Driver'),
            "主分類": tr('main_category', 'Main Category'),
            "子分類": tr('sub_category', 'Sub Category'),
            "變更類型": tr('change_type', 'Change Type'),
            "分類信心度": tr('confidence', 'Confidence'),
            "類型說明": tr('description', 'Description'),
            "部件": tr('part', 'Part'),
            "日期": tr('date', 'Date')
        }
        
        # 建立反向映射：顯示欄位 -> API中文欄位
        self.reverse_field_mapping = {v: k for k, v in self.field_mapping.items()}
        
        self.setup_ui()
        self.setup_connections()
        
    def get_field_value(self, record, display_field_name, default=""):
        """通過顯示欄位名獲取API數據值"""
        api_field = self.reverse_field_mapping.get(display_field_name, display_field_name)
        return record.get(api_field, default)
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 篩選工具列
        self.setup_filter_toolbar(layout)
        
        # 統計摘要列
        self.setup_statistics_bar(layout)
        
        # 主要表格
        self.setup_main_table(layout)
        
    def setup_filter_toolbar(self, layout):
        """設置篩選工具列 - 增加主分類和子分類篩選"""
        toolbar_layout = QHBoxLayout()
        
        # 賽事篩選
        self.race_combo = QComboBox()
        self.race_combo.addItem(tr('all_races', 'All Races'), "")
        self.race_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(QLabel(tr('race', 'Race') + ":"))
        toolbar_layout.addWidget(self.race_combo)
        
        # 車隊篩選
        self.team_combo = QComboBox()
        self.team_combo.addItem(tr('all_teams', 'All Teams'), "")
        self.team_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(QLabel(tr('team', 'Team') + ":"))
        toolbar_layout.addWidget(self.team_combo)
        
        # 車手篩選
        self.driver_combo = QComboBox()
        self.driver_combo.addItem(tr('all_drivers', 'All Drivers'), "")
        self.driver_combo.setMinimumWidth(180)
        toolbar_layout.addWidget(QLabel(tr('driver', 'Driver') + ":"))
        toolbar_layout.addWidget(self.driver_combo)
        
        # 主分類篩選（新增）
        self.main_category_combo = QComboBox()
        self.main_category_combo.addItem(tr('all_main_categories', 'All Main Categories'), "")
        self.main_category_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(QLabel(tr('main_category', 'Main Cat') + ":"))
        toolbar_layout.addWidget(self.main_category_combo)
        
        # 子分類篩選（新增）
        self.sub_category_combo = QComboBox()
        self.sub_category_combo.addItem(tr('all_sub_categories', 'All Sub Categories'), "")
        self.sub_category_combo.setMinimumWidth(150)
        toolbar_layout.addWidget(QLabel(tr('sub_category', 'Sub Cat') + ":"))
        toolbar_layout.addWidget(self.sub_category_combo)
        
        # 變更類型篩選
        self.type_combo = QComboBox()
        self.type_combo.addItem(tr('all_types', 'All Types'), "")
        self.type_combo.setMinimumWidth(180)
        toolbar_layout.addWidget(QLabel(tr('change_type', 'Type') + ":"))
        toolbar_layout.addWidget(self.type_combo)
        
        # 關鍵字搜尋
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr('search_description', 'Search description or keywords...'))
        self.search_input.setMinimumWidth(200)
        toolbar_layout.addWidget(self.search_input)
        
        layout.addLayout(toolbar_layout)
        
    def setup_statistics_bar(self, layout):
        """設置統計摘要列"""
        self.stats_frame = QFrame()
        self.stats_frame.setFrameStyle(QFrame.StyledPanel)
        self.stats_frame.setFixedHeight(40)
        
        stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_label = QLabel(tr('loading', 'Loading...'))
        self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(self.stats_frame)
        
    def setup_main_table(self, layout):
        """設置主要表格"""
        self.table_widget = QTableWidget()
        self.setup_table_structure()
        layout.addWidget(self.table_widget)
        
    def setup_table_structure(self):
        """設置表格結構 - 增加 Action 欄位"""
        headers = [
            tr('sequence_number', 'No.'),
            tr('race', 'Race'),
            tr('team', 'Team'),
            tr('driver', 'Driver'),
            tr('part', 'Part'),
            tr('date', 'Date'),
            tr('action', 'Action')  # 新增 Action 欄位
        ]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 表格屬性
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSortingEnabled(True)
        
        # 響應式列寬設定
        header = self.table_widget.horizontalHeader()
        
        # 設定初始寬度（增加 Action 欄位）
        self.table_widget.setColumnWidth(0, 40)   # 序號
        self.table_widget.setColumnWidth(1, 120)  # 賽事
        self.table_widget.setColumnWidth(2, 120)  # 車隊
        self.table_widget.setColumnWidth(3, 150)  # 車手
        self.table_widget.setColumnWidth(4, 400)  # 部件
        self.table_widget.setColumnWidth(5, 100)  # 日期
        self.table_widget.setColumnWidth(6, 80)   # Action
        
        # 所有欄位都設為可手動調整
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            
    def setup_connections(self):
        """設置信號連接 - 只保留 PDF 原始欄位篩選"""
        # UI事件連接
        self.race_combo.currentTextChanged.connect(self.apply_filters)
        self.team_combo.currentTextChanged.connect(self.apply_filters)
        self.driver_combo.currentTextChanged.connect(self.apply_filters)
        self.search_input.textChanged.connect(self.apply_filters)
        
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功 - 從 MDI 調用"""
        try:
            self.logger.debug("🔥🔥🔥 [DEBUG] PartsAnalysisWidget.on_data_loaded called")
            self.logger.debug("🔥🔥🔥 [DEBUG] Data type: %s", type(data))
            self.logger.debug("🔥🔥🔥 [DEBUG] Data keys: %s", list(data.keys()) if isinstance(data, dict) else 'Not a dict')
            
            # 🔍 深度調試：檢查是否有嵌套的 data
            if isinstance(data, dict):
                if 'data' in data:
                    self.logger.debug("🔥 [DEBUG] Found nested 'data' key")
                    self.logger.debug("🔥 [DEBUG] Nested data type: %s", type(data['data']))
                    if isinstance(data['data'], dict):
                        self.logger.debug("🔥 [DEBUG] Nested data keys: %s", list(data['data'].keys()))
                if 'records' in data:
                    self.logger.debug("🔥 [DEBUG] Found 'records' at top level, count: %s", len(data['records']))
            
            self.logger.debug("🔥 [DEBUG] 準備調用 _validate_records_data()...")
            records_list = self._validate_records_data(data)
            self.logger.debug(
                "🔥🔥🔥 [DEBUG] _validate_records_data() 返回: %s, is None: %s",
                type(records_list),
                records_list is None
            )
            
            if records_list is None:
                self.logger.error("❌❌❌ [ERROR] Data validation failed - records_list is None!")
                self.show_error_message(tr('invalid_data_format', 'Invalid data format'))
                return

            self.logger.debug("🔥 [DEBUG] records_list 不是 None，準備賦值...")
            self.logger.debug("🔥 [DEBUG] records_list 不是 None，準備賦值...")
            self.records_data = records_list
            self.logger.debug(
                "🔥🔥🔥 [DEBUG] Successfully got records list, count: %s, source path: %s",
                len(self.records_data),
                self._last_record_path or 'unknown'
            )

            # 重置狀態樣式
            self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")

            # 更新篩選選項
            self.logger.debug("🔥 [DEBUG] 準備調用 update_filter_options()...")
            self.update_filter_options()
            self.logger.debug("🔥 [DEBUG] update_filter_options() 完成, _is_initializing=%s", self._is_initializing)
            
            # 🔥 確保初始化標誌已重置
            self._is_initializing = False
            self.logger.debug("🔥 [DEBUG] 強制設置 _is_initializing=False")
            
            # 應用當前篩選
            self.logger.debug("🔥 [DEBUG] 準備調用 apply_filters()...")
            self.apply_filters()
            self.logger.debug("🔥 [DEBUG] apply_filters() 完成")
            
            # 更新統計
            self.logger.debug("🔥 [DEBUG] 準備調用 update_statistics()...")
            self.update_statistics()
            self.logger.debug("🔥🔥🔥 [DEBUG] on_data_loaded() 全部完成！")
            
        except Exception as e:
            self.logger.exception("[ERROR] Failed to update records data: %s", str(e))
            self.show_error_message(f"Failed to update records data: {str(e)}")
            
    def _validate_records_data(self, data: Dict[str, Any]) -> Optional[List[Dict]]:
        """驗證記錄數據格式"""
        try:
            records, path = self._extract_records_list(data)

            if records is None:
                self.logger.error("[ERROR] [VALIDATE] PartsAnalysisWidget: Cannot find records list in data")
                return None

            if not isinstance(records, list):
                self.logger.error("[ERROR] [VALIDATE] PartsAnalysisWidget: Records is not a list type")
                return None

            self._last_record_path = " -> ".join(path) if path else "data.records"
            self.logger.info("[OK] [VALIDATE] PartsAnalysisWidget: Data validation passed, path: %s", self._last_record_path)
            return records
        except Exception as e:
            self.logger.exception("[ERROR] [VALIDATE] PartsAnalysisWidget: Validation exception: %s", e)
            return None

    def _extract_records_list(self, data: Any) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
        """在多層資料結構中尋找記錄列表"""
        
        target_keys = {"records", "changes", "parts_changes", "classified_changes"}
        visited: Set[int] = set()

        def _search(node: Any, breadcrumbs: List[str]) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
            node_id = id(node)
            if node_id in visited:
                return None, []
            visited.add(node_id)

            if isinstance(node, dict):
                for key in target_keys:
                    value = node.get(key)
                    if isinstance(value, list):
                        return value, breadcrumbs + [key]
                for key, value in node.items():
                    result, path = _search(value, breadcrumbs + [key])
                    if result is not None:
                        return result, path
            elif isinstance(node, list):
                for item in node:
                    result, path = _search(item, breadcrumbs)
                    if result is not None:
                        return result, path
            return None, []

        if isinstance(data, list):
            return data, ["<list>"]

        if not isinstance(data, dict):
            return None, []

        return _search(data, [])
            
    def update_filter_options(self):
        """更新篩選選項 - 增加主分類和子分類"""
        # 暫時禁用篩選觸發
        self._is_initializing = True
        
        # 收集所有唯一值
        races = set()
        teams = set()
        drivers = set()
        types = set()
        main_categories = set()
        sub_categories = set()
        
        for record in self.records_data:
            # ⚠️ 跳過噪音記錄
            change_type = record.get("變更類型", "")
            if "噪音" in change_type or "Noise" in change_type.upper():
                continue
            
            # 使用中文 API 欄位名
            race = record.get("賽事", "")
            if race:
                races.add(race)
                
            team = record.get("車隊", "")
            if team:
                teams.add(team)
                
            driver = record.get("車手", "")
            if driver:
                drivers.add(driver)
                
            change_type = record.get("變更類型", "")
            if change_type:
                types.add(change_type)
            
            # 新增主分類和子分類
            main_cat = record.get("主分類", "")
            if main_cat:
                main_categories.add(main_cat)
            
            sub_cat = record.get("子分類", "")
            if sub_cat:
                sub_categories.add(sub_cat)
        
        # 更新下拉選單
        self._update_combo_options(self.race_combo, sorted(races))
        self._update_combo_options(self.team_combo, sorted(teams))
        self._update_combo_options(self.driver_combo, sorted(drivers))
        self._update_combo_options(self.main_category_combo, sorted(main_categories))
        self._update_combo_options(self.sub_category_combo, sorted(sub_categories))
        self._update_combo_options(self.type_combo, sorted(types))
        
        # 重新啟用篩選觸發
        self._is_initializing = False
        
    def _update_combo_options(self, combo: QComboBox, options: list):
        """更新下拉選單選項"""
        current_text = combo.currentText()
        default_text = combo.itemText(0) if combo.count() > 0 else tr('all', 'All')
        default_data = combo.itemData(0) if combo.count() > 0 else ""

        combo.clear()
        combo.addItem(default_text or tr('all', 'All'), default_data if default_data is not None else "")
        
        for option in options:
            if option:  # 排除空值
                combo.addItem(option, option)
                
        # 恢復之前的選擇
        index = combo.findText(current_text)
        if index >= 0:
            combo.setCurrentIndex(index)
            
    def on_main_category_changed(self):
        """主分類變更時更新子分類選項"""
        # 如果正在初始化，跳過
        if self._is_initializing:
            return
            
        main_category = self.main_category_combo.currentData()
        
        # 暫時禁用篩選觸發
        self._is_initializing = True
        
        if not main_category:
            # 如果選擇「所有主分類」，顯示所有子分類
            sub_categories = set()
            for record in self.records_data:
                sub_cat = record.get("子分類", "")
                if sub_cat:
                    sub_categories.add(sub_cat)
            self._update_combo_options(self.sub_category_combo, sorted(sub_categories))
        else:
            # 只顯示該主分類下的子分類
            sub_categories = set()
            for record in self.records_data:
                if record.get("主分類", "") == main_category:
                    sub_cat = record.get("子分類", "")
                    if sub_cat:
                        sub_categories.add(sub_cat)
            
            self._update_combo_options(self.sub_category_combo, sorted(sub_categories))
        
        # 重新啟用篩選觸發
        self._is_initializing = False
        
        # 應用篩選
        self.apply_filters()
    
    def apply_filters(self, _=None):
        """應用篩選條件 - 增加主分類和子分類篩選"""
        self.logger.debug("🔥🔥 [FILTER] apply_filters() 開始執行")
        self.logger.debug("🔥🔥 [FILTER] _is_initializing=%s", self._is_initializing)
        
        # 如果正在初始化，跳過篩選
        if self._is_initializing:
            self.logger.debug("🔥🔥 [FILTER] 跳過篩選（正在初始化）")
            return
        
        self.logger.debug("🔥🔥 [FILTER] records_data 數量: %s", len(self.records_data))
        
        # 收集篩選條件
        try:
            filters = {
                "race": self.race_combo.currentData() if self.race_combo.currentData() else "",
                "team": self.team_combo.currentData() if self.team_combo.currentData() else "",
                "driver": self.driver_combo.currentData() if self.driver_combo.currentData() else "",
                "main_category": self.main_category_combo.currentData() if self.main_category_combo.currentData() else "",
                "sub_category": self.sub_category_combo.currentData() if self.sub_category_combo.currentData() else "",
                "type": self.type_combo.currentData() if self.type_combo.currentData() else "",
                "search": self.search_input.text().strip().lower()
            }
            self.logger.debug("🔥🔥 [FILTER] 篩選條件: %s", filters)
        except Exception as e:
            self.logger.exception("❌❌ [FILTER] 收集篩選條件時出錯: %s", e)
            return
        
        # 篩選數據
        self.logger.debug("🔥🔥 [FILTER] 開始篩選...")
        self.filtered_data = []
        for record in self.records_data:
            if self._matches_filters(record, filters):
                self.filtered_data.append(record)
        
        self.logger.debug("🔥🔥🔥 [DEBUG] Filter result: %s/%s records", len(self.filtered_data), len(self.records_data))
        
        # 更新表格
        self.logger.debug("🔥🔥 [FILTER] 準備調用 populate_table()...")
        self.populate_table()
        self.logger.debug("🔥🔥 [FILTER] populate_table() 完成")
        
        # 更新統計
        self.logger.debug("🔥🔥 [FILTER] 準備調用 update_statistics()...")
        self.update_statistics()
        self.logger.debug("🔥🔥 [FILTER] apply_filters() 全部完成")
        
    def _matches_filters(self, record: dict, filters: dict) -> bool:
        """檢查記錄是否符合篩選條件 - 只檢查 PDF 原始欄位"""
        # 賽事篩選
        if filters["race"]:
            race = record.get("賽事", "")
            if race != filters["race"]:
                return False
        
        # 車隊篩選
        if filters["team"]:
            team = record.get("車隊", "")
            if team != filters["team"]:
                return False
        
        # 車手篩選
        if filters["driver"]:
            driver = record.get("車手", "")
            if driver != filters["driver"]:
                return False
        
        # 文字搜尋（只搜尋 PDF 原始欄位）
        if filters["search"]:
            search_text = filters["search"].lower()
            searchable_fields = [
                str(record.get("部件", "")),
                str(record.get("車隊", "")),
                str(record.get("車手", "")),
                str(record.get("賽事", ""))
            ]
            
            search_content = " ".join(searchable_fields).lower()
            if search_text not in search_content:
                return False
                
        return True
        
    def populate_table(self):
        """填充表格數據 - 只顯示 PDF 原始欄位（6欄：序號、賽事、車隊、車手、部件、日期）"""
        self.logger.debug("🔥🔥 [POPULATE] 開始填充表格，filtered_data 數量: %s", len(self.filtered_data))
        self.table_widget.setRowCount(len(self.filtered_data))
        
        # 🎨 確保顏色配置已載入
        if color_palette_provider:
            try:
                color_palette_provider.ensure_loaded()
            except Exception as e:
                self.logger.warning("[PARTS_WIDGET] ⚠️ 顏色配置載入失敗: %s", e)
        
        for row, record in enumerate(self.filtered_data):
            try:
                # 欄 0: 序號
                seq_item = QTableWidgetItem(str(row + 1))
                seq_item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 0, seq_item)
                
                # 欄 1: 賽事
                race = record.get("賽事", "")
                race_item = QTableWidgetItem(str(race))
                self.table_widget.setItem(row, 1, race_item)
                
                # 🔄 將車手全名轉換為代碼（與 Ideal Lap Ranking 一致）
                driver_full_name = record.get("車手", "")
                driver_code = DRIVER_NAME_TO_CODE.get(driver_full_name, None)
                
                # 如果找不到映射，使用前三個字母並記錄警告
                if driver_code is None:
                    driver_code = driver_full_name[:3].upper() if driver_full_name else "UNK"
                    self.logger.warning(
                        "⚠️ [POPULATE] 找不到車手映射: '%s' (車隊: %s)",
                        driver_full_name,
                        record.get('車隊', 'Unknown')
                    )
                
                # 🔄 獲取翻譯後的車隊名稱（與 Ideal Lap Ranking 一致）
                team_original = record.get("車隊", "")
                team_translated = get_team_name_text(team_original)
                
                # 🎨 獲取車手顏色
                driver_color = self._get_driver_color(driver_code)
                
                # 欄 2: 車隊（使用車手顏色背景 + 翻譯後的車隊名稱）
                team_item = self._create_colored_item(team_translated, driver_color)
                team_item.setToolTip(f"{team_translated} - {driver_full_name}")
                self.table_widget.setItem(row, 2, team_item)
                
                # 欄 3: 車手（使用車手代碼 + 車手顏色背景）
                driver_item = self._create_colored_item(driver_code, driver_color)
                driver_item.setToolTip(f"{driver_code} - {team_translated}")
                self.table_widget.setItem(row, 3, driver_item)
                
                # 欄 4: 部件
                part = record.get("部件", "")
                part_item = QTableWidgetItem(str(part))
                self.table_widget.setItem(row, 4, part_item)
                
                # 欄 5: 日期
                race_date = record.get("賽事日期", "")
                date_item = QTableWidgetItem(str(race_date))
                self.table_widget.setItem(row, 5, date_item)
                
                # 欄 6: Action（來自 PDF 文件，固定顯示 N/A）
                action_item = QTableWidgetItem("N/A")
                action_item.setTextAlignment(Qt.AlignCenter)
                action_item.setForeground(QColor("#888888"))  # 灰色文字表示不適用
                action_item.setToolTip(tr('action_na_tooltip', 'Data from PDF document - Action not available'))
                self.table_widget.setItem(row, 6, action_item)
                
            except Exception as e:
                self.logger.exception("❌ [POPULATE] 填充第 %s 行時出錯: %s", row, e)
        
        self.logger.debug("🔥🔥 [POPULATE] 表格填充完成，共 %s 行", len(self.filtered_data))
            
    def get_type_color(self, change_type: str) -> str:
        """
        獲取變更類型顏色
        
        Args:
            change_type: 變更類型（中文格式，如 "維修 (Repair)"）
            
        Returns:
            顏色代碼
        """
        # 將中文類型轉換為統一格式進行匹配
        type_str = str(change_type).upper()
        
        # 使用中英文混合匹配
        colors = {
            "重大更新": "#f5c6cb",      # 淺紅色
            "MAJOR UPDATE": "#f5c6cb",
            "變更": "#d4edda",          # 淺綠色
            "CHANGE": "#d4edda",
            "維修": "#fff3cd",          # 淺黃色
            "REPAIR": "#fff3cd",
            "參數調整": "#d1ecf1",      # 淺青色
            "PARAMETER ADJUSTMENT": "#d1ecf1",
            "PARAMETER": "#d1ecf1",
            "安全": "#d4edda",          # 淺綠色
            "SAFETY": "#d4edda",
            "未分類": "#f5f5f5",        # 淺灰色
            "UNCLASSIFIED": "#f5f5f5",
            "噪音": "#e9ecef",          # 更淺灰色
            "NOISE": "#e9ecef"
        }
        
        # 檢查是否包含任何關鍵字
        for key, color in colors.items():
            if key in type_str:
                return color
        
        return "#ffffff"  # 預設白色
        
    def get_confidence_color(self, confidence) -> str:
        """獲取信心度顏色"""
        try:
            conf_value = float(confidence) if confidence else 0
        except (ValueError, TypeError):
            return "#ffffff"
        
        if conf_value >= 0.95:
            return "#d4edda"  # 深綠色 (極高信心)
        elif conf_value >= 0.80:
            return "#d1ecf1"  # 淺青色 (高信心)
        elif conf_value >= 0.70:
            return "#fff3cd"  # 淺黃色 (中信心)
        elif conf_value >= 0.60:
            return "#f8d7da"  # 淺橙色 (低信心)
        else:
            return "#f5c6cb"  # 淺紅色 (極低信心)
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """
        獲取車手顏色（使用通用顏色系統，與 Ideal Lap Ranking 完全一致）
        
        Args:
            driver_code: 車手代碼（例如: "VER", "HAM"）或車手全名（例如: "Max Verstappen"）
            
        Returns:
            QColor: 車手顏色
        """
        if not driver_code:
            return QColor(128, 128, 128)
        
        # 🔍 如果是全名，轉換為代碼
        actual_code = DRIVER_NAME_TO_CODE.get(driver_code, driver_code)
        
        # 📊 DEBUG: 打印映射結果（首次使用時）
        if not hasattr(self, '_debug_driver_mapping_printed'):
            self._debug_driver_mapping_printed = set()
        
        if driver_code not in self._debug_driver_mapping_printed:
            if driver_code != actual_code:
                self.logger.info("[PARTS_WIDGET] 🗺️ 車手映射: %s → %s", driver_code, actual_code)
            self._debug_driver_mapping_printed.add(driver_code)
        
        if color_palette_provider:
            try:
                color = color_palette_provider.get_driver_color(actual_code, fallback=True)
                return color
            except Exception as e:
                self.logger.warning("[PARTS_WIDGET] ⚠️ 獲取車手顏色失敗 (%s): %s", actual_code, e)
        
        # Fallback: 返回預設灰色
        return QColor(128, 128, 128)
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """
        創建帶背景色的表格項目，自動選擇文字顏色（與 Ideal Lap Ranking 完全一致）
        
        Args:
            text: 顯示文字
            bg_color: 背景顏色（QColor）
            
        Returns:
            QTableWidgetItem: 帶顏色的表格項目
        """
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # 根據背景色亮度決定文字顏色（與 Ideal Lap Ranking 使用相同算法）
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item
            
    def update_statistics(self):
        """更新統計摘要"""
        if not self.filtered_data:
            self.stats_label.setText(tr('no_data', 'No data'))
            return
            
        total = len(self.filtered_data)
        
        # 按變更類型統計
        type_counts = {}
        for record in self.filtered_data:
            change_type = record.get("變更類型", "")
            type_counts[change_type] = type_counts.get(change_type, 0) + 1
        
        # 計算平均信心度
        confidences = []
        for record in self.filtered_data:
            conf = record.get("分類信心度", 0)
            try:
                confidences.append(float(conf))
            except (ValueError, TypeError):
                pass
        
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
        
        # 構建統計文字（全面多國語言化）
        stats_parts = [f"{tr('total_records', 'Total Records')}: {total}"]
        stats_parts.append(f"{tr('avg_confidence', 'Avg Confidence')}: {avg_conf:.2f}")
        
        # 顯示主要類型（翻譯變更類型名稱）
        main_types = [
            "維修 (Repair)",
            "重大更新 (Major Update)", 
            "變更 (Change)",
            "參數調整 (Parameter Adjustment)"
        ]
        
        type_display_map = {
            "維修 (Repair)": tr('repair', 'Repair'),
            "重大更新 (Major Update)": tr('major_update', 'Major'),
            "變更 (Change)": tr('change', 'Change'),
            "參數調整 (Parameter Adjustment)": tr('param_adj', 'Param Adj')
        }
        
        for change_type in main_types:
            if change_type in type_counts:
                display_name = type_display_map.get(change_type, change_type)
                stats_parts.append(f"{display_name}: {type_counts[change_type]}")
        
        # 其他類型總計
        other_count = sum(count for ctype, count in type_counts.items() 
                         if ctype not in main_types)
        if other_count > 0:
            stats_parts.append(f"{tr('other', 'Other')}: {other_count}")
        
        self.stats_label.setText(" | ".join(stats_parts))
    
    def _translate_change_type(self, change_type: str) -> str:
        """
        翻譯變更類型（從 JSON 中文內容到多國語言）
        
        Args:
            change_type: 變更類型（如 "維修 (Repair)"）
            
        Returns:
            翻譯後的文字
        """
        # 從映射表獲取翻譯鍵
        trans_key = CHANGE_TYPE_TRANSLATION_MAP.get(change_type)
        if trans_key:
            # 🌐 使用翻譯鍵獲取多國語言文字
            # fallback 使用括號內的英文部分
            english_part = self._extract_english_from_parentheses(change_type)
            return tr(trans_key, english_part)
        
        # 如果沒有映射，嘗試提取英文部分
        english_part = self._extract_english_from_parentheses(change_type)
        return english_part if english_part else change_type
    
    def _extract_english_from_parentheses(self, text: str) -> str:
        """
        從中文(English)格式中提取英文部分
        
        Args:
            text: 原始文字（如 "維修 (Repair)"）
            
        Returns:
            英文部分（如 "Repair"）或原文
        """
        import re
        # 匹配括號內的英文
        match = re.search(r'\(([^)]+)\)', text)
        if match:
            return match.group(1).strip()
        return text
    
    def _translate_category(self, category: str, is_main: bool = True) -> str:
        """
        翻譯分類名稱（從英文到多國語言）
        
        Args:
            category: 分類名稱（英文，如 "Aerodynamics"）
            is_main: 是否為主分類
            
        Returns:
            翻譯後的文字
        """
        # 選擇映射表
        mapping = MAIN_CATEGORY_TRANSLATION_MAP if is_main else SUB_CATEGORY_TRANSLATION_MAP
        
        # 從映射表獲取翻譯鍵
        trans_key = mapping.get(category)
        if trans_key:
            return tr(trans_key, category)
        
        # 如果沒有映射，返回原文
        return category
    
    def _translate_description(self, description: str) -> str:
        """
        翻譯類型說明（從中文到多國語言）
        
        Args:
            description: 類型說明（中文，如 "損壞後更換舊件/備件、小零件維護、冷卻系統管路"）
            
        Returns:
            翻譯後的文字
        """
        # 從映射表獲取翻譯鍵
        trans_key = DESCRIPTION_TRANSLATION_MAP.get(description)
        if trans_key:
            # 🌐 使用翻譯鍵獲取多國語言文字
            # 保留中文作為 fallback（因為沒有括號格式）
            return tr(trans_key, description)
        
        # 如果沒有映射，返回原文
        return description
        
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        QMessageBox.critical(
            self,
            tr('error', 'Error'),
            message
        )


# ========== 測試程式 ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = PartsAnalysisWidget(
        api_base_url="https://api.f1telemetrystationpro.org",
        year=2025
    )
    window.setWindowTitle(tr('fia_parts_analysis', "FIA Parts Analysis Widget - API-ONLY Test"))
    window.resize(1400, 800)
    window.show()
    
    sys.exit(app.exec_())
