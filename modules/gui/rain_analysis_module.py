#!/usr/bin/env python3
"""
雨量分析模組 - 符合架構文檔規範
Rain Analysis Module - Following Architecture Documentation
"""

import sys
import os
import json
import subprocess
import time
import gc
import hashlib
from concurrent.futures import ThreadPoolExecutor
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QProgressBar, QLabel, QProgressDialog, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from datetime import datetime

# 導入通用圖表
try:
    from .universal_chart_widget import UniversalChartWidget, ChartDataSeries, ChartAnnotation
    # 強制重新載入模組以確保最新方法可用
    import importlib
    import modules.gui.universal_chart_widget
    importlib.reload(modules.gui.universal_chart_widget)
    from .universal_chart_widget import UniversalChartWidget, ChartDataSeries, ChartAnnotation
except ImportError:
    from universal_chart_widget import UniversalChartWidget, ChartDataSeries, ChartAnnotation
    # 強制重新載入模組以確保最新方法可用
    import importlib
    import universal_chart_widget
    importlib.reload(universal_chart_widget)
    from universal_chart_widget import UniversalChartWidget, ChartDataSeries, ChartAnnotation

# 獲取專案根目錄
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class RainAnalysisCache:
    """降雨分析緩存管理器 - 符合架構文檔"""
    
    def __init__(self):
        self.cache_dir = os.path.join(project_root, "json")
        self.cache_expiry = 24 * 60 * 60  # 24小時過期
        
        # 確保緩存目錄存在
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def get_cache_key(self, year, race, session, parameters_hash=None):
        """生成緩存鍵值"""
        if parameters_hash is None:
            # 基本緩存鍵值
            return f"rain_analysis_{year}_{race}_{session}"
        else:
            # 包含參數的緩存鍵值
            return f"rain_analysis_{year}_{race}_{session}_{parameters_hash}"
    
    def generate_parameters_hash(self, parameters):
        """生成參數哈希值"""
        param_str = json.dumps(parameters, sort_keys=True)
        return hashlib.md5(param_str.encode()).hexdigest()[:8]
    
    def find_cache_file(self, cache_key):
        """尋找符合條件的緩存檔案"""
        # 檢查今天的檔案 - 支援舊格式(8位數)和新格式(6位數)
        today_8digit = datetime.now().strftime("%Y%m%d")
        today_6digit = datetime.now().strftime("%y%m%d")
        
        # 解析 cache_key 獲取年份、地點等資訊
        parts = cache_key.replace('rain_analysis_', '').split('_')
        if len(parts) >= 3:
            year, location, session = parts[0], parts[1], parts[2]
            
            # 新格式: rain_analysis_YYYY_location_賽段.json
            new_format_pattern = f"rain_analysis_{year}_{location}_{session}.json"
            cache_path = os.path.join(self.cache_dir, new_format_pattern)
            if os.path.exists(cache_path):
                return cache_path
        
        # 舊格式檢查
        cache_patterns = [
            f"{cache_key}_{today_8digit}.json",
            f"rain_analysis_{cache_key.replace('rain_analysis_', '')}_{today_8digit}.json",
        ]
        
        for pattern in cache_patterns:
            cache_path = os.path.join(self.cache_dir, pattern)
            if os.path.exists(cache_path):
                return cache_path
        
        # 檢查最新的相關檔案
        cache_files = [f for f in os.listdir(self.cache_dir) 
                      if cache_key.replace('rain_analysis_', '') in f 
                      and f.endswith('.json')]
        
        if cache_files:
            cache_files.sort(reverse=True)  # 按檔案名排序（日期倒序）
            return os.path.join(self.cache_dir, cache_files[0])
        
        return None
    
    def is_cache_valid(self, cache_path):
        """檢查緩存是否有效"""
        if not os.path.exists(cache_path):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_path)
        is_valid = file_age < self.cache_expiry
        
        print(f"[CACHE] 緩存檔案: {os.path.basename(cache_path)}")
        print(f"[CACHE] 檔案年齡: {file_age/3600:.1f} 小時")
        print(f"[CACHE] 緩存有效: {'是' if is_valid else '否'}")
        
        return is_valid
    
    def load_cache(self, cache_path):
        """載入緩存數據"""
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"緩存載入成功: {os.path.basename(cache_path)}")
            return data
        except Exception as e:
            print(f"[ERROR] 緩存載入失敗: {e}")
            return None
    
    def save_cache(self, data, cache_key):
        """保存分析結果到緩存"""
        today = datetime.now().strftime("%Y%m%d")
        cache_filename = f"{cache_key}_{today}.json"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[SAVE] 降雨分析結果已緩存: {cache_filename}")
            return cache_path
        except Exception as e:
            print(f"[ERROR] 緩存保存失敗: {e}")
            return None


class RainAnalysisProgressDialog(QProgressDialog):
    """降雨分析進度對話框 - 符合架構文檔"""
    
    def __init__(self, parent=None):
        super().__init__("正在分析降雨數據...", "取消", 0, 100, parent)
        self.setWindowTitle("[RAIN] 降雨分析進行中")
        self.setWindowModality(Qt.WindowModal)
        self.setMinimumDuration(0)
        # self.setMinimumSize(400, 150) - 尺寸限制已移除
        
        # 設置進度階段說明
        self.progress_stages = {
            10: "[SEARCH] 檢查緩存數據...",
            20: "📥 初始化分析模組...",
            40: "[NETWORK] 載入比賽數據...",
            60: "[RAIN] 執行降雨影響分析...",
            80: "處理分析結果...",
            90: "[DESIGN] 準備圖表數據...",
            100: "[OK] 分析完成！"
        }
    
    def update_progress(self, value, custom_message=None):
        """更新進度並顯示階段說明"""
        self.setValue(value)
        
        if custom_message:
            self.setLabelText(custom_message)
        elif value in self.progress_stages:
            self.setLabelText(self.progress_stages[value])


