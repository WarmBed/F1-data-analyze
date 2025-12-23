#!/usr/bin/env python3
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

from modules.gui.themes.color_palette_provider import color_palette_provider


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
