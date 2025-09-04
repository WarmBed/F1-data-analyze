#!/usr/bin/env python3
"""
降雨分析圖表組件
Rain Analysis Chart Widget
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QCheckBox, QMessageBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

# 導入matplotlib相關
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle

# 設置中文字體支援
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'Arial Unicode MS', 'DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

class RainAnalysisWorker(QThread):
    """降雨分析背景工作線程"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, year, race, session):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        
    def run(self):
        """執行降雨分析"""
        try:
            self.progress_updated.emit(10)
            
            # 導入降雨分析模組
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from .rain_intensity_analyzer_json_fixed import RainIntensityAnalyzer
            from modules.base import initialize_data_loader
            
            self.progress_updated.emit(30)
            
            # 初始化數據載入器
            data_loader = initialize_data_loader()
            data_loader.load_session_data(self.year, self.race, self.session)
            
            self.progress_updated.emit(50)
            
            # 創建降雨分析器
            analyzer = RainIntensityAnalyzer()
            if not analyzer.initialize_from_data_loader(data_loader):
                self.error_occurred.emit("降雨分析器初始化失敗")
                return
                
            self.progress_updated.emit(70)
            
            # 執行分析
            if not analyzer.analyze_rain_patterns():
                self.error_occurred.emit("降雨模式分析失敗")
                return
                
            self.progress_updated.emit(90)
            
            # 生成結果
            result = analyzer.generate_json_output()
            if result.get("success", False):
                # 提取原始天氣數據以供圖表使用
                weather_data = analyzer.weather_data
                result["raw_weather_data"] = weather_data
                self.analysis_completed.emit(result)
            else:
                self.error_occurred.emit(result.get("error", "未知錯誤"))
                
            self.progress_updated.emit(100)
            
        except Exception as e:
            self.error_occurred.emit(f"分析過程中發生錯誤: {str(e)}")

