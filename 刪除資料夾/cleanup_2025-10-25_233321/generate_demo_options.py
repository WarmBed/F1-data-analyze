#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成方案 B-E 的 Demo 檔案
使用 Python 確保正確的 UTF-8 編碼
"""

import os

# ============================================================================
# 方案 B：簡化版圖表視圖
# ============================================================================
DEMO_B_CONTENT = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Option B - Simplified Chart View
方案 B：簡化版圖表視圖 - 專注於視覺化
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QComboBox, QLabel, QCheckBox, QGroupBox, QPushButton)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.gui.base.color_palette_provider import color_palette_provider


class SimplifiedPositionChartWidget(QWidget):
    """簡化版圖表視圖：專注於視覺化"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 圖表
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)
        
        # 統計面板
        stats_panel = self._create_stats_panel()
        layout.addWidget(stats_panel)
        
    def _create_control_panel(self):
        """創建控制面板"""
        panel = QGroupBox("顯示選項")
        layout = QHBoxLayout()
        
        # 圖表模式選擇
        layout.addWidget(QLabel("圖表模式:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "最終名次",
            "名次變化",
            "起始 vs 最終"
        ])
        self.mode_combo.currentTextChanged.connect(self.update_chart)
        layout.addWidget(self.mode_combo)
        
        layout.addSpacing(20)
        
        # 顯示數字標籤
        self.show_labels_check = QCheckBox("顯示數字標籤")
        self.show_labels_check.setChecked(True)
        self.show_labels_check.toggled.connect(self.update_chart)
        layout.addWidget(self.show_labels_check)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
    def _create_stats_panel(self):
        """創建統計面板"""
        panel = QGroupBox("統計資訊")
        layout = QHBoxLayout()
        
        self.stats_label = QLabel("載入數據以查看統計")
        layout.addWidget(self.stats_label)
        
        panel.setLayout(layout)
        return panel
        
    def load_data(self, data):
        """載入數據"""
        self.data = data
        self.update_chart()
        self.update_stats()
        
    def update_chart(self):
        """更新圖表"""
        if not self.data:
            return
            
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        mode = self.mode_combo.currentText()
        show_labels = self.show_labels_check.isChecked()
        
        if mode == "最終名次":
            self._draw_final_position(ax, show_labels)
        elif mode == "名次變化":
            self._draw_position_change(ax, show_labels)
        else:  # 起始 vs 最終
            self._draw_start_vs_final(ax, show_labels)
            
        self.canvas.draw()
        
    def _draw_final_position(self, ax, show_labels):
        """繪製最終名次圖"""
        # 配置中文字體
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        
        # 準備數據
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
        
        # 繪製水平長條圖
        y_pos = range(len(drivers))
        bars = ax.barh(y_pos, positions, color=colors, edgecolor="black", linewidth=0.5)
        
        # 標籤
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("最終名次", fontsize=12, fontweight="bold")
        ax.set_title("車手最終名次", fontsize=14, fontweight="bold")
        ax.invert_xaxis()  # 反轉 X 軸，讓第 1 名在右邊
        ax.grid(axis="x", alpha=0.3)
        
        # 顯示數字標籤
        if show_labels:
            for bar, pos in zip(bars, positions):
                if pos < 99:
                    ax.text(pos, bar.get_y() + bar.get_height()/2, 
                           f"P{pos}", ha="left", va="center", fontsize=9)
        
    def _draw_position_change(self, ax, show_labels):
        """繪製名次變化圖"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        
        # 準備數據
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
            
            # 上升用綠色，下降用紅色，持平用灰色
            if pc > 0:
                colors_list.append("#2ecc71")
            elif pc < 0:
                colors_list.append("#e74c3c")
            else:
                colors_list.append("#95a5a6")
        
        # 繪製水平長條圖
        y_pos = range(len(drivers))
        bars = ax.barh(y_pos, changes, color=colors_list, edgecolor="black", linewidth=0.5)
        
        # 標籤
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("名次變化", fontsize=12, fontweight="bold")
        ax.set_title("車手名次變化（正值=上升，負值=下降）", fontsize=14, fontweight="bold")
        ax.axvline(x=0, color="black", linestyle="--", linewidth=1)
        ax.grid(axis="x", alpha=0.3)
        
        # 顯示數字標籤
        if show_labels:
            for bar, change in zip(bars, changes):
                if change != 0:
                    x_pos = change + (0.3 if change > 0 else -0.3)
                    ax.text(x_pos, bar.get_y() + bar.get_height()/2, 
                           f"{change:+d}", ha="center", va="center", fontsize=9)
        
    def _draw_start_vs_final(self, ax, show_labels):
        """繪製起始 vs 最終名次對比"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        plt.rcParams["axes.unicode_minus"] = False
        
        # 準備數據
        drivers = []
        start_positions = []
        final_positions = []
        colors = []
        
        for driver, info in sorted(self.data.items(), 
                                   key=lambda x: x[1].get("starting_position") or 99):
            sp = info.get("starting_position")
            fp = info.get("finishing_position")
            if sp is None:
                sp = 99
            if fp is None:
                fp = 99
            
            drivers.append(driver)
            start_positions.append(sp)
            final_positions.append(fp)
            
            color = color_palette_provider.get_driver_color(driver, format="hex") or "#808080"
            colors.append(color)
        
        # 繪製分組長條圖
        y_pos = range(len(drivers))
        bar_height = 0.35
        
        bars1 = ax.barh([y - bar_height/2 for y in y_pos], start_positions, 
                       bar_height, label="起始名次", color="#3498db", alpha=0.7)
        bars2 = ax.barh([y + bar_height/2 for y in y_pos], final_positions, 
                       bar_height, label="最終名次", color=colors, alpha=0.9)
        
        # 標籤
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers)
        ax.set_xlabel("名次", fontsize=12, fontweight="bold")
        ax.set_title("起始名次 vs 最終名次", fontsize=14, fontweight="bold")
        ax.invert_xaxis()
        ax.legend()
        ax.grid(axis="x", alpha=0.3)
        
        # 顯示數字標籤
        if show_labels:
            for bar, pos in zip(bars1, start_positions):
                if pos < 99:
                    ax.text(pos, bar.get_y() + bar.get_height()/2, 
                           f"P{pos}", ha="left", va="center", fontsize=8)
            for bar, pos in zip(bars2, final_positions):
                if pos < 99:
                    ax.text(pos, bar.get_y() + bar.get_height()/2, 
                           f"P{pos}", ha="left", va="center", fontsize=8)
        
    def update_stats(self):
        """更新統計資訊"""
        if not self.data:
            return
            
        total = len(self.data)
        finished = sum(1 for v in self.data.values() if v.get("finishing_position") is not None)
        dnf = total - finished
        
        avg_change = sum(v.get("position_change") or 0 for v in self.data.values()) / total
        
        stats_text = f"總車手數: {total} | 完賽: {finished} | DNF: {dnf} | 平均名次變化: {avg_change:.2f}"
        self.stats_label.setText(stats_text)