class RainAnalysisWorker(QThread):
    """降雨分析工作執行緒 - 符合架構文檔"""
    
    progress_updated = pyqtSignal(int, str)  # 進度值, 自定義訊息
    analysis_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    cache_status = pyqtSignal(str, bool)  # 緩存狀態訊息, 是否使用緩存
    
    def __init__(self, year, race, session, parameters=None):
        super().__init__()
        self.year = year
        self.race = race
        self.session = session
        self.parameters = parameters or self.get_default_parameters()
        self.cache_manager = RainAnalysisCache()
        self.cancelled = False
    
    def get_default_parameters(self):
        """獲取預設分析參數"""
        return {
            "analysis_type": "comprehensive",
            "include_telemetry": True,
            "include_weather": True,
            "time_resolution": "1s",
            "output_format": "universal_chart"
        }
    
    def run(self):
        """執行降雨分析流程 - 完整架構實現"""
        try:
            # 階段 1: 緩存檢查
            self.progress_updated.emit(10, "[SEARCH] 檢查降雨分析緩存...")
            
            cache_key = self.cache_manager.get_cache_key(self.year, self.race, self.session)
            cache_file = self.cache_manager.find_cache_file(cache_key)
            
            if cache_file and self.cache_manager.is_cache_valid(cache_file):
                # 有效緩存存在 - 直接使用
                self.progress_updated.emit(50, "載入緩存數據...")
                cached_data = self.cache_manager.load_cache(cache_file)
                
                if cached_data:
                    self.cache_status.emit("使用緩存數據", True)
                    self.progress_updated.emit(100, "[OK] 緩存數據載入完成！")
                    self.analysis_completed.emit(cached_data)
                    return
            
            # 階段 2: 無緩存 - 執行參數化分析
            self.cache_status.emit("緩存未命中，執行新分析", False)
            self.progress_updated.emit(20, "📥 初始化分析模組...")
            
            if self.cancelled:
                return
            
            # 階段 3: 執行分析
            analysis_result = self.execute_parameterized_analysis()
            
            if self.cancelled:
                return
            
            # 階段 4: 保存緩存
            self.progress_updated.emit(90, "[SAVE] 保存分析結果...")
            self.cache_manager.save_cache(analysis_result, cache_key)
            
            # 階段 5: 完成
            self.progress_updated.emit(100, "[OK] 分析完成！")
            self.analysis_completed.emit(analysis_result)
            
        except Exception as e:
            error_msg = f"降雨分析執行失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.error_occurred.emit(error_msg)
    
    def execute_parameterized_analysis(self):
        """執行參數化分析 - 符合架構規範"""
        try:
            self.progress_updated.emit(40, "[DATA] 收集分析參數...")
            
            # 收集參數化分析參數 (符合架構文檔)
            parameters = {
                "year": self.year,
                "race": self.race, 
                "session": self.session,
                "analysis_type": "comprehensive",    # 分析類型
                "include_telemetry": True,          # 包含遙測數據
                "include_weather": True,            # 包含天氣數據
                "time_resolution": "1s",            # 時間解析度
                "output_format": "universal_chart"  # 輸出格式
            }
            
            print(f"[PARAM] 參數化分析設定: {parameters}")
            
            # 構建分析命令 - 專注JSON生成
            main_script = os.path.join(project_root, "f1_analysis_modular_main.py")
            cmd = [
                sys.executable, main_script,
                "--function", "1",  # 降雨強度分析
                "--year", str(self.year),
                "--race", self.race,
                "--session", self.session,
                "--show-detailed-output"  # 使用成功的參數
            ]
            
            print(f"[EXEC] 執行參數化分析: {' '.join(cmd)}")
            
            # 執行分析 - 簡化處理，專注JSON生成
            self.progress_updated.emit(60, "[RAIN] 執行降雨影響分析...")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                encoding='utf-8',
                errors='replace',
                timeout=300  # 5分鐘超時
            )
            
            # 簡化結果處理 - 只檢查JSON是否生成
            self.progress_updated.emit(80, "[DATA] 檢查分析結果...")
            
            # 添加詳細的調試信息
            print(f"[DEBUG] CLI執行完成，退出碼: {result.returncode}")
            if result.stdout:
                print(f"[DEBUG] CLI標準輸出: {result.stdout[-500:]}")  # 只顯示最後500字符
            if result.stderr:
                print(f"[DEBUG] CLI標準錯誤: {result.stderr}")
            
            # 檢查JSON文件是否生成
            cache_key = self.cache_manager.get_cache_key(self.year, self.race, self.session)
            json_file = self.cache_manager.find_cache_file(cache_key)
            
            print(f"[DEBUG] 查找緩存檔案: cache_key={cache_key}, json_file={json_file}")
            
            if json_file:
                print(f"[SUCCESS] 參數化分析完成，JSON已生成: {json_file}")
                return self.cache_manager.load_cache(json_file)
            else:
                # 檢查退出碼，但不依賴print輸出
                if result.returncode != 0:
                    error_msg = f"分析執行失敗 (退出碼: {result.returncode})"
                    if result.stderr:
                        error_msg += f"\n錯誤信息: {result.stderr}"
                    raise Exception(error_msg)
                else:
                    # 顯示更詳細的診斷信息
                    print(f"[DEBUG] JSON目錄內容: {os.listdir('json')}")
                    print(f"[DEBUG] 期望找到包含: {cache_key.replace('rain_analysis_', '')}")
                    raise Exception("分析完成但未找到JSON結果檔案")
                
        except subprocess.TimeoutExpired:
            raise Exception("參數化分析執行超時（超過5分鐘）")
        except Exception as e:
            raise Exception(f"參數化分析失敗: {str(e)}")
    
    def cancel_analysis(self):
        """取消分析操作"""
        self.cancelled = True
        print("[DEBUG] 降雨分析已取消")


