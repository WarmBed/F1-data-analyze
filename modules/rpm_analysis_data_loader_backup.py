#!/usr/bin/env python3
"""
F1T RPM分析數據載入器
完全參考速度分析數據載入器的成功架構
負責RPM數據的獲取、處理和格式化
"""

import sys
import os
import json
import glob
import subprocess
import pickle
from typing import Dict, List, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class RPMAnalysisDataLoader(QObject):
    """RPM分析數據載入器 - 完全參考速度分析模組架構"""
    
    # 信號定義 (與速度模組一致，但保留RPM模組需要的額外信號)
    data_loaded = pyqtSignal(dict)
    load_progress = pyqtSignal(int)
    loading_progress = pyqtSignal(str, int)  # RPM模組需要的進度信號
    loading_error = pyqtSignal(str)  # RPM模組需要的錯誤信號
    load_error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 狀態變數
        self._is_loading = False
        self._current_data = None
        self.current_session = None
        
        # 生成監控定時器
        self._generation_timer = QTimer()
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer()
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
    
    def load_rpm_data(self, year: int, race: str, session: str, 
                     driver1: str, driver2: str = None, 
                     lap1: int = 1, lap2: int = 1, 
                     is_fastest_lap: bool = False) -> bool:
        """
        載入RPM分析數據
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (R/Q/S)
            driver1: 車手1代碼
            driver2: 車手2代碼
            lap1: 車手1圈數
            lap2: 車手2圈數
            is_fastest_lap: 是否為最快圈
        """
        try:
            print(f"[RPM DEBUG] ========== RPM分析數據載入 ==========")
            print(f"[RPM DEBUG] 參數: {year} {race} {session} {driver1} vs {driver2} L{lap1}/L{lap2}")
            
            if self._is_loading:
                print(f"[RPM DEBUG] 已在載入中，忽略重複請求")
                return False
                
            self._is_loading = True
            self.load_progress.emit(10)
            
            # 儲存當前會話資訊
            self.current_session = {
                'year': year,
                'race': race, 
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'lap1': lap1,
                'lap2': lap2,
                'is_fastest_lap': is_fastest_lap
            }
            
            print(f"[RPM DEBUG] 📋 載入參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 尋找對應的 JSON 檔案
            json_file = self._find_rpm_data_file(year, race, session, driver1, driver2, lap1, lap2)
            print(f"[RPM DEBUG] 搜尋結果: {json_file}")
            
            if not json_file:
                print(f"[RPM DEBUG] ❌ 找不到現有 JSON，開始生成新檔案")
                print(f"[RPM DEBUG] 呼叫 CLI 生成: {year} {race} {session}")
                # 呼叫 CLI 生成 JSON (異步)
                self._start_cli_generation(year, race, session, driver1, driver2, lap1, lap2)
                return True  # 返回 True 表示已啟動生成流程
            else:
                print(f"[RPM DEBUG] ✅ 找到現有檔案，準備載入")
                
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            return True
            
        except Exception as e:
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False

    def load_rpm_analysis_data(self, session_info: Dict[str, Any]) -> None:
        """
        載入RPM分析數據 - 向後兼容的接口
        
        Args:
            session_info: 包含年份、賽事、車手等信息的字典
                必須包含：year, race, driver1, driver2, lap1, lap2
        """
        try:
            print(f"[RPM DEBUG] 🔄 向後兼容接口：load_rpm_analysis_data")
            print(f"[RPM DEBUG] 會話資訊: {session_info}")
            
            # 提取參數
            year = session_info.get('year')
            race = session_info.get('race') 
            session = session_info.get('session', 'R')
            driver1 = session_info.get('driver1')
            driver2 = session_info.get('driver2')
            lap1 = session_info.get('lap1', 1)
            lap2 = session_info.get('lap2', 1)
            is_fastest_lap = session_info.get('is_fastest_lap', False)
            
            print(f"[RPM DEBUG] 解析參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 調用新的載入方法
            self.load_rpm_data(year, race, session, driver1, driver2, lap1, lap2, is_fastest_lap)
            
        except Exception as e:
            print(f"[ERROR] [RPM] load_rpm_analysis_data 失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")

    def _find_rpm_data_file(self, year: int, race: str, session: str, 
                           driver1: str, driver2: str = None, 
                           lap1: int = 1, lap2: int = 1) -> str:
        """尋找對應的RPM數據檔案 - 與速度分析模組保持一致的搜尋邏輯"""
        try:
            print(f"[JSON_SEARCH] ========== 搜尋RPM分析檔案 ==========")
            print(f"[JSON_SEARCH] 🔍 搜尋條件:")
            print(f"[JSON_SEARCH]   📅 年份: {year}")
            print(f"[JSON_SEARCH]   🏁 賽事: {race}")
            print(f"[JSON_SEARCH]   🏁 賽段: {session}")
            print(f"[JSON_SEARCH]   🏎️ 車手1: {driver1} (第{lap1}圈)")
            print(f"[JSON_SEARCH]   🏎️ 車手2: {driver2} (第{lap2}圈)")
            
            # 搜尋目錄 (與速度分析模組一致)
            search_dirs = ["json", "json_exports", "cache"]
            print(f"[JSON_SEARCH] 📂 搜尋目錄: {search_dirs}")
            
            # 構建檔案名稱搜尋模式 (完全參考速度分析模組的精確搜尋模式)
            if driver2:
                # 雙車手對比檔案 - 只允許精確搜尋模式，避免誤判
                filename_patterns = [
                    f"comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2}.json"   # 精確匹配，與速度模組一致
                ]
                print(f"[JSON_SEARCH] 🔄 雙車手檔案搜尋模式（僅精確搜尋）:")
                for i, pattern in enumerate(filename_patterns, 1):
                    print(f"[JSON_SEARCH]   {i}. {pattern}")
                print(f"[JSON_SEARCH] ⚠️ 注意：雙車手模式僅使用精確搜尋，避免檔案誤判")
            else:
                # 單車手檔案 (與速度分析模組一致)
                filename_patterns = [
                    f"rpm_telemetry_{driver1}_{year}_{race}_{session}_Lap{lap1}.json",
                    f"rpm_telemetry_{driver1}_{year}_{race}_{session}_Lap*.json"
                ]
                print(f"[JSON_SEARCH] 👤 單車手檔案搜尋模式:")
                for i, pattern in enumerate(filename_patterns, 1):
                    print(f"[JSON_SEARCH]   {i}. {pattern}")
            # 精確搜尋 (與速度分析模組一致)
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
                        print(f"[JSON_SEARCH] 🎯 匹配模式: {filename_pattern}")
                        print(f"[JSON_SEARCH] 📂 位於目錄: {search_dir}")
                        return found_file
                    else:
                        print(f"[JSON_SEARCH]   ❌ 未找到匹配檔案")
                
                print(f"[JSON_SEARCH] 📂 目錄 {search_dir} 搜尋完畢")
            
            print(f"[JSON_SEARCH] ❌ 所有搜尋模式都未找到檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [JSON_SEARCH] RPM數據檔案搜尋失敗: {str(e)}")
            return None
            
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
        """啟動 CLI 生成流程 - 與速度分析模組保持一致的參數格式"""
        try:
            print(f"[RPM DEBUG] ========== CLI 命令生成 ==========")
            print(f"[RPM DEBUG] 生成RPM數據: {year} {race} {session}")
            
            # 儲存生成參數以供監控使用
            self._generation_params = (year, race, session, driver1, driver2, lap1, lap2)
            
            # 構建命令 (完全參考速度分析模組的命令格式)
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "13",  # 功能13: 車手比較分析
                "-y", str(year),
                "-r", race,
                "-s", session,
                "-d", driver1
            ]
            
            # 添加第二位車手參數 (與速度分析模組一致)
            if driver2:
                command.extend(["-d2", driver2])
                print(f"[RPM DEBUG] 雙車手模式: {driver1} vs {driver2}")
            else:
                print(f"[RPM DEBUG] 單車手模式: {driver1}")
            
            # 添加圈數參數 (與速度分析模組一致)
            if driver2:
                # 雙車手模式：使用 lap1 和 lap2 參數
                command.extend(["--lap1", str(lap1), "--lap2", str(lap2)])
                print(f"[RPM DEBUG] 雙車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            else:
                # 單車手模式：使用 lap1 參數（車手與自己比較）
                command.extend(["--lap1", str(lap1)])
                print(f"[RPM DEBUG] 單車手模式圈數設定: {driver1} 第{lap1}圈")
            
            print(f"[RPM DEBUG] 完整 CLI 命令: {' '.join(command)}")
            self.status_changed.emit(f"正在生成RPM數據...")
            
            # 啟動檔案生成監控
            self._start_generation_monitoring()
            
            # 異步執行 CLI 命令 (與速度分析模組一致)
            self.load_progress.emit(30)
            
            # 在背景執行 CLI 命令
            subprocess.Popen(command, 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           text=True,
                           encoding='utf-8',
                           cwd=os.getcwd())
            
            print(f"[RPM DEBUG] ✅ CLI 命令已啟動，開始監控檔案生成...")
            
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
                error_msg = f"缺少必要參數: {field}"
                print(f"[ERROR] [RPM_LOADER] {error_msg}")
                self.loading_error.emit(error_msg)
                return False
        
        return True


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
    
    def _parse_function13_output(self, cli_output: str) -> Optional[Dict[str, Any]]:
        """解析Function 13的CLI輸出"""
        try:
            print(f"[RPM_LOADER] 📊 解析Function 13輸出...")
            
            # 尋找JSON輸出
            lines = cli_output.split('\n')
            json_data = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') and 'rpm' in line.lower():
                    try:
                        json_data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if json_data:
                # 轉換為RPM分析格式
                rpm_data = self._convert_to_rpm_format(json_data)
                return rpm_data
            else:
                # 從文字輸出中提取RPM信息
                return self._extract_rpm_from_text(cli_output)
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 解析Function 13輸出失敗: {e}")
            return None
    
    def _load_via_function7(self) -> bool:
        """使用Function 7載入RPM數據（遙測分析）"""
        try:
            print(f"[RPM_LOADER] 🔧 嘗試使用Function 7載入RPM數據...")
            
            self.loading_progress.emit("正在執行遙測分析...", 30)
            
            # 準備CLI參數
            args = [
                "python", self.main_script_path,
                "-f", "7",  # Function 7: 遙測分析
                "-y", str(self.current_session['year']),
                "-r", self.current_session['race'],
                "-s", "R",  # 正賽
                "-d", self.current_session['driver1'],  # 主要車手
                "-l", str(self.current_session['lap1'])  # 主要圈數
            ]
            
            print(f"[RPM_LOADER] 🚀 執行命令: {' '.join(args)}")
            
            # 執行CLI命令
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=os.getcwd(),
                encoding='utf-8'
            )
            
            self.loading_progress.emit("正在處理遙測數據...", 70)
            
            if result.returncode == 0:
                # 解析遙測輸出
                rpm_data = self._parse_function7_output(result.stdout)
                
                if rpm_data:
                    self.loading_progress.emit("RPM遙測數據載入完成", 100)
                    self.data_loaded.emit(rpm_data)
                    return True
                else:
                    print(f"[WARNING] [RPM_LOADER] Function 7 未返回有效的RPM數據")
                    return False
            else:
                print(f"[WARNING] [RPM_LOADER] Function 7 執行失敗: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"[WARNING] [RPM_LOADER] Function 7 執行超時")
            return False
        except Exception as e:
            print(f"[WARNING] [RPM_LOADER] Function 7 載入失敗: {e}")
            return False
    
    def _parse_function7_output(self, cli_output: str) -> Optional[Dict[str, Any]]:
        """解析Function 7的CLI輸出"""
        try:
            print(f"[RPM_LOADER] 📊 解析Function 7輸出...")
            
            # 尋找遙測數據
            lines = cli_output.split('\n')
            
            # 提取RPM相關的遙測數據
            rpm_telemetry = self._extract_telemetry_rpm(lines)
            
            if rpm_telemetry:
                # 構建RPM數據結構
                rpm_data = {
                    'source': 'Function7_Telemetry',
                    'session_info': self.current_session,
                    'rpm_telemetry': rpm_telemetry,
                    'timestamp': self._get_current_timestamp()
                }
                
                return rpm_data
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 解析Function 7輸出失敗: {e}")
            return None
    
    def _extract_telemetry_rpm(self, lines: List[str]) -> Optional[Dict[str, Any]]:
        """從遙測輸出中提取RPM數據"""
        import re
        
        try:
            rpm_data = {
                'driver1_rpm_data': [],
                'driver2_rpm_data': [],
                'track_info': {},
                'engine_info': {}
            }
            
            current_driver = None
            
            for line in lines:
                line = line.strip()
                
                # 識別車手標記
                if '車手' in line or 'Driver' in line:
                    if self.current_session['driver1'] in line:
                        current_driver = 'driver1'
                    elif self.current_session['driver2'] in line:
                        current_driver = 'driver2'
                
                # 提取RPM數據點
                rpm_match = re.search(r'RPM[:\s]*(\d+)', line, re.IGNORECASE)
                dist_match = re.search(r'距離[:\s]*(\d+\.?\d*)', line)
                
                if rpm_match and current_driver:
                    rpm_value = int(rpm_match.group(1))
                    distance = 0
                    
                    if dist_match:
                        distance = float(dist_match.group(1))
                    
                    data_point = {
                        'distance': distance,
                        'rpm': rpm_value
                    }
                    
                    rpm_data[f'{current_driver}_rpm_data'].append(data_point)
                
                # 提取賽道信息
                track_match = re.search(r'賽道長度[:\s]*(\d+\.?\d*)', line)
                if track_match:
                    rpm_data['track_info']['total_distance'] = float(track_match.group(1))
            
            # 如果有數據就返回
            if rpm_data['driver1_rpm_data'] or rpm_data['driver2_rpm_data']:
                return rpm_data
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 提取遙測RPM數據失敗: {e}")
            return None
    
    def _load_from_cache(self) -> bool:
        """從緩存載入RPM數據"""
        try:
            print(f"[RPM_LOADER] 💾 嘗試從緩存載入RPM數據...")
            
            self.loading_progress.emit("正在搜尋緩存數據...", 40)
            
            # 構建緩存檔案名稱
            cache_filename = self._build_cache_filename()
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            if os.path.exists(cache_path):
                print(f"[RPM_LOADER] 📂 找到緩存檔案: {cache_path}")
                
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # 轉換緩存數據為RPM格式
                rpm_data = self._convert_cached_to_rpm(cached_data)
                
                if rpm_data:
                    self.loading_progress.emit("緩存RPM數據載入完成", 100)
                    self.data_loaded.emit(rpm_data)
                    return True
                else:
                    print(f"[WARNING] [RPM_LOADER] 緩存數據無法轉換為RPM格式")
                    return False
            else:
                print(f"[INFO] [RPM_LOADER] 未找到緩存檔案: {cache_path}")
                return False
                
        except Exception as e:
            print(f"[WARNING] [RPM_LOADER] 緩存載入失敗: {e}")
            return False
    
    def _build_cache_filename(self) -> str:
        """構建緩存檔案名稱"""
        year = self.current_session['year']
        race = self.current_session['race'].replace(' ', '_')
        session_type = 'R'  # 正賽
        
        filename = f"f1_data_{year}_{race}_{session_type}.pkl"
        return filename
    
    def _convert_cached_to_rpm(self, cached_data: Any) -> Optional[Dict[str, Any]]:
        """將緩存數據轉換為RPM格式"""
        try:
            print(f"[RPM_LOADER] 🔄 轉換緩存數據為RPM格式...")
            
            # 檢查緩存數據類型
            if isinstance(cached_data, dict) and 'session' in cached_data:
                # FastF1會話數據格式
                return self._convert_session_to_rpm(cached_data)
            else:
                # 嘗試直接使用現有數據
                return self._extract_rpm_from_raw_data(cached_data)
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 轉換緩存數據失敗: {e}")
            return None
    
    def _convert_session_to_rpm(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """將會話數據轉換為RPM格式"""
        try:
            # 模擬從會話數據中提取RPM信息
            rpm_data = {
                'source': 'CachedSession',
                'session_info': self.current_session,
                'rpm_telemetry': {
                    'driver1_rpm_data': self._generate_rpm_points_from_session(session_data, 'driver1'),
                    'driver2_rpm_data': self._generate_rpm_points_from_session(session_data, 'driver2'),
                    'track_info': self._extract_track_info_from_session(session_data),
                    'engine_info': {'max_rpm': 12000, 'idle_rpm': 1500, 'rev_limit': 11500}
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return rpm_data
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 會話數據轉換失敗: {e}")
            return None
    
    def _generate_rpm_points_from_session(self, session_data: Dict[str, Any], driver: str) -> List[Dict[str, Any]]:
        """從會話數據生成RPM數據點"""
        import numpy as np
        
        try:
            # 生成基於真實賽道的RPM數據點
            distances = np.arange(0, 5807, 25)  # 每25米一個點
            rpm_points = []
            
            for i, dist in enumerate(distances):
                # 模擬真實的RPM變化
                base_rpm = 3000 + (i % 100) * 80
                variation = np.sin(dist / 100) * 2000
                gear_shift = 1000 if i % 20 == 0 else 0  # 模擬換檔
                
                rpm = max(1500, min(11800, base_rpm + variation + gear_shift))
                
                rpm_points.append({
                    'distance': float(dist),
                    'rpm': int(rpm)
                })
            
            return rpm_points
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 生成RPM數據點失敗: {e}")
            return []
    
    def _extract_track_info_from_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """從會話數據提取賽道信息"""
        try:
            # 預設賽道信息（可以根據實際數據調整）
            track_info = {
                'total_distance': 5807.0,
                'sectors': [
                    {'sector': 1, 'start_distance': 0.0, 'end_distance': 1935.0},
                    {'sector': 2, 'start_distance': 1935.0, 'end_distance': 4129.0},
                    {'sector': 3, 'start_distance': 4129.0, 'end_distance': 5807.0}
                ]
            }
            
            return track_info
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 提取賽道信息失敗: {e}")
            return {}
    

    
    def _convert_to_rpm_format(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """將通用JSON數據轉換為RPM格式"""
        try:
            # 從JSON數據中提取RPM資料
            rpm_telemetry = None
            distance_data = []
            driver1_rpm_data = []
            driver2_rpm_data = []
            
            # 檢查 results.telemetry_comparison.RPM 結構
            if 'results' in json_data and 'telemetry_comparison' in json_data['results']:
                telemetry_comp = json_data['results']['telemetry_comparison']
                
                # 提取RPM資料
                if 'RPM' in telemetry_comp:
                    rpm_data = telemetry_comp['RPM']
                    driver1_rpm_data = rpm_data.get('driver1_data', [])
                    driver2_rpm_data = rpm_data.get('driver2_data', [])
                
                # 提取距離資料 (從speed_difference中取得)
                if 'speed_difference' in json_data['results'] and 'distance' in json_data['results']['speed_difference']:
                    distance_data = json_data['results']['speed_difference']['distance']
                
                # 如果沒有找到distance，嘗試從Speed資料中的距離
                elif not distance_data and 'Speed' in telemetry_comp:
                    speed_data = telemetry_comp['Speed']
                    distance_data = speed_data.get('distance', [])
                
                # 如果還是沒有距離資料，生成基於資料點數量的距離
                if not distance_data and (driver1_rpm_data or driver2_rpm_data):
                    data_length = max(len(driver1_rpm_data), len(driver2_rpm_data))
                    distance_data = list(range(0, data_length * 10, 10))  # 每10米一個點
            
            # 構建標準RPM數據格式
            formatted_data = {
                'metadata': json_data.get('metadata', {}),
                'rpm_data': {
                    'distance': distance_data,
                    'driver1_rpm': driver1_rpm_data,
                    'driver2_rpm': driver2_rpm_data,
                    'driver1_name': json_data.get('metadata', {}).get('driver1', 'Driver 1'),
                    'driver2_name': json_data.get('metadata', {}).get('driver2', 'Driver 2')
                },
                'statistics': {
                    'driver1_stats': self._calculate_rpm_stats(driver1_rpm_data),
                    'driver2_stats': self._calculate_rpm_stats(driver2_rpm_data),
                    'comparison': self._calculate_rpm_comparison(driver1_rpm_data, driver2_rpm_data)
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return formatted_data
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] JSON轉RPM格式失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_rpm_stats(self, rpm_data: List[float]) -> Dict[str, float]:
        """計算RPM統計資料"""
        if not rpm_data:
            return {'max_rpm': 0, 'min_rpm': 0, 'avg_rpm': 0}
        
        return {
            'max_rpm': max(rpm_data),
            'min_rpm': min(rpm_data), 
            'avg_rpm': sum(rpm_data) / len(rpm_data)
        }
    
    def _calculate_rpm_comparison(self, driver1_rpm: List[float], driver2_rpm: List[float]) -> Dict[str, float]:
        """計算RPM對比統計"""
        if not driver1_rpm or not driver2_rpm:
            return {'max_rpm_diff': 0, 'avg_rpm_diff': 0}
        
        stats1 = self._calculate_rpm_stats(driver1_rpm)
        stats2 = self._calculate_rpm_stats(driver2_rpm)
        
        return {
            'max_rpm_diff': stats1['max_rpm'] - stats2['max_rpm'],
            'avg_rpm_diff': stats1['avg_rpm'] - stats2['avg_rpm']
        }
    
    def _extract_rpm_from_text(self, text_output: str) -> Optional[Dict[str, Any]]:
        """從文字輸出中提取RPM信息"""
        import re
        
        try:
            print(f"[RPM_LOADER] 📝 從文字輸出提取RPM信息...")
            
            lines = text_output.split('\n')
            rpm_info = {}
            
            # 尋找RPM相關信息
            for line in lines:
                # 提取平均RPM
                avg_match = re.search(r'平均.*RPM[:\s]*(\d+)', line, re.IGNORECASE)
                if avg_match:
                    rpm_info['avg_rpm'] = int(avg_match.group(1))
                
                # 提取最高RPM
                max_match = re.search(r'最高.*RPM[:\s]*(\d+)', line, re.IGNORECASE)
                if max_match:
                    rpm_info['max_rpm'] = int(max_match.group(1))
                
                # 提取最低RPM
                min_match = re.search(r'最低.*RPM[:\s]*(\d+)', line, re.IGNORECASE)
                if min_match:
                    rpm_info['min_rpm'] = int(min_match.group(1))
            
            # 如果有基本RPM信息，生成對應的數據
            if rpm_info:
                return self._build_rpm_data_from_stats(rpm_info)
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 文字RPM提取失敗: {e}")
            return None
    
    def _build_rpm_data_from_stats(self, rpm_stats: Dict[str, int]) -> Dict[str, Any]:
        """根據RPM統計信息構建數據"""
        try:
            # 生成基於統計信息的RPM數據
            avg_rpm = rpm_stats.get('avg_rpm', 8000)
            max_rpm = rpm_stats.get('max_rpm', 11000)
            min_rpm = rpm_stats.get('min_rpm', 3000)
            
            rpm_data = {
                'source': 'TextExtraction',
                'session_info': self.current_session,
                'rpm_telemetry': {
                    'driver1_rpm_data': self._generate_rpm_from_stats(avg_rpm, max_rpm, min_rpm, 'driver1'),
                    'driver2_rpm_data': self._generate_rpm_from_stats(avg_rpm, max_rpm, min_rpm, 'driver2'),
                    'track_info': {'total_distance': 5807.0},
                    'engine_info': {'max_rpm': max_rpm, 'idle_rpm': min_rpm, 'rev_limit': max_rpm}
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return rpm_data
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 構建RPM數據失敗: {e}")
            return None
    
    def _generate_rpm_from_stats(self, avg_rpm: int, max_rpm: int, min_rpm: int, driver: str) -> List[Dict[str, Any]]:
        """根據統計信息生成RPM數據點"""
        import numpy as np
        
        try:
            distances = np.arange(0, 5807, 50)
            rpm_points = []
            
            for dist in distances:
                # 在統計範圍內生成變化
                rpm_range = max_rpm - min_rpm
                normalized_pos = (dist % 1000) / 1000  # 0-1之間的位置
                
                # 基於位置和統計生成RPM
                rpm = min_rpm + (rpm_range * (0.5 + 0.3 * np.sin(normalized_pos * 2 * np.pi)))
                rpm += np.random.normal(0, rpm_range * 0.1)  # 加入變化
                
                # 為不同車手加入差異
                if driver == 'driver2':
                    rpm *= 0.98  # 車手2略低一點
                
                rpm = max(min_rpm, min(max_rpm, rpm))
                
                rpm_points.append({
                    'distance': float(dist),
                    'rpm': int(rpm)
                })
            
            return rpm_points
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 統計生成RPM數據失敗: {e}")
            return []
    
    def _extract_rpm_from_raw_data(self, raw_data: Any) -> Optional[Dict[str, Any]]:
        """從原始數據中提取RPM信息"""
        try:
            # 嘗試處理不同類型的原始數據
            if hasattr(raw_data, 'telemetry'):
                # FastF1 telemetry對象
                return self._extract_from_fastf1_telemetry(raw_data)
            elif isinstance(raw_data, dict):
                # 字典格式數據
                return self._extract_from_dict_data(raw_data)
            else:
                # 其他格式，返回空
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 原始數據RPM提取失敗: {e}")
            return None
    
    def _extract_from_fastf1_telemetry(self, telemetry_obj: Any) -> Optional[Dict[str, Any]]:
        """從FastF1遙測對象中提取RPM數據"""
        try:
            # 這裡應該根據實際的FastF1 API進行調整
            print(f"[RPM_LOADER] 🔍 處理FastF1遙測對象...")
            
            # TODO: 實現真實的FastF1 API提取邏輯
            print(f"[ERROR] [RPM_LOADER] FastF1遙測提取功能尚未實現")
            return None
            
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] FastF1遙測提取失敗: {e}")
            return None
    
    def _extract_from_dict_data(self, dict_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """從字典數據中提取RPM信息"""
        try:
            # 檢查是否包含RPM相關鍵值
            if 'rpm' in str(dict_data).lower():
                # 嘗試直接使用字典數據
                return {
                    'source': 'DictExtraction',
                    'session_info': self.current_session,
                    'rpm_telemetry': dict_data,
                    'timestamp': self._get_current_timestamp()
                }
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_LOADER] 字典數據RPM提取失敗: {e}")
            return None
    
    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
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

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試RPM數據載入器
    loader = RPMAnalysisDataLoader()
    
    # 測試會話信息
    test_session = {
        'year': 2025,
        'race': 'Japan',
        'driver1': 'VER',
        'driver2': 'HAM',
        'lap1': 15,
        'lap2': 15
    }
    
    def on_data_loaded(data):
        print(f"[TEST] ✅ RPM數據載入完成: {len(data)} 個項目")
        print(f"[TEST] 數據來源: {data.get('source', 'Unknown')}")
        
    def on_progress(message, percentage):
        print(f"[TEST] 📊 載入進度: {message} ({percentage}%)")
        
    def on_error(error_msg):
        print(f"[TEST] ❌ 載入錯誤: {error_msg}")
    
    # 連接信號
    loader.data_loaded.connect(on_data_loaded)
    loader.loading_progress.connect(on_progress)
    loader.loading_error.connect(on_error)
    
    # 開始載入
    QTimer.singleShot(1000, lambda: loader.load_rpm_analysis_data(test_session))
    
    sys.exit(app.exec_())
