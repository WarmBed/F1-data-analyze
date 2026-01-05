#!/usr/bin/env python3
"""
Detailed Data Tab

Lap-by-lap simulation data with export capability.

Author: F1T Team
Date: 2025-12-30
"""

from typing import List, Optional
from pathlib import Path
import json
import csv
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QPushButton, QFileDialog,
    QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class DetailedDataTab(QWidget):
    """
    Detailed data tab showing lap-by-lap simulation data.
    
    Features:
    - Complete lap-by-lap breakdown
    - All time components visible
    - Export to CSV/JSON
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: List = []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        # Strategy selector
        controls_layout.addWidget(QLabel("策略:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_changed)
        controls_layout.addWidget(self.strategy_combo)
        
        controls_layout.addStretch()
        
        # Export buttons
        export_csv_btn = QPushButton("匯出 CSV")
        export_csv_btn.clicked.connect(self._export_csv)
        controls_layout.addWidget(export_csv_btn)
        
        export_json_btn = QPushButton("匯出 JSON")
        export_json_btn.clicked.connect(self._export_json)
        controls_layout.addWidget(export_json_btn)
        
        export_all_btn = QPushButton("匯出所有策略")
        export_all_btn.clicked.connect(self._export_all)
        controls_layout.addWidget(export_all_btn)
        
        layout.addLayout(controls_layout)
        
        # Summary panel
        self.summary_group = QGroupBox("策略摘要")
        summary_layout = QHBoxLayout(self.summary_group)
        
        self.summary_labels = {}
        for key in ['notation', 'stops', 'total_time', 'pit_loss', 'pit_laps']:
            label = QLabel("-")
            self.summary_labels[key] = label
            summary_layout.addWidget(label)
        
        layout.addWidget(self.summary_group)
        
        # Data table
        table_group = QGroupBox("逐圈數據")
        table_layout = QVBoxLayout(table_group)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(9)
        self.data_table.setHorizontalHeaderLabels([
            "圈數", "複合物", "輪胎壽命", "燃油(kg)",
            "基準時間", "複合物Δ", "燃油調整", "衰退", "淨時間"
        ])
        
        # Configure columns
        header = self.data_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)  # Lap
        header.setSectionResizeMode(1, QHeaderView.Fixed)  # Compound
        header.setSectionResizeMode(2, QHeaderView.Fixed)  # Tyre Age
        for i in range(3, 9):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        self.data_table.setColumnWidth(0, 50)
        self.data_table.setColumnWidth(1, 80)
        self.data_table.setColumnWidth(2, 70)
        
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        table_layout.addWidget(self.data_table)
        layout.addWidget(table_group)
    
    def update_results(self, results: List):
        """Update with simulation results."""
        self._results = results
        
        # Populate combo
        self.strategy_combo.clear()
        for result in results:
            notation = result.get_stint_notation()
            self.strategy_combo.addItem(f"{result.strategy_name}: {notation}")
        
        # Show first strategy
        if results:
            self._update_table(0)
    
    def _on_strategy_changed(self, index: int):
        """Handle strategy selection change."""
        if 0 <= index < len(self._results):
            self._update_table(index)
    
    def _update_table(self, strategy_idx: int):
        """Update table with strategy data."""
        if strategy_idx >= len(self._results):
            return
        
        result = self._results[strategy_idx]
        
        # Update summary
        self.summary_labels['notation'].setText(
            f"<b>策略:</b> {result.get_stint_notation()}"
        )
        self.summary_labels['stops'].setText(
            f"<b>停站:</b> {result.num_stops}"
        )
        self.summary_labels['total_time'].setText(
            f"<b>總時間:</b> {result.total_time_formatted}"
        )
        self.summary_labels['pit_loss'].setText(
            f"<b>進站損失:</b> {result.total_pit_loss:.1f}s"
        )
        self.summary_labels['pit_laps'].setText(
            f"<b>進站圈:</b> {', '.join(f'L{p}' for p in result.pit_laps)}"
        )
        
        # Update table
        lap_results = result.lap_results
        self.data_table.setRowCount(len(lap_results))
        
        for row, lap in enumerate(lap_results):
            # Lap number
            lap_item = QTableWidgetItem(str(lap.lap_number))
            lap_item.setTextAlignment(Qt.AlignCenter)
            
            # Highlight pit laps
            if lap.lap_number in result.pit_laps:
                lap_item.setBackground(QColor(255, 200, 200))
            
            self.data_table.setItem(row, 0, lap_item)
            
            # Compound
            compound_item = QTableWidgetItem(lap.compound.value)
            compound_item.setTextAlignment(Qt.AlignCenter)
            compound_item.setFont(QFont("Consolas", 9, QFont.Bold))
            compound_item.setBackground(self._get_compound_color(lap.compound.value))
            self.data_table.setItem(row, 1, compound_item)
            
            # Tyre age
            age_item = QTableWidgetItem(str(lap.tyre_age))
            age_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row, 2, age_item)
            
            # Fuel
            fuel_item = QTableWidgetItem(f"{lap.fuel_remaining:.1f}")
            fuel_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row, 3, fuel_item)
            
            # Base time
            base_item = QTableWidgetItem(f"{lap.base_time:.3f}")
            base_item.setTextAlignment(Qt.AlignCenter)
            self.data_table.setItem(row, 4, base_item)
            
            # Compound delta
            delta_item = QTableWidgetItem(f"{lap.compound_delta:+.3f}")
            delta_item.setTextAlignment(Qt.AlignCenter)
            delta_item.setForeground(
                QColor(0, 150, 0) if lap.compound_delta < 0 else QColor(150, 0, 0)
            )
            self.data_table.setItem(row, 5, delta_item)
            
            # Fuel adjustment
            fuel_adj_item = QTableWidgetItem(f"{lap.fuel_adjustment:+.3f}")
            fuel_adj_item.setTextAlignment(Qt.AlignCenter)
            fuel_adj_item.setForeground(QColor(0, 150, 0))  # Always beneficial
            self.data_table.setItem(row, 6, fuel_adj_item)
            
            # Degradation
            deg_item = QTableWidgetItem(f"+{lap.degradation:.3f}")
            deg_item.setTextAlignment(Qt.AlignCenter)
            deg_item.setForeground(QColor(150, 0, 0))  # Always a penalty
            self.data_table.setItem(row, 7, deg_item)
            
            # Net time
            net_item = QTableWidgetItem(f"{lap.net_time:.3f}")
            net_item.setTextAlignment(Qt.AlignCenter)
            net_item.setFont(QFont("Consolas", 9, QFont.Bold))
            self.data_table.setItem(row, 8, net_item)
    
    def _get_compound_color(self, compound: str) -> QColor:
        """Get background color for compound."""
        colors = {
            'SOFT': QColor(255, 220, 220),
            'MEDIUM': QColor(255, 255, 200),
            'HARD': QColor(220, 220, 220),
        }
        return colors.get(compound.upper(), QColor(240, 240, 240))
    
    def _export_csv(self):
        """Export current strategy to CSV."""
        if not self._results:
            QMessageBox.warning(self, "匯出", "無數據可匯出。")
            return
        
        idx = self.strategy_combo.currentIndex()
        if idx < 0 or idx >= len(self._results):
            return
        
        result = self._results[idx]
        
        # Get save path
        default_name = f"strategy_{result.strategy_name}_{datetime.now():%Y%m%d_%H%M%S}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "匯出 CSV", default_name, "CSV 檔案 (*.csv)"
        )
        
        if not path:
            return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Header
                writer.writerow([
                    'Lap', 'Compound', 'Tyre Age', 'Fuel (kg)',
                    'Base Time', 'Compound Delta', 'Fuel Adjustment',
                    'Degradation', 'Net Time'
                ])
                
                # Data
                for lap in result.lap_results:
                    writer.writerow([
                        lap.lap_number,
                        lap.compound.value,
                        lap.tyre_age,
                        f"{lap.fuel_remaining:.1f}",
                        f"{lap.base_time:.3f}",
                        f"{lap.compound_delta:.3f}",
                        f"{lap.fuel_adjustment:.3f}",
                        f"{lap.degradation:.3f}",
                        f"{lap.net_time:.3f}",
                    ])
            
            QMessageBox.information(
                self, "匯出", f"已成功匯出至:\n{path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "匯出錯誤", f"匯出失敗:\n{e}")
    
    def _export_json(self):
        """Export current strategy to JSON."""
        if not self._results:
            QMessageBox.warning(self, "匯出", "無數據可匯出。")
            return
        
        idx = self.strategy_combo.currentIndex()
        if idx < 0 or idx >= len(self._results):
            return
        
        result = self._results[idx]
        
        # Get save path
        default_name = f"strategy_{result.strategy_name}_{datetime.now():%Y%m%d_%H%M%S}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "匯出 JSON", default_name, "JSON 檔案 (*.json)"
        )
        
        if not path:
            return
        
        try:
            data = result.to_dict()
            data['lap_details'] = [lap.to_dict() for lap in result.lap_results]
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, "匯出", f"已成功匯出至:\n{path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "匯出錯誤", f"匯出失敗:\n{e}")
    
    def _export_all(self):
        """Export all strategies to JSON."""
        if not self._results:
            QMessageBox.warning(self, "匯出", "無數據可匯出。")
            return
        
        # Get save path
        default_name = f"all_strategies_{datetime.now():%Y%m%d_%H%M%S}.json"
        path, _ = QFileDialog.getSaveFileName(
            self, "匯出所有策略", default_name, "JSON 檔案 (*.json)"
        )
        
        if not path:
            return
        
        try:
            data = {
                'export_time': datetime.now().isoformat(),
                'strategies': []
            }
            
            for result in self._results:
                strategy_data = result.to_dict()
                strategy_data['lap_details'] = [lap.to_dict() for lap in result.lap_results]
                data['strategies'].append(strategy_data)
            
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            QMessageBox.information(
                self, "匯出", 
                f"已成功匯出 {len(self._results)} 個策略至:\n{path}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "匯出錯誤", f"匯出失敗:\n{e}")
