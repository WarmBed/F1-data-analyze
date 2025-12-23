#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Option D - Split View (Table + Chart)
方案 D：分割視圖 - 表格與圖表同時顯示
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QTableWidget, QTableWidgetItem, QSplitter, QLabel,
                             QHeaderView, QComboBox, QGroupBox)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.gui.themes.color_palette_provider import color_palette_provider


class CompactTableWidget(QWidget):
    """緊湊型表格視圖（30% 寬度）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["車手", "起始", "最終"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        layout.addWidget(self.table)
        
    def load_data(self, data):
        """載入數據"""
        self.data = data
        self.populate_table()
        
    def populate_table(self):
        """填充表格"""
        self.table.setRowCount(0)
        
        for driver, info in sorted(self.data.items(), 
                                   key=lambda x: x[1].get("finishing_position") or 99):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # 車手
            self.table.setItem(row, 0, QTableWidgetItem(driver))
            
            # 起始
            sp = info.get("starting_position")
            sp_text = f"P{sp}" if sp is not None else "N/A"
            self.table.setItem(row, 1, QTableWidgetItem(sp_text))
            
            # 最終
            fp = info.get("finishing_position")
            fp_text = f"P{fp}" if fp is not None else "DNF"
            self.table.setItem(row, 2, QTableWidgetItem(fp_text))


class LargeChartWidget(QWidget):
    """大圖表視圖（70% 寬度）"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 控制面板
        control_panel = QGroupBox("圖表控制")
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
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
    def load_data(self, data):
        """載入數據"""
        self.data = data
        self.update_chart()
        
    def update_chart(self):
        """更新圖表"""
        if not self.data:
            return
            
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
        bars = ax.barh(y_pos, positions, color=colors, edgecolor="black", linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers, fontsize=11)
        ax.set_xlabel("最終名次", fontsize=12, fontweight="bold")
        ax.set_title("車手最終名次分佈", fontsize=14, fontweight="bold")
        ax.invert_xaxis()
        ax.grid(axis="x", alpha=0.3)
        
        # 標籤
        for bar, pos in zip(bars, positions):
            if pos < 99:
                ax.text(pos, bar.get_y() + bar.get_height()/2, 
                       f"P{pos}", ha="left", va="center", fontsize=10, fontweight="bold")
        
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
            colors_list.append("#27ae60" if pc > 0 else "#c0392b" if pc < 0 else "#7f8c8d")
        
        y_pos = range(len(drivers))
        bars = ax.barh(y_pos, changes, color=colors_list, edgecolor="black", linewidth=0.8)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers, fontsize=11)
        ax.set_xlabel("名次變化（正=上升，負=下降）", fontsize=12, fontweight="bold")
        ax.set_title("車手名次變化分析", fontsize=14, fontweight="bold")
        ax.axvline(x=0, color="black", linestyle="--", linewidth=1.5)
        ax.grid(axis="x", alpha=0.3)
        
        # 標籤
        for bar, change in zip(bars, changes):
            if change != 0:
                x_pos = change + (0.4 if change > 0 else -0.4)
                ax.text(x_pos, bar.get_y() + bar.get_height()/2, 
                       f"{change:+d}", ha="center", va="center", 
                       fontsize=10, fontweight="bold")
        
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
        
        bars1 = ax.barh([y - bar_height/2 for y in y_pos], start_pos, bar_height, 
                       label="起始名次", color="#3498db", alpha=0.8, edgecolor="black", linewidth=0.5)
        bars2 = ax.barh([y + bar_height/2 for y in y_pos], final_pos, bar_height, 
                       label="最終名次", color="#e74c3c", alpha=0.8, edgecolor="black", linewidth=0.5)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers, fontsize=11)
        ax.set_xlabel("名次", fontsize=12, fontweight="bold")
        ax.set_title("起始名次 vs 最終名次對比", fontsize=14, fontweight="bold")
        ax.invert_xaxis()
        ax.legend(fontsize=11)
        ax.grid(axis="x", alpha=0.3)


class SplitViewWidget(QWidget):
    """分割視圖容器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 創建分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側：緊湊表格（30%）
        self.table_widget = CompactTableWidget()
        splitter.addWidget(self.table_widget)
        
        # 右側：大圖表（70%）
        self.chart_widget = LargeChartWidget()
        splitter.addWidget(self.chart_widget)
        
        # 設定初始比例
        splitter.setSizes([300, 700])
        
        layout.addWidget(splitter)
        
    def load_data(self, data):
        """載入數據"""
        self.table_widget.load_data(data)
        self.chart_widget.load_data(data)


class OptionDDemo(QWidget):
    """方案 D Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo D: 分割視圖（表格 30% + 圖表 70%）")
        self.resize(1200, 700)
        self.init_ui()
        self.load_test_data()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("方案 D：分割視圖 - 表格與圖表並排顯示")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 分割視圖
        self.split_view = SplitViewWidget()
        layout.addWidget(self.split_view)
        
    def load_test_data(self):
        """載入測試數據"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "all_drivers_position_analysis" in data:
                    self.split_view.load_data(data["all_drivers_position_analysis"])
                    print("✅ 數據載入成功")
                else:
                    print("❌ 數據格式錯誤")
        else:
            print(f"❌ 找不到測試數據: {json_path}")


if __name__ == "__main__":
    color_palette_provider.ensure_loaded(year=2024)
    
    app = QApplication(sys.argv)
    demo = OptionDDemo()
    demo.show()
    sys.exit(app.exec_())
