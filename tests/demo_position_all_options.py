#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
車手名次分析 GUI - 統一 Demo（包含 A-E 五個方案）
使用命令列參數選擇方案：python demo_position_all_options.py [A|B|C|D|E]
"""

import sys
import json
from pathlib import Path

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from modules.gui.themes.color_palette_provider import color_palette_provider


# ==================== 方案 A：雙 Tab 視圖 ====================
class OptionATableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        layout = QVBoxLayout(self)
        
        title = QLabel("車手名次詳細數據表")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "車手", "起始名次", "最終名次", "名次變化", "最佳名次", "最差名次", "完賽狀態"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
    
    def update_data(self, data: dict):
        self.current_data = data
        driver_positions = data.get("all_drivers_position_analysis", {})
        
        self.table.setRowCount(len(driver_positions))
        
        for row, (driver, pos_data) in enumerate(sorted(
            driver_positions.items(),
            key=lambda x: (x[1].get("finishing_position") or 99)
        )):
            driver_item = QTableWidgetItem(driver)
            color = color_palette_provider.get_driver_color(driver)
            if color:
                driver_item.setBackground(color)
                driver_item.setForeground(QColor("white"))
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, driver_item)
            
            start_pos = pos_data.get("starting_position", "-")
            final_pos = pos_data.get("finishing_position", "-")
            change = pos_data.get("position_change", 0) or 0
            best_pos = pos_data.get("best_position", "-")
            worst_pos = pos_data.get("worst_position", "-")
            status = pos_data.get("status", "Unknown")
            
            items_data = [
                f"P{start_pos}" if start_pos != "-" else "-",
                f"P{final_pos}" if final_pos != "-" else "-",
                f"{'↑' if change > 0 else '↓' if change < 0 else '→'} {abs(change)}",
                f"P{best_pos}" if best_pos != "-" else "-",
                f"P{worst_pos}" if worst_pos != "-" else "-",
                status
            ]
            
            for col, text in enumerate(items_data, start=1):
                item = QTableWidgetItem(str(text))
                item.setTextAlignment(Qt.AlignCenter)
                if col == 3:  # 名次變化
                    if change > 0:
                        item.setForeground(QColor("green"))
                    elif change < 0:
                        item.setForeground(QColor("red"))
                self.table.setItem(row, col, item)


class OptionAChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.chart_type = "final_position"
        
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItem("最終名次圖表", "final_position")
        self.chart_combo.addItem("名次變化圖表", "position_change")
        self.chart_combo.currentIndexChanged.connect(self._on_chart_switch)
        
        control_layout.addWidget(QLabel("圖表類型："))
        control_layout.addWidget(self.chart_combo)
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: dict):
        self.current_data = data
        self.draw_chart()
    
    def draw_chart(self):
        if not self.current_data:
            return
        
        driver_positions = self.current_data.get("all_drivers_position_analysis", {})
        
        drivers = []
        values = []
        colors = []
        
        for driver, pos_data in driver_positions.items():
            drivers.append(driver)
            
            if self.chart_type == "final_position":
                fp = pos_data.get("finishing_position")
                values.append(99 if fp is None else fp)
            else:
                pc = pos_data.get("position_change")
                values.append(0 if pc is None else pc)
            
            color = color_palette_provider.get_driver_color(driver, format="hex")
            colors.append(color if color else "#808080")
        
        if self.chart_type == "final_position":
            sorted_data = sorted(zip(drivers, values, colors), key=lambda x: x[1])
        else:
            sorted_data = sorted(zip(drivers, values, colors), key=lambda x: x[1], reverse=True)
        
        drivers, values, colors = zip(*sorted_data)
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        y_pos = np.arange(len(drivers))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.8, 
                       edgecolor='black', linewidth=0.5)
        
        for i, (bar, val) in enumerate(zip(bars, values)):
            if self.chart_type == "final_position":
                label = f"P{val}"
            else:
                label = f"{'+' if val > 0 else ''}{val}"
            
            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, 
                   f' {label}', va='center', ha='left', fontsize=9, fontweight='bold')
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers, fontsize=10)
        ax.invert_yaxis()
        
        if self.chart_type == "final_position":
            ax.set_xlabel("最終名次", fontsize=12, fontweight='bold')
            ax.set_title("2024 日本 GP - 車手最終名次", fontsize=14, fontweight='bold')
            ax.invert_xaxis()
        else:
            ax.set_xlabel("名次變化", fontsize=12, fontweight='bold')
            ax.set_title("2024 日本 GP - 車手名次變化", fontsize=14, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
        
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _on_chart_switch(self, index):
        self.chart_type = self.chart_combo.itemData(index)
        self.draw_chart()


class OptionADualView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        
        self.table_view = OptionATableWidget()
        self.tab_widget.addTab(self.table_view, "表格視圖")
        
        self.chart_view = None
        self.chart_placeholder = QWidget()
        self.tab_widget.addTab(self.chart_placeholder, "圖表視圖")
        
        layout.addWidget(self.tab_widget)
        
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def update_data(self, data: dict):
        self.current_data = data
        self.table_view.update_data(data)
        
        if self.chart_view:
            self.chart_view.update_data(data)
    
    def _on_tab_changed(self, index: int):
        if index == 1 and self.chart_view is None:
            print("[DEMO] 延遲載入圖表視圖...")
            self.chart_view = OptionAChartWidget()
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.chart_view, "圖表視圖")
            self.tab_widget.setCurrentIndex(1)
            
            if self.current_data:
                self.chart_view.update_data(self.current_data)


# ==================== 主視窗 ====================
class DemoWindow(QMainWindow):
    def __init__(self, option="A"):
        super().__init__()
        self.option = option.upper()
        
        titles = {
            "A": "方案 A - 雙 Tab 視圖（表格 + 圖表）",
            "B": "方案 B - 單一圖表視圖（簡化版）",
            "C": "方案 C - 表格優先 + 彈出圖表",
            "D": "方案 D - 垂直分割視圖",
            "E": "方案 E - 互動式圖表 + 懸浮詳情"
        }
        
        self.setWindowTitle(f"車手名次分析 GUI - {titles.get(self.option, '未知方案')}")
        self.setGeometry(100, 100, 1200, 800)
        
        if self.option == "A":
            self.dual_view = OptionADualView()
            self.setCentralWidget(self.dual_view)
        else:
            label = QLabel(f"方案 {self.option} 的完整實現請參考原始 demo_position_option_{self.option.lower()}.py")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14pt;")
            self.setCentralWidget(label)
        
        self.load_data()
    
    def load_data(self):
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if not json_path.exists():
            QMessageBox.critical(self, "錯誤", f"找不到數據檔案：{json_path}")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if self.option == "A":
            self.dual_view.update_data(data)
        
        print(f"[DEMO-{self.option}] 數據載入完成")


def main():
    app = QApplication(sys.argv)
    
    color_palette_provider.ensure_loaded(year=2024)
    
    option = sys.argv[1].upper() if len(sys.argv) > 1 else "A"
    
    if option not in ['A', 'B', 'C', 'D', 'E']:
        print(f"錯誤：無效的方案 '{option}'")
        print("有效選項：A, B, C, D, E")
        print("使用方法：python demo_position_all_options.py A")
        sys.exit(1)
    
    window = DemoWindow(option)
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
