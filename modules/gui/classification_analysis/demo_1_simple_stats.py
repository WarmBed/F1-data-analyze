#!/usr/bin/env python3
"""
Demo 1: FIA Parts Changes Classification - Simple Statistics
==============================================================

極簡統計版本 - 只顯示核心數據排行

功能特點：
- 賽事分析 Top 10
- 車隊排行 Top 10
- 車手排行 Top 10
- 頂部過濾工具列

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
    QPushButton, QHeaderView, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QColor
import requests
import time

from core.gui_i18n import tr
from core.api_base_url import resolve_api_base_url


class SimpleStatsApiWorker(QThread):
    """API 數據獲取背景執行緒"""
    
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, base_url: str, year: int, parent=None):
        super().__init__(parent)
        self.base_url = base_url.rstrip('/')
        self.year = year
        
    def run(self):
        try:
            endpoint = f"{self.base_url}/api/v2/analysis/execute"
            response = requests.post(
                endpoint,
                params={"function_id": "29", "year": self.year},
                timeout=30.0
            )
            response.raise_for_status()
            payload = response.json()
            
            if payload.get("success"):
                self.success.emit(payload.get("data", {}))
            else:
                self.failure.emit(payload.get("message", "API failed"))
        except Exception as e:
            self.failure.emit(str(e))


class SimpleStatsWidget(QWidget):
    """極簡統計 Widget"""
    
    def __init__(self, year: int = 2025, parent=None):
        super().__init__(parent)
        self.year = year
        self._api_base_url = resolve_api_base_url()
        self._api_worker = None
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        """設置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 標題
        title = QLabel(tr('simple_stats_title', 'FIA Parts Classification - Simple Statistics'))
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        
        # 過濾工具列
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel(tr('filter', 'Filter') + ":"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem(tr('all', 'All'), "")
        filter_layout.addWidget(self.filter_combo)
        
        self.refresh_btn = QPushButton(tr('refresh', 'Refresh'))
        self.refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(self.refresh_btn)
        filter_layout.addStretch()
        
        layout.addLayout(filter_layout)
        
        # 三個排行表格
        tables_layout = QHBoxLayout()
        
        # 賽事排行
        self.race_table = self.create_ranking_table(tr('race_ranking', 'Race Ranking'))
        tables_layout.addWidget(self.race_table)
        
        # 車隊排行
        self.team_table = self.create_ranking_table(tr('team_ranking', 'Team Ranking'))
        tables_layout.addWidget(self.team_table)
        
        # 車手排行
        self.driver_table = self.create_ranking_table(tr('driver_ranking', 'Driver Ranking'))
        tables_layout.addWidget(self.driver_table)
        
        layout.addLayout(tables_layout)
        
        # 狀態標籤
        self.status_label = QLabel(tr('ready', 'Ready'))
        self.status_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(self.status_label)
    
    def create_ranking_table(self, title: str) -> QTableWidget:
        """創建排行表格"""
        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels([title, tr('count', 'Count')])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setColumnWidth(1, 60)
        table.setAlternatingRowColors(True)
        return table
    
    def load_data(self):
        """載入數據"""
        self.status_label.setText(tr('loading', '載入中...'))
        self.status_label.setStyleSheet("color: #f39c12;")
        
        if self._api_worker and self._api_worker.isRunning():
            return
        
        self._api_worker = SimpleStatsApiWorker(self._api_base_url, self.year, self)
        self._api_worker.success.connect(self.on_data_loaded)
        self._api_worker.failure.connect(self.on_load_error)
        self._api_worker.start()
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """數據載入成功"""
        try:
            # 提取排行數據
            race_stats = self.extract_race_stats(data)
            team_stats = self.extract_team_stats(data)
            driver_stats = self.extract_driver_stats(data)
            
            # 填充表格
            self.populate_table(self.race_table, race_stats[:10])
            self.populate_table(self.team_table, team_stats[:10])
            self.populate_table(self.driver_table, driver_stats[:10])
            
            self.status_label.setText(tr('loaded_successfully', '✅ 載入成功'))
            self.status_label.setStyleSheet("color: #27ae60;")
            
        except Exception as e:
            self.on_load_error(str(e))
    
    def on_load_error(self, error: str):
        """載入失敗"""
        self.status_label.setText(f"❌ {tr('load_failed', 'Load failed')}: {error}")
        self.status_label.setStyleSheet("color: #e74c3c;")
    
    def extract_race_stats(self, data: Dict) -> List[tuple]:
        """提取賽事統計（使用中文欄位）"""
        stats = {}
        records = self._get_records(data)
        
        for record in records:
            race = record.get("比賽", record.get("race", record.get("event", "Unknown")))
            stats[race] = stats.get(race, 0) + 1
        
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    def extract_team_stats(self, data: Dict) -> List[tuple]:
        """提取車隊統計（使用中文欄位）"""
        stats = {}
        records = self._get_records(data)
        
        for record in records:
            team = record.get("車隊", record.get("team", "Unknown"))
            if team:
                stats[team] = stats.get(team, 0) + 1
        
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    def extract_driver_stats(self, data: Dict) -> List[tuple]:
        """提取車手統計（使用中文欄位）"""
        stats = {}
        records = self._get_records(data)
        
        for record in records:
            driver = record.get("車手", record.get("driver", "Unknown"))
            if driver:
                stats[driver] = stats.get(driver, 0) + 1
        
        return sorted(stats.items(), key=lambda x: x[1], reverse=True)
    
    def _get_records(self, data: Dict) -> List[Dict]:
        """提取記錄列表"""
        for key in ["records", "changes", "parts_changes", "classified_changes"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        if isinstance(data, list):
            return data
        
        return []
    
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
    window = SimpleStatsWidget(2025)
    window.setWindowTitle("Demo 1: Simple Statistics")
    window.resize(900, 600)
    window.show()
    sys.exit(app.exec_())
