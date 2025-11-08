#!/usr/bin/env python3
"""
Demo 3: FIA Parts Changes Classification - Interactive Filter
==============================================================

互動過濾版本 - 完整過濾控制

功能特點：
- 完整過濾工具列（賽事/車隊/車手/類型/信心度）
- 即時過濾更新
- 3 個排行表格

Author: F1T Team
Date: 2025-11-07
"""

import sys
import os

# 添加專案根目錄到 Python 路徑（用於獨立執行）
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from typing import Dict, List, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QComboBox,
    QPushButton, QDoubleSpinBox, QCheckBox,
    QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests

from core.gui_i18n import tr
from core.api_base_url import resolve_api_base_url


class InteractiveFilterApiWorker(QThread):
    """API Worker"""
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, year: int, params: Dict = None, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.year = year
        self.params = params or {}
    
    def run(self):
        try:
            query = {"function_id": "29", "year": self.year}
            
            if self.params.get("team"):
                query["team"] = self.params["team"]
            if self.params.get("driver"):
                query["driver"] = self.params["driver"]
            if self.params.get("race"):
                query["race"] = self.params["race"]
            if self.params.get("change_type"):
                query["change_type"] = self.params["change_type"]
            if self.params.get("min_confidence"):
                query["min_confidence"] = self.params["min_confidence"]
            
            response = requests.post(
                f"{self.base_url}/api/v2/analysis/execute",
                params=query,
                timeout=30.0
            )
            response.raise_for_status()
            payload = response.json()
            
            if payload.get("success"):
                self.success.emit(payload.get("data", {}))
            else:
                self.failure.emit(payload.get("message", "Failed"))
        except Exception as e:
            self.failure.emit(str(e))