class RainAnalysisChart(FigureCanvas):
    """降雨分析圖表"""
    
    def __init__(self, parent=None):
        self.figure = Figure(figsize=(12, 8), facecolor='black')
        super().__init__(self.figure)
        self.setParent(parent)
        
        # 設置圖表樣式
        self.figure.patch.set_facecolor('black')
        
        # 初始化軸
        self.ax_temp = None  # 溫度軸 (左Y軸)
        self.ax_wind = None  # 風速軸 (右Y軸)
        
        self.setup_chart()
        
    def setup_chart(self):
        """設置圖表基本結構"""
        self.figure.clear()
        
        # 創建主軸 (溫度)
        self.ax_temp = self.figure.add_subplot(111)
        self.ax_temp.set_facecolor('black')
        
        # 創建次軸 (風速)
        self.ax_wind = self.ax_temp.twinx()
        
        # 設置標籤和標題
        self.ax_temp.set_xlabel('時間', color='white', fontsize=12)
        self.ax_temp.set_ylabel('溫度 (°C)', color='#FF6B6B', fontsize=12)
        self.ax_wind.set_ylabel('風速 (km/h)', color='#4ECDC4', fontsize=12)
        
        # 設置軸顏色
        self.ax_temp.tick_params(axis='x', colors='white')
        self.ax_temp.tick_params(axis='y', colors='#FF6B6B')
        self.ax_wind.tick_params(axis='y', colors='#4ECDC4')
        
        # 設置網格
        self.ax_temp.grid(True, alpha=0.3, color='white')
        
        # 設置背景
        for spine in self.ax_temp.spines.values():
            spine.set_color('white')
        for spine in self.ax_wind.spines.values():
            spine.set_color('white')
            
        self.draw()
        
    def plot_weather_data(self, weather_data):
        """繪製天氣數據"""
        if weather_data is None or weather_data.empty:
            self.plot_no_data()
            return
            
        try:
            # 清除現有圖表
            self.ax_temp.clear()
            self.ax_wind.clear()
            
            # 準備時間數據
            if 'Time' in weather_data.columns:
                # 將時間轉換為分鐘數
                time_data = []
                for i, time_val in enumerate(weather_data['Time']):
                    if isinstance(time_val, timedelta):
                        time_data.append(time_val.total_seconds() / 60)  # 轉換為分鐘
                    else:
                        time_data.append(i * 1)  # 假設每分鐘一個數據點
            else:
                # 如果沒有時間欄位，使用索引
                time_data = list(range(len(weather_data)))
            
            # 繪製溫度曲線 (左Y軸)
            if 'AirTemp' in weather_data.columns:
                temp_data = weather_data['AirTemp'].dropna()
                if not temp_data.empty:
                    self.ax_temp.plot(time_data[:len(temp_data)], temp_data, 
                                    color='#FF6B6B', linewidth=2, label='氣溫', marker='o', markersize=3)
            
            # 繪製風速曲線 (右Y軸)
            if 'WindSpeed' in weather_data.columns:
                wind_data = weather_data['WindSpeed'].dropna()
                if not wind_data.empty:
                    self.ax_wind.plot(time_data[:len(wind_data)], wind_data, 
                                    color='#4ECDC4', linewidth=2, label='風速', marker='s', markersize=3)
            
            # 標記降雨時段
            if 'Rainfall' in weather_data.columns:
                self.mark_rain_periods(time_data, weather_data['Rainfall'])
            
            # 設置軸標籤和樣式
            self.ax_temp.set_xlabel('時間 (分鐘)', color='white', fontsize=12)
            self.ax_temp.set_ylabel('溫度 (°C)', color='#FF6B6B', fontsize=12)
            self.ax_wind.set_ylabel('風速 (km/h)', color='#4ECDC4', fontsize=12)
            
            # 設置軸顏色
            self.ax_temp.tick_params(axis='x', colors='white')
            self.ax_temp.tick_params(axis='y', colors='#FF6B6B')
            self.ax_wind.tick_params(axis='y', colors='#4ECDC4')
            
            # 設置背景和網格
            self.ax_temp.set_facecolor('black')
            self.ax_temp.grid(True, alpha=0.3, color='white')
            
            # 設置邊框顏色
            for spine in self.ax_temp.spines.values():
                spine.set_color('white')
            for spine in self.ax_wind.spines.values():
                spine.set_color('white')
            
            # 添加圖例
            lines1, labels1 = self.ax_temp.get_legend_handles_labels()
            lines2, labels2 = self.ax_wind.get_legend_handles_labels()
            if lines1 or lines2:
                self.ax_temp.legend(lines1 + lines2, labels1 + labels2, 
                                  loc='upper left', facecolor='black', 
                                  edgecolor='white', labelcolor='white')
            
            # 設置標題
            title = f"天氣狀況分析"
            self.ax_temp.set_title(title, color='white', fontsize=14, pad=20)
            
            self.draw()
            
        except Exception as e:
            print(f"繪製天氣數據時發生錯誤: {e}")
            self.plot_error(f"繪製錯誤: {str(e)}")
    
    def mark_rain_periods(self, time_data, rainfall_data):
        """標記降雨時段"""
        try:
            rain_periods = []
            in_rain = False
            start_time = None
            
            for i, (time_val, rain_val) in enumerate(zip(time_data, rainfall_data)):
                if pd.notna(rain_val) and rain_val > 0:  # 有降雨
                    if not in_rain:
                        start_time = time_val
                        in_rain = True
                else:  # 無降雨
                    if in_rain:
                        rain_periods.append((start_time, time_val))
                        in_rain = False
            
            # 處理最後一個降雨期間
            if in_rain and start_time is not None:
                rain_periods.append((start_time, time_data[-1]))
            
            # 在圖表上標記降雨時段
            for start, end in rain_periods:
                # 添加半透明藍色背景
                self.ax_temp.axvspan(start, end, alpha=0.3, color='lightblue', 
                                   label='降雨時段' if start == rain_periods[0][0] else "")
                
                # 在頂部添加降雨標記
                mid_time = (start + end) / 2
                y_max = self.ax_temp.get_ylim()[1] if self.ax_temp.get_ylim()[1] > 0 else 30
                self.ax_temp.text(mid_time, y_max * 0.95, '🌧️', 
                                fontsize=16, ha='center', va='top', color='blue')
            
            if rain_periods:
                print(f"標記了 {len(rain_periods)} 個降雨時段")
                
        except Exception as e:
            print(f"標記降雨時段時發生錯誤: {e}")
    
    def plot_no_data(self):
        """顯示無數據消息"""
        self.ax_temp.clear()
        self.ax_wind.clear()
        
        self.ax_temp.text(0.5, 0.5, '暫無天氣數據\n請先載入比賽數據', 
                         transform=self.ax_temp.transAxes,
                         horizontalalignment='center', verticalalignment='center',
                         fontsize=16, color='white')
        
        self.ax_temp.set_facecolor('black')
        for spine in self.ax_temp.spines.values():
            spine.set_color('white')
        for spine in self.ax_wind.spines.values():
            spine.set_color('white')
            
        self.draw()
    
    def plot_error(self, error_message):
        """顯示錯誤消息"""
        self.ax_temp.clear()
        self.ax_wind.clear()
        
        self.ax_temp.text(0.5, 0.5, f'❌ 錯誤\n{error_message}', 
                         transform=self.ax_temp.transAxes,
                         horizontalalignment='center', verticalalignment='center',
                         fontsize=14, color='red')
        
        self.ax_temp.set_facecolor('black')
        for spine in self.ax_temp.spines.values():
            spine.set_color('white')
        for spine in self.ax_wind.spines.values():
            spine.set_color('white')
            
        self.draw()