class OptionBDemo(QWidget):
    """方案 B Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo B: 簡化版圖表視圖")
        self.resize(1000, 700)
        self.init_ui()
        self.load_test_data()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("方案 B：簡化版圖表視圖")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 圖表視圖
        self.chart_widget = SimplifiedPositionChartWidget()
        layout.addWidget(self.chart_widget)
        
    def load_test_data(self):
        """載入測試數據"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "all_drivers_position_analysis" in data:
                    self.chart_widget.load_data(data["all_drivers_position_analysis"])
                    print("✅ 數據載入成功")
                else:
                    print("❌ 數據格式錯誤")
        else:
            print(f"❌ 找不到測試數據: {json_path}")


if __name__ == "__main__":
    # 確保調色板載入
    color_palette_provider.ensure_loaded(year=2024)
    
    app = QApplication(sys.argv)
    demo = OptionBDemo()
    demo.show()
    sys.exit(app.exec_())
'''

# ============================================================================
# 方案 C：表格優先 + 彈出式圖表
# ============================================================================
DEMO_C_CONTENT = '''#!/usr/bin/env python3
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

from modules.gui.base.color_palette_provider import color_palette_provider


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
'''

# ============================================================================
# 方案 D：分割視圖（表格 + 圖表）
# ============================================================================
DEMO_D_CONTENT = '''#!/usr/bin/env python3
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

