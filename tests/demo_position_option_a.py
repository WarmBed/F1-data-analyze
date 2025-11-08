#!/usr/bin/env python3
"""
方案 A Demo：雙 Tab 視圖（表格 + 圖表）
完全複製 all_drivers_speed 的架構
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

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QComboBox, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

# 車隊配色
from modules.gui.themes.color_palette_provider import color_palette_provider


class PositionTableWidget(QWidget):
    """表格視圖：顯示所有車手的詳細名次數據"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 標題
        title = QLabel("📊 車手名次詳細數據表")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; padding: 5px;")
        layout.addWidget(title)
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "車手", "起始名次", "最終名次", "名次變化", "最佳名次", "最差名次", "完賽狀態"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)
    
    def update_data(self, data: dict):
        """更新表格數據"""
        self.current_data = data
        driver_positions = data.get("all_drivers_position_analysis", {})
        
        self.table.setRowCount(len(driver_positions))
        
        for row, (driver, pos_data) in enumerate(sorted(
            driver_positions.items(),
            key=lambda x: x[1].get("finishing_position") or 99
        )):
            # 車手名稱（帶顏色背景）
            driver_item = QTableWidgetItem(driver)
            color = color_palette_provider.get_driver_color(driver)
            driver_item.setBackground(QColor(color))
            driver_item.setForeground(QColor("white"))
            driver_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, driver_item)
            
            # 名次數據
            start_pos = pos_data.get("starting_position", "-")
            final_pos = pos_data.get("finishing_position", "-")
            change = pos_data.get("position_change", 0)
            best_pos = pos_data.get("best_position", "-")
            worst_pos = pos_data.get("worst_position", "-")
            status = pos_data.get("status", "Unknown")
            
            # 填充數據
            items = [
                QTableWidgetItem(f"P{start_pos}"),
                QTableWidgetItem(f"P{final_pos}"),
                self._create_change_item(change),
                QTableWidgetItem(f"P{best_pos}"),
                QTableWidgetItem(f"P{worst_pos}"),
                QTableWidgetItem(status)
            ]
            
            for col, item in enumerate(items, start=1):
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)
    
    def _create_change_item(self, change: int) -> QTableWidgetItem:
        """創建名次變化單元格（帶顏色標記）"""
        if change > 0:
            text = f"↑ {change}"
            item = QTableWidgetItem(text)
            item.setForeground(QColor("green"))
        elif change < 0:
            text = f"↓ {abs(change)}"
            item = QTableWidgetItem(text)
            item.setForeground(QColor("red"))
        else:
            text = "→ 0"
            item = QTableWidgetItem(text)
            item.setForeground(QColor("gray"))
        
        item.setTextAlignment(Qt.AlignCenter)
        return item


