#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PitLossTableMDI - F1T 進站時間損失表格 MDI 模組
================================================

顯示各賽道在不同條件下的進站時間損失：
- Green Flag: 正常比賽條件
- Safety Car: 安全車期間
- Virtual Safety Car: VSC 期間

資料來源：config/pit_loss_database.json (本地配置文件)

API-ONLY 模式：
- 從本地 JSON 讀取數據 (符合政策允許)
- 不調用 CLI 或外部 API

作者: F1T Team
日期: 2026-01-12
版本: 1.0.0
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QStatusBar, QPushButton, QComboBox
)
from PyQt5.QtGui import QColor, QBrush

from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class PitLossTableMDI(QWidget):
    """
    進站時間損失表格 MDI 模組
    
    顯示各賽道在不同條件下的進站時間損失，
    支援按欄位排序和條件化顏色編碼。
    """
    
    # Signals
    data_loaded = pyqtSignal(object)
    load_error = pyqtSignal(str)
    
    # Workspace 保存/載入所需屬性
    analysis_type = 'pit_loss_table'
    module_name = 'pit_loss_table'
    display_name = 'Pit Loss Database'
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Workspace 兼容屬性
        self.current_year = None
        self.current_race = None
        self.current_session = None
        
        # State
        self._data: Optional[Dict[str, Any]] = None
        self._sort_column = 1  # Default sort by Green Flag
        self._sort_order = Qt.AscendingOrder
        
        # Setup UI
        self._setup_ui()
        
        # Load data immediately (local JSON)
        self._load_data()
    
    def _setup_ui(self):
        """Setup the main UI layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Table
        self._create_table()
        layout.addWidget(self.table)
        
        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)
        
        self._update_status(tr('pit_loss_table.ready', 'Ready'))
    
    def _create_header(self) -> QWidget:
        """Create header widget with title and controls"""
        header = QFrame()
        header.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(8, 4, 8, 4)
        
        # Title
        title = QLabel(tr('pit_loss_table.title', 'Pit Lane Time Loss Database'))
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Sort by dropdown
        layout.addWidget(QLabel(tr('pit_loss_table.sort_by', 'Sort by:')))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            tr('pit_loss_table.col_circuit', 'Circuit'),
            tr('pit_loss_table.col_green_flag', 'Green Flag'),
            tr('pit_loss_table.col_vsc', 'VSC'),
            tr('pit_loss_table.col_sc', 'Safety Car'),
            tr('pit_loss_table.col_samples', 'Samples')
        ])
        self.sort_combo.setCurrentIndex(1)  # Default: Green Flag
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)
        
        # Refresh button
        refresh_btn = QPushButton(tr('common.refresh', 'Refresh'))
        refresh_btn.clicked.connect(self._load_data)
        layout.addWidget(refresh_btn)
        
        return header
    
    def _create_table(self):
        """Create the main data table"""
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            tr('pit_loss_table.col_circuit', 'Circuit'),
            tr('pit_loss_table.col_green_flag', 'Green Flag'),
            tr('pit_loss_table.col_vsc', 'VSC'),
            tr('pit_loss_table.col_sc', 'Safety Car'),
            tr('pit_loss_table.col_samples', 'Samples'),
            tr('pit_loss_table.col_source', 'Source')
        ])
        
        # Table settings
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSortingEnabled(True)
        
        # Column widths
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Circuit - stretch
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        # Connect sort signal
        header.sectionClicked.connect(self._on_header_clicked)
    
    def _load_data(self):
        """Load pit loss data from local JSON file"""
        try:
            # Find config file path
            # 支援 EXE 模式和開發模式
            if getattr(sys, 'frozen', False):
                # EXE mode
                base_path = Path(sys._MEIPASS)
            else:
                # Development mode
                base_path = Path(__file__).resolve().parent.parent.parent.parent.parent
            
            json_path = base_path / 'config' / 'pit_loss_database.json'
            
            if not json_path.exists():
                # Fallback: try relative path
                json_path = Path('config/pit_loss_database.json')
            
            if not json_path.exists():
                raise FileNotFoundError(f"Cannot find pit_loss_database.json at {json_path}")
            
            with open(json_path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
            
            logger.info(f"[PIT_LOSS_TABLE] Loaded data from {json_path}")
            self._populate_table()
            
        except Exception as e:
            logger.error(f"[PIT_LOSS_TABLE] Failed to load data: {e}")
            self._update_status(tr('pit_loss_table.load_error', 'Error loading data'))
            QMessageBox.critical(
                self,
                tr('error', 'Error'),
                tr('pit_loss_table.load_error_msg', 'Failed to load pit loss database: {0}').format(str(e))
            )
    
    def _populate_table(self):
        """Populate table with circuit data"""
        if not self._data or 'circuits' not in self._data:
            return
        
        circuits = self._data['circuits']
        self.table.setRowCount(len(circuits))
        
        # Calculate thresholds for color coding (based on green flag times)
        green_times = [
            c.get('pit_loss_times', {}).get('green_flag', 22.0)
            for c in circuits.values()
        ]
        if green_times:
            avg_time = sum(green_times) / len(green_times)
            low_threshold = avg_time - 2.0  # Green zone (fast pit)
            high_threshold = avg_time + 2.0  # Red zone (slow pit)
        else:
            low_threshold, high_threshold = 20.0, 24.0
        
        for row, (circuit_key, circuit_data) in enumerate(circuits.items()):
            pit_times = circuit_data.get('pit_loss_times', {})
            
            # Column 0: Circuit name
            circuit_item = QTableWidgetItem(circuit_key)
            circuit_item.setData(Qt.UserRole, circuit_key)  # Store key for sorting
            self.table.setItem(row, 0, circuit_item)
            
            # Column 1: Green Flag
            green_flag = pit_times.get('green_flag', 0)
            green_item = self._create_time_item(green_flag, low_threshold, high_threshold)
            self.table.setItem(row, 1, green_item)
            
            # Column 2: VSC
            vsc = pit_times.get('virtual_safety_car', 0)
            vsc_item = self._create_time_item(vsc, low_threshold * 0.38, high_threshold * 0.38)
            self.table.setItem(row, 2, vsc_item)
            
            # Column 3: Safety Car
            sc = pit_times.get('safety_car', 0)
            sc_item = self._create_time_item(sc, low_threshold * 0.52, high_threshold * 0.52)
            self.table.setItem(row, 3, sc_item)
            
            # Column 4: Samples
            samples = circuit_data.get('training_samples', 0)
            samples_item = QTableWidgetItem()
            samples_item.setData(Qt.DisplayRole, samples if samples else '--')
            samples_item.setData(Qt.UserRole, samples if samples else 0)
            samples_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 4, samples_item)
            
            # Column 5: Source
            trained = circuit_data.get('trained_from_data', False)
            source_text = tr('pit_loss_table.trained', 'Trained') if trained else tr('pit_loss_table.estimated', 'Estimated')
            source_item = QTableWidgetItem(source_text)
            source_item.setTextAlignment(Qt.AlignCenter)
            if not trained:
                source_item.setForeground(QBrush(QColor('#FFA500')))  # Orange for estimated
            self.table.setItem(row, 5, source_item)
        
        # Apply default sort
        self.table.sortItems(self._sort_column, self._sort_order)
        
        # Update status
        total_circuits = len(circuits)
        trained_count = sum(1 for c in circuits.values() if c.get('trained_from_data', False))
        total_samples = sum(c.get('training_samples', 0) for c in circuits.values())
        
        status = tr(
            'pit_loss_table.status',
            '{0} circuits | {1} trained | {2} total samples'
        ).format(total_circuits, trained_count, total_samples)
        self._update_status(status)
    
    def _create_time_item(self, time_value: float, low_threshold: float, high_threshold: float) -> QTableWidgetItem:
        """Create a table item with conditional color coding"""
        item = QTableWidgetItem()
        item.setData(Qt.DisplayRole, f"{time_value:.1f}s")
        item.setData(Qt.UserRole, time_value)  # Store numeric value for sorting
        item.setTextAlignment(Qt.AlignCenter)
        
        # Color coding
        if time_value <= low_threshold:
            # Green - fast pit lane
            item.setForeground(QBrush(QColor('#22C55E')))
        elif time_value >= high_threshold:
            # Red - slow pit lane
            item.setForeground(QBrush(QColor('#EF4444')))
        else:
            # Yellow - medium
            item.setForeground(QBrush(QColor('#EAB308')))
        
        return item
    
    def _on_sort_changed(self, index: int):
        """Handle sort dropdown change"""
        self._sort_column = index
        self.table.sortItems(index, self._sort_order)
    
    def _on_header_clicked(self, column: int):
        """Handle header click for sorting"""
        if column == self._sort_column:
            # Toggle sort order
            self._sort_order = Qt.DescendingOrder if self._sort_order == Qt.AscendingOrder else Qt.AscendingOrder
        else:
            self._sort_column = column
            self._sort_order = Qt.AscendingOrder
        
        self.sort_combo.setCurrentIndex(column)
    
    def _update_status(self, message: str):
        """Update status bar message"""
        self.status_bar.showMessage(message)
    
    # =====================================================
    # Public API for MDI Integration
    # =====================================================
    
    def get_widget(self) -> QWidget:
        """Return module's main widget for MDI embedding"""
        return self
    
    def get_title(self) -> str:
        """Get window title for MDI"""
        return tr('pit_loss_table.window_title', 'Pit Loss Database')
    
    def get_window_title(self, year: int = None, race: str = None, session: str = None) -> str:
        """Generate window title with parameters"""
        return tr('pit_loss_table.window_title', 'Pit Loss Database')
    
    def get_default_size(self) -> tuple:
        """Get default window size"""
        return (800, 600)
    
    def set_parent_window(self, parent_window):
        """Set parent window reference for popout integration"""
        self._parent_window = parent_window
    
    def refresh_data(self):
        """Refresh data from JSON file"""
        self._load_data()
