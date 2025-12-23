#!/usr/bin/env python3
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

from modules.gui.themes.color_palette_provider import color_palette_provider


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
