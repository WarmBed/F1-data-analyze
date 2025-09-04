#!/usr/bin/env python3
"""
降雨分析圖表組件
Rain Analysis Chart Widget

通用的雙Y軸曲線圖組件，用於顯示：
- 左Y軸：溫度
- 右Y軸：風速  
- X軸：時間
- 降雨段落標記
"""

import sys
import os
import json
import subprocess
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QProgressBar, QTextEdit, QSplitter
)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# 設置中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 確保模組路徑正確
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

class RainAnalysisWorker(QThread):
    """降雨分析背景工作執行緒"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, year, race, session):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        
    def run(self):
        """執行降雨分析 - 智能緩存策略"""
        try:
            self.progress_updated.emit(10)
            
            # 1. 先檢查是否有現有的 JSON 檔案
            from datetime import datetime
            today = datetime.now().strftime("%Y%m%d")
            session_name = "Race" if self.session == "R" else self.session
            json_file_pattern = f"rain_analysis_{self.year}_{self.race}_{session_name}.json"
            json_path = os.path.join(project_root, "json", json_file_pattern)
            
            self.progress_updated.emit(30)
            
            # 2. 如果今天的檔案不存在，尋找最新的雨量分析檔案
            if not os.path.exists(json_path):
                json_dir = os.path.join(project_root, "json")
                if os.path.exists(json_dir):
                    rain_files = [f for f in os.listdir(json_dir) 
                                if f.startswith(f"rain_analysis_{self.year}_{self.race}") 
                                and f.endswith(".json")]
                    if rain_files:
                        rain_files.sort(reverse=True)
                        json_path = os.path.join(json_dir, rain_files[0])
                        print(f"[INFO] 使用現有的雨量分析檔案: {rain_files[0]}")
                    else:
                        json_path = None
                        
            self.progress_updated.emit(50)
            
            # 3. 如果有 JSON 檔案，直接讀取
            if json_path and os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    self.progress_updated.emit(100)
                    print(f"[OK] 成功讀取現有 JSON 檔案: {json_path}")
                    self.analysis_completed.emit(data)
                    return
                except Exception as e:
                    print(f"[ERROR] 讀取 JSON 檔案失敗: {e}")
            
            # 4. 如果沒有 JSON 檔案，執行參數化分析生成
            print(f"[INFO] 未找到現有 JSON，執行參數化分析生成...")
            main_script = os.path.join(project_root, "f1_analysis_modular_main.py")
            cmd = [
                sys.executable, main_script,
                "--function", "1",  # 降雨強度分析
                "--year", str(self.year),
                "--race", self.race,
                "--session", self.session,
                "--show-detailed-output"
            ]
            
            self.progress_updated.emit(70)
            
            print(f"[START] 執行命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                encoding='utf-8',
                errors='replace'
            )
            
            self.progress_updated.emit(85)
            
            if result.returncode != 0:
                raise Exception(f"參數化分析執行失敗: {result.stderr}")
            
            # 5. 重新檢查 JSON 檔案是否生成
            if json_path and os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    self.progress_updated.emit(100)
                    print(f"[OK] 成功讀取新生成的 JSON 檔案: {json_path}")
                    self.analysis_completed.emit(data)
                except Exception as e:
                    print(f"[ERROR] 讀取新生成的 JSON 檔案失敗: {e}")
                    self.error_occurred.emit(f"讀取新生成的 JSON 檔案失敗: {str(e)}")
            else:
                # 如果還是沒有 JSON 檔案，返回分析輸出
                self.analysis_completed.emit({
                    "success": True,
                    "message": "分析完成，但未生成 JSON 輸出檔案",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                
        except Exception as e:
            self.error_occurred.emit(f"降雨分析執行失敗: {str(e)}")


class RainAnalysisChartWidget(QWidget):
    """降雨分析圖表組件 - 通用雙Y軸曲線圖"""
    
    def __init__(self, year=2025, race="Japan", session="R", parent=None):
        super().__init__(parent)
        self.year = year
        self.race = race
        self.session = session
        self.rain_data = None
        self.current_analysis_data = None
        self.init_ui()
        
        # 自動開始分析
        QTimer.singleShot(1000, self.start_analysis)
        
    def init_ui(self):
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        
        # 標題和控制區域
        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"🌧️ 降雨分析 - {self.year} {self.race} {self.session}")
        title_label.setFont(QFont("Microsoft JhengHei", 12, QFont.Bold))
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 重新分析按鈕
        self.refresh_btn = QPushButton("🔄 重新分析")
        self.refresh_btn.setFixedSize(100, 30)
        self.refresh_btn.clicked.connect(self.start_analysis)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 狀態標籤
        self.status_label = QLabel("準備分析...")
        layout.addWidget(self.status_label)
        
        # 分割器：圖表和資訊
        splitter = QSplitter()
        layout.addWidget(splitter)
        
        # 圖表區域
        self.figure = Figure(figsize=(12, 6))
        self.canvas = FigureCanvas(self.figure)
        splitter.addWidget(self.canvas)
        
        # 資訊面板
        self.info_panel = QTextEdit()
        self.info_panel.setMaximumHeight(150)
        self.info_panel.setReadOnly(True)
        splitter.addWidget(self.info_panel)
        
        # 設置分割器比例
        splitter.setSizes([400, 150])
        
    def start_analysis(self):
        """開始降雨分析"""
        self.status_label.setText(f"🚀 開始分析 {self.year} {self.race} {self.session} 降雨數據...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.refresh_btn.setEnabled(False)
        
        # 創建並啟動工作執行緒
        self.worker = RainAnalysisWorker(self.year, self.race, self.session)
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
        self.refresh_btn.setEnabled(True)
        self.status_label.setText("✅ 分析完成")
        
        self.current_analysis_data = data
        print(f"📊 返回數據: {str(data)[:200]}...")
        
        # 更新資訊面板
        self.update_info_panel(data)
        
        # 繪製圖表
        self.plot_rain_analysis_chart(data)
        
    def on_analysis_error(self, error_message):
        """分析錯誤處理"""
        self.progress_bar.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_label.setText(f"❌ 分析失敗: {error_message}")
        
        # 顯示錯誤資訊
        self.info_panel.setPlainText(f"錯誤：{error_message}")
        
    def update_info_panel(self, data):
        """更新資訊面板"""
        try:
            info_text = ""
            
            if 'metadata' in data:
                metadata = data['metadata']
                info_text += f"分析類型: {metadata.get('analysis_type', 'N/A')}\n"
                info_text += f"生成時間: {metadata.get('generated_at', 'N/A')}\n"
                info_text += f"年份: {metadata.get('year', 'N/A')}\n"
                info_text += f"賽事: {metadata.get('race_name', 'N/A')}\n\n"
                
            if 'summary' in data:
                summary = data['summary']
                info_text += f"總數據點: {summary.get('total_data_points', 'N/A')}\n"
                
                if 'rain_data_points' in summary:
                    info_text += f"降雨數據點: {summary['rain_data_points']}\n"
                    
                if 'temperature_range' in summary:
                    temp_range = summary['temperature_range']
                    info_text += f"溫度範圍: {temp_range.get('min', 'N/A')}°C - {temp_range.get('max', 'N/A')}°C\n"
                    
                if 'wind_speed_range' in summary:
                    wind_range = summary['wind_speed_range']
                    info_text += f"風速範圍: {wind_range.get('min', 'N/A')} - {wind_range.get('max', 'N/A')} km/h\n"
                    
            self.info_panel.setPlainText(info_text)
            
        except Exception as e:
            self.info_panel.setPlainText(f"資訊解析錯誤: {e}")
            
    def plot_rain_analysis_chart(self, data):
        """繪製降雨分析雙Y軸圖表"""
        try:
            self.figure.clear()
            
            # 檢查數據結構
            if 'weather_data' not in data:
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, '無法找到天氣數據', ha='center', va='center', transform=ax.transAxes)
                self.canvas.draw()
                return
                
            weather_data = data['weather_data']
            
            # 創建雙Y軸
            ax1 = self.figure.add_subplot(111)
            ax2 = ax1.twinx()
            
            # 提取時間、溫度、風速數據
            times = []
            temperatures = []
            wind_speeds = []
            rain_periods = []
            
            for entry in weather_data:
                if 'Time' in entry and 'AirTemp' in entry and 'WindSpeed' in entry:
                    times.append(entry['Time'])
                    temperatures.append(float(entry['AirTemp']))
                    wind_speeds.append(float(entry['WindSpeed']))
                    
                    # 檢查是否有降雨（根據 Rainfall 字段）
                    if entry.get('Rainfall', False) or entry.get('rainfall', False):
                        rain_periods.append(len(times) - 1)
            
            if not times:
                ax1.text(0.5, 0.5, '無有效的天氣數據', ha='center', va='center', transform=ax1.transAxes)
                self.canvas.draw()
                return
            
            # 轉換時間格式
            x_values = range(len(times))
            
            # 繪製溫度曲線（左Y軸）
            line1 = ax1.plot(x_values, temperatures, 'r-', linewidth=2, label='溫度 (°C)')
            ax1.set_xlabel('時間軸')
            ax1.set_ylabel('溫度 (°C)', color='red')
            ax1.tick_params(axis='y', labelcolor='red')
            ax1.grid(True, alpha=0.3)
            
            # 繪製風速曲線（右Y軸）
            line2 = ax2.plot(x_values, wind_speeds, 'b-', linewidth=2, label='風速 (km/h)')
            ax2.set_ylabel('風速 (km/h)', color='blue')
            ax2.tick_params(axis='y', labelcolor='blue')
            
            # 標記降雨時段
            if rain_periods:
                for rain_idx in rain_periods:
                    if rain_idx < len(x_values):
                        ax1.axvline(x=x_values[rain_idx], color='gray', alpha=0.7, linestyle='--', linewidth=1)
                        ax2.axvline(x=x_values[rain_idx], color='gray', alpha=0.7, linestyle='--', linewidth=1)
                
                # 在圖表上方添加降雨標記
                y_top = max(temperatures) * 1.1
                for rain_idx in rain_periods:
                    if rain_idx < len(x_values):
                        ax1.text(x_values[rain_idx], y_top, '🌧️', ha='center', va='bottom', fontsize=12)
            
            # 設置標題和圖例
            self.figure.suptitle(f'降雨分析 - {self.year} {self.race} {self.session}', fontsize=14, fontweight='bold')
            
            # 組合圖例
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # 設置X軸標籤（簡化顯示）
            if len(times) > 10:
                step = len(times) // 10
                ax1.set_xticks(x_values[::step])
                ax1.set_xticklabels([f"T{i//step}" for i in x_values[::step]], rotation=45)
            else:
                ax1.set_xticks(x_values)
                ax1.set_xticklabels([f"T{i}" for i in x_values], rotation=45)
            
            # 調整佈局
            self.figure.tight_layout()
            self.canvas.draw()
            
            print(f"[OK] 降雨分析圖表繪製完成 - 溫度點數: {len(temperatures)}, 風速點數: {len(wind_speeds)}, 降雨時段: {len(rain_periods)}")
            
        except Exception as e:
            print(f"[ERROR] 繪製圖表失敗: {e}")
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, f'圖表繪製錯誤: {e}', ha='center', va='center', transform=ax.transAxes)
            self.canvas.draw()


if __name__ == "__main__":
    """測試降雨分析圖表組件"""
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    widget = RainAnalysisChartWidget(2025, "Japan", "R")
    widget.setWindowTitle("降雨分析測試")
    widget.resize(800, 600)
    widget.show()
    
    sys.exit(app.exec_())
