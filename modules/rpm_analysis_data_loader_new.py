#!/usr/bin/env python3
"""
F1T RPM分析數據載入器
基於速度分析數據載入器的成功架構
負責RPM數據的獲取、處理和格式化
"""

import sys
import os
import json
import glob
import subprocess
import pickle
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer
from PyQt5.QtWidgets import QMessageBox, QApplication

class RPMAnalysisDataLoader(QObject):
    """RPM分析數據載入器"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)  # 數據載入完成信號
    loading_progress = pyqtSignal(str, int)  # 載入進度信號 (message, percentage)
    loading_error = pyqtSignal(str)  # 載入錯誤信號
    load_error = pyqtSignal(str)  # 載入錯誤信號 (與speed模組統一)
    status_changed = pyqtSignal(str)  # 狀態變更信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 配置設定
        self.main_script_path = "f1_analysis_modular_main.py"
        self.cache_dir = "f1_analysis_cache"
        
        # 狀態變數
        self.current_session = None
        self.last_error = None
        self._is_loading = False
        self._current_data = None
        
        # 確保緩存目錄存在
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self):
        """確保緩存目錄存在"""
        try:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
                print(f"[RPM_LOADER] 📁 創建緩存目錄: {self.cache_dir}")
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 創建緩存目錄失敗: {e}")
    
    def load_rpm_analysis_data(self, session_info: Dict[str, Any]) -> None:
        """
        載入RPM分析數據
        
        Args:
            session_info: 包含年份、賽事、車手等信息的字典
                必須包含：year, race, driver1, driver2, lap1, lap2
        """
        try:
            print(f"[RPM_LOADER] 🔄 開始載入RPM分析數據...")
            
            # 驗證參數
            if not self._validate_session_info(session_info):
                return
                
            self.current_session = session_info
            self._is_loading = True
            
            # 發出載入開始信號
            self.loading_progress.emit("正在準備RPM數據載入...", 5)
            
            # 提取參數
            year = session_info.get('year')
            race = session_info.get('race')
            session = session_info.get('session', 'R')
            driver1 = session_info.get('driver1')
            driver2 = session_info.get('driver2')
            lap1 = session_info.get('lap1', 1)
            lap2 = session_info.get('lap2', 1)
            
            print(f"[RPM_LOADER] 📋 載入參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 策略1: 尋找現有的 JSON 檔案
            json_file = self._find_rpm_data_file(year, race, session, driver1, driver2, lap1, lap2)
            print(f"[RPM_LOADER] 搜尋結果: {json_file}")
            
            if json_file:
                print(f"[RPM_LOADER] ✅ 找到現有檔案，準備載入")
                # 使用 QTimer 模擬異步載入
                QTimer.singleShot(10, lambda: self._load_json_file(json_file))
                return
            
            print(f"[RPM_LOADER] ❌ 找不到現有 JSON，開始生成新檔案")
            
            # 策略2: 呼叫 CLI 生成 JSON (異步)
            self._start_cli_generation(year, race, session, driver1, driver2, lap1, lap2)
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 載入RPM數據失敗: {e}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False

    def _find_rpm_data_file(self, year: int, race: str, session: str, 
                           driver1: str, driver2: str = None, 
                           lap1: int = 1, lap2: int = 1) -> str:
        """尋找對應的RPM數據檔案"""
        try:
            print(f"[JSON_SEARCH] 🔍 開始搜尋RPM數據檔案...")
            print(f"[JSON_SEARCH] 參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 定義搜尋目錄（按優先級排序）
            search_dirs = [
                "json",
                "json_exports", 
                "cache",
                f"cache/{year}",
                "."
            ]
            
            # 定義檔案名稱模式（按優先級排序）
            filename_patterns = [
                # 精確匹配模式
                f"comparison_telemetry_{year}_{race}_{session}_{driver1}_{driver2}_*.json",
                f"comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_*.json",
                f"telemetry_comparison_{year}_{race}_{session}_{driver1}_{driver2}_*.json",
                
                # 通用匹配模式
                f"*telemetry*{year}*{race}*{session}*{driver1}*{driver2}*.json",
                f"*comparison*{year}*{race}*{session}*{driver1}*{driver2}*.json",
                f"*{year}*{race}*{session}*telemetry*.json",
                f"*{year}*{race}*{session}*comparison*.json"
            ]
            
            print(f"[JSON_SEARCH] 📂 搜尋目錄清單:")
            for i, search_dir in enumerate(search_dirs, 1):
                print(f"[JSON_SEARCH]   {i}. {search_dir}")
            
            print(f"[JSON_SEARCH] 📝 檔案模式清單:")
            for i, pattern in enumerate(filename_patterns, 1):
                print(f"[JSON_SEARCH]   {i}. {pattern}")
            
            # 精確搜尋
            print(f"[JSON_SEARCH] 🔍 開始精確搜尋...")
            found_file = None
            
            for search_dir in search_dirs:
                print(f"[JSON_SEARCH] 📂 搜尋目錄: {search_dir}")
                
                # 按順序搜尋各種模式
                for i, filename_pattern in enumerate(filename_patterns, 1):
                    search_pattern = os.path.join(search_dir, filename_pattern)
                    print(f"[JSON_SEARCH]   🔍 模式 {i}: {search_pattern}")
                    matches = glob.glob(search_pattern)
                    
                    if matches:
                        # 如果有多個匹配，選擇最新的
                        found_file = max(matches, key=os.path.getmtime)
                        print(f"[JSON_SEARCH] ✅ 找到檔案: {found_file}")
                        print(f"[JSON_SEARCH] 📊 匹配檔案數量: {len(matches)}")
                        if len(matches) > 1:
                            print(f"[JSON_SEARCH] 📋 所有匹配檔案:")
                            for match in matches:
                                print(f"[JSON_SEARCH]     - {match}")
                        break
                    else:
                        print(f"[JSON_SEARCH]   ❌ 模式 {i} 無匹配")
                
                # 如果找到檔案就跳出目錄循環
                if found_file:
                    break
                
                print(f"[JSON_SEARCH] ❌ 目錄 {search_dir} 無匹配檔案")
            
            if found_file:
                print(f"[JSON_SEARCH] ✅ 搜尋成功: {found_file}")
                return found_file
            
            # 精確搜尋失敗，直接生成新檔案
            print(f"[JSON_SEARCH] ❌ 未找到符合的JSON檔案，需要生成新檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 搜尋檔案時發生錯誤: {str(e)}")
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None

    def _start_cli_generation(self, year: int, race: str, session: str,
                             driver1: str, driver2: str = None,
                             lap1: int = 1, lap2: int = 1):
        """啟動 CLI 生成流程"""
        try:
            print(f"[RPM_LOADER] 🚀 啟動 CLI 生成流程...")
            print(f"[RPM_LOADER] 參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 儲存生成參數以供監控使用
            self._generation_params = (year, race, session, driver1, driver2, lap1, lap2)
            
            # 構建 CLI 命令
            cmd = [
                sys.executable,
                "f1_analysis_modular_main.py",
                "-f", "13",  # Function 13: 遙測比較
                "-y", str(year),
                "-r", race,
                "-s", session,
                "-d", driver1,
                "-d2", driver2,
                "-l", str(lap1),
                "-l2", str(lap2)
            ]
            
            print(f"[RPM_LOADER] 📝 CLI 命令: {' '.join(cmd)}")
            
            # 啟動檔案生成監控
            self._start_generation_monitoring()
            
            # 異步執行 CLI 命令
            self.loading_progress.emit("正在生成RPM數據...", 30)
            
            # 在背景執行 CLI 命令
            subprocess.Popen(cmd, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           text=True,
                           cwd=".")
            
            print(f"[RPM_LOADER] ✅ CLI 命令已啟動，開始監控檔案生成...")
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 啟動 CLI 生成失敗: {str(e)}")
            self.load_error.emit(f"生成數據失敗: {str(e)}")
            self._is_loading = False
    
    def _start_generation_monitoring(self):
        """啟動檔案生成監控"""
        # 初始化定時器
        if not hasattr(self, '_generation_timer'):
            self._generation_timer = QTimer()
            self._generation_timer.timeout.connect(self._check_generation_progress)
        
        if not hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer = QTimer()
            self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)
        self.status_changed.emit("正在生成數據，請稍候...")
        
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        if hasattr(self, '_generation_params'):
            year, race, session, driver1, driver2, lap1, lap2 = self._generation_params
            
            # 檢查是否有新檔案生成
            json_file = self._find_rpm_data_file(year, race, session, driver1, driver2, lap1, lap2)
            
            if json_file:
                print(f"[OK] [RPM_LOADER] 檔案生成完成: {json_file}")
                
                # 停止監控
                self._stop_generation_monitoring()
                
                # 載入新生成的檔案
                QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            else:
                print(f"⏳ [RPM_LOADER] 繼續等待檔案生成...")
                
    def _on_generation_timeout(self):
        """處理生成超時"""
        print(f"[TIMEOUT] [RPM_LOADER] 檔案生成超時")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或重試")
        self._is_loading = False
        
    def _stop_generation_monitoring(self):
        """停止檔案生成監控"""
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()

    def _load_json_file(self, file_path: str):
        """載入 JSON 檔案"""
        try:
            print(f"[RPM_LOADER] ========== JSON 檔案載入 ==========")
            print(f"[RPM_LOADER] 載入檔案: {file_path}")
            
            # 檢查檔案狀態
            if not os.path.exists(file_path):
                print(f"[RPM_LOADER] ❌ 檔案不存在: {file_path}")
                self.load_error.emit(f"檔案不存在: {file_path}")
                return
                
            file_size = os.path.getsize(file_path)
            print(f"[RPM_LOADER] 檔案大小: {file_size} bytes")
            
            self.loading_progress.emit("正在處理數據...", 90)
            self.status_changed.emit("正在處理數據...")
            
            # 載入JSON檔案
            print(f"[RPM_LOADER] 開始讀取 JSON 內容...")
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print(f"[RPM_LOADER] JSON 載入成功")
            print(f"[RPM_LOADER] 頂層鍵值: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
            
            # 驗證數據格式
            print(f"[RPM_LOADER] 開始驗證數據格式...")
            if self._validate_rpm_data(raw_data):
                print(f"[RPM_LOADER] ✅ 數據格式驗證通過")
                # 處理為RPM分析格式
                processed_data = self._process_rpm_data(raw_data)
                
                print(f"[RPM_LOADER] ========== 即將發送數據 ==========")
                print(f"[RPM_LOADER] 處理後數據類型: {type(processed_data)}")
                print(f"[RPM_LOADER] 處理後數據鍵值: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
                
                if 'rpm_data' in processed_data:
                    rpm_data = processed_data['rpm_data']
                    print(f"[RPM_LOADER] RPM數據鍵值: {list(rpm_data.keys())}")
                    print(f"[RPM_LOADER] 距離數據點數: {len(rpm_data.get('distance', []))}")
                    print(f"[RPM_LOADER] 車手1 RPM點數: {len(rpm_data.get('driver1_rpm', []))}")
                    print(f"[RPM_LOADER] 車手2 RPM點數: {len(rpm_data.get('driver2_rpm', []))}")
                
                self.loading_progress.emit("數據載入完成", 100)
                self.status_changed.emit("數據載入完成")
                self._current_data = processed_data
                self._is_loading = False
                
                print(f"[RPM_LOADER] 🚀 即將發送 data_loaded 信號...")
                self.data_loaded.emit(processed_data)
                print(f"[RPM_LOADER] ✅ data_loaded 信號已發送")
                
            else:
                print(f"[RPM_LOADER] ❌ 數據格式驗證失敗")
                self.load_error.emit("數據格式驗證失敗")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] JSON 檔案載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False

    def _validate_rpm_data(self, raw_data: dict) -> bool:
        """驗證RPM數據格式"""
        try:
            print(f"[RPM_LOADER] 🔍 驗證數據格式...")
            
            # 檢查基本結構
            if not isinstance(raw_data, dict):
                print(f"[RPM_LOADER] ❌ 數據不是字典格式")
                return False
            
            # 檢查是否有遙測比較數據
            if 'results' not in raw_data:
                print(f"[RPM_LOADER] ❌ 缺少 results 字段")
                return False
                
            results = raw_data['results']
            if 'telemetry_comparison' not in results:
                print(f"[RPM_LOADER] ❌ 缺少 telemetry_comparison 字段")
                return False
                
            telemetry_comp = results['telemetry_comparison']
            if 'RPM' not in telemetry_comp:
                print(f"[RPM_LOADER] ❌ 缺少 RPM 字段")
                return False
            
            rpm_data = telemetry_comp['RPM']
            required_fields = ['driver1_data', 'driver2_data', 'distance']
            
            for field in required_fields:
                if field not in rpm_data:
                    print(f"[RPM_LOADER] ❌ RPM數據缺少必需字段: {field}")
                    return False
                
                if not isinstance(rpm_data[field], list):
                    print(f"[RPM_LOADER] ❌ {field} 不是列表格式")
                    return False
            
            # 檢查數據長度一致性
            driver1_len = len(rpm_data['driver1_data'])
            driver2_len = len(rpm_data['driver2_data'])
            distance_len = len(rpm_data['distance'])
            
            print(f"[RPM_LOADER] 數據長度檢查: driver1={driver1_len}, driver2={driver2_len}, distance={distance_len}")
            
            if not (driver1_len == driver2_len == distance_len):
                print(f"[RPM_LOADER] ⚠️ 數據長度不一致，但仍可嘗試處理")
            
            print(f"[RPM_LOADER] ✅ 數據格式驗證通過")
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 數據格式驗證失敗: {str(e)}")
            return False

    def _process_rpm_data(self, raw_data: dict) -> dict:
        """處理原始數據為RPM分析格式"""
        try:
            print(f"[RPM_LOADER] ========== 數據處理 ==========")
            print(f"[RPM_LOADER] 開始處理原始數據...")
            
            # 檢查數據格式類型
            if raw_data.get('analysis_type') == 'two_driver_telemetry_comparison':
                # 新格式：comparison_telemetry JSON
                print(f"[RPM_LOADER] 📊 處理新格式數據")
                return self._process_new_format_rpm_data(raw_data)
            else:
                # 舊格式：function 13 直接輸出
                print(f"[RPM_LOADER] 📊 處理舊格式數據")
                return self._process_old_format_rpm_data(raw_data)
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 數據處理失敗: {str(e)}")
            raise

    def _process_new_format_rpm_data(self, raw_data: dict) -> dict:
        """處理新格式的遙測比較數據"""
        try:
            print(f"[RPM_LOADER] ========== 解析新格式遙測數據 ==========")
            
            metadata = raw_data.get('metadata', {})
            results = raw_data.get('results', {})
            comparison_info = results.get('comparison_info', {})
            telemetry_comparison = results.get('telemetry_comparison', {})
            
            print(f"[RPM_LOADER] 元數據: {metadata}")
            print(f"[RPM_LOADER] 比較信息: {comparison_info}")
            print(f"[RPM_LOADER] 遙測比較鍵值: {list(telemetry_comparison.keys())}")
            
            # 提取RPM數據
            rpm_data = telemetry_comparison.get('RPM', {})
            driver1_rpm = rpm_data.get('driver1_data', [])
            driver2_rpm = rpm_data.get('driver2_data', [])
            distance_data = rpm_data.get('distance', [])
            
            print(f"[RPM_LOADER] 車手1 RPM數據點數: {len(driver1_rpm)}")
            print(f"[RPM_LOADER] 車手2 RPM數據點數: {len(driver2_rpm)}")
            print(f"[RPM_LOADER] 距離數據點數: {len(distance_data)}")
            
            # 顯示一些樣本數據
            if driver1_rpm:
                print(f"[RPM_LOADER] 車手1 RPM樣本: {driver1_rpm[:5]} ... {driver1_rpm[-5:]}")
            if driver2_rpm:
                print(f"[RPM_LOADER] 車手2 RPM樣本: {driver2_rpm[:5]} ... {driver2_rpm[-5:]}")
            if distance_data:
                print(f"[RPM_LOADER] 距離樣本: {distance_data[:5]} ... {distance_data[-5:]}")
            
            # 構建處理後的數據結構
            processed = {
                'metadata': {
                    'analysis_type': 'rpm_comparison',
                    'drivers': [
                        {
                            'code': comparison_info.get('driver1', 'Unknown'),
                            'lap_time': comparison_info.get('lap_time1', 'N/A'),
                            'compound': comparison_info.get('compound1', 'Unknown'),
                            'tyre_life': comparison_info.get('tyre_life1', 0)
                        },
                        {
                            'code': comparison_info.get('driver2', 'Unknown'),
                            'lap_time': comparison_info.get('lap_time2', 'N/A'),
                            'compound': comparison_info.get('compound2', 'Unknown'),
                            'tyre_life': comparison_info.get('tyre_life2', 0)
                        }
                    ],
                    'track_length': max(distance_data) if distance_data else 5807.0,
                    'sectors': self._generate_sector_data(distance_data)
                },
                'rpm_data': {
                    'distance': distance_data,
                    'driver1_rpm': driver1_rpm,
                    'driver2_rpm': driver2_rpm,
                    'driver1_name': comparison_info.get('driver1', 'Driver 1'),
                    'driver2_name': comparison_info.get('driver2', 'Driver 2')
                },
                'statistics': self._calculate_rpm_statistics_new(driver1_rpm, driver2_rpm, distance_data),
                'timestamp': self._get_current_timestamp()
            }
            
            print(f"[RPM_LOADER] ✅ 新格式數據處理完成")
            return processed
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 新格式數據處理失敗: {str(e)}")
            raise

    def _process_old_format_rpm_data(self, raw_data: dict) -> dict:
        """處理舊格式數據 (直接從results.telemetry_comparison.RPM)"""
        try:
            print(f"[RPM_LOADER] ========== 解析舊格式數據 ==========")
            
            # 直接從results結構提取
            results = raw_data.get('results', {})
            telemetry_comparison = results.get('telemetry_comparison', {})
            comparison_info = results.get('comparison_info', {})
            
            # 提取RPM數據
            rpm_data = telemetry_comparison.get('RPM', {})
            driver1_rpm = rpm_data.get('driver1_data', [])
            driver2_rpm = rpm_data.get('driver2_data', [])
            distance_data = rpm_data.get('distance', [])
            
            print(f"[RPM_LOADER] 舊格式 RPM數據點數: {len(driver1_rpm)}, {len(driver2_rpm)}, {len(distance_data)}")
            
            # 構建處理後的數據結構
            processed = {
                'metadata': {
                    'analysis_type': 'rpm_comparison',
                    'drivers': [
                        {
                            'code': comparison_info.get('driver1', 'Driver 1'),
                            'lap_time': comparison_info.get('lap_time1', 'N/A'),
                            'compound': comparison_info.get('compound1', 'Unknown'),
                            'tyre_life': comparison_info.get('tyre_life1', 0)
                        },
                        {
                            'code': comparison_info.get('driver2', 'Driver 2'),
                            'lap_time': comparison_info.get('lap_time2', 'N/A'),
                            'compound': comparison_info.get('compound2', 'Unknown'),
                            'tyre_life': comparison_info.get('tyre_life2', 0)
                        }
                    ],
                    'track_length': max(distance_data) if distance_data else 5807.0,
                    'sectors': self._generate_sector_data(distance_data)
                },
                'rpm_data': {
                    'distance': distance_data,
                    'driver1_rpm': driver1_rpm,
                    'driver2_rpm': driver2_rpm,
                    'driver1_name': comparison_info.get('driver1', 'Driver 1'),
                    'driver2_name': comparison_info.get('driver2', 'Driver 2')
                },
                'statistics': self._calculate_rpm_statistics_new(driver1_rpm, driver2_rpm, distance_data),
                'timestamp': self._get_current_timestamp()
            }
            
            print(f"[RPM_LOADER] ✅ 舊格式數據處理完成")
            return processed
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 舊格式數據處理失敗: {str(e)}")
            raise

    def _generate_sector_data(self, distance_data: List[float]) -> List[Dict[str, Any]]:
        """生成賽道分段數據"""
        try:
            if not distance_data:
                return []
            
            max_distance = max(distance_data)
            sector_length = max_distance / 3
            
            sectors = []
            for i in range(3):
                start_dist = i * sector_length
                end_dist = (i + 1) * sector_length
                sectors.append({
                    'sector': i + 1,
                    'start_distance': start_dist,
                    'end_distance': end_dist,
                    'length': sector_length
                })
            
            return sectors
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 生成分段數據失敗: {str(e)}")
            return []

    def _calculate_rpm_statistics_new(self, driver1_rpm: List[float], driver2_rpm: List[float], distance_data: List[float]) -> Dict[str, Any]:
        """計算RPM統計數據"""
        try:
            stats = {
                'driver1': {
                    'max_rpm': max(driver1_rpm) if driver1_rpm else 0,
                    'min_rpm': min(driver1_rpm) if driver1_rpm else 0,
                    'avg_rpm': sum(driver1_rpm) / len(driver1_rpm) if driver1_rpm else 0,
                    'data_points': len(driver1_rpm)
                },
                'driver2': {
                    'max_rpm': max(driver2_rpm) if driver2_rpm else 0,
                    'min_rpm': min(driver2_rpm) if driver2_rpm else 0,
                    'avg_rpm': sum(driver2_rpm) / len(driver2_rpm) if driver2_rpm else 0,
                    'data_points': len(driver2_rpm)
                },
                'comparison': {
                    'total_data_points': len(distance_data),
                    'track_coverage': max(distance_data) if distance_data else 0
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 計算統計數據失敗: {str(e)}")
            return {}

    def _get_current_timestamp(self) -> str:
        """取得當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def _validate_session_info(self, session_info: Dict[str, Any]) -> bool:
        """驗證會話信息"""
        required_fields = ['year', 'race', 'driver1', 'driver2', 'lap1', 'lap2']
        
        for field in required_fields:
            if field not in session_info:
                print(f"[ERROR] [RPM_LOADER] 缺少必需參數: {field}")
                self.load_error.emit(f"缺少必需參數: {field}")
                return False
        
        return True

    def cache_rpm_data(self, rpm_data: Dict[str, Any]) -> bool:
        """緩存RPM數據"""
        try:
            cache_filename = self._build_rpm_cache_filename()
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(rpm_data, f)
            
            print(f"[RPM_LOADER] 💾 RPM數據已緩存至: {cache_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 緩存RPM數據失敗: {e}")
            return False
    
    def _build_rpm_cache_filename(self) -> str:
        """構建RPM緩存檔案名稱"""
        if not self.current_session:
            return "rpm_data_cache.pkl"
            
        year = self.current_session['year']
        race = self.current_session['race'].replace(' ', '_')
        driver1 = self.current_session['driver1']
        driver2 = self.current_session['driver2']
        
        filename = f"rpm_analysis_{year}_{race}_{driver1}_vs_{driver2}.pkl"
        return filename


# 主程式測試（已移除模擬數據功能）
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試RPM數據載入器
    loader = RPMAnalysisDataLoader()
    
    print("[TEST] RPM分析數據載入器已完全重構，移除所有模擬數據功能")
    print("[TEST] 現在只會從真實JSON檔案載入數據")
    
    sys.exit(0)