class RainAnalysisWidget(QWidget):
    """降雨分析主組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_data = None
        self.worker = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用戶界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 控制面板
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 5px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #4ECDC4;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 圖表
        self.chart = RainAnalysisChart(self)
        layout.addWidget(self.chart)
        
        # 設置整體樣式
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #FFFFFF;
            }
        """)
    
    def create_control_panel(self):
        """創建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 標題
        title_label = QLabel("🌧️ 降雨分析")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        title_label.setStyleSheet("color: #4ECDC4;")
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # 年份選擇
        layout.addWidget(QLabel("年份:"))
        self.year_combo = QComboBox()
        self.year_combo.addItems(['2025', '2024', '2023'])
        self.year_combo.setCurrentText('2025')
        layout.addWidget(self.year_combo)
        
        # 比賽選擇
        layout.addWidget(QLabel("比賽:"))
        self.race_combo = QComboBox()
        self.race_combo.addItems(['Japan', 'Belgium', 'Monaco', 'Silverstone', 'Spa'])
        self.race_combo.setCurrentText('Japan')
        layout.addWidget(self.race_combo)
        
        # 會話選擇
        layout.addWidget(QLabel("會話:"))
        self.session_combo = QComboBox()
        self.session_combo.addItems(['R', 'Q', 'FP1', 'FP2', 'FP3'])
        self.session_combo.setCurrentText('R')
        layout.addWidget(self.session_combo)
        
        # 分析按鈕
        self.analyze_button = QPushButton("🔄 開始分析")
        self.analyze_button.clicked.connect(self.start_analysis)
        self.analyze_button.setStyleSheet("""
            QPushButton {
                background-color: #4ECDC4;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45B7B8;
            }
            QPushButton:disabled {
                background-color: #666666;
                color: #999999;
            }
        """)
        layout.addWidget(self.analyze_button)
        
        # 重置按鈕
        reset_button = QPushButton("🔄 重置")
        reset_button.clicked.connect(self.reset_chart)
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #FF6B6B;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FF5252;
            }
        """)
        layout.addWidget(reset_button)
        
        panel.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                border: 1px solid #333333;
                border-radius: 5px;
            }
            QComboBox {
                background-color: #333333;
                border: 1px solid #555555;
                padding: 4px 8px;
                border-radius: 3px;
                min-width: 80px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                width: 10px;
                height: 10px;
            }
            QLabel {
                color: #CCCCCC;
                font-size: 11px;
            }
        """)
        
        return panel
    
    def start_analysis(self):
        """開始降雨分析"""
        if self.worker and self.worker.isRunning():
            return
            
        year = int(self.year_combo.currentText())
        race = self.race_combo.currentText()
        session = self.session_combo.currentText()
        
        print(f"🌧️ 開始降雨分析: {year} {race} {session}")
        
        # 創建工作線程
        self.worker = RainAnalysisWorker(year, race, session)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.analysis_completed.connect(self.on_analysis_completed)
        self.worker.error_occurred.connect(self.on_analysis_error)
        
        # 更新UI狀態
        self.analyze_button.setEnabled(False)
        self.analyze_button.setText("🔄 分析中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # 開始分析
        self.worker.start()
    
    def update_progress(self, value):
        """更新進度"""
        self.progress_bar.setValue(value)
    
    def on_analysis_completed(self, result):
        """分析完成處理"""
        print("✅ 降雨分析完成")
        
        # 更新UI狀態
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🔄 開始分析")
        self.progress_bar.setVisible(False)
        
        # 保存數據並繪製圖表
        self.current_data = result
        
        if "raw_weather_data" in result:
            weather_data = result["raw_weather_data"]
            self.chart.plot_weather_data(weather_data)
        else:
            self.chart.plot_no_data()
    
    def on_analysis_error(self, error_message):
        """分析錯誤處理"""
        print(f"❌ 降雨分析錯誤: {error_message}")
        
        # 更新UI狀態
        self.analyze_button.setEnabled(True)
        self.analyze_button.setText("🔄 開始分析")
        self.progress_bar.setVisible(False)
        
        # 顯示錯誤
        self.chart.plot_error(error_message)
        
        # 顯示錯誤對話框
        QMessageBox.warning(self, "分析錯誤", f"降雨分析失敗:\n{error_message}")
    
    def reset_chart(self):
        """重置圖表"""
        self.chart.setup_chart()
        self.current_data = None

# 測試用的主程式
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    widget = RainAnalysisWidget()
    widget.setWindowTitle("降雨分析測試")
    widget.resize(1200, 800)
    widget.show()
    
    sys.exit(app.exec_())