class PositionChartWidget(QWidget):
    """圖表視圖：水平長條圖"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.chart_type = "final_position"  # "final_position" 或 "position_change"
        
        # Matplotlib 中文字體
        plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        
        self.figure = Figure(figsize=(12, 8), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItem("📊 最終名次圖表", "final_position")
        self.chart_combo.addItem("📈 名次變化圖表", "position_change")
        self.chart_combo.currentIndexChanged.connect(self._on_chart_switch)
        
        self.export_btn = QPushButton("💾 匯出圖表")
        self.export_btn.clicked.connect(self._export_chart)
        
        control_layout.addWidget(QLabel("圖表類型："))
        control_layout.addWidget(self.chart_combo)
        control_layout.addStretch()
        control_layout.addWidget(self.export_btn)
        
        layout.addLayout(control_layout)
        layout.addWidget(self.canvas)
    
    def update_data(self, data: dict):
        """更新圖表數據"""
        self.current_data = data
        self.draw_chart()
    
    def draw_chart(self):
        """繪製水平長條圖"""
        if not self.current_data:
            return
        
        driver_positions = self.current_data.get("all_drivers_position_analysis", {})
        
        # 準備數據
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
            
            # 獲取顏色（Matplotlib 需要 hex 格式）
            color = color_palette_provider.get_driver_color(driver, format="hex")
            colors.append(color if color else "#808080")
        
        # 排序（處理 None 值）
        if self.chart_type == "final_position":
            sorted_data = sorted(zip(drivers, values, colors), key=lambda x: x[1] if x[1] is not None else 99)
        else:
            sorted_data = sorted(zip(drivers, values, colors), key=lambda x: x[1] if x[1] is not None else 0, reverse=True)
        
        drivers, values, colors = zip(*sorted_data)
        
        # 清除舊圖
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 繪製水平長條圖
        y_pos = np.arange(len(drivers))
        bars = ax.barh(y_pos, values, color=colors, alpha=0.8, 
                       edgecolor='black', linewidth=0.5)
        
        # 在長條上顯示數值
        for i, (bar, val) in enumerate(zip(bars, values)):
            if self.chart_type == "final_position":
                label = f"P{val}"
            else:
                label = f"{'+' if val > 0 else ''}{val}"
            
            ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, 
                   f' {label}', va='center', ha='left', fontsize=9, fontweight='bold')
        
        # 設定 Y 軸
        ax.set_yticks(y_pos)
        ax.set_yticklabels(drivers, fontsize=10)
        ax.invert_yaxis()
        
        # 設定 X 軸和標題
        if self.chart_type == "final_position":
            ax.set_xlabel("最終名次", fontsize=12, fontweight='bold')
            ax.set_title("2024 日本 GP - 車手最終名次", fontsize=14, fontweight='bold')
            ax.invert_xaxis()  # 第1名在右側
        else:
            ax.set_xlabel("名次變化（正值=進步，負值=退步）", fontsize=12, fontweight='bold')
            ax.set_title("2024 日本 GP - 車手名次變化", fontsize=14, fontweight='bold')
            ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
        
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        self.figure.tight_layout()
        self.canvas.draw()
    
    def _on_chart_switch(self, index):
        """切換圖表類型"""
        self.chart_type = self.chart_combo.itemData(index)
        self.draw_chart()
    
    def _export_chart(self):
        """匯出圖表"""
        QMessageBox.information(self, "匯出", "匯出功能示範（實際版本會儲存圖片）")


class PositionDualView(QWidget):
    """雙 Tab 容器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        
        # Tab 1: 表格視圖
        self.table_view = PositionTableWidget()
        self.tab_widget.addTab(self.table_view, "📊 表格視圖")
        
        # Tab 2: 圖表視圖（延遲載入）
        self.chart_view = None
        self.chart_placeholder = QWidget()
        self.tab_widget.addTab(self.chart_placeholder, "📈 圖表視圖")
        
        layout.addWidget(self.tab_widget)
        
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def update_data(self, data: dict):
        """更新數據"""
        self.current_data = data
        self.table_view.update_data(data)
        
        if self.chart_view:
            self.chart_view.update_data(data)
    
    def _on_tab_changed(self, index: int):
        """Tab 切換事件"""
        if index == 1 and self.chart_view is None:
            print("[DEMO-A] 延遲載入圖表視圖...")
            self.chart_view = PositionChartWidget()
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.chart_view, "📈 圖表視圖")
            self.tab_widget.setCurrentIndex(1)
            
            if self.current_data:
                self.chart_view.update_data(self.current_data)


class DemoAWindow(QMainWindow):
    """方案 A 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🏎️ 方案 A Demo - 雙 Tab 視圖（表格 + 圖表）")
        self.setGeometry(100, 100, 1200, 800)
        
        # 創建中心 widget
        self.dual_view = PositionDualView()
        self.setCentralWidget(self.dual_view)
        
        # 載入數據
        self.load_data()
    
    def load_data(self):
        """載入 JSON 數據"""
        json_path = Path("cache/position_analysis_2024_Japan_R_all_drivers.json")
        
        if not json_path.exists():
            QMessageBox.critical(self, "錯誤", f"找不到數據檔案：{json_path}")
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.dual_view.update_data(data)
        print("[DEMO-A] ✅ 數據載入完成")


def main():
    app = QApplication(sys.argv)
    
    # 確保配色系統初始化
    color_palette_provider.ensure_loaded(year=2024)
    
    window = DemoAWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