class RainAnalysisModule(QWidget):
    """降雨分析模組 - 符合架構文檔"""
    
    def __init__(self, year=2025, race="Japan", session="R", parent=None):
        super().__init__(parent)
        self.year = year
        self.race = race
        self.session = session
        self.current_json_data = None
        self.cache_manager = RainAnalysisCache()
        self.progress_dialog = None
        self.worker = None
        
        self.init_ui()
        
        # 自動開始分析
        self.auto_start_analysis()
    
    def init_ui(self):
        """初始化用戶界面 - 簡化版（僅圖表）"""
        layout = QVBoxLayout(self)
        
        # 移除所有邊距，讓圖表佔滿整個空間
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 只保留通用圖表視窗 - 填滿整個模組空間
        self.chart_widget = UniversalChartWidget(f"降雨分析 - {self.year} {self.race}")
        from PyQt5.QtWidgets import QSizePolicy
        self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # 移除最小尺寸限制，允許完全自由縮放
        # self.chart_widget.setMinimumSize(400, 300) - 已移除
        layout.addWidget(self.chart_widget)
        
        # 隱藏的控制元素（為了代碼兼容性保留，但不顯示）
        self.refresh_button = None
        self.reset_view_button = None
        self.cache_status_label = None
        self.status_label = None
        self.refresh_status_label = None
        self.data_info_label = None
        self.performance_label = None
    
    def safe_update_ui(self, element_name, text):
        """安全更新UI元素文字 - 處理簡化模式"""
        element = getattr(self, element_name, None)
        if element is not None:
            element.setText(text)
        else:
            # 在簡化模式下，將狀態信息輸出到控制台
            print(f"[UI] {element_name}: {text}")
    
    def safe_set_enabled(self, element_name, enabled):
        """安全設置UI元素啟用狀態"""
        element = getattr(self, element_name, None)
        if element is not None:
            element.setEnabled(enabled)
    
    def auto_start_analysis(self):
        """自動開始分析 - 符合架構流程"""
        # 延遲一點時間讓UI完全載入
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, self.start_analysis_workflow)
    
    def start_analysis_workflow(self):
        """開始分析工作流程 - 完整架構實現"""
        print(f"[RAIN] 開始降雨分析工作流程: {self.year} {self.race} {self.session}")
        
        # 創建並顯示進度對話框
        self.progress_dialog = RainAnalysisProgressDialog(self)
        self.progress_dialog.canceled.connect(self.cancel_analysis)
        
        # 創建並配置工作執行緒
        self.worker = RainAnalysisWorker(self.year, self.race, self.session)
        
        # 連接信號
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.analysis_completed.connect(self.on_analysis_completed)
        self.worker.error_occurred.connect(self.on_analysis_error)
        self.worker.cache_status.connect(self.on_cache_status_updated)
        
        # 開始分析
        self.worker.start()
        self.progress_dialog.show()
    
    def on_progress_updated(self, value, message):
        """進度更新處理"""
        if self.progress_dialog:
            self.progress_dialog.update_progress(value, message)
        
        self.safe_update_ui('status_label', message)
    
    def on_cache_status_updated(self, status_message, using_cache):
        """緩存狀態更新"""
        if using_cache:
            self.safe_update_ui('cache_status_label', "使用緩存")
        else:
            self.safe_update_ui('cache_status_label', "新分析")
        
        print(f"[CACHE] {status_message}")
    
    def on_analysis_completed(self, json_data):
        """分析完成處理 - 改進版"""
        print("[OK] 降雨分析完成，開始載入圖表數據...")
        
        # 關閉進度對話框
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # 保存分析結果
        self.current_json_data = json_data
        
        # 載入數據到圖表
        self.load_data_to_chart(json_data)
        
        # 更新UI狀態
        self.safe_update_ui('status_label', "[OK] 分析完成 - 圖表已載入")
        self.safe_set_enabled('refresh_button', True)
        self.safe_set_enabled('reset_view_button', True)
        
        # 顯示數據資訊
        self.update_data_info(json_data)
        
        # 記憶體優化
        self.optimize_memory_usage()
    
    def on_analysis_error(self, error_message):
        """分析錯誤處理 - 符合架構要求"""
        print(f"[ERROR] 降雨分析失敗: {error_message}")
        
        # 關閉進度對話框
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        
        # 顯示錯誤對話框
        self.show_error_dialog(error_message)
        
        # 更新UI狀態
        self.safe_update_ui('status_label', f"[ERROR] 分析失敗: {error_message}")
        self.safe_update_ui('cache_status_label', "[ERROR] 錯誤")
        self.safe_set_enabled('refresh_button', True)
    
    def show_error_dialog(self, error_message):
        """顯示錯誤對話框"""
        error_dialog = QMessageBox(self)
        error_dialog.setIcon(QMessageBox.Critical)
        error_dialog.setWindowTitle("降雨分析錯誤")
        error_dialog.setText("降雨分析過程中發生錯誤")
        error_dialog.setDetailedText(error_message)
        error_dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Retry)
        
        # 添加自定義按鈕
        retry_button = error_dialog.button(QMessageBox.Retry)
        retry_button.setText("重新嘗試")
        
        result = error_dialog.exec_()
        
        if result == QMessageBox.Retry:
            self.force_refresh_analysis()
    
    def cancel_analysis(self):
        """取消分析"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel_analysis()
            self.worker.wait(3000)  # 等待3秒
        
        self.safe_update_ui('status_label', "⏹️ 分析已取消")
        
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
    
    def force_refresh_analysis(self):
        """強制重新分析"""
        # 清除緩存
        cache_key = self.cache_manager.get_cache_key(self.year, self.race, self.session)
        cache_file = self.cache_manager.find_cache_file(cache_key)
        
        if cache_file and os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                print(f"🗑️ 已清除緩存檔案: {os.path.basename(cache_file)}")
            except Exception as e:
                print(f"[WARNING] 清除緩存失敗: {e}")
        
        # 重新開始分析
        self.start_analysis_workflow()
    
    def reset_chart_view(self):
        """重置圖表視圖"""
        if self.chart_widget:
            self.chart_widget.reset_view()
            self.safe_update_ui('refresh_status_label', "視圖已重置 | ")
    
    def force_chart_refresh(self):
        """強制刷新圖表 - 用於MDI視窗大小變化時"""
        if self.chart_widget and self.current_json_data:
            print("[DEBUG] 強制刷新降雨分析圖表")
            # 重新載入數據到圖表
            self.load_data_to_chart(self.current_json_data)
            # 重置視圖
            self.chart_widget.reset_view()
            self.safe_update_ui('refresh_status_label', "圖表已刷新 | ")
    
    def load_data_to_chart(self, json_data):
        """將JSON數據載入到通用圖表 - 支援JSON降雨標記視覺化"""
        try:
            # 清除現有數據
            if hasattr(self.chart_widget, 'clear_data'):
                self.chart_widget.clear_data()
            else:
                print("[WARNING] chart_widget 缺少 clear_data 方法")
            
            # 轉換雨量分析數據為通用圖表格式
            chart_data = self.convert_rain_data_to_chart_format(json_data)
            
            # 載入到通用圖表
            if hasattr(self.chart_widget, 'load_from_json'):
                self.chart_widget.load_from_json(chart_data)
            else:
                print("[WARNING] chart_widget 缺少 load_from_json 方法")
            
            # 【新增】處理JSON降雨標記視覺化 - 符合架構文檔
            self.process_json_rain_markers(json_data, chart_data)
            
            print(f"[OK] 圖表數據載入完成 (含JSON降雨標記)")
            
        except Exception as e:
            error_msg = f"圖表數據載入失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            self.safe_update_ui('status_label', f"[ERROR] {error_msg}")
    
    def process_json_rain_markers(self, json_data, chart_data):
        """處理JSON降雨標記視覺化 - 符合架構文檔規範"""
        try:
            print(f"[DEBUG] 開始處理JSON降雨標記...")
            
            # 從JSON提取降雨標記數據
            rain_markers_data = self.extract_rain_markers_from_json(json_data)
            print(f"[DEBUG] 提取到降雨數據: {rain_markers_data['total_rain_periods']} 個降雨期間")
            
            if rain_markers_data["total_rain_periods"] > 0:
                print(f"[DEBUG] 背景區間數量: {len(rain_markers_data['background_regions'])}")
                print(f"[DEBUG] 標記數量: {len(rain_markers_data['rain_markers'])}")
                
                # 檢查 chart_widget 物件類型和方法
                print(f"[DEBUG] chart_widget 類型: {type(self.chart_widget)}")
                print(f"[DEBUG] chart_widget 類別名稱: {self.chart_widget.__class__.__name__}")
                print(f"[DEBUG] chart_widget 可用方法: {[method for method in dir(self.chart_widget) if 'render_rain' in method]}")
                print(f"[DEBUG] chart_widget 所有方法數量: {len(dir(self.chart_widget))}")
                
                # 檢查具體方法的存在性
                print(f"[DEBUG] hasattr render_rain_background_regions: {hasattr(self.chart_widget, 'render_rain_background_regions')}")
                print(f"[DEBUG] hasattr render_rain_text_markers: {hasattr(self.chart_widget, 'render_rain_text_markers')}")
                
                # 渲染降雨背景區間 
                try:
                    method = getattr(self.chart_widget, 'render_rain_background_regions', None)
                    print(f"[DEBUG] getattr 結果: {method}")
                    if method:
                        print(f"[DEBUG] 呼叫 render_rain_background_regions")
                        method(rain_markers_data["background_regions"])
                        print(f"🎨 已渲染 {len(rain_markers_data['background_regions'])} 個降雨背景區間")
                    else:
                        print(f"[DEBUG] ❌ getattr 返回 None")
                except Exception as e:
                    print(f"[DEBUG] ❌ 呼叫方法時發生錯誤: {e}")
                
                # 不再渲染降雨標記文字 - 只保留顏色區塊
                print(f"[INFO] 略過降雨標記文字渲染 - 只顯示背景顏色區塊")
                
                # 連接降雨區間懸停信號
                if hasattr(self.chart_widget, 'rain_region_hovered'):
                    self.chart_widget.rain_region_hovered.connect(self.on_rain_region_hovered)
            else:
                print(f"[DEBUG] ❌ 沒有檢測到降雨期間")
                print("📝 未檢測到降雨數據，跳過標記渲染")
                
        except Exception as e:
            print(f"[WARNING] JSON降雨標記處理失敗: {e}")
            print(f"[DEBUG] 錯誤詳情: {str(e)}")
    
    def extract_rain_markers_from_json(self, json_data):
        """從JSON數據中提取降雨標記 - 符合架構文檔規範"""
        
        print(f"[DEBUG] 開始從JSON提取降雨標記...")
        
        rain_markers = []
        background_regions = []
        rain_count = 0
        total_points = 0
        
        if "detailed_weather_timeline" in json_data:
            timeline = json_data["detailed_weather_timeline"]
            current_rain_region = None
            
            print(f"[DEBUG] 時間軸數據長度: {len(timeline)}")
            
            for i, entry in enumerate(timeline):
                total_points += 1
                time_point = entry["time_point"]
                rainfall_data = entry["weather_data"]["rainfall"]
                
                is_raining = rainfall_data["is_raining"]
                if is_raining:
                    rain_count += 1
                
                # 每100個點輸出一次統計
                if i % 100 == 0:
                    print(f"[DEBUG] 處理到第 {i} 個時間點，累計降雨點: {rain_count}")
                
                if is_raining:
                    # 降雨開始或持續
                    if current_rain_region is None:
                        # 新降雨區間開始
                        intensity = self.determine_rain_intensity_from_json(rainfall_data)
                        current_rain_region = {
                            "start_time": time_point,
                            "start_index": i,
                            "intensity": intensity,
                            "data_points": [entry]
                        }
                        print(f"[DEBUG] 新降雨區間開始: {time_point}, 強度: {intensity}")
                    else:
                        # 降雨持續，添加數據點
                        current_rain_region["data_points"].append(entry)
                else:
                    # 降雨結束
                    if current_rain_region is not None:
                        current_rain_region["end_time"] = timeline[i-1]["time_point"] if i > 0 else time_point
                        current_rain_region["end_index"] = i-1
                        
                        print(f"[DEBUG] 降雨區間結束: {current_rain_region['start_time']} -> {current_rain_region['end_time']}")
                        print(f"[DEBUG] 數據點數量: {len(current_rain_region['data_points'])}")
                        
                        # 生成背景區間和標記
                        background_region = self.create_background_region(current_rain_region)
                        background_regions.append(background_region)
                        
                        marker = self.create_rain_marker(current_rain_region)
                        rain_markers.append(marker)
                        
                        current_rain_region = None
            
            # 處理到結尾仍在下雨的情況
            if current_rain_region is not None:
                current_rain_region["end_time"] = timeline[-1]["time_point"]
                current_rain_region["end_index"] = len(timeline) - 1
                
                print(f"[DEBUG] 最終降雨區間: {current_rain_region['start_time']} -> {current_rain_region['end_time']}")
                
                background_region = self.create_background_region(current_rain_region)
                background_regions.append(background_region)
                marker = self.create_rain_marker(current_rain_region)
                rain_markers.append(marker)
        else:
            print(f"[DEBUG] ❌ JSON中沒有找到 detailed_weather_timeline")
        
        print(f"[DEBUG] 統計結果:")
        print(f"[DEBUG] - 總時間點: {total_points}")
        print(f"[DEBUG] - 降雨時間點: {rain_count}")
        print(f"[DEBUG] - 降雨比例: {rain_count/total_points*100:.1f}%")
        print(f"[DEBUG] - 背景區間數: {len(background_regions)}")
        print(f"[DEBUG] - 標記數量: {len(rain_markers)}")
        
        return {
            "rain_markers": rain_markers,
            "background_regions": background_regions,
            "total_rain_periods": len(rain_markers)
        }
    
    def create_background_region(self, rain_region):
        """創建圖表背景顏色區間 - 符合架構文檔規範"""
        intensity = rain_region["intensity"]
        
        print(f"[DEBUG] 創建背景區間: 強度={intensity}, 時間={rain_region['start_time']}->{rain_region['end_time']}")
        
        # 降雨強度背景顏色映射 - 新配色方案
        intensity_colors = {
            "light": "rgba(144, 238, 144, 0.3)",      # 淺綠色 30% 透明度
            "droplet": "rgba(144, 238, 144, 0.3)",    # 淺綠色 30% 透明度
            "moderate": "rgba(173, 216, 230, 0.3)",   # 淺藍色 30% 透明度
            "shower": "rgba(173, 216, 230, 0.3)",     # 淺藍色 30% 透明度
            "heavy": "rgba(221, 160, 221, 0.3)",      # 淺紫色 30% 透明度
            "storm": "rgba(221, 160, 221, 0.3)"       # 淺紫色 30% 透明度
        }
        
        selected_color = intensity_colors.get(intensity, intensity_colors["light"])
        print(f"[DEBUG] 選擇顏色: {selected_color}")
        
        background_region = {
            "type": "background_region",
            "start_time": rain_region["start_time"],
            "end_time": rain_region["end_time"],
            "color": selected_color,
            "intensity": intensity,
            "data_points_count": len(rain_region["data_points"]),
            "label": "",  # 移除標籤顯示，只保留背景顏色
            "description": f"降雨強度: {intensity} ({len(rain_region['data_points'])} 數據點)"
        }
        
        print(f"[DEBUG] 背景區間創建完成: {background_region}")
        return background_region
    
    def create_rain_marker(self, rain_region):
        """創建降雨標記文字 - 符合架構文檔規範"""
        intensity = rain_region["intensity"]
        
        # 降雨強度標記符號 - 擴展版本
        intensity_symbols = {
            "light": "[DROPLET]",
            "droplet": "[DROPLET]",
            "moderate": "[SHOWER]",
            "shower": "[SHOWER]", 
            "heavy": "[STORM]",
            "storm": "[STORM]"
        }
        
        return {
            "type": "rain_marker",
            "time_position": rain_region["start_time"],
            "text": intensity_symbols.get(intensity, "[DROPLET]"),
            "intensity": intensity,
            "duration": f"{rain_region['start_time']} - {rain_region['end_time']}",
            "tooltip": f"降雨期間: {rain_region['start_time']} 至 {rain_region['end_time']}\\n強度: {intensity}"
        }
    
    def on_rain_region_hovered(self, region_info):
        """處理降雨區間懸停事件 - 符合架構文檔規範"""
        # 顯示降雨強度詳細信息
        self.safe_update_ui('status_label', f"降雨區間: {region_info['duration']} | 強度: {region_info['intensity']}")
        print(f"💧 懸停於降雨區間: 強度={region_info['intensity']}, 持續時間={region_info['duration']}")
    
    def convert_rain_data_to_chart_format(self, rain_json_data):
        """將雨量分析JSON轉換為通用圖表格式 - 符合架構規範"""
        try:
            print(f"開始數據格式轉換...")
            
            # 檢查數據完整性
            if "detailed_weather_timeline" not in rain_json_data:
                raise ValueError("JSON數據中缺少detailed_weather_timeline字段")
            
            timeline_data = rain_json_data["detailed_weather_timeline"]
            
            if not timeline_data or len(timeline_data) == 0:
                raise ValueError("detailed_weather_timeline數據為空")
            
            print(f"處理 {len(timeline_data)} 個天氣數據點")
            
            # [DEBUG] 顯示JSON前10筆原始數據
            print(f"[DEBUG] JSON原始數據 (前10筆):")
            for i, entry in enumerate(timeline_data[:10]):
                time_str = entry.get('time_point', 'N/A')
                weather_data = entry.get('weather_data', {})
                temp = weather_data.get('air_temperature', {}).get('value', 'N/A')
                wind = weather_data.get('wind_speed', {}).get('value', 'N/A')
                rainfall = weather_data.get('rainfall', {})
                is_raining = rainfall.get('is_raining', False)
                rain_status = rainfall.get('status', 'unknown')
                print(f"   [{i}] time: {time_str}, temp: {temp}°C, wind: {wind}m/s, rain: {is_raining} ({rain_status})")
            
            # 數據提取和處理
            x_data, temp_data, wind_speed_data, rain_periods = self.extract_weather_data(timeline_data)
            
            # 數據抽樣 - 使用當前圖表的間距設定
            interval_minutes = getattr(self.chart_widget, 'x_axis_interval_minutes', 15)
            x_data, temp_data, wind_speed_data = self.sample_data_by_interval(
                x_data, temp_data, wind_speed_data, interval_minutes=interval_minutes
            )
            
            # 數據驗證
            self.validate_extracted_data(x_data, temp_data, wind_speed_data)
            
            # 構建圖表數據
            chart_data = {
                "chart_title": f"降雨分析 - {self.year} {self.race} ({self.session})",
                "x_axis": {
                    "label": "比賽時間",
                    "unit": "秒",
                    "data": x_data
                },
                "left_y_axis": {
                    "label": "氣溫",
                    "unit": "°C",
                    "data": temp_data
                },
                "right_y_axis": {
                    "label": "風速",
                    "unit": "km/h", 
                    "data": wind_speed_data
                },
                "annotations": self.create_rain_annotations(rain_periods)
            }
            
            print(f"[OK] 數據轉換完成:")
            print(f"   [CHART] 時間範圍: {min(x_data):.1f}s - {max(x_data):.1f}s")
            print(f"   [TEMP] 溫度範圍: {min(temp_data):.1f}°C - {max(temp_data):.1f}°C")
            print(f"   [WIND] 風速範圍: {min(wind_speed_data):.1f}km/h - {max(wind_speed_data):.1f}km/h")
            print(f"   [RAIN] 降雨期間: {len(rain_periods)} 個")
            
            # [DEBUG] 顯示前10筆數據
            print(f"\n[DEBUG] 前10筆轉換數據:")
            for i in range(min(10, len(x_data))):
                print(f"   [{i}] 時間: {x_data[i]:.2f}s, 溫度: {temp_data[i]:.1f}°C, 風速: {wind_speed_data[i]:.1f}km/h")
            
            return chart_data
            
        except Exception as e:
            print(f"[ERROR] 數據轉換失敗: {e}")
            return self.create_fallback_chart_data()
    
    def extract_weather_data(self, timeline_data):
        """提取天氣數據 - 改進版，X軸從0開始"""
        x_data = []
        temp_data = []
        wind_speed_data = []
        rain_periods = []
        
        current_rain_start = None
        first_time_offset = None  # 記錄第一個時間點，用於計算相對時間
        
        for i, entry in enumerate(timeline_data):
            try:
                # 時間解析
                time_str = entry.get("time_point", f"{i}:00.000")
                total_seconds = self.parse_time_string(time_str, i)
                
                # 設定時間基準：第一個數據點作為0秒
                if first_time_offset is None:
                    first_time_offset = total_seconds
                
                # 計算相對時間（從0開始）
                relative_time = total_seconds - first_time_offset
                x_data.append(relative_time)
                
                # 天氣數據提取
                weather = entry.get("weather_data", {})
                
                # 溫度處理
                air_temp = weather.get("air_temperature", {}).get("value", 20.0)
                temp_data.append(float(air_temp))
                
                # 風速處理 (m/s -> km/h)
                wind_speed_ms = weather.get("wind_speed", {}).get("value", 0.0)
                wind_speed_kmh = float(wind_speed_ms) * 3.6
                wind_speed_data.append(wind_speed_kmh)
                
                # 降雨檢測和強度分析 - 新增JSON降雨標記功能
                rainfall_data = weather.get("rainfall", {})
                is_raining = rainfall_data.get("is_raining", False)
                
                # 提取降雨強度信息 - 符合架構文檔規範
                rain_intensity = self.determine_rain_intensity_from_json(rainfall_data)
                
                rain_periods = self.process_rain_detection_with_intensity(
                    is_raining, relative_time, current_rain_start, rain_periods, rain_intensity
                )
                
                if is_raining and current_rain_start is None:
                    current_rain_start = {"time": relative_time, "intensity": rain_intensity}
                elif not is_raining and current_rain_start is not None:
                    current_rain_start = None
                    
            except Exception as e:
                print(f"[WARNING] 處理第{i}個數據點時出錯: {e}")
                continue
        
        # 處理未結束的降雨
        if current_rain_start is not None and x_data:
            rain_periods.append({
                "start_x": current_rain_start["time"],
                "end_x": x_data[-1],
                "intensity": current_rain_start["intensity"],
                "label": "降雨期間"
            })
        
        return x_data, temp_data, wind_speed_data, rain_periods
    
    def parse_time_string(self, time_str, fallback_index):
        """解析時間字符串"""
        try:
            time_parts = time_str.split(":")
            
            if len(time_parts) == 2:
                # 格式: "MM:SS.mmm"
                minutes = int(time_parts[0])
                seconds_parts = time_parts[1].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                return minutes * 60 + seconds + milliseconds / 1000.0
            
            elif len(time_parts) == 3:
                # 格式: "H:MM:SS.mmm"
                hours = int(time_parts[0])
                minutes = int(time_parts[1])
                seconds_parts = time_parts[2].split(".")
                seconds = int(seconds_parts[0])
                milliseconds = int(seconds_parts[1]) if len(seconds_parts) > 1 else 0
                return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000.0
            
        except:
            pass
        
        # 備用方案
        return fallback_index * 10  # 每10秒一個數據點
    
    def sample_data_by_interval(self, x_data, temp_data, wind_speed_data, interval_minutes=15):
        """按指定時間間距抽樣數據 - 從0開始"""
        if not x_data or len(x_data) == 0:
            return x_data, temp_data, wind_speed_data
        
        interval_seconds = interval_minutes * 60  # 轉換為秒
        
        # 找到數據的起始和結束時間
        start_time = min(x_data)
        end_time = max(x_data)
        
        # 計算抽樣時間點 - 從0或最接近0的整數倍開始
        sample_times = []
        # 確保從0開始對齊到間距
        current_time = 0  # 直接從0開始
        
        while current_time <= end_time:
            if current_time >= start_time:
                sample_times.append(current_time)
            current_time += interval_seconds
        
        # 為每個抽樣時間點找到最接近的數據
        sampled_x = []
        sampled_temp = []
        sampled_wind = []
        
        for target_time in sample_times:
            # 找到最接近的數據點
            closest_index = 0
            min_diff = abs(x_data[0] - target_time)
            
            for i, actual_time in enumerate(x_data):
                diff = abs(actual_time - target_time)
                if diff < min_diff:
                    min_diff = diff
                    closest_index = i
            
            # 只有當差距在合理範圍內才添加數據點 (不超過間距的一半)
            if min_diff <= interval_seconds / 2:
                sampled_x.append(target_time)  # 使用目標時間以保持間距一致
                sampled_temp.append(temp_data[closest_index])
                sampled_wind.append(wind_speed_data[closest_index])
        
        print(f"[SAMPLE] 原始數據點: {len(x_data)} → 抽樣後: {len(sampled_x)} (間距: {interval_minutes}分鐘)")
        return sampled_x, sampled_temp, sampled_wind
    
    def process_rain_detection(self, is_raining, total_seconds, current_rain_start, rain_periods):
        """處理降雨檢測邏輯 - 保持向後兼容"""
        return self.process_rain_detection_with_intensity(
            is_raining, total_seconds, current_rain_start, rain_periods, "light"
        )
    
    def process_rain_detection_with_intensity(self, is_raining, total_seconds, current_rain_start, rain_periods, intensity):
        """處理降雨檢測邏輯 - 支援強度分析"""
        # 這個方法可以在子類中覆寫以實現更複雜的降雨檢測邏輯
        return rain_periods
    
    def determine_rain_intensity_from_json(self, rainfall_data):
        """從JSON降雨數據中判斷降雨強度 - 擴展支援所有強度類型"""
        
        # 檢查描述字段中的強度關鍵字
        description = rainfall_data.get("description", "").lower()
        status = rainfall_data.get("status", "").lower()
        
        print(f"[DEBUG] 判斷降雨強度: description='{description}', status='{status}'")
        
        # 強度判斷邏輯 - 擴展版本
        if any(keyword in description for keyword in ["heavy", "暴雨", "大雨"]):
            intensity = "heavy"
        elif any(keyword in description for keyword in ["storm", "雷暴", "風暴"]):
            intensity = "storm"
        elif any(keyword in description for keyword in ["moderate", "中雨"]):
            intensity = "moderate"
        elif any(keyword in description for keyword in ["shower", "陣雨"]):
            intensity = "shower"
        elif any(keyword in description for keyword in ["light", "毛毛雨", "輕微", "小雨"]):
            intensity = "light"
        elif any(keyword in description for keyword in ["droplet", "水滴", "細雨"]):
            intensity = "droplet"
        elif status == "wet":
            intensity = "light"  # 默認為輕微降雨
        else:
            intensity = "light"  # 默認強度
        
        print(f"[DEBUG] 強度判斷結果: {intensity}")
        return intensity
    
    def create_rain_annotations(self, rain_periods):
        """創建降雨標註 - 支援JSON降雨標記視覺化"""
        annotations = []
        
        for i, rain_period in enumerate(rain_periods):
            duration = rain_period["end_x"] - rain_period["start_x"]
            
            # 確定降雨強度 (如果有的話)
            intensity = rain_period.get("intensity", "light")
            
            # 根據降雨強度決定顏色和標記 - 符合架構文檔規範
            intensity_config = self.get_rain_intensity_config(intensity, duration)
            
            annotation = {
                "type": "rain_background",
                "start_x": rain_period["start_x"],
                "end_x": rain_period["end_x"],
                "label": intensity_config["label"],
                "color": intensity_config["background_color"],
                "intensity": intensity,
                "duration": duration,
                "description": f"降雨期間: {rain_period['start_x']:.0f}s 至 {rain_period['end_x']:.0f}s\\n強度: {intensity}\\n持續時間: {duration:.0f}s"
            }
            annotations.append(annotation)
            
            # 添加降雨標記符號 - 在降雨區間開始處
            marker_annotation = {
                "type": "rain_marker",
                "x_position": rain_period["start_x"],
                "text": intensity_config["marker_symbol"],
                "intensity": intensity,
                "marker_style": {
                    "background_color": intensity_config["marker_bg"],
                    "text_color": intensity_config["marker_text"],
                    "border": "1px solid #333",
                    "border_radius": "4px",
                    "padding": "2px 6px",
                    "font_size": 10,
                    "font_weight": "bold"
                },
                "tooltip": f"降雨標記\\n強度: {intensity}\\n持續時間: {duration:.0f}s"
            }
            annotations.append(marker_annotation)
        
        print(f"[RAIN_ANNOTATIONS] 已創建 {len(rain_periods)} 個降雨背景區間和 {len(rain_periods)} 個標記符號")
        return annotations
    
    def get_rain_intensity_config(self, intensity, duration):
        """獲取降雨強度配置 - 符合架構文檔規範"""
        
        # 降雨強度顏色配置 - 新配色方案
        intensity_configs = {
            "light": {
                "background_color": "rgba(144, 238, 144, 0.3)",  # 淺綠色 30% 透明度
                "marker_symbol": "[DROPLET]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#333",
                "label": "輕微降雨"
            },
            "droplet": {
                "background_color": "rgba(144, 238, 144, 0.3)",  # 淺綠色 30% 透明度
                "marker_symbol": "[DROPLET]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#333",
                "label": "水滴降雨"
            },
            "moderate": {
                "background_color": "rgba(173, 216, 230, 0.3)",  # 淺藍色 30% 透明度
                "marker_symbol": "[SHOWER]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#000",
                "label": "中等降雨"
            },
            "shower": {
                "background_color": "rgba(173, 216, 230, 0.3)",  # 淺藍色 30% 透明度
                "marker_symbol": "[SHOWER]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#000",
                "label": "陣雨"
            },
            "heavy": {
                "background_color": "rgba(221, 160, 221, 0.3)",  # 淺紫色 30% 透明度
                "marker_symbol": "[STORM]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#000",
                "label": "強烈降雨"
            },
            "storm": {
                "background_color": "rgba(221, 160, 221, 0.3)",  # 淺紫色 30% 透明度
                "marker_symbol": "[STORM]",
                "marker_bg": "rgba(255, 255, 255, 0.9)",
                "marker_text": "#000",
                "label": "風暴"
            }
        }
        
        # 如果沒有指定強度，根據持續時間判斷
        if intensity not in intensity_configs:
            if duration > 300:  # 5分鐘以上
                intensity = "heavy"
            elif duration > 60:  # 1分鐘以上
                intensity = "moderate"
            else:
                intensity = "light"
        
        config = intensity_configs.get(intensity, intensity_configs["light"])
        config["label"] += f" ({duration:.0f}s)"
        
        return config
    
    def validate_extracted_data(self, x_data, temp_data, wind_speed_data):
        """驗證提取的數據"""
        if len(x_data) == 0:
            raise ValueError("無有效的時間數據")
        
        if len(temp_data) != len(x_data):
            raise ValueError(f"溫度數據長度不匹配: {len(temp_data)} vs {len(x_data)}")
        
        if len(wind_speed_data) != len(x_data):
            raise ValueError(f"風速數據長度不匹配: {len(wind_speed_data)} vs {len(x_data)}")
        
        # 檢查數據範圍合理性
        if min(temp_data) < -50 or max(temp_data) > 80:
            print("[WARNING] 溫度數據範圍異常")
        
        if min(wind_speed_data) < 0 or max(wind_speed_data) > 200:
            print("[WARNING] 風速數據範圍異常")
    
    def create_fallback_chart_data(self):
        """創建備用圖表數據"""
        print("使用備用圖表數據...")
        
        # 使用當前圖表的間距設定
        interval_minutes = getattr(self.chart_widget, 'x_axis_interval_minutes', 15)
        interval_seconds = interval_minutes * 60
        
        # 生成1小時的數據，按間距
        x_data = list(range(0, 3600, interval_seconds))
        data_points = len(x_data)
        
        return {
            "chart_title": f"降雨分析 - {self.year} {self.race} (模擬數據)",
            "x_axis": {
                "label": "比賽時間",
                "unit": "秒", 
                "data": x_data
            },
            "left_y_axis": {
                "label": "氣溫",
                "unit": "°C",
                "data": [20 + (i % 10) * 0.5 for i in range(data_points)]
            },
            "right_y_axis": {
                "label": "風速", 
                "unit": "km/h",
                "data": [15 + (i % 8) * 2 for i in range(data_points)]
            },
            "annotations": [
                {"type": "rain", "start_x": 600, "end_x": 900, "label": "模擬降雨", "color": "blue"}
            ]
        }
    
    def update_data_info(self, json_data):
        """更新數據資訊顯示"""
        try:
            timeline_data = json_data.get("detailed_weather_timeline", [])
            data_points = len(timeline_data)
            
            # 計算時間範圍
            if timeline_data:
                first_time = timeline_data[0].get("time_point", "0:00.000")
                last_time = timeline_data[-1].get("time_point", "0:00.000")
                self.safe_update_ui('data_info_label',
                    f"數據點: {data_points} | ⏱️ 時間範圍: {first_time} - {last_time}"
                )
            else:
                self.safe_update_ui('data_info_label', "無可用數據")
                
        except Exception as e:
            self.safe_update_ui('data_info_label', f"數據資訊獲取失敗: {e}")
    
    def optimize_memory_usage(self):
        """記憶體優化 - 符合架構要求"""
        try:
            # 清理不需要的數據
            if hasattr(self, 'worker') and self.worker:
                if not self.worker.isRunning():
                    self.worker.deleteLater()
                    self.worker = None
            
            # 強制垃圾回收
            gc.collect()
            
            print("🧹 記憶體優化完成")
            
        except Exception as e:
            print(f"[WARNING] 記憶體優化失敗: {e}")


if __name__ == "__main__":
    # 測試代碼 - 2025 Japan Race 案例
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建降雨分析模組 - 使用指定的測試案例
    rain_module = RainAnalysisModule(year=2025, race="Japan", session="R")
    rain_module.show()
    rain_module.resize(1200, 800)
    
    print("[RAIN] 降雨分析模組測試 - 2025 Japan Race")
    print("   - 完全符合架構文檔規範")
    print("   - 智能緩存管理")
    print("   - 完整錯誤處理")
    print("   - 性能優化")
    
    sys.exit(app.exec_())