class InteractiveFilterWidget(QWidget):
    """互動過濾 Widget"""
    
    def __init__(self, year: int = 2025, parent=None):
        super().__init__(parent)
        self.year = year
        self._api_base_url = resolve_api_base_url()
        self._api_worker = None
        self.all_records = []
        self.filtered_records = []
        
        self.setup_ui()
        self.load_all_data()
    
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel(tr('interactive_filter_title', 'FIA Parts Classification - Interactive Filter'))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 過濾控制列
        self.setup_filter_controls(layout)
        
        # 表格區域
        tables_layout = QHBoxLayout()
        
        self.race_table = self.create_table(tr('race_ranking', 'Race Ranking'))
        tables_layout.addWidget(self.race_table)
        
        self.team_table = self.create_table(tr('team_ranking', 'Team Ranking'))
        tables_layout.addWidget(self.team_table)
        
        self.driver_table = self.create_table(tr('driver_ranking', 'Driver Ranking'))
        tables_layout.addWidget(self.driver_table)
        
        layout.addLayout(tables_layout)
        
        # 狀態
        self.status_label = QLabel(tr('ready', 'Ready'))
        layout.addWidget(self.status_label)
    
    def setup_filter_controls(self, layout):
        """設置過濾控制"""
        filter_layout = QVBoxLayout()
        
        # 第一行：賽事/車隊/車手
        row1 = QHBoxLayout()
        
        row1.addWidget(QLabel(tr('race', 'Race') + ":"))
        self.race_combo = QComboBox()
        self.race_combo.addItem(tr('all', 'All'), "")
        row1.addWidget(self.race_combo)
        
        row1.addWidget(QLabel(tr('team', 'Team') + ":"))
        self.team_combo = QComboBox()
        self.team_combo.addItem(tr('all', 'All'), "")
        row1.addWidget(self.team_combo)
        
        row1.addWidget(QLabel(tr('driver', 'Driver') + ":"))
        self.driver_combo = QComboBox()
        self.driver_combo.addItem(tr('all', 'All'), "")
        row1.addWidget(self.driver_combo)
        
        filter_layout.addLayout(row1)
        
        # 第二行：變更類型/信心度/刷新
        row2 = QHBoxLayout()
        
        row2.addWidget(QLabel(tr('change_type', 'Type') + ":"))
        self.type_combo = QComboBox()
        self.type_combo.addItem(tr('all', 'All'), "")
        row2.addWidget(self.type_combo)
        
        row2.addWidget(QLabel(tr('min_confidence', 'Min Conf') + ":"))
        self.conf_spin = QDoubleSpinBox()
        self.conf_spin.setRange(0.0, 1.0)
        self.conf_spin.setSingleStep(0.1)
        self.conf_spin.setValue(0.0)
        row2.addWidget(self.conf_spin)
        
        self.apply_btn = QPushButton(tr('apply_filter', 'Apply Filter'))
        self.apply_btn.clicked.connect(self.apply_filters)
        row2.addWidget(self.apply_btn)
        
        self.refresh_btn = QPushButton(tr('refresh', 'Refresh'))
        self.refresh_btn.clicked.connect(self.load_all_data)
        row2.addWidget(self.refresh_btn)
        
        row2.addStretch()
        filter_layout.addLayout(row2)
        
        layout.addLayout(filter_layout)
    
    def create_table(self, title: str) -> QTableWidget:
        """創建表格"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([title, tr('count', 'Count')])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 60)
        table.setAlternatingRowColors(True)
        return table
    
    def load_all_data(self):
        """載入所有數據"""
        self.status_label.setText(tr('loading', '載入中...'))
        
        if self._api_worker and self._api_worker.isRunning():
            return
        
        self._api_worker = InteractiveFilterApiWorker(self._api_base_url, self.year, parent=self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_load_error)
        self._api_worker.start()
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功"""
        try:
            self.all_records = self._get_records(data)
            self.filtered_records = self.all_records.copy()
            
            # 更新過濾選項
            self.update_filter_options()
            
            # 更新表格
            self.update_tables()
            
            self.status_label.setText(f"✅ {len(self.all_records)} {tr('records_loaded', 'records loaded')}")
            
        except Exception as e:
            self.on_load_error(str(e))
    
    def on_load_error(self, error: str):
        """載入失敗"""
        self.status_label.setText(f"❌ {error}")
    
    def _get_records(self, data: Dict) -> List[Dict]:
        """提取記錄"""
        for key in ["records", "changes", "parts_changes"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        return data if isinstance(data, list) else []
    
    def update_filter_options(self):
        """更新過濾選項（使用中文欄位）"""
        races = set()
        teams = set()
        drivers = set()
        types = set()
        
        for record in self.all_records:
            # 使用中文 API 欄位
            races.add(record.get("比賽", record.get("race", record.get("event", ""))))
            teams.add(record.get("車隊", record.get("team", "")))
            drivers.add(record.get("車手", record.get("driver", "")))
            types.add(record.get("變更類型", record.get("change_type", record.get("type", ""))))
        
        self._update_combo(self.race_combo, sorted(races))
        self._update_combo(self.team_combo, sorted(teams))
        self._update_combo(self.driver_combo, sorted(drivers))
        self._update_combo(self.type_combo, sorted(types))
    
    def _update_combo(self, combo: QComboBox, options: List[str]):
        """更新下拉選單"""
        current = combo.currentText()
        default = combo.itemText(0)
        
        combo.clear()
        combo.addItem(default, "")
        
        for opt in options:
            if opt:
                combo.addItem(opt, opt)
        
        idx = combo.findText(current)
        if idx >= 0:
            combo.setCurrentIndex(idx)
    
    def apply_filters(self):
        """應用過濾（使用中文欄位）"""
        self.filtered_records = []
        
        race_filter = self.race_combo.currentData()
        team_filter = self.team_combo.currentData()
        driver_filter = self.driver_combo.currentData()
        type_filter = self.type_combo.currentData()
        conf_filter = self.conf_spin.value()
        
        for record in self.all_records:
            # 使用中文 API 欄位
            if race_filter and record.get("比賽", record.get("race", record.get("event", ""))) != race_filter:
                continue
            if team_filter and record.get("車隊", record.get("team", "")) != team_filter:
                continue
            if driver_filter and record.get("車手", record.get("driver", "")) != driver_filter:
                continue
            if type_filter and record.get("變更類型", record.get("change_type", record.get("type", ""))) != type_filter:
                continue
            
            conf = record.get("分類信心度", record.get("confidence", record.get("confidence_score", 0)))
            try:
                if float(conf) < conf_filter:
                    continue
            except:
                pass
            
            self.filtered_records.append(record)
        
        self.update_tables()
        self.status_label.setText(f"🔍 {len(self.filtered_records)}/{len(self.all_records)} {tr('records_filtered', 'records')}")
    
    def update_tables(self):
        """更新表格（使用中文欄位）"""
        race_stats = {}
        team_stats = {}
        driver_stats = {}
        
        for record in self.filtered_records:
            # 使用中文 API 欄位
            race = record.get("比賽", record.get("race", record.get("event", "Unknown")))
            team = record.get("車隊", record.get("team", "Unknown"))
            driver = record.get("車手", record.get("driver", "Unknown"))
            
            race_stats[race] = race_stats.get(race, 0) + 1
            team_stats[team] = team_stats.get(team, 0) + 1
            driver_stats[driver] = driver_stats.get(driver, 0) + 1
        
        self.populate_table(self.race_table, sorted(race_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        self.populate_table(self.team_table, sorted(team_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        self.populate_table(self.driver_table, sorted(driver_stats.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def populate_table(self, table: QTableWidget, data: List[tuple]):
        """填充表格"""
        table.setRowCount(len(data))
        
        for row, (name, count) in enumerate(data):
            name_item = QTableWidgetItem(str(name))
            count_item = QTableWidgetItem(str(count))
            count_item.setTextAlignment(Qt.AlignCenter)
            
            table.setItem(row, 0, name_item)
            table.setItem(row, 1, count_item)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = InteractiveFilterWidget(2025)
    window.setWindowTitle("Demo 3: Interactive Filter")
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec_())
