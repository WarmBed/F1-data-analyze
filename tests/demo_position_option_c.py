#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Option C - Table First with Popup Chart
方案 C：表格優先 + 彈出式圖表對話框
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QPushButton, QDialog,
                             QLabel, QHeaderView, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.gui.themes.color_palette_provider import color_palette_provider


class ChartDialog(QDialog):
    """圖表對話框"""
    
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.setWindowTitle("名次視覺化圖表")
        self.resize(900, 600)
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 圖表模式選擇
        control_panel = QGroupBox("圖表選項")
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("圖表類型:"))
        
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["最終名次", "名次變化", "起始 vs 最終"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        control_layout.addWidget(self.chart_type_combo)
        control_layout.addStretch()
        
        control_panel.setLayout(control_layout)
        layout.addWidget(control_panel)
        
        # 圖表
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 關閉按鈕
        close_btn = QPushButton("關閉")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        # 初始繪製
        self.update_chart()
        
    def update_chart(self):
        """更新圖表"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "最終名次":
            self._draw_final_position(ax)
        elif chart_type == "名次變化":
            self._draw_position_change(ax)
        else:
            self._draw_start_vs_final(ax)
            
        self.canvas.draw()
        
    def _draw_final_position(self, ax):
        """繪製最終名次"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        drivers = []
        positions = []
        colors = []
        
        for driver, info in sorted(self.data.items(), 
                                   key=lambda x: x[1].get("finishing_position") or 99):
            fp = info.get("finishing_position")
            if fp is None:
                fp = 99
            
            drivers.append(driver)
            positions.append(fp)
            color = color_palette_provider.get_driver_color(driver, format="hex") or "#808080"
            colors.append(color)
        
        y_pos = range(len(drivers))
        ax.barh(y_pos, positions, color=colors, edgecolor="black", linewidth=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("最終名次")
        ax.set_title("車手最終名次分佈")
        ax.invert_xaxis()
        ax.grid(axis="x", alpha=0.3)
        
    def _draw_position_change(self, ax):
        """繪製名次變化"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        drivers = []
        changes = []
        colors_list = []
        
        for driver, info in sorted(self.data.items(), 
                                   key=lambda x: x[1].get("position_change") or 0,
                                   reverse=True):
            pc = info.get("position_change")
            if pc is None:
                pc = 0
            
            drivers.append(driver)
            changes.append(pc)
            colors_list.append("#2ecc71" if pc > 0 else "#e74c3c" if pc < 0 else "#95a5a6")
        
        y_pos = range(len(drivers))
        ax.barh(y_pos, changes, color=colors_list, edgecolor="black", linewidth=0.5)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("名次變化")
        ax.set_title("車手名次變化")
        ax.axvline(x=0, color="black", linestyle="--")
        ax.grid(axis="x", alpha=0.3)
        
    def _draw_start_vs_final(self, ax):
        """繪製起始 vs 最終"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        drivers = []
        start_pos = []
        final_pos = []
        
        for driver, info in sorted(self.data.items(), 
                                   key=lambda x: x[1].get("starting_position") or 99):
            sp = info.get("starting_position")
            fp = info.get("finishing_position")
            if sp is None:
                sp = 99
            if fp is None:
                fp = 99
            
            drivers.append(driver)
            start_pos.append(sp)
            final_pos.append(fp)
        
        y_pos = range(len(drivers))
        bar_height = 0.35
        
        ax.barh([y - bar_height/2 for y in y_pos], start_pos, bar_height, 
               label="起始", color="#3498db", alpha=0.7)
        ax.barh([y + bar_height/2 for y in y_pos], final_pos, bar_height, 
               label="最終", color="#e74c3c", alpha=0.7)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("名次")
        ax.set_title("起始 vs 最終名次")
        ax.invert_xaxis()
        ax.legend()
        ax.grid(axis="x", alpha=0.3)


class TableFirstWidget(QWidget):
    """表格優先視圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "車手代碼", "起始名次", "最終名次", "名次變化", "狀態"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
        
        # 按鈕區
        btn_layout = QHBoxLayout()
        
        self.show_chart_btn = QPushButton("顯示圖表視覺化")
        self.show_chart_btn.clicked.connect(self.show_chart_dialog)
        self.show_chart_btn.setEnabled(False)
        btn_layout.addWidget(self.show_chart_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
    def load_data(self, data):
        """載入數據"""
        self.data = data
        self.populate_table()
        self.show_chart_btn.setEnabled(True)
        
    def populate_table(self):
        """填充表格"""
        self.table.setRowCount(0)
        
        for driver, info in sorted(self.data.items()):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 車手代碼
            self.table.setItem(row, 0, QTableWidgetItem(driver))
            
            # 起始名次
            sp = info.get("starting_position")
            sp_text = f"P{sp}" if sp is not None else "N/A"
            self.table.setItem(row, 1, QTableWidgetItem(sp_text))
            
            # 最終名次
            fp = info.get("finishing_position")
            fp_text = f"P{fp}" if fp is not None else "DNF"
            self.table.setItem(row, 2, QTableWidgetItem(fp_text))
            
            # 名次變化
            pc = info.get("position_change")
            if pc is not None:
                pc_text = f"{pc:+d}" if pc != 0 else "0"
            else:
                pc_text = "N/A"
            self.table.setItem(row, 3, QTableWidgetItem(pc_text))
            
            # 狀態
            status = "完賽" if fp is not None else "未完賽"
            self.table.setItem(row, 4, QTableWidgetItem(status))
            
    def show_chart_dialog(self):
        """顯示圖表對話框"""
        if self.data:
            dialog = ChartDialog(self.data, self)
            dialog.exec_()


class OptionCDemo(QWidget):
    """方案 C Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo C: 表格優先 + 彈出式圖表")
        self.resize(900, 600)
        self.init_ui()
        self.load_test_data()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("方案 C：表格優先視圖 + 按需彈出圖表")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 表格視圖
        self.table_widget = TableFirstWidget()
        layout.addWidget(self.table_widget)
        
    def load_test_data(self):
        """載入測試數據"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "all_drivers_position_analysis" in data:
                    self.table_widget.load_data(data["all_drivers_position_analysis"])
                    print("✅ 數據載入成功")
                else:
                    print("❌ 數據格式錯誤")
        else:
            print(f"❌ 找不到測試數據: {json_path}")


if __name__ == "__main__":
    color_palette_provider.ensure_loaded(year=2024)
    
    app = QApplication(sys.argv)
    demo = OptionCDemo()
    demo.show()
    sys.exit(app.exec_())
