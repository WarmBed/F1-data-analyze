#!/usr/bin/env python3
"""
降雨分析雙Y軸圖表組件
Rain Analysis Dual-Axis Chart Widget

支援特定圖表格式：
- 左Y軸：溫度
- 右Y軸：風速
- X軸：時間
- 降雨時段標註
"""

import sys
import os
import json
import subprocess
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QCheckBox, QMessageBox, QProgressBar, QTextEdit,
    QGroupBox, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

# 導入matplotlib相關
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np

# 設置中文字體支援
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# 確保能載入專案模組
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


class RainAnalysisWorker(QThread):
    """降雨分析背景工作線程 - 調用參數化主程式"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, year, race, session):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        
    def run(self):
        """執行降雨分析 - 調用f1_analysis_modular_main.py功能1"""
        try:
            self.progress_updated.emit(10)
            
            # 構建命令調用參數化主程式 (功能1 = 降雨強度分析)
            main_script = os.path.join(project_root, "f1_analysis_modular_main.py")
            cmd = [
                sys.executable, main_script,
                "--function", "1",  # 降雨強度分析
                "--year", str(self.year),
                "--race", self.race,
                "--session", self.session,
                "--show_detailed_output"  # 啟用詳細輸出
            ]
            
            self.progress_updated.emit(30)
            
            # 執行分析
            print(f"🚀 執行命令: {' '.join(cmd)}")
            
            # 使用更寬容的編碼處理
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                encoding='utf-8',  # 統一使用UTF-8編碼
                errors='replace'  # 替換無法解碼的字符
            )
            
            self.progress_updated.emit(60)
            
            if result.returncode != 0:
                raise Exception(f"分析執行失敗: {result.stderr}")
            
            # 嘗試從JSON輸出讀取結果
            json_file_pattern = f"rain_analysis_{self.year}_{self.race}_{self.session}.json"
            json_path = os.path.join(project_root, "json", json_file_pattern)
            
            self.progress_updated.emit(80)
            
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.progress_updated.emit(100)
                self.analysis_completed.emit(data)
            else:
                # 如果JSON檔案不存在，解析標準輸出
                output_lines = result.stdout.split('\n')
                success_msg = "分析完成，但未找到JSON輸出檔案"
                self.analysis_completed.emit({
                    "success": True,
                    "message": success_msg,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                
        except Exception as e:
            self.error_occurred.emit(f"降雨分析執行失敗: {str(e)}")


class RainAnalysisDualAxisChart(QWidget):
    """降雨分析雙Y軸圖表組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rain_data = None
        self.current_analysis_data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用戶界面"""
        layout = QVBoxLayout(self)
        
        # 標題
        title_label = QLabel("🌧️ 降雨分析 - 雙Y軸圖表")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 主內容區域 - 使用分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 圖表區域
        self.chart_frame = QFrame()
        self.chart_frame.setFrameStyle(QFrame.StyledPanel)
        self.chart_layout = QVBoxLayout(self.chart_frame)
        
        # 創建matplotlib圖表
        self.figure = Figure(figsize=(12, 8))
        self.canvas = FigureCanvas(self.figure)
        self.chart_layout.addWidget(self.canvas)
        
        # 結果顯示區域
        self.results_text = QTextEdit()
        self.results_text.setMaximumWidth(300)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: white;
                border: 1px solid #444;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        splitter.addWidget(self.chart_frame)
        splitter.addWidget(self.results_text)
        splitter.setStretchFactor(0, 3)  # 圖表佔更多空間
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
    def create_control_panel(self):
        """創建控制面板"""
        panel = QGroupBox("分析參數")
        layout = QHBoxLayout(panel)
        
        # 年份選擇
        layout.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.addItems(["2024", "2025"])
        self.year_combo.setCurrentText("2025")
        layout.addWidget(self.year_combo)
        
        # 賽事選擇
        layout.addWidget(QLabel("賽事:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems([
            "Japan", "Britain", "Brazil", "Singapore", 
            "Australia", "Bahrain", "Saudi Arabia", "China"
        ])
        self.race_combo.setCurrentText("Japan")
        layout.addWidget(self.race_combo)
        
        # 賽段選擇
        layout.addWidget(QLabel("賽段:"))
        self.session_combo = QComboBox()
        self.session_combo.addItems(["FP1", "FP2", "FP3", "Q", "R"])
        self.session_combo.setCurrentText("R")
        layout.addWidget(self.session_combo)
        
        layout.addStretch()
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 分析按鈕
        self.analyze_button = QPushButton("🚀 開始降雨分析")
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #666666;
            }
        """)
        self.analyze_button.clicked.connect(self.start_analysis)
        layout.addWidget(self.analyze_button)
        
        return panel
        
    def start_analysis(self):
        """開始降雨分析"""
        year = int(self.year_combo.currentText())
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        # 顯示進度條
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.analyze_button.setEnabled(False)
        
        # 清空結果顯示
        self.results_text.clear()
        self.results_text.append(f"🚀 開始分析 {year} {race} {session} 降雨數據...")
        
        # 創建並啟動工作線程
        self.worker = RainAnalysisWorker(year, race, session)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.analysis_completed.connect(self.on_analysis_completed)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.start()
        
    def update_progress(self, value):
        """更新進度條"""
        self.progress_bar.setValue(value)
        
    def on_analysis_completed(self, data):
        """分析完成處理"""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.current_analysis_data = data
        
        try:
            # 顯示結果摘要
            if isinstance(data, dict) and "weather_timeline" in data:
                self.display_analysis_summary(data)
                self.create_dual_axis_chart(data)
            else:
                self.results_text.append("✅ 分析完成")
                self.results_text.append(f"📊 返回數據: {str(data)[:500]}...")
                
        except Exception as e:
            self.results_text.append(f"❌ 圖表生成失敗: {str(e)}")
            
    def on_analysis_error(self, error_msg):
        """分析錯誤處理"""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.results_text.append(f"❌ 分析失敗: {error_msg}")
        QMessageBox.critical(self, "分析錯誤", error_msg)
        
    def display_analysis_summary(self, data):
        """顯示分析結果摘要"""
        self.results_text.clear()
        self.results_text.append("✅ 降雨分析完成\n")
        
        if "summary" in data:
            summary = data["summary"]
            self.results_text.append("📊 分析摘要:")
            self.results_text.append(f"  • 總降雨量: {summary.get('total_rainfall', 'N/A')} mm")
            self.results_text.append(f"  • 平均溫度: {summary.get('average_temperature', 'N/A')}°C")
            self.results_text.append(f"  • 最大濕度: {summary.get('max_humidity', 'N/A')}%")
            self.results_text.append(f"  • 降雨事件: {summary.get('rain_events', 'N/A')} 次")
            
        timeline = data.get("weather_timeline", [])
        if timeline:
            self.results_text.append(f"\n📈 天氣數據點: {len(timeline)} 個")
            self.results_text.append("🌧️ 圖表已生成 - 雙Y軸降雨分析")
        
    def create_dual_axis_chart(self, data):
        """創建雙Y軸降雨分析圖表"""
        self.figure.clear()
        
        timeline = data.get("weather_timeline", [])
        if not timeline:
            return
            
        # 準備數據
        times = []
        temperatures = []
        wind_speeds = []
        rainfall = []
        
        for entry in timeline:
            try:
                # 時間處理
                time_str = entry.get("time", "")
                if time_str:
                    time_obj = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    times.append(time_obj)
                
                # 溫度 (左Y軸)
                temp = entry.get("air_temperature", None)
                temperatures.append(temp if temp is not None else np.nan)
                
                # 風速 (右Y軸)  
                wind = entry.get("wind_speed", None)
                wind_speeds.append(wind if wind is not None else np.nan)
                
                # 降雨狀態
                rain = entry.get("rainfall", 0) > 0
                rainfall.append(rain)
                
            except Exception as e:
                print(f"數據處理錯誤: {e}")
                continue
                
        if not times:
            self.results_text.append("❌ 無有效時間數據")
            return
            
        # 創建雙Y軸圖表
        ax1 = self.figure.add_subplot(111)
        
        # 左Y軸 - 溫度
        color_temp = 'tab:red'
        ax1.set_xlabel('時間', fontsize=12)
        ax1.set_ylabel('溫度 (°C)', color=color_temp, fontsize=12)
        line1 = ax1.plot(times, temperatures, color=color_temp, linewidth=2, 
                        label='溫度', marker='o', markersize=3)
        ax1.tick_params(axis='y', labelcolor=color_temp)
        ax1.grid(True, alpha=0.3)
        
        # 右Y軸 - 風速
        ax2 = ax1.twinx()
        color_wind = 'tab:blue'
        ax2.set_ylabel('風速 (km/h)', color=color_wind, fontsize=12)
        line2 = ax2.plot(times, wind_speeds, color=color_wind, linewidth=2,
                        label='風速', marker='s', markersize=3)
        ax2.tick_params(axis='y', labelcolor=color_wind)
        
        # 標註降雨時段
        self.add_rain_annotations(ax1, times, rainfall)
        
        # 格式化X軸時間顯示
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax1.xaxis.set_major_locator(mdates.HourLocator(interval=1))
        
        # 設置標題
        race_info = f"{self.year_combo.currentText()} {self.race_combo.currentText()} {self.session_combo.currentText()}"
        self.figure.suptitle(f'降雨分析 - 溫度與風速 ({race_info})', fontsize=14, fontweight='bold')
        
        # 添加圖例
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
        
        # 調整佈局
        self.figure.tight_layout()
        
        # 刷新畫布
        self.canvas.draw()
        
    def add_rain_annotations(self, ax, times, rainfall):
        """在圖表上標註降雨時段"""
        rain_periods = []
        start_rain = None
        
        for i, is_raining in enumerate(rainfall):
            if is_raining and start_rain is None:
                start_rain = i
            elif not is_raining and start_rain is not None:
                rain_periods.append((start_rain, i-1))
                start_rain = None
                
        # 處理在分析結束時仍在下雨的情況
        if start_rain is not None:
            rain_periods.append((start_rain, len(rainfall)-1))
            
        # 繪製降雨時段背景
        y_min, y_max = ax.get_ylim()
        for start_idx, end_idx in rain_periods:
            if start_idx < len(times) and end_idx < len(times):
                start_time = times[start_idx]
                end_time = times[end_idx]
                
                # 添加半透明藍色背景
                ax.axvspan(start_time, end_time, alpha=0.3, color='lightblue', 
                          label='降雨時段' if rain_periods.index((start_idx, end_idx)) == 0 else "")
                          
        # 如果有降雨時段，在圖例中顯示
        if rain_periods:
            self.results_text.append(f"\n🌧️ 檢測到 {len(rain_periods)} 個降雨時段")


# 測試用主程式
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    
    # 設置應用程式樣式
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f0f0f0;
        }
        QGroupBox {
            font-weight: bold;
            border: 2px solid #cccccc;
            border-radius: 5px;
            margin-top: 1ex;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
        }
    """)
    
    widget = RainAnalysisDualAxisChart()
    widget.resize(1200, 800)
    widget.setWindowTitle("降雨分析 - 雙Y軸圖表")
    widget.show()
    
    sys.exit(app.exec_())
