#!/usr/bin/env python3
"""
雨量分析通用視窗模組
使用通用的 TelemetryChartWidget 顯示雨量分析結果
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

# 確保可以導入主 GUI
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

class RainAnalysisWorker(QThread):
    """雨量分析背景工作執行緒"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, year, race, session):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        
    def run(self):
        """執行降雨分析 - 按照正確流程：先檢查JSON，沒有才執行參數化"""
        try:
            self.progress_updated.emit(10)
            
            # 步驟1: 先檢查 JSON 檔案是否存在
            today = datetime.now().strftime("%Y%m%d")
            session_name = "Race" if self.session == "R" else self.session
            json_file_pattern = f"rain_intensity_{self.year}_{self.race}_{session_name}_{today}.json"
            json_path = os.path.join(project_root, "json", json_file_pattern)
            
            # 嘗試尋找現有的雨量分析檔案
            existing_json_path = None
            json_dir = os.path.join(project_root, "json")
            if os.path.exists(json_dir):
                rain_files = [f for f in os.listdir(json_dir) 
                            if f.startswith(f"rain_intensity_{self.year}_{self.race}") 
                            and f.endswith(".json")]
                if rain_files:
                    rain_files.sort(reverse=True)  # 最新的檔案在前
                    existing_json_path = os.path.join(json_dir, rain_files[0])
                    print(f"[CHECK] 發現現有雨量分析檔案: {rain_files[0]}")
            
            self.progress_updated.emit(30)
            
            # 步驟2: 如果有現有檔案，直接讀取
            if existing_json_path and os.path.exists(existing_json_path):
                print(f"[CACHE] 使用現有 JSON 檔案: {existing_json_path}")
                try:
                    with open(existing_json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    self.progress_updated.emit(100)
                    print(f"[OK] 成功讀取現有 JSON 檔案")
                    self.analysis_completed.emit(data)
                    return
                except Exception as e:
                    print(f"[WARNING] 讀取現有 JSON 檔案失敗: {e}")
                    # 繼續執行參數化分析
            
            # 步驟3: 沒有現有檔案，執行參數化主程式
            print(f"[GENERATE] 沒有找到現有檔案，開始執行參數化分析...")
            main_script = os.path.join(project_root, "f1_analysis_modular_main.py")
            cmd = [
                sys.executable, main_script,
                "--function", "1",  # 降雨強度分析
                "--year", str(self.year),
                "--race", self.race,
                "--session", self.session,
                "--show-detailed-output"
            ]
            
            self.progress_updated.emit(50)
            
            # 執行分析
            print(f"[START] 執行命令: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                encoding='utf-8',
                errors='replace'
            )
            
            self.progress_updated.emit(70)
            
            if result.returncode != 0:
                raise Exception(f"參數化分析執行失敗: {result.stderr}")
            
            # 步驟4: 參數化完成後，讀取新生成的 JSON
            print(f"[COMPLETE] 參數化分析完成，尋找新生成的 JSON 檔案...")
            
            # 重新搜尋 JSON 檔案 (應該有新的了)
            if os.path.exists(json_dir):
                rain_files = [f for f in os.listdir(json_dir) 
                            if f.startswith(f"rain_intensity_{self.year}_{self.race}") 
                            and f.endswith(".json")]
                if rain_files:
                    rain_files.sort(reverse=True)  # 最新的檔案在前
                    json_path = os.path.join(json_dir, rain_files[0])
                    print(f"[INFO] 使用新生成的雨量分析檔案: {rain_files[0]}")
                else:
                    json_path = None
            
            self.progress_updated.emit(90)
            
            if json_path and os.path.exists(json_path):
                try:
                    with open(json_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    self.progress_updated.emit(100)
                    print(f"[OK] 成功讀取 JSON 檔案: {json_path}")
                    self.analysis_completed.emit(data)
                except Exception as e:
                    print(f"[ERROR] 讀取 JSON 檔案失敗: {e}")
                    self.error_occurred.emit(f"讀取 JSON 檔案失敗: {str(e)}")
            else:
                # 如果JSON檔案不存在，解析標準輸出
                success_msg = f"分析完成，但未找到JSON輸出檔案 (尋找: {json_file_pattern})"
                print(f"[WARNING] {success_msg}")
                self.analysis_completed.emit({
                    "success": True,
                    "message": success_msg,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
                
        except Exception as e:
            self.error_occurred.emit(f"降雨分析執行失敗: {str(e)}")


class RainAnalysisUniversalWidget(QWidget):
    """雨量分析通用視窗 - 使用 TelemetryChartWidget"""
    
    def __init__(self, year=2025, race="Japan", session="R", telemetry_chart_widget=None):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        self.telemetry_chart_widget = telemetry_chart_widget  # 通用圖表視窗
        self.rain_data = None
        self.init_ui()
        
    def init_ui(self):
        """初始化用戶介面 - 簡化版本"""
        layout = QVBoxLayout()
        
        # 進度條 (只在分析時顯示)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(8)  # 較薄的進度條
        layout.addWidget(self.progress_bar)
        
        # 狀態標籤 (放在底部，黃色字體)
        self.status_label = QLabel("準備就緒")
        self.status_label.setStyleSheet("color: #FFD700; font-size: 11px; padding: 5px;")  # 黃色字體
        layout.addWidget(self.status_label)
        
        # 設置緊湊的佈局
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        self.setLayout(layout)
        
        # 自動載入現有數據
        QTimer.singleShot(500, self.auto_load_existing_data)
        
    def auto_load_existing_data(self):
        """自動載入現有的JSON數據"""
        try:
            # 嘗試找到現有的JSON檔案
            today = datetime.now().strftime("%Y%m%d")
            session_name = "Race" if self.session == "R" else self.session
            json_file_pattern = f"rain_intensity_{self.year}_{self.race}_{session_name}_{today}.json"
            json_path = os.path.join(project_root, "json", json_file_pattern)
            
            # 如果今天的檔案不存在，嘗試尋找最新的雨量分析檔案
            if not os.path.exists(json_path):
                json_dir = os.path.join(project_root, "json")
                if os.path.exists(json_dir):
                    rain_files = [f for f in os.listdir(json_dir) 
                                if f.startswith(f"rain_intensity_{self.year}_{self.race}") 
                                and f.endswith(".json")]
                    if rain_files:
                        rain_files.sort(reverse=True)
                        json_path = os.path.join(json_dir, rain_files[0])
                        print(f"[INFO] 自動載入: {rain_files[0]}")
                    else:
                        json_path = None
            
            if json_path and os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.display_rain_data(data)
                self.status_label.setText(f"已載入現有數據: {os.path.basename(json_path)}")
            else:
                self.status_label.setText("未找到現有數據，請點擊「重新分析」")
                
        except Exception as e:
            print(f"[WARNING] 自動載入失敗: {e}")
            self.status_label.setText("自動載入失敗，請點擊「重新分析」")
    
    def start_analysis(self):
        """開始分析"""
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在執行雨量分析...")
        
        # 啟動背景工作執行緒
        self.worker = RainAnalysisWorker(self.year, self.race, self.session)
        self.worker.progress_updated.connect(self.progress_bar.setValue)
        self.worker.analysis_completed.connect(self.on_analysis_completed)
        self.worker.error_occurred.connect(self.on_error_occurred)
        self.worker.start()
    
    def on_analysis_completed(self, data):
        """分析完成"""
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.rain_data = data
        
        if "success" in data and data["success"]:
            self.display_rain_data(data)
            self.status_label.setText("分析完成")
        else:
            self.status_label.setText("分析完成，但未找到有效數據")
        
    def on_error_occurred(self, error_msg):
        """處理錯誤"""
        self.analyze_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"錯誤: {error_msg}")
        
        QMessageBox.critical(self, "分析錯誤", error_msg)
    
    def display_rain_data(self, data):
        """在通用圖表中顯示雨量數據"""
        if not self.telemetry_chart_widget:
            print("[ERROR] 未提供通用圖表視窗")
            return
        
        try:
            # 提取數據 - 修正JSON結構匹配
            weather_timeline = None
            
            # 檢查多種可能的數據結構
            if "detailed_weather_timeline" in data:
                weather_timeline = data["detailed_weather_timeline"]
                print(f"[CHECK] 找到 detailed_weather_timeline，包含 {len(weather_timeline)} 個數據點")
            elif "weather_data" in data:
                weather_timeline = data["weather_data"]
                print(f"[CHECK] 找到 weather_data，包含 {len(weather_timeline)} 個數據點")
            else:
                print(f"[ERROR] JSON中沒有找到天氣數據，可用鍵值: {list(data.keys())}")
                return
                
            if not weather_timeline:
                print("[ERROR] 天氣時間軸數據為空")
                return
                
            # 提取時間軸數據
            x_data = []
            temp_data = []  # 溫度數據
            humidity_data = []  # 濕度數據 (改為右Y軸)
            rain_annotations = []  # 降雨標註
            
            # 解析天氣數據 - 適應新的JSON結構
            for i, item in enumerate(weather_timeline):
                # 提取時間 - 正確解析 H:MM:SS.mmm 格式
                time_value = None
                if "time_point" in item:
                    time_str = item["time_point"]
                    # 解析時間格式 (支援 "H:MM:SS.mmm" 和 "M:SS.mmm")
                    try:
                        if ":" in time_str:
                            parts = time_str.split(":")
                            if len(parts) == 3:  # H:MM:SS.mmm 格式
                                hours = int(parts[0])
                                minutes = int(parts[1])
                                seconds_part = float(parts[2])
                                total_seconds = hours * 3600 + minutes * 60 + seconds_part
                                x_data.append(total_seconds)
                            elif len(parts) == 2:  # M:SS.mmm 格式
                                minutes = int(parts[0])
                                seconds_part = float(parts[1])
                                total_seconds = minutes * 60 + seconds_part
                                x_data.append(total_seconds)
                            else:
                                print(f"[WARNING] 未知時間格式 '{time_str}'")
                                x_data.append(i)
                        else:
                            x_data.append(float(time_str))
                    except Exception as e:
                        print(f"[WARNING] 時間解析失敗 '{time_str}': {e}")
                        x_data.append(i)  # 使用索引作為備選
                elif "time" in item:
                    time_value = item["time"]
                    x_data.append(float(time_value) if isinstance(time_value, (int, float)) else i)
                elif "time_index" in item:
                    x_data.append(item["time_index"])
                else:
                    x_data.append(i)  # 使用索引作為時間
                
                # 提取天氣數據 - 支援嵌套結構
                weather_data = item.get("weather_data", item)  # 支援嵌套或直接結構
                
                # 提取溫度 (左Y軸)
                temp_value = None
                if "air_temperature" in weather_data:
                    temp_info = weather_data["air_temperature"]
                    if isinstance(temp_info, dict) and "value" in temp_info:
                        temp_value = temp_info["value"]
                    else:
                        temp_value = temp_info
                
                if temp_value is not None:
                    temp_data.append(float(temp_value))
                else:
                    temp_data.append(0.0)  # 預設值
                
                # 提取濕度 (右Y軸) - 修正為濕度而非風速
                humidity_value = None
                if "humidity" in weather_data:
                    humidity_info = weather_data["humidity"]
                    if isinstance(humidity_info, dict) and "value" in humidity_info:
                        humidity_value = humidity_info["value"]
                    else:
                        humidity_value = humidity_info
                
                if humidity_value is not None:
                    humidity_data.append(float(humidity_value))
                else:
                    humidity_data.append(0.0)  # 預設值
                
                # 檢查降雨狀態
                rainfall_info = weather_data.get("rainfall", {})
                if isinstance(rainfall_info, dict):
                    is_raining = rainfall_info.get("is_raining", False)
                    if is_raining:
                        rain_annotations.append({
                            "start_x": x_data[-1],
                            "end_x": x_data[-1] + 1,
                            "label": "降雨"
                        })
                elif rainfall_info:  # 如果是布林值或其他真值
                    rain_annotations.append({
                        "start_x": x_data[-1],
                        "end_x": x_data[-1] + 1,
                        "label": "降雨"
                    })
            
            print(f"[DATA] 解析完成: X軸{len(x_data)}點, 溫度{len(temp_data)}點, 濕度{len(humidity_data)}點, 降雨{len(rain_annotations)}次")
            print(f"[TIME] 時間範圍: {min(x_data):.1f}s - {max(x_data):.1f}s (約{max(x_data)/60:.1f}分鐘)")
            
            # 數據驗證
            if not x_data or not temp_data:
                print(f"[ERROR] 數據不足: X軸={len(x_data)}, 溫度={len(temp_data)}")
                return
            
            # 準備通用圖表數據
            chart_data = {
                "x_data": x_data,
                "y_data": temp_data,  # 左Y軸：溫度
                "y2_data": humidity_data,  # 右Y軸：濕度
                "annotations": rain_annotations,
                "labels": {
                    "x_label": "時間 (秒)",
                    "y_label": "溫度",
                    "y2_label": "濕度"
                },
                "units": {
                    "y_unit": "°C",
                    "y2_unit": "%"  # 濕度單位
                },
                "colors": {
                    "y_color": [255, 0, 0],  # 紅色溫度線
                    "y2_color": [0, 0, 255]  # 藍色濕度線
                }
            }
            
            # 設置到通用圖表
            self.telemetry_chart_widget.set_custom_data(chart_data)
            print(f"[OK] 雨量數據已設置到通用圖表: 溫度範圍{min(temp_data):.1f}-{max(temp_data):.1f}°C, 濕度範圍{min(humidity_data):.1f}-{max(humidity_data):.1f}%")
            
        except Exception as e:
            print(f"[ERROR] 顯示雨量數據失敗: {e}")
            import traceback
            traceback.print_exc()
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"顯示數據失敗: {str(e)}")
    
    def clear_chart(self):
        """清除圖表"""
        if self.telemetry_chart_widget:
            self.telemetry_chart_widget.clear_custom_data()
            self.status_label.setText("圖表已清除")
    
    def start_analysis_external(self):
        """外部調用的分析方法 (供MDI按鈕使用)"""
        self.start_analysis()
    
    def clear_chart_external(self):
        """外部調用的清除方法 (供MDI按鈕使用)"""
        self.clear_chart()
