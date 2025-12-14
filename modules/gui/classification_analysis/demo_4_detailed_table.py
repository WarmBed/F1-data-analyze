#!/usr/bin/env python3
"""
FIA Parts Changes Classification - Detailed Records Widget
===========================================================

完全參照 AccidentDetailedListWidget 實現的詳細記錄表格版本

功能特點：
- 頂部過濾工具列（賽事/車隊/車手/類型 + 搜尋）
- 統計摘要列
- 完整變更記錄表格（所有欄位）
- 支援排序、搜尋、顏色標記

表格欄位：
- 序號 | 賽事 | 車隊 | 車手 | 變更類型 | 信心度 | 變更描述 | 部件 | 日期

Author: F1T Team  
Date: 2025-11-07
Version: 2.0 (完全參照 accident_analysis)
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
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor
import requests

from core.gui_i18n import tr
from core.api_base_url import resolve_api_base_url


class ClassificationApiWorker(QThread):
    """API 數據獲取背景執行緒"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, year: int, params: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.year = year
        self.params = params or {}
    
    def run(self):
        ""執行 API 請求並從 JSON 檔案獲取完整數據"""
        try:
            # ✅ 中斷檢查點 1: 開始時
            if self.isInterruptionRequested():
                return
            print(f"[WORKER] Starting API request for year {self.year}")
            
            # 步驟 1: 先呼叫 API 獲取統計資訊
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            payload = {
                "function_id": "29",
                "year": self.year,
                **self.params
            }
            
            # ✅ 中斷檢查點 2: HTTP 請求前
            if self.isInterruptionRequested():
                return
            response = requests.post(endpoint, params=payload, timeout=30.0)
            # ✅ 中斷檢查點 3: HTTP 請求後
            if self.isInterruptionRequested():
                return
            response.raise_for_status()
            api_result = response.json()
            
            if not api_result.get("success"):
                self.failure.emit(api_result.get("message", "API request failed"))
                return
            
            api_data = api_result.get("data", {})
            
            # 步驟 2: 從本地 JSON 檔案讀取完整數據（優先使用 classified_with_categories）
            import os
            json_file_with_cat = f"{self.year}_f1_parts_changes_v2_classified_with_categories.json"
            json_file_normalized = f"{self.year}_f1_parts_changes_v2_normalized.json"
            json_file_v2 = f"{self.year}_f1_parts_changes_v2_classified.json"
            
            # 優先使用帶分類的版本
            if os.path.exists(json_file_with_cat):
                print(f"[WORKER] Loading classified_with_categories data: {json_file_with_cat}")
                import json
                with open(json_file_with_cat, 'r', encoding='utf-8') as f:
                    all_records = json.load(f)
            elif os.path.exists(json_file_normalized):
                print(f"[WORKER] Loading normalized data: {json_file_normalized}")
                import json
                with open(json_file_normalized, 'r', encoding='utf-8') as f:
                    all_records = json.load(f)
            elif os.path.exists(json_file_v2):
                print(f"[WORKER] Loading complete data from local file: {json_file_v2}")
                import json
                with open(json_file_v2, 'r', encoding='utf-8') as f:
                    all_records = json.load(f)
            else:
                print(f"[WARNING] Local files not found, using API data only")
                self.success.emit(api_data)
                return
            
            # 排除噪音記錄（與 CLI 一致）
            filtered_records = [r for r in all_records if "噪音" not in r.get("變更類型", "")]
            print(f"[WORKER] Loaded {len(filtered_records)} records (excluded noise)")
            
            # 合併數據：使用 API 的統計資訊 + 本地完整記錄
            api_data["records"] = filtered_records
            api_data["statistics"]["total_records"] = len(filtered_records)
            
            # ✅ 中斷檢查：被中斷時不發送信號
            if self.isInterruptionRequested():
                return
            self.success.emit(api_data)
                
        except Exception as e:
            print(f"[WORKER] API request error: {str(e)}")
            # ✅ 中斷檢查：被中斷時不發送錯誤信號
            if self.isInterruptionRequested():
                return
            self.failure.emit(str(e))


class ClassificationDetailedTableWidget(QWidget):
    """FIA Parts Classification 詳細記錄表格 Widget - 完全參照 AccidentDetailedListWidget"""
    
    def __init__(self, api_base_url: str, year: int = 2025, parent=None):
        super().__init__(parent)
        self.year = year
        self._api_base_url = api_base_url
        self._api_worker = None
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
        self.load_data()
        
    def get_field_value(self, record, display_field_name, default=""):
        """通過顯示欄位名獲取API數據值"""
        api_field = self.reverse_field_mapping.get(display_field_name, display_field_name)
        return record.get(api_field, default)
        
    def setup_ui(self):
        """設置使用者界面 - 完全參照 AccidentDetailedListWidget"""
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
        self.race_combo.setMinimumWidth(150)  # 設定最小寬度以顯示完整名稱
        toolbar_layout.addWidget(QLabel(tr('race', 'Race') + ":"))
        toolbar_layout.addWidget(self.race_combo)
        
        # 車隊篩選
        self.team_combo = QComboBox()
        self.team_combo.addItem(tr('all_teams', 'All Teams'), "")
        self.team_combo.setMinimumWidth(150)  # 設定最小寬度
        toolbar_layout.addWidget(QLabel(tr('team', 'Team') + ":"))
        toolbar_layout.addWidget(self.team_combo)
        
        # 車手篩選
        self.driver_combo = QComboBox()
        self.driver_combo.addItem(tr('all_drivers', 'All Drivers'), "")
        self.driver_combo.setMinimumWidth(180)  # 車手名稱較長
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
        self.type_combo.setMinimumWidth(180)  # 類型名稱較長
        toolbar_layout.addWidget(QLabel(tr('change_type', 'Type') + ":"))
        toolbar_layout.addWidget(self.type_combo)
        
        # 關鍵字搜尋
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr('search_description', 'Search description or keywords...'))
        self.search_input.setMinimumWidth(200)
        toolbar_layout.addWidget(self.search_input)
        
        # 刷新按鈕
        self.refresh_button = QPushButton(tr('refresh', 'Refresh'))
        self.refresh_button.clicked.connect(self.refresh_data)
        toolbar_layout.addWidget(self.refresh_button)
        
        layout.addLayout(toolbar_layout)
        
    def setup_statistics_bar(self, layout):
        """設置統計摘要列 - 完全參照 AccidentDetailedListWidget"""
        self.stats_frame = QFrame()
        self.stats_frame.setFrameStyle(QFrame.StyledPanel)
        self.stats_frame.setFixedHeight(40)
        
        stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_label = QLabel(tr('loading', 'Loading...'))
        self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")
        stats_layout.addWidget(self.stats_label)
        
        layout.addWidget(self.stats_frame)
        
    def setup_main_table(self, layout):
        """設置主要表格 - 完全參照 AccidentDetailedListWidget"""
        self.table_widget = QTableWidget()
        self.setup_table_structure()
        layout.addWidget(self.table_widget)
        
    def setup_table_structure(self):
        """設置表格結構 - 增加主分類和子分類欄位"""
        headers = [
            tr('sequence_number', 'No.'),
            tr('race', 'Race'),
            tr('team', 'Team'),
            tr('driver', 'Driver'),
            tr('main_category', 'Main Cat'),      # 新增主分類
            tr('sub_category', 'Sub Cat'),        # 新增子分類
            tr('change_type', 'Type'),
            tr('confidence', 'Confidence'),
            tr('description', 'Description'),
            tr('part', 'Part'),
            tr('date', 'Date')
        ]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 表格屬性 - 完全參照 AccidentDetailedListWidget
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSortingEnabled(True)
        
        # 響應式列寬設定 - 優化為完整顯示名稱
        header = self.table_widget.horizontalHeader()
        
        # 設定初始寬度（增加主分類和子分類欄位）
        self.table_widget.setColumnWidth(0, 40)   # 序號
        self.table_widget.setColumnWidth(1, 120)  # 賽事（減少）
        self.table_widget.setColumnWidth(2, 120)  # 車隊（減少）
        self.table_widget.setColumnWidth(3, 150)  # 車手（減少）
        self.table_widget.setColumnWidth(4, 100)  # 主分類（減少）
        self.table_widget.setColumnWidth(5, 120)  # 子分類（減少）
        self.table_widget.setColumnWidth(6, 150)  # 變更類型（減少）
        self.table_widget.setColumnWidth(7, 80)   # 信心度（減少）
        self.table_widget.setColumnWidth(8, 350)  # 描述（增加！）
        self.table_widget.setColumnWidth(9, 250)  # 部件（增加）
        self.table_widget.setColumnWidth(10, 100) # 日期
        
        # 所有欄位都設為可手動調整
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
            
    def setup_connections(self):
        """設置信號連接 - 增加主分類和子分類篩選"""
        # UI事件連接
        self.race_combo.currentTextChanged.connect(self.apply_filters)
        self.team_combo.currentTextChanged.connect(self.apply_filters)
        self.driver_combo.currentTextChanged.connect(self.apply_filters)
        self.main_category_combo.currentTextChanged.connect(self.on_main_category_changed)  # 主分類變更時更新子分類
        self.sub_category_combo.currentTextChanged.connect(self.apply_filters)
        self.type_combo.currentTextChanged.connect(self.apply_filters)
        self.search_input.textChanged.connect(self.apply_filters)
        
    def load_data(self):
        """載入數據"""
        print(f"[DEMO4] Loading data for year {self.year}")
        self.stats_label.setText(tr('loading', 'Loading...'))
        
        if self._api_worker and self._api_worker.isRunning():
            return
        
        self._api_worker = ClassificationApiWorker(self._api_base_url, self.year, parent=self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_load_error)
        self._api_worker.start()
        
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功 - 完全參照 AccidentDetailedListWidget.update_data"""
        try:
            print(f"[DEBUG] ClassificationDetailedTableWidget.on_data_loaded called")
            print(f"[DEBUG] Data type: {type(data)}")
            print(f"[DEBUG] Data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            
            records_list = self._validate_records_data(data)
            if records_list is None:
                print(f"[ERROR] Data validation failed")
                self.show_error_message(tr('invalid_data_format', 'Invalid data format'))
                return

            self.records_data = records_list
            print(
                f"[DEBUG] Successfully got records list, count: {len(self.records_data)}, "
                f"source path: {self._last_record_path or 'unknown'}"
            )

            # 重置狀態樣式
            self.stats_label.setStyleSheet("font-weight: bold; color: #495057;")

            # 更新篩選選項
            self.update_filter_options()
            
            # 應用當前篩選
            self.apply_filters()
            
            # 更新統計
            self.update_statistics()
            
        except Exception as e:
            print(f"[ERROR] Failed to update records data: {str(e)}")
            self.show_error_message(f"Failed to update records data: {str(e)}")
            
    def on_load_error(self, error_msg: str):
        """數據載入失敗"""
        print(f"[DEMO4] Load error: {error_msg}")
        self.stats_label.setText(f"{tr('load_failed', 'Load failed')}: {error_msg}")
        self.stats_label.setStyleSheet("font-weight: bold; color: #e74c3c;")
        
        QMessageBox.warning(
            self,
            tr('load_error', 'Load Error'),
            tr('load_error_message', 'Failed to load data: {}').format(error_msg)
        )
            
    def _validate_records_data(self, data: Dict[str, Any]) -> Optional[List[Dict]]:
        """驗證記錄數據格式 - 完全參照 AccidentDetailedListWidget._validate_incidents_data"""
        try:
            records, path = self._extract_records_list(data)

            if records is None:
                print("[ERROR] [VALIDATE] ClassificationDetailedTableWidget: Cannot find records list in data")
                return None

            if not isinstance(records, list):
                print("[ERROR] [VALIDATE] ClassificationDetailedTableWidget: Records is not a list type")
                return None

            self._last_record_path = " -> ".join(path) if path else "data.records"
            print(f"[OK] [VALIDATE] ClassificationDetailedTableWidget: Data validation passed, path: {self._last_record_path}")
            return records
        except Exception as e:
            print(f"[ERROR] [VALIDATE] ClassificationDetailedTableWidget: Validation exception: {e}")
            return None

    def _extract_records_list(self, data: Any) -> Tuple[Optional[List[Dict[str, Any]]], List[str]]:
        """在多層資料結構中尋找記錄列表 - 完全參照 AccidentDetailedListWidget._extract_incidents_list"""
        
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
            # 使用中文 API 欄位名
            race = record.get("比賽", "")
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
        """更新下拉選單選項 - 完全參照 AccidentDetailedListWidget._update_combo_options"""
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
        """應用篩選條件 - 增加主分類和子分類篩選（_參數用於接收信號參數）"""
        # 如果正在初始化，跳過篩選
        if self._is_initializing:
            return
            
        # 收集篩選條件
        filters = {
            "race": self.race_combo.currentData() if self.race_combo.currentData() else "",
            "team": self.team_combo.currentData() if self.team_combo.currentData() else "",
            "driver": self.driver_combo.currentData() if self.driver_combo.currentData() else "",
            "main_category": self.main_category_combo.currentData() if self.main_category_combo.currentData() else "",
            "sub_category": self.sub_category_combo.currentData() if self.sub_category_combo.currentData() else "",
            "type": self.type_combo.currentData() if self.type_combo.currentData() else "",
            "search": self.search_input.text().strip().lower()
        }
        
        # 篩選數據
        self.filtered_data = []
        for record in self.records_data:
            if self._matches_filters(record, filters):
                self.filtered_data.append(record)
        
        print(f"[DEBUG] Filter result: {len(self.filtered_data)}/{len(self.records_data)} records")
        
        # 更新表格
        self.populate_table()
        
        # 更新統計
        self.update_statistics()
        
    def _matches_filters(self, record: dict, filters: dict) -> bool:
        """檢查記錄是否符合篩選條件 - 增加主分類和子分類篩選"""
        # 賽事篩選
        if filters["race"]:
            race = record.get("比賽", "")
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
        
        # 主分類篩選（新增）
        if filters.get("main_category"):
            main_cat = record.get("主分類", "")
            if main_cat != filters["main_category"]:
                return False
        
        # 子分類篩選（新增）
        if filters.get("sub_category"):
            sub_cat = record.get("子分類", "")
            if sub_cat != filters["sub_category"]:
                return False
        
        # 變更類型篩選
        if filters["type"]:
            change_type = record.get("變更類型", "")
            if change_type != filters["type"]:
                return False
        
        # 文字搜尋
        if filters["search"]:
            search_text = filters["search"].lower()
            searchable_fields = [
                str(record.get("類型說明", "")),
                str(record.get("部件", "")),
                str(record.get("車隊", "")),
                str(record.get("車手", "")),
                str(record.get("比賽", "")),
                str(record.get("變更類型", "")),
                str(record.get("主分類", "")),
                str(record.get("子分類", ""))
            ]
            
            search_content = " ".join(searchable_fields).lower()
            if search_text not in search_content:
                return False
                
        return True
        
    def populate_table(self):
        """填充表格數據 - 增加主分類和子分類欄位顯示"""
        self.table_widget.setRowCount(len(self.filtered_data))
        
        for row, record in enumerate(self.filtered_data):
            # 序號
            seq_item = QTableWidgetItem(str(row + 1))
            seq_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 0, seq_item)
            
            # 賽事
            race = record.get("比賽", "")
            self.table_widget.setItem(row, 1, QTableWidgetItem(str(race)))
            
            # 車隊
            team = record.get("車隊", "")
            self.table_widget.setItem(row, 2, QTableWidgetItem(str(team)))
            
            # 車手
            driver = record.get("車手", "")
            driver_item = QTableWidgetItem(str(driver))
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 3, driver_item)
            
            # 主分類（新增）
            main_cat = record.get("主分類", "")
            main_cat_item = QTableWidgetItem(str(main_cat))
            main_cat_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 4, main_cat_item)
            
            # 子分類（新增）
            sub_cat = record.get("子分類", "")
            sub_cat_item = QTableWidgetItem(str(sub_cat))
            self.table_widget.setItem(row, 5, sub_cat_item)
            
            # 變更類型（帶顏色）
            change_type = record.get("變更類型", "")
            type_item = QTableWidgetItem(str(change_type))
            type_item.setBackground(QColor(self.get_type_color(change_type)))
            self.table_widget.setItem(row, 6, type_item)
            
            # 信心度（帶顏色）
            confidence = record.get("分類信心度", 0)
            try:
                conf_value = float(confidence) if confidence else 0
                conf_text = f"{conf_value:.2f}"
            except (ValueError, TypeError):
                conf_text = str(confidence)
            confidence_item = QTableWidgetItem(conf_text)
            confidence_item.setTextAlignment(Qt.AlignCenter)
            confidence_item.setBackground(QColor(self.get_confidence_color(confidence)))
            self.table_widget.setItem(row, 7, confidence_item)
            
            # 描述
            description = record.get("類型說明", "")
            self.table_widget.setItem(row, 8, QTableWidgetItem(str(description)))
            
            # 部件
            part = record.get("部件", "")
            self.table_widget.setItem(row, 9, QTableWidgetItem(str(part)))
            
            # 日期
            date = record.get("日期", "")
            self.table_widget.setItem(row, 10, QTableWidgetItem(str(date)))
            
    def get_type_color(self, change_type: str) -> str:
        """獲取變更類型顏色 - 參照 AccidentDetailedListWidget.get_severity_color"""
        type_str = str(change_type).upper()
        
        colors = {
            "MAJOR UPDATE": "#f5c6cb",         # 淺紅色 (類似 CRITICAL)
            "CHANGE": "#d4edda",               # 淺綠色 (類似 LOW)
            "REPAIR": "#fff3cd",               # 淺黃色 (類似 MEDIUM)
            "PARAMETER ADJUSTMENT": "#d1ecf1", # 淺青色
            "SAFETY": "#d4edda",               # 淺綠色
            "UNCLASSIFIED": "#f5f5f5",         # 淺灰色
            "NOISE": "#e9ecef"                 # 更淺灰色
        }
        
        for key, color in colors.items():
            if key in type_str:
                return color
        
        return "#ffffff"
        
    def get_confidence_color(self, confidence) -> str:
        """獲取信心度顏色 - 參照 AccidentDetailedListWidget.get_impact_color"""
        try:
            conf_value = float(confidence) if confidence else 0
        except (ValueError, TypeError):
            return "#ffffff"
        
        # 類似影響程度的顏色分級
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
            
    def update_statistics(self):
        """更新統計摘要 - 完全參照 AccidentDetailedListWidget.update_statistics"""
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
        
        # 構建統計文字（直接使用英文避免 tr() 遞迴問題）
        stats_parts = [f"Total Records: {total}"]
        stats_parts.append(f"Avg Confidence: {avg_conf:.2f}")
        
        # 顯示主要類型
        main_types = ["MAJOR UPDATE", "CHANGE", "REPAIR", "PARAMETER ADJUSTMENT"]
        for change_type in main_types:
            if change_type in type_counts:
                # 簡化類型名稱顯示
                display_name = {
                    "MAJOR UPDATE": "Major",
                    "CHANGE": "Change",
                    "REPAIR": "Repair",
                    "PARAMETER ADJUSTMENT": "Param Adj"
                }.get(change_type, change_type)
                stats_parts.append(f"{display_name}: {type_counts[change_type]}")
        
        # 其他類型總計
        other_count = sum(count for ctype, count in type_counts.items() 
                         if ctype not in main_types)
        if other_count > 0:
            stats_parts.append(f"Other: {other_count}")
        
        self.stats_label.setText(" | ".join(stats_parts))
        
    def refresh_data(self):
        """刷新數據 - 完全參照 AccidentDetailedListWidget.refresh_data"""
        self.load_data()
        
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
    
    window = ClassificationDetailedTableWidget(2025)
    window.setWindowTitle("Demo 4: FIA Parts Classification - Detailed Table (v2.0)")
    window.resize(1400, 800)
    window.show()
    
    sys.exit(app.exec_())