from modules.gui.base.color_palette_provider import color_palette_provider


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
'''

# ============================================================================
# 方案 E：互動式圖表 + 詳細資訊面板
# ============================================================================
DEMO_E_CONTENT = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demo: Option E - Interactive Chart with Details Panel
方案 E：互動式圖表 + 點擊顯示詳細資訊
"""

import sys
import json
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QGroupBox, QTextEdit, QComboBox, QCheckBox,
                             QSplitter)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from modules.gui.base.color_palette_provider import color_palette_provider


class DetailsPanel(QWidget):
    """詳細資訊面板"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("車手詳細資訊")
        title_label.setStyleSheet("font-size: 12pt; font-weight: bold;")
        layout.addWidget(title_label)
        
        # 資訊顯示
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(200)
        layout.addWidget(self.info_text)
        
        self.show_default_message()
        
    def show_default_message(self):
        """顯示預設訊息"""
        self.info_text.setHtml("""
        <p style="color: #7f8c8d; font-size: 11pt;">
        <b>使用說明：</b><br>
        點擊圖表中的長條以查看該車手的詳細資訊。<br>
        包含起始名次、最終名次、名次變化等數據。
        </p>
        """)
        
    def show_driver_info(self, driver, info):
        """顯示車手資訊"""
        sp = info.get("starting_position")
        fp = info.get("finishing_position")
        pc = info.get("position_change")
        
        sp_text = f"P{sp}" if sp is not None else "N/A"
        fp_text = f"P{fp}" if fp is not None else "DNF"
        pc_text = f"{pc:+d}" if pc is not None and pc != 0 else "0" if pc == 0 else "N/A"
        
        # 名次變化分析
        if pc is not None:
            if pc > 0:
                trend = f'<span style="color: #27ae60; font-weight: bold;">上升 {pc} 個名次</span>'
            elif pc < 0:
                trend = f'<span style="color: #c0392b; font-weight: bold;">下降 {abs(pc)} 個名次</span>'
            else:
                trend = '<span style="color: #7f8c8d;">名次維持</span>'
        else:
            trend = '<span style="color: #95a5a6;">無數據</span>'
        
        html = f"""
        <div style="font-size: 11pt;">
            <h3 style="color: #2c3e50;">{driver}</h3>
            <table border="0" cellpadding="5">
                <tr>
                    <td><b>起始名次：</b></td>
                    <td>{sp_text}</td>
                </tr>
                <tr>
                    <td><b>最終名次：</b></td>
                    <td>{fp_text}</td>
                </tr>
                <tr>
                    <td><b>名次變化：</b></td>
                    <td>{pc_text}</td>
                </tr>
                <tr>
                    <td><b>趨勢分析：</b></td>
                    <td>{trend}</td>
                </tr>
            </table>
        </div>
        """
        
        self.info_text.setHtml(html)


class InteractiveChartWidget(QWidget):
    """互動式圖表視圖"""
    
    def __init__(self, details_panel, parent=None):
        super().__init__(parent)
        self.details_panel = details_panel
        self.data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 圖表
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.on_chart_click)
        layout.addWidget(self.canvas)
        
    def _create_control_panel(self):
        """創建控制面板"""
        panel = QGroupBox("圖表設定")
        layout = QHBoxLayout()
        
        # 圖表類型
        layout.addWidget(QLabel("圖表類型:"))
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["最終名次", "名次變化", "起始 vs 最終"])
        self.chart_type_combo.currentTextChanged.connect(self.update_chart)
        layout.addWidget(self.chart_type_combo)
        
        layout.addSpacing(20)
        
        # 過濾選項
        self.only_finished_check = QCheckBox("僅顯示完賽車手")
        self.only_finished_check.toggled.connect(self.update_chart)
        layout.addWidget(self.only_finished_check)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
        
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
        
        # 過濾數據
        filtered_data = self.data
        if self.only_finished_check.isChecked():
            filtered_data = {d: i for d, i in self.data.items() 
                           if i.get("finishing_position") is not None}
        
        chart_type = self.chart_type_combo.currentText()
        
        if chart_type == "最終名次":
            self._draw_final_position(ax, filtered_data)
        elif chart_type == "名次變化":
            self._draw_position_change(ax, filtered_data)
        else:
            self._draw_start_vs_final(ax, filtered_data)
            
        self.canvas.draw()
        
    def _draw_final_position(self, ax, data):
        """繪製最終名次"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        self.driver_list = []
        positions = []
        colors = []
        
        for driver, info in sorted(data.items(), 
                                   key=lambda x: x[1].get("finishing_position") or 99):
            fp = info.get("finishing_position")
            if fp is None:
                fp = 99
            
            self.driver_list.append(driver)
            positions.append(fp)
            color = color_palette_provider.get_driver_color(driver, format="hex") or "#808080"
            colors.append(color)
        
        y_pos = range(len(self.driver_list))
        self.bars = ax.barh(y_pos, positions, color=colors, edgecolor="black", 
                           linewidth=1, picker=True)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(self.driver_list, fontsize=11)
        ax.set_xlabel("最終名次", fontsize=12, fontweight="bold")
        ax.set_title("車手最終名次（點擊長條查看詳情）", fontsize=14, fontweight="bold")
        ax.invert_xaxis()
        ax.grid(axis="x", alpha=0.3)
        
    def _draw_position_change(self, ax, data):
        """繪製名次變化"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        self.driver_list = []
        changes = []
        colors_list = []
        
        for driver, info in sorted(data.items(), 
                                   key=lambda x: x[1].get("position_change") or 0,
                                   reverse=True):
            pc = info.get("position_change")
            if pc is None:
                pc = 0
            
            self.driver_list.append(driver)
            changes.append(pc)
            colors_list.append("#27ae60" if pc > 0 else "#c0392b" if pc < 0 else "#7f8c8d")
        
        y_pos = range(len(self.driver_list))
        self.bars = ax.barh(y_pos, changes, color=colors_list, edgecolor="black", 
                           linewidth=1, picker=True)
        ax.set_yticks(y_pos)
        ax.set_yticklabels(self.driver_list, fontsize=11)
        ax.set_xlabel("名次變化", fontsize=12, fontweight="bold")
        ax.set_title("車手名次變化（點擊長條查看詳情）", fontsize=14, fontweight="bold")
        ax.axvline(x=0, color="black", linestyle="--", linewidth=1.5)
        ax.grid(axis="x", alpha=0.3)
        
    def _draw_start_vs_final(self, ax, data):
        """繪製起始 vs 最終"""
        plt.rcParams["font.sans-serif"] = ["Microsoft JhengHei", "SimHei", "DejaVu Sans"]
        
        self.driver_list = []
        start_pos = []
        final_pos = []
        
        for driver, info in sorted(data.items(), 
                                   key=lambda x: x[1].get("starting_position") or 99):
            sp = info.get("starting_position")
            fp = info.get("finishing_position")
            if sp is None:
                sp = 99
            if fp is None:
                fp = 99
            
            self.driver_list.append(driver)
            start_pos.append(sp)
            final_pos.append(fp)
        
        y_pos = range(len(self.driver_list))
        bar_height = 0.35
        
        self.bars = ax.barh([y - bar_height/2 for y in y_pos], start_pos, bar_height, 
                           label="起始", color="#3498db", alpha=0.8, picker=True)
        ax.barh([y + bar_height/2 for y in y_pos], final_pos, bar_height, 
               label="最終", color="#e74c3c", alpha=0.8, picker=True)
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(self.driver_list, fontsize=11)
        ax.set_xlabel("名次", fontsize=12, fontweight="bold")
        ax.set_title("起始 vs 最終名次（點擊長條查看詳情）", fontsize=14, fontweight="bold")
        ax.invert_xaxis()
        ax.legend(fontsize=11)
        ax.grid(axis="x", alpha=0.3)
        
    def on_chart_click(self, event):
        """處理圖表點擊事件"""
        if event.inaxes is None or not hasattr(self, 'bars'):
            return
            
        for i, bar in enumerate(self.bars):
            if bar.contains(event)[0]:
                driver = self.driver_list[i]
                info = self.data[driver]
                self.details_panel.show_driver_info(driver, info)
                break


class OptionEDemo(QWidget):
    """方案 E Demo 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Demo E: 互動式圖表 + 詳細資訊面板")
        self.resize(1200, 800)
        self.init_ui()
        self.load_test_data()
        
    def init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("方案 E：互動式圖表 - 點擊長條查看詳細資訊")
        title.setStyleSheet("font-size: 16pt; font-weight: bold; padding: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 創建分割器
        splitter = QSplitter(Qt.Vertical)
        
        # 上方：互動式圖表（70%）
        self.details_panel = DetailsPanel()
        self.chart_widget = InteractiveChartWidget(self.details_panel)
        splitter.addWidget(self.chart_widget)
        
        # 下方：詳細資訊面板（30%）
        splitter.addWidget(self.details_panel)
        
        # 設定初始比例
        splitter.setSizes([600, 200])
        
        layout.addWidget(splitter)
        
    def load_test_data(self):
        """載入測試數據"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "all_drivers_position_analysis" in data:
                    self.chart_widget.load_data(data["all_drivers_position_analysis"])
                    print("✅ 數據載入成功")
                else:
                    print("❌ 數據格式錯誤")
        else:
            print(f"❌ 找不到測試數據: {json_path}")


if __name__ == "__main__":
    color_palette_provider.ensure_loaded(year=2024)
    
    app = QApplication(sys.argv)
    demo = OptionEDemo()
    demo.show()
    sys.exit(app.exec_())
'''


def create_demo_files():
    """創建所有 Demo 檔案"""
    demos = {
        'demo_position_option_b.py': DEMO_B_CONTENT,
        'demo_position_option_c.py': DEMO_C_CONTENT,
        'demo_position_option_d.py': DEMO_D_CONTENT,
        'demo_position_option_e.py': DEMO_E_CONTENT,
    }
    
    print("開始生成 Demo 檔案...\n")
    
    for filename, content in demos.items():
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ 已創建: {filename}")
        except Exception as e:
            print(f"❌ 創建失敗 {filename}: {e}")
    
    print("\n🎉 所有 Demo 檔案生成完成！")
    print("\n測試命令：")
    print("  python demo_position_option_b.py")
    print("  python demo_position_option_c.py")
    print("  python demo_position_option_d.py")
    print("  python demo_position_option_e.py")


if __name__ == "__main__":
    create_demo_files()
