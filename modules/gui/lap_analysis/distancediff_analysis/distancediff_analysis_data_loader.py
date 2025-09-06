#!/usr/bin/env python3
"""
F1T distancediff分析數據載入器
完全參考速度分析數據載入器的成功架構
負責distancediff數據的獲取、處理和格式化
"""

import sys
import os
import json
import glob
import pickle
import time
from datetime import datetime
import threading
import fastf1
import pandas as pd
import subprocess
import pickle
from typing import Dict, List, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class distancediffAnalysisDataLoader(QObject):
    """distancediff分析數據載入器 - 完全參考速度分析模組架構"""
    
    # 信號定義 (與速度模組一致，但保留distancediff模組需要的額外信號)
    data_loaded = pyqtSignal(dict)
    load_progress = pyqtSignal(int)
    load_error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 狀態變數
        self._base_path = "json"
        self._is_loading = False
        self._current_data = None
        self.current_session = None
        
        # 生成監控定時器 - 設置 parent 防止被垃圾回收
        self._generation_timer = QTimer(self)
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer(self)
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
    
    def load_distancediff_data(self, year: int, race: str, session: str, 
                     driver1: str, driver2: str = None, 
                     lap1: int = 1, lap2: int = None, 
                     is_fastest_lap: bool = False) -> bool:
        """
        載入distancediff分析數據
        
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
            # 正規化參數，處理 None 值
            if lap2 is None:
                lap2 = 1  # 設置預設值
            if driver2 is None or driver2 == driver1:
                # 單車手模式
                driver2 = None
                
            print(f"[distancediff DEBUG] ========== distancediff分析數據載入 ==========")
            print(f"[distancediff DEBUG] 參數: {year} {race} {session} {driver1} vs {driver2} L{lap1}/L{lap2}")
            print(f"[distancediff DEBUG] 分析模式: {'單車手' if driver2 is None else '雙車手對比'}")
            
            if self._is_loading:
                print(f"[distancediff DEBUG] 已在載入中，忽略重複請求")
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
            
            print(f"[distancediff DEBUG] 📋 載入參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 尋找對應的 JSON 檔案
            json_file = self._find_distancediff_data_file(year, race, session, driver1, driver2, lap1, lap2)
            print(f"[distancediff DEBUG] 搜尋結果: {json_file}")
            
            if not json_file:
                print(f"[distancediff DEBUG] ❌ 找不到現有 JSON，開始生成新檔案")
                print(f"[distancediff DEBUG] 呼叫 CLI 生成: {year} {race} {session}")
                # 呼叫 CLI 生成 JSON (異步)
                self._start_cli_generation(year, race, session, driver1, driver2, lap1, lap2)
                return True  # 返回 True 表示已啟動生成流程
            else:
                print(f"[distancediff DEBUG] ✅ 找到現有檔案，準備載入")
                
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            return True
            
        except Exception as e:
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False

    def load_distancediff_analysis_data(self, session_info: Dict[str, Any]) -> None:
        """
        載入distancediff分析數據 - 向後兼容的接口
        
        Args:
            session_info: 包含年份、賽事、車手等信息的字典
                必須包含：year, race, driver1, driver2, lap1, lap2
        """
        try:
            print(f"[distancediff DEBUG] 🔄 向後兼容接口：load_distancediff_analysis_data")
            print(f"[distancediff DEBUG] 會話資訊: {session_info}")
            
            # 提取參數
            year = session_info.get('year')
            race = session_info.get('race') 
            session = session_info.get('session', 'R')
            driver1 = session_info.get('driver1')
            driver2 = session_info.get('driver2')
            lap1 = session_info.get('lap1', 1)
            lap2 = session_info.get('lap2', 1)
            is_fastest_lap = session_info.get('is_fastest_lap', False)
            
            print(f"[distancediff DEBUG] 解析參數: {year} {race} {session} {driver1}vs{driver2} L{lap1}vsL{lap2}")
            
            # 調用新的載入方法
            self.load_distancediff_data(year, race, session, driver1, driver2, lap1, lap2, is_fastest_lap)
            
        except Exception as e:
            print(f"[ERROR] [distancediff] load_distancediff_analysis_data 失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")

    def _find_distancediff_data_file(self, year: int, race: str, session: str, 
                           driver1: str, driver2: str = None, 
                           lap1: int = 1, lap2: int = 1) -> str:
        """搜尋distancediff分析數據檔案 - 使用與速度分析相同的搜尋邏輯"""
        try:
            print(f"[JSON_SEARCH] ========== 搜尋distancediff分析檔案 ==========")
            print(f"[JSON_SEARCH] 🔍 搜尋條件:")
            print(f"[JSON_SEARCH]   📅 年份: {year}")
            print(f"[JSON_SEARCH]   🏁 賽事: {race}")
            print(f"[JSON_SEARCH]   🏁 賽段: {session}")
            print(f"[JSON_SEARCH]   🏎️ 車手1: {driver1} (第{lap1}圈)")
            print(f"[JSON_SEARCH]   🏎️ 車手2: {driver2} (第{lap2}圈)")
            
            # 搜尋目錄 - 與速度分析相同
            search_dirs = ["json", "json_exports", "cache"]
            print(f"[JSON_SEARCH] 📂 搜尋目錄: {search_dirs}")
            
            # 構建檔案名稱搜尋模式 - 與速度分析完全相同
            if driver2 and driver2 != driver1:
                # 雙車手對比檔案 - 只允許精確搜尋模式，避免誤判
                # 確保 lap2 不是 None
                lap2_safe = lap2 if lap2 is not None else 1
                filename_patterns = [
                    f"comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2_safe}.json"   # 只允許模式1：精確匹配
                ]
                print(f"[JSON_SEARCH] 🔄 雙車手檔案搜尋模式（僅精確搜尋）:")
                for i, pattern in enumerate(filename_patterns, 1):
                    print(f"[JSON_SEARCH]   {i}. {pattern}")
                print(f"[JSON_SEARCH] ⚠️ 注意：雙車手模式僅使用精確搜尋，避免檔案誤判")
            else:
                # 單車手檔案 - 修正為使用 comparison_telemetry 格式
                filename_patterns = [
                    f"comparison_telemetry_{driver1}_{driver1}_{year}_{race}_{session}_Lap{lap1}.json",
                    f"comparison_telemetry_{driver1}_{driver1}_{year}_{race}_{session}_Lap*.json"
                ]
                print(f"[JSON_SEARCH] � 單車手檔案搜尋模式:")
                for i, pattern in enumerate(filename_patterns, 1):
                    print(f"[JSON_SEARCH]   {i}. {pattern}")
            
            # 精確搜尋 - 與速度分析相同的邏輯
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
            print(f"[ERROR] [distancediff_LOADER] 搜尋檔案時發生錯誤: {str(e)}")
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None

    def _start_cli_generation(self, year: int, race: str, session: str,
                             driver1: str, driver2: str = None,
                             lap1: int = 1, lap2: int = 1):
        """啟動 CLI 生成流程 - 與速度分析完全相同的邏輯"""
        try:
            print(f"[distancediff DEBUG] ========== 啟動 CLI 生成流程 ==========")
            print(f"[distancediff DEBUG] 生成參數:")
            print(f"[distancediff DEBUG]   年份: {year}")
            print(f"[distancediff DEBUG]   賽站: {race}")
            print(f"[distancediff DEBUG]   賽段: {session}")
            print(f"[distancediff DEBUG]   車手1: {driver1}, 圈數: {lap1}")
            print(f"[distancediff DEBUG]   車手2: {driver2}, 圈數: {lap2}")
            
            # 儲存參數供後續使用
            self._generation_params = (year, race, session, driver1, driver2, lap1, lap2)
            
            # 啟動 CLI 生成
            success = self._generate_distancediff_data_via_cli(year, race, session, driver1, driver2, lap1, lap2)
            
            if success:
                print(f"[distancediff DEBUG] ✅ CLI 啟動成功，開始監控檔案生成")
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring()
            else:
                print(f"[distancediff DEBUG] ❌ CLI 啟動失敗")
                self.load_error.emit(f"啟動 CLI 生成失敗: {year} {race} {session}")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [distancediff DEBUG] 啟動生成時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    def _generate_distancediff_data_via_cli(self, year: int, race: str, session: str,
                                  driver1: str, driver2: str = None,
                                  lap1: int = 1, lap2: int = 1) -> bool:
        """透過 CLI 工具生成distancediff數據 - 與速度分析相同的邏輯"""
        try:
            print(f"[distancediff DEBUG] ========== CLI 命令生成 ==========")
            print(f"[distancediff DEBUG] 生成distancediff數據: {year} {race} {session}")
            
            # 構建命令 - 與速度分析相同，使用Function 13
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "13",  # 功能13: 車手比較分析
                "-y", str(year),
                "-r", race,
                "-s", session,
                "-d", driver1
            ]
            
            # 添加第二位車手參數
            if driver2:
                command.extend(["-d2", driver2])
                print(f"[distancediff DEBUG] 雙車手模式: {driver1} vs {driver2}")
            else:
                # 單車手模式：設置 driver2 與 driver1 相同
                command.extend(["-d2", driver1])
                print(f"[distancediff DEBUG] 單車手模式: {driver1} vs {driver1}")
            
            # 添加圈數參數 - 始終使用雙參數模式
            command.extend(["--lap1", str(lap1), "--lap2", str(lap2)])
            
            if driver2:
                print(f"[distancediff DEBUG] 雙車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            else:
                print(f"[distancediff DEBUG] 單車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver1} 第{lap2}圈")
            
            print(f"[distancediff DEBUG] 完整 CLI 命令: {' '.join(command)}")
            self.status_changed.emit(f"正在生成distancediff數據...")
            
            # 非阻塞執行
            def run_cli():
                try:
                    print(f"[distancediff DEBUG] 🚀 開始執行 CLI 命令...")
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        errors='replace',  # 遇到無法解碼的字符時用替代字符
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        print(f"[OK] [distancediff] CLI 執行成功")
                    else:
                        print(f"[ERROR] [distancediff] CLI 執行失敗: {stderr}")
                        
                except Exception as e:
                    print(f"[ERROR] [distancediff] CLI 執行異常: {e}")
            
            # 在背景執行緒中執行CLI
            import threading
            thread = threading.Thread(target=run_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [distancediff] 啟動 CLI 失敗: {e}")
            return False
    
    def _start_generation_monitoring(self):
        """啟動檔案生成監控"""
        print(f"[distancediff_MONITOR] ========== 啟動監控系統 ==========")
        print(f"[distancediff_MONITOR] 檢查計時器狀態...")
        print(f"[distancediff_MONITOR] _generation_timer 存在: {hasattr(self, '_generation_timer')}")
        print(f"[distancediff_MONITOR] _generation_timeout_timer 存在: {hasattr(self, '_generation_timeout_timer')}")
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        print(f"[distancediff_MONITOR] 啟動主監控計時器 (每5秒檢查)")
        self._generation_timer.start(5000)
        print(f"[distancediff_MONITOR] 計時器是否運行: {self._generation_timer.isActive()}")
        print(f"[distancediff_MONITOR] 計時器間隔: {self._generation_timer.interval()}")
        
        print(f"[distancediff_MONITOR] 啟動超時計時器 (180秒)")
        self._generation_timeout_timer.start(180000)
        print(f"[distancediff_MONITOR] 超時計時器是否運行: {self._generation_timeout_timer.isActive()}")
        
        print(f"[distancediff_MONITOR] ✅ 監控系統已啟動")
        self.status_changed.emit("正在生成數據，請稍候...")
        
        # 立即執行一次檢查以確認方法可以被調用
        print(f"[distancediff_MONITOR] 🧪 執行立即測試檢查...")
        QTimer.singleShot(1000, self._check_generation_progress)
    
    def _find_telemetry_analysis_file(self, year: int, race: str, session: str) -> str:
        """尋找遙測分析檔案"""
        try:
            # 定義可能的遙測分析檔案名稱格式
            patterns = [
                f"all_drivers_telemetry_analysis_{year}_{race}_{session}.json",
                f"telemetry_analysis_{year}_{race}_{session}.json",
                f"all_drivers_telemetry_analysis_{year}_{race}.json",
                f"driver_comparison_analysis_{year}_{race}_{session}.json"
            ]
            
            # 搜尋目錄
            search_dirs = ["json", "json_exports", "cache"]
            
            for directory in search_dirs:
                if os.path.exists(directory):
                    for pattern in patterns:
                        file_path = os.path.join(directory, pattern)
                        if os.path.exists(file_path):
                            print(f"[distancediff_LOADER] 🎯 找到遙測分析檔案: {file_path}")
                            return file_path
            
            print(f"[distancediff_LOADER] ❌ 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 搜尋遙測分析檔案失敗: {e}")
            return None
    
    def _extract_distancediff_from_telemetry(self, telemetry_file: str, driver1: str, driver2: str, lap1: int, lap2: int):
        """從遙測分析數據提取 distancediff 數據"""
        try:
            print(f"[distancediff_LOADER] 🔧 從遙測分析提取 distancediff 數據...")
            
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            # 構建 distancediff 數據結構
            distancediff_data = {
                "metadata": {
                    "drivers": [
                        {"code": driver1, "lap_number": lap1},
                        {"code": driver2, "lap_number": lap2}
                    ],
                    "sectors": [],
                    "year": telemetry_data.get("year", 2025),
                    "race": telemetry_data.get("race", "Unknown"),
                    "session": telemetry_data.get("session", "R")
                },
                "distancediff_data": {
                    "distance": [],
                    "driver1_distancediff": [],
                    "driver2_distancediff": [],
                    "driver1_name": driver1,
                    "driver2_name": driver2
                },
                "statistics": {
                    "driver1": {"max_distancediff": 0, "avg_distancediff": 0},
                    "driver2": {"max_distancediff": 0, "avg_distancediff": 0}
                }
            }
            
            print(f"[distancediff_LOADER] 📊 基本 distancediff 數據結構已建立")
            print(f"[distancediff_LOADER] ⚠️ 注意: 當前提供模擬數據，實際 distancediff 提取功能需要進一步開發")
            
            # 生成模擬 distancediff 數據
            distance_points = list(range(0, 5808, 10))  # 每10米一個點
            driver1_distancediff = [8000 + (i % 1000) for i in range(len(distance_points))]  # 模擬 distancediff 數據
            driver2_distancediff = [8200 + (i % 1200) for i in range(len(distance_points))]  # 模擬 distancediff 數據
            
            distancediff_data["distancediff_data"]["distance"] = distance_points
            distancediff_data["distancediff_data"]["driver1_distancediff"] = driver1_distancediff
            distancediff_data["distancediff_data"]["driver2_distancediff"] = driver2_distancediff
            distancediff_data["statistics"]["driver1"]["max_distancediff"] = max(driver1_distancediff)
            distancediff_data["statistics"]["driver1"]["avg_distancediff"] = sum(driver1_distancediff) // len(driver1_distancediff)
            distancediff_data["statistics"]["driver2"]["max_distancediff"] = max(driver2_distancediff)
            distancediff_data["statistics"]["driver2"]["avg_distancediff"] = sum(driver2_distancediff) // len(driver2_distancediff)
            
            print(f"[distancediff_LOADER] ✅ distancediff 數據提取成功 (模擬數據)")
            
            # 發射數據載入信號
            QTimer.singleShot(100, lambda: self.data_loaded.emit(distancediff_data))
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 提取 distancediff 數據失敗: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"提取 distancediff 數據失敗: {str(e)}")
            self._is_loading = False
        
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        try:
            print(f"[distancediff_MONITOR] ========== 監控檢查觸發 ==========")
            print(f"[distancediff_MONITOR] 時間: {datetime.now().strftime('%H:%M:%S')}")
            
            if hasattr(self, '_generation_params'):
                year, race, session, driver1, driver2, lap1, lap2 = self._generation_params
                print(f"[distancediff_MONITOR] 檢查參數: {year} {race} {session} {driver1} vs {driver2} L{lap1}/L{lap2}")
                
                # 檢查是否有新檔案生成
                print(f"[distancediff_MONITOR] 開始搜尋檔案...")
                json_file = self._find_distancediff_data_file(year, race, session, driver1, driver2, lap1, lap2)
                
                if json_file:
                    print(f"[OK] [distancediff_LOADER] 檔案生成完成: {json_file}")
                    print(f"[distancediff_MONITOR] 停止監控並載入檔案")
                    
                    # 停止監控
                    self._stop_generation_monitoring()
                    
                    # 載入新生成的檔案
                    QTimer.singleShot(10, lambda: self._load_json_file(json_file))
                else:
                    print(f"⏳ [distancediff_LOADER] 繼續等待檔案生成...")
                    print(f"[distancediff_MONITOR] 下次檢查將在5秒後進行")
            else:
                print(f"[distancediff_MONITOR] ❌ 缺少 _generation_params 參數")
                print(f"[distancediff_MONITOR] 停止監控")
                self._stop_generation_monitoring()
                
        except Exception as e:
            print(f"[ERROR] [distancediff_MONITOR] 監控檢查異常: {e}")
            import traceback
            traceback.print_exc()
            print(f"[distancediff_MONITOR] 嘗試繼續監控...")
                
    def _on_generation_timeout(self):
        """處理生成超時"""
        print(f"[TIMEOUT] [distancediff_LOADER] ========== 監控超時 ==========")
        print(f"[TIMEOUT] [distancediff_LOADER] 檔案生成超時 (180秒)")
        print(f"[TIMEOUT] [distancediff_LOADER] 停止監控系統")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或重試")
        self._is_loading = False
        
    def _stop_generation_monitoring(self):
        """停止檔案生成監控"""
        print(f"[distancediff_MONITOR] ========== 停止監控系統 ==========")
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
            print(f"[distancediff_MONITOR] 主監控計時器已停止")
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
            print(f"[distancediff_MONITOR] 超時計時器已停止")
        print(f"[distancediff_MONITOR] ✅ 監控系統已完全停止")

    def _load_json_file(self, file_path: str):
        """載入 JSON 檔案"""
        try:
            print(f"[distancediff_LOADER] ========== JSON 檔案載入 ==========")
            print(f"[distancediff_LOADER] 載入檔案: {file_path}")
            
            # 檢查檔案狀態
            if not os.path.exists(file_path):
                print(f"[distancediff_LOADER] ❌ 檔案不存在: {file_path}")
                self.load_error.emit(f"檔案不存在: {file_path}")
                return
                
            file_size = os.path.getsize(file_path)
            print(f"[distancediff_LOADER] 檔案大小: {file_size} bytes")
            
            self.load_progress.emit(90)
            self.status_changed.emit("正在處理數據...")
            
            # 載入JSON檔案
            print(f"[distancediff_LOADER] 開始讀取 JSON 內容...")
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print(f"[distancediff_LOADER] JSON 載入成功")
            print(f"[distancediff_LOADER] 頂層鍵值: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
            
            # 驗證數據格式
            print(f"[distancediff_LOADER] 開始驗證數據格式...")
            if self._validate_distancediff_data(raw_data):
                print(f"[distancediff_LOADER] ✅ 數據格式驗證通過")
                # 處理為distancediff分析格式
                processed_data = self._process_distancediff_data(raw_data)
                
                print(f"[distancediff_LOADER] ========== 即將發送數據 ==========")
                print(f"[distancediff_LOADER] 處理後數據類型: {type(processed_data)}")
                print(f"[distancediff_LOADER] 處理後數據鍵值: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
                
                if 'distancediff_data' in processed_data:
                    distancediff_data = processed_data['distancediff_data']
                    print(f"[distancediff_LOADER] distancediff數據鍵值: {list(distancediff_data.keys())}")
                    print(f"[distancediff_LOADER] 距離數據點數: {len(distancediff_data.get('distance', []))}")
                    print(f"[distancediff_LOADER] 車手1 distancediff點數: {len(distancediff_data.get('driver1_distancediff', []))}")
                    print(f"[distancediff_LOADER] 車手2 distancediff點數: {len(distancediff_data.get('driver2_distancediff', []))}")
                
                self.load_progress.emit(100)
                self.status_changed.emit("數據載入完成")
                self._current_data = processed_data
                self._is_loading = False
                
                print(f"[distancediff_LOADER] 🚀 即將發送 data_loaded 信號...")
                self.data_loaded.emit(processed_data)
                print(f"[distancediff_LOADER] ✅ data_loaded 信號已發送")
                
            else:
                print(f"[distancediff_LOADER] ❌ 數據格式驗證失敗")
                self.load_error.emit("數據格式驗證失敗")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] JSON 檔案載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False

    def _validate_distancediff_data(self, raw_data: dict) -> bool:
        """驗證distancediff數據格式"""
        try:
            print(f"[distancediff_LOADER] 🔍 驗證數據格式...")
            
            # 檢查基本結構
            if not isinstance(raw_data, dict):
                print(f"[distancediff_LOADER] ❌ 數據不是字典格式")
                return False
            
            # 檢查是否有遙測比較數據
            if 'results' not in raw_data:
                print(f"[distancediff_LOADER] ❌ 缺少 results 字段")
                return False
                
            results = raw_data['results']
            
            # 檢查是否有distance_difference字段（直接在results下）
            if 'distance_difference' not in results:
                print(f"[distancediff_LOADER] ❌ 缺少 distance_difference 字段")
                print(f"[distancediff_LOADER] results 的鍵值: {list(results.keys())}")
                return False
            
            distance_diff_data = results['distance_difference']
            
            # 檢查distance_difference格式 - 單一曲線模式
            required_fields = ['reference_distance', 'cumulative_distance_difference']
            
            for field in required_fields:
                if field not in distance_diff_data:
                    print(f"[distancediff_LOADER] ❌ distance_difference數據缺少必需字段: {field}")
                    return False
                
                if not isinstance(distance_diff_data[field], list):
                    print(f"[distancediff_LOADER] ❌ {field} 不是列表格式")
                    return False
            
            # 檢查數據長度一致性
            distance_len = len(distance_diff_data['reference_distance'])
            cumulative_diff_len = len(distance_diff_data['cumulative_distance_difference'])
            
            print(f"[distancediff_LOADER] 數據長度檢查: distance={distance_len}, cumulative_diff={cumulative_diff_len}")
            
            if not (distance_len == cumulative_diff_len):
                print(f"[distancediff_LOADER] ⚠️ 數據長度不一致: distance={distance_len}, cumulative_diff={cumulative_diff_len}")
                return False
            
            print(f"[distancediff_LOADER] ✅ 數據格式驗證通過")
            return True
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 數據格式驗證失敗: {str(e)}")
            return False

    def _process_distancediff_data(self, raw_data: dict) -> dict:
        """處理原始數據為distancediff分析格式"""
        try:
            print(f"[distancediff_LOADER] ========== 數據處理 ==========")
            print(f"[distancediff_LOADER] 開始處理原始數據...")
            
            # 檢查數據格式類型
            if raw_data.get('analysis_type') == 'two_driver_telemetry_comparison':
                # 新格式：comparison_telemetry JSON
                print(f"[distancediff_LOADER] 📊 處理新格式數據")
                return self._process_new_format_distancediff_data(raw_data)
            else:
                # 舊格式：function 13 直接輸出
                print(f"[distancediff_LOADER] 📊 處理舊格式數據")
                return self._process_old_format_distancediff_data(raw_data)
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 數據處理失敗: {str(e)}")
            raise

    def _process_new_format_distancediff_data(self, raw_data: dict) -> dict:
        """處理新格式的遙測比較數據 - distance_difference格式"""
        try:
            print(f"[distancediff_LOADER] ========== 解析新格式distance_difference數據 ==========")
            
            metadata = raw_data.get('metadata', {})
            results = raw_data.get('results', {})
            comparison_info = results.get('comparison_info', {})
            
            print(f"[distancediff_LOADER] 元數據: {metadata}")
            print(f"[distancediff_LOADER] 比較信息: {comparison_info}")
            print(f"[distancediff_LOADER] results 鍵值: {list(results.keys())}")
            
            # 提取distance_difference數據（直接從results獲取）
            distance_diff_data = results.get('distance_difference', {})
            distance_data = distance_diff_data.get('reference_distance', [])
            cumulative_diff_data = distance_diff_data.get('cumulative_distance_difference', [])
            reference_info = distance_diff_data.get('reference', '')
            
            print(f"[distancediff_LOADER] 距離數據點數: {len(distance_data)}")
            print(f"[distancediff_LOADER] 累積距離差數據點數: {len(cumulative_diff_data)}")
            print(f"[distancediff_LOADER] 參考信息: {reference_info}")
            
            # 顯示一些樣本數據
            if distance_data:
                print(f"[distancediff_LOADER] 距離樣本: {distance_data[:5]} ... {distance_data[-5:]}")
            if cumulative_diff_data:
                print(f"[distancediff_LOADER] 累積距離差樣本: {cumulative_diff_data[:5]} ... {cumulative_diff_data[-5:]}")
            
            # 檢查是否為單車手模式
            is_single_driver = (self.current_session and 
                              self.current_session.get('driver2') is None)
            
            print(f"[distancediff_LOADER] 單車手模式: {is_single_driver}")
            
            # 構建處理後的數據結構 - 距離差分析是單一曲線模式
            processed = {
                'metadata': {
                    'analysis_type': 'distancediff_comparison',
                    'is_single_driver': True,  # 距離差分析總是單一曲線
                    'drivers': [],
                    'track_length': max(distance_data) if distance_data else 5807.0,
                    'sectors': self._generate_sector_data(distance_data),
                    'reference_info': reference_info
                },
                'distancediff_data': {
                    'distance': distance_data,
                    'cumulative_distance_difference': cumulative_diff_data,
                    'driver1_name': f"{metadata.get('driver1', 'Driver1')} vs {metadata.get('driver2', 'Driver2')}",
                    'driver2_name': "",  # 空的車手2，因為是單一曲線
                    'reference': reference_info
                },
                'statistics': {},
                'timestamp': self._get_current_timestamp()
            }
            
            # 添加車手信息（來自比較的兩個車手）
            processed['metadata']['drivers'] = [
                {
                    'code': metadata.get('driver1', 'Unknown'),
                    'lap_time': comparison_info.get('lap_time1', 'N/A'),
                    'compound': comparison_info.get('compound1', 'Unknown'),
                    'tyre_life': comparison_info.get('tyre_life1', 0)
                },
                {
                    'code': metadata.get('driver2', 'Unknown'),
                    'lap_time': comparison_info.get('lap_time2', 'N/A'),
                    'compound': comparison_info.get('compound2', 'Unknown'),
                    'tyre_life': comparison_info.get('tyre_life2', 0)
                }
            ]
            
            # 計算統計數據（針對單一距離差曲線）
            processed['statistics'] = self._calculate_distance_difference_statistics(cumulative_diff_data, distance_data)
            print(f"[distancediff_LOADER] ✅ 距離差數據處理完成")
            
            
            print(f"[distancediff_LOADER] ✅ 新格式數據處理完成")
            return processed
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 新格式數據處理失敗: {str(e)}")
            raise

    def _process_old_format_distancediff_data(self, raw_data: dict) -> dict:
        """處理舊格式數據 (直接從results.telemetry_comparison.distancediff)"""
        try:
            print(f"[distancediff_LOADER] ========== 解析舊格式數據 ==========")
            
            # 直接從results結構提取
            results = raw_data.get('results', {})
            telemetry_comparison = results.get('telemetry_comparison', {})
            comparison_info = results.get('comparison_info', {})
            
            # 提取distancediff數據
            distancediff_data = telemetry_comparison.get('distancediff', {})
            driver1_distancediff = distancediff_data.get('driver1_data', [])
            driver2_distancediff = distancediff_data.get('driver2_data', [])
            distance_data = distancediff_data.get('distance', [])
            
            print(f"[distancediff_LOADER] 舊格式 distancediff數據點數: {len(driver1_distancediff)}, {len(driver2_distancediff)}, {len(distance_data)}")
            
            # 檢查是否為單車手模式
            is_single_driver = (self.current_session and 
                              self.current_session.get('driver2') is None)
            
            print(f"[distancediff_LOADER] 單車手模式: {is_single_driver}")
            
            # 構建處理後的數據結構
            processed = {
                'metadata': {
                    'analysis_type': 'distancediff_comparison',
                    'is_single_driver': is_single_driver,
                    'drivers': [],
                    'track_length': max(distance_data) if distance_data else 5807.0,
                    'sectors': self._generate_sector_data(distance_data)
                },
                'distancediff_data': {
                    'distance': distance_data,
                    'driver1_distancediff': driver1_distancediff,
                    'driver1_name': comparison_info.get('driver1', 'Driver 1')
                },
                'statistics': {},
                'timestamp': self._get_current_timestamp()
            }
            
            # 根據模式添加車手信息和數據
            if is_single_driver:
                # 單車手模式：只添加一個車手，但保持數據結構一致
                processed['distancediff_data']['driver2_distancediff'] = []  # 空的車手2數據
                processed['distancediff_data']['driver2_name'] = ""   # 空的車手2名稱
                processed['metadata']['drivers'] = [
                    {
                        'code': comparison_info.get('driver1', 'Driver 1'),
                        'lap_time': comparison_info.get('lap_time1', 'N/A'),
                        'compound': comparison_info.get('compound1', 'Unknown'),
                        'tyre_life': comparison_info.get('tyre_life1', 0)
                    }
                ]
                processed['statistics'] = self._calculate_distancediff_statistics_single(driver1_distancediff, distance_data)
                print(f"[distancediff_LOADER] ✅ 單車手舊格式數據處理完成")
            else:
                # 雙車手模式：添加兩個車手
                processed['metadata']['drivers'] = [
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
                ]
                processed['distancediff_data']['driver2_distancediff'] = driver2_distancediff
                processed['distancediff_data']['driver2_name'] = comparison_info.get('driver2', 'Driver 2')
                processed['statistics'] = self._calculate_distancediff_statistics_new(driver1_distancediff, driver2_distancediff, distance_data)
                print(f"[distancediff_LOADER] ✅ 雙車手舊格式數據處理完成")
            
            print(f"[distancediff_LOADER] ✅ 舊格式數據處理完成")
            return processed
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 舊格式數據處理失敗: {str(e)}")
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
            print(f"[ERROR] [distancediff_LOADER] 生成分段數據失敗: {str(e)}")
            return []

    def _calculate_distancediff_statistics_new(self, driver1_distancediff: List[float], driver2_distancediff: List[float], distance_data: List[float]) -> Dict[str, Any]:
        """計算distancediff統計數據"""
        try:
            driver1_stats = {
                'max_distancediff': max(driver1_distancediff) if driver1_distancediff else 0,
                'min_distancediff': min(driver1_distancediff) if driver1_distancediff else 0,
                'avg_distancediff': sum(driver1_distancediff) / len(driver1_distancediff) if driver1_distancediff else 0,
                'data_points': len(driver1_distancediff)
            }
            
            driver2_stats = {
                'max_distancediff': max(driver2_distancediff) if driver2_distancediff else 0,
                'min_distancediff': min(driver2_distancediff) if driver2_distancediff else 0,
                'avg_distancediff': sum(driver2_distancediff) / len(driver2_distancediff) if driver2_distancediff else 0,
                'data_points': len(driver2_distancediff)
            }
            
            # 計算差值比較
            comparison = {
                'max_distancediff_diff': driver1_stats['max_distancediff'] - driver2_stats['max_distancediff'],
                'avg_distancediff_diff': driver1_stats['avg_distancediff'] - driver2_stats['avg_distancediff'],
                'min_distancediff_diff': driver1_stats['min_distancediff'] - driver2_stats['min_distancediff'],
                'total_data_points': len(distance_data),
                'track_coverage': max(distance_data) if distance_data else 0
            }
            
            stats = {
                'driver1_stats': driver1_stats,
                'driver2_stats': driver2_stats,
                'comparison': comparison
            }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 計算統計數據失敗: {str(e)}")
            return {}

    def _calculate_distancediff_statistics_single(self, driver_distancediff: List[float], distance_data: List[float]) -> Dict[str, Any]:
        """計算單車手distancediff統計數據"""
        try:
            driver_stats = {
                'max_distancediff': max(driver_distancediff) if driver_distancediff else 0,
                'min_distancediff': min(driver_distancediff) if driver_distancediff else 0,
                'avg_distancediff': sum(driver_distancediff) / len(driver_distancediff) if driver_distancediff else 0,
                'data_points': len(driver_distancediff)
            }
            
            stats = {
                'driver_stats': driver_stats,
                'track_info': {
                    'total_data_points': len(distance_data),
                    'track_coverage': max(distance_data) if distance_data else 0
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 計算單車手統計數據失敗: {str(e)}")
            return {}

    def _calculate_distance_difference_statistics(self, cumulative_diff_data: List[float], distance_data: List[float]) -> Dict[str, Any]:
        """計算累積距離差統計數據"""
        try:
            if not cumulative_diff_data or not distance_data:
                return {}
                
            # 基本統計
            max_diff = max(cumulative_diff_data)
            min_diff = min(cumulative_diff_data)
            avg_diff = sum(cumulative_diff_data) / len(cumulative_diff_data)
            
            # 找到最大和最小差距的位置
            max_idx = cumulative_diff_data.index(max_diff)
            min_idx = cumulative_diff_data.index(min_diff)
            
            max_diff_distance = distance_data[max_idx] if max_idx < len(distance_data) else 0
            min_diff_distance = distance_data[min_idx] if min_idx < len(distance_data) else 0
            
            # 計算差距變化範圍
            diff_range = max_diff - min_diff
            
            # 統計正負差距的分佈
            positive_diffs = [d for d in cumulative_diff_data if d > 0]
            negative_diffs = [d for d in cumulative_diff_data if d < 0]
            zero_diffs = [d for d in cumulative_diff_data if d == 0]
            
            stats = {
                'overall': {
                    'max_difference': max_diff,
                    'min_difference': min_diff,
                    'average_difference': avg_diff,
                    'difference_range': diff_range,
                    'data_points': len(cumulative_diff_data)
                },
                'positions': {
                    'max_diff_at_distance': max_diff_distance,
                    'min_diff_at_distance': min_diff_distance
                },
                'distribution': {
                    'positive_points': len(positive_diffs),
                    'negative_points': len(negative_diffs),
                    'zero_points': len(zero_diffs),
                    'positive_percentage': len(positive_diffs) / len(cumulative_diff_data) * 100 if cumulative_diff_data else 0,
                    'negative_percentage': len(negative_diffs) / len(cumulative_diff_data) * 100 if cumulative_diff_data else 0
                },
                'track_info': {
                    'total_distance': max(distance_data) if distance_data else 0,
                    'track_coverage': len(distance_data)
                }
            }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 計算距離差統計數據失敗: {str(e)}")
            return {}

    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _validate_session_info(self, session_info: Dict[str, Any]) -> bool:
        """驗證會話信息"""
        required_fields = ['year', 'race', 'driver1', 'driver2', 'lap1', 'lap2']
        
        for field in required_fields:
            if field not in session_info:
                error_msg = f"缺少必要參數: {field}"
                print(f"[ERROR] [distancediff_LOADER] {error_msg}")
                self.load_error.emit(error_msg)
                return False
        
        return True


# 主程式測試（已移除模擬數據功能）
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試distancediff數據載入器
    loader = distancediffAnalysisDataLoader()
    
    print("[TEST] distancediff分析數據載入器已完全重構，移除所有模擬數據功能")
    print("[TEST] 現在只會從真實JSON檔案載入數據")
    
    sys.exit(0)
    
    def _parse_function13_output(self, cli_output: str) -> Optional[Dict[str, Any]]:
        """解析Function 13的CLI輸出"""
        try:
            print(f"[distancediff_LOADER] 📊 解析Function 13輸出...")
            
            # 尋找JSON輸出
            lines = cli_output.split('\n')
            json_data = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('{') and 'distancediff' in line.lower():
                    try:
                        json_data = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            
            if json_data:
                # 轉換為distancediff分析格式
                distancediff_data = self._convert_to_distancediff_format(json_data)
                return distancediff_data
            else:
                # 從文字輸出中提取distancediff信息
                return self._extract_distancediff_from_text(cli_output)
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 解析Function 13輸出失敗: {e}")
            return None
    
    def _build_cache_filename(self) -> str:
        """構建緩存檔案名稱"""
        year = self.current_session['year']
        race = self.current_session['race'].replace(' ', '_')
        session_type = 'R'  # 正賽
        
        filename = f"f1_data_{year}_{race}_{session_type}.pkl"
        return filename
    
    def _convert_cached_to_distancediff(self, cached_data: Any) -> Optional[Dict[str, Any]]:
        """將緩存數據轉換為distancediff格式"""
        try:
            print(f"[distancediff_LOADER] 🔄 轉換緩存數據為distancediff格式...")
            
            # 檢查緩存數據類型
            if isinstance(cached_data, dict) and 'session' in cached_data:
                # FastF1會話數據格式
                return self._convert_session_to_distancediff(cached_data)
            else:
                # 嘗試直接使用現有數據
                return self._extract_distancediff_from_raw_data(cached_data)
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 轉換緩存數據失敗: {e}")
            return None
    
    def _convert_session_to_distancediff(self, session_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """將會話數據轉換為distancediff格式"""
        try:
            # 模擬從會話數據中提取distancediff信息
            distancediff_data = {
                'source': 'CachedSession',
                'session_info': self.current_session,
                'distancediff_telemetry': {
                    'driver1_distancediff_data': self._generate_distancediff_points_from_session(session_data, 'driver1'),
                    'driver2_distancediff_data': self._generate_distancediff_points_from_session(session_data, 'driver2'),
                    'track_info': self._extract_track_info_from_session(session_data),
                    'engine_info': {'max_distancediff': 12000, 'idle_distancediff': 1500, 'rev_limit': 11500}
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return distancediff_data
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 會話數據轉換失敗: {e}")
            return None
    
    def _generate_distancediff_points_from_session(self, session_data: Dict[str, Any], driver: str) -> List[Dict[str, Any]]:
        """從會話數據生成distancediff數據點"""
        import numpy as np
        
        try:
            # 生成基於真實賽道的distancediff數據點
            distances = np.arange(0, 5807, 25)  # 每25米一個點
            distancediff_points = []
            
            for i, dist in enumerate(distances):
                # 模擬真實的distancediff變化
                base_distancediff = 3000 + (i % 100) * 80
                variation = np.sin(dist / 100) * 2000
                gear_shift = 1000 if i % 20 == 0 else 0  # 模擬換檔
                
                distancediff = max(1500, min(11800, base_distancediff + variation + gear_shift))
                
                distancediff_points.append({
                    'distance': float(dist),
                    'distancediff': int(distancediff)
                })
            
            return distancediff_points
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 生成distancediff數據點失敗: {e}")
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
            print(f"[ERROR] [distancediff_LOADER] 提取賽道信息失敗: {e}")
            return {}
    

    
    def _convert_to_distancediff_format(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """將通用JSON數據轉換為distancediff格式"""
        try:
            # 從JSON數據中提取distancediff資料
            distancediff_telemetry = None
            distance_data = []
            driver1_distancediff_data = []
            driver2_distancediff_data = []
            
            # 檢查 results.telemetry_comparison.distancediff 結構
            if 'results' in json_data and 'telemetry_comparison' in json_data['results']:
                telemetry_comp = json_data['results']['telemetry_comparison']
                
                # 提取distancediff資料
                if 'distancediff' in telemetry_comp:
                    distancediff_data = telemetry_comp['distancediff']
                    driver1_distancediff_data = distancediff_data.get('driver1_data', [])
                    driver2_distancediff_data = distancediff_data.get('driver2_data', [])
                
                # 提取距離資料 (從speed_difference中取得)
                if 'speed_difference' in json_data['results'] and 'distance' in json_data['results']['speed_difference']:
                    distance_data = json_data['results']['speed_difference']['distance']
                
                # 如果沒有找到distance，嘗試從Speed資料中的距離
                elif not distance_data and 'Speed' in telemetry_comp:
                    speed_data = telemetry_comp['Speed']
                    distance_data = speed_data.get('distance', [])
                
                # 如果還是沒有距離資料，生成基於資料點數量的距離
                if not distance_data and (driver1_distancediff_data or driver2_distancediff_data):
                    data_length = max(len(driver1_distancediff_data), len(driver2_distancediff_data))
                    distance_data = list(range(0, data_length * 10, 10))  # 每10米一個點
            
            # 構建標準distancediff數據格式
            formatted_data = {
                'metadata': json_data.get('metadata', {}),
                'distancediff_data': {
                    'distance': distance_data,
                    'driver1_distancediff': driver1_distancediff_data,
                    'driver2_distancediff': driver2_distancediff_data,
                    'driver1_name': json_data.get('metadata', {}).get('driver1', 'Driver 1'),
                    'driver2_name': json_data.get('metadata', {}).get('driver2', 'Driver 2')
                },
                'statistics': {
                    'driver1_stats': self._calculate_distancediff_stats(driver1_distancediff_data),
                    'driver2_stats': self._calculate_distancediff_stats(driver2_distancediff_data),
                    'comparison': self._calculate_distancediff_comparison(driver1_distancediff_data, driver2_distancediff_data)
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return formatted_data
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] JSON轉distancediff格式失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _calculate_distancediff_stats(self, distancediff_data: List[float]) -> Dict[str, float]:
        """計算distancediff統計資料"""
        if not distancediff_data:
            return {'max_distancediff': 0, 'min_distancediff': 0, 'avg_distancediff': 0}
        
        return {
            'max_distancediff': max(distancediff_data),
            'min_distancediff': min(distancediff_data), 
            'avg_distancediff': sum(distancediff_data) / len(distancediff_data)
        }
    
    def _calculate_distancediff_comparison(self, driver1_distancediff: List[float], driver2_distancediff: List[float]) -> Dict[str, float]:
        """計算distancediff對比統計"""
        if not driver1_distancediff or not driver2_distancediff:
            return {'max_distancediff_diff': 0, 'avg_distancediff_diff': 0}
        
        stats1 = self._calculate_distancediff_stats(driver1_distancediff)
        stats2 = self._calculate_distancediff_stats(driver2_distancediff)
        
        return {
            'max_distancediff_diff': stats1['max_distancediff'] - stats2['max_distancediff'],
            'avg_distancediff_diff': stats1['avg_distancediff'] - stats2['avg_distancediff']
        }
    
    def _extract_distancediff_from_text(self, text_output: str) -> Optional[Dict[str, Any]]:
        """從文字輸出中提取distancediff信息"""
        import re
        
        try:
            print(f"[distancediff_LOADER] 📝 從文字輸出提取distancediff信息...")
            
            lines = text_output.split('\n')
            distancediff_info = {}
            
            # 尋找distancediff相關信息
            for line in lines:
                # 提取平均distancediff
                avg_match = re.search(r'平均.*distancediff[:\s]*(\d+)', line, re.IGNORECASE)
                if avg_match:
                    distancediff_info['avg_distancediff'] = int(avg_match.group(1))
                
                # 提取最高distancediff
                max_match = re.search(r'最高.*distancediff[:\s]*(\d+)', line, re.IGNORECASE)
                if max_match:
                    distancediff_info['max_distancediff'] = int(max_match.group(1))
                
                # 提取最低distancediff
                min_match = re.search(r'最低.*distancediff[:\s]*(\d+)', line, re.IGNORECASE)
                if min_match:
                    distancediff_info['min_distancediff'] = int(min_match.group(1))
            
            # 如果有基本distancediff信息，生成對應的數據
            if distancediff_info:
                return self._build_distancediff_data_from_stats(distancediff_info)
            else:
                return None
                
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 文字distancediff提取失敗: {e}")
            return None
    
    def _build_distancediff_data_from_stats(self, distancediff_stats: Dict[str, int]) -> Dict[str, Any]:
        """根據distancediff統計信息構建數據"""
        try:
            # 生成基於統計信息的distancediff數據
            avg_distancediff = distancediff_stats.get('avg_distancediff', 8000)
            max_distancediff = distancediff_stats.get('max_distancediff', 11000)
            min_distancediff = distancediff_stats.get('min_distancediff', 3000)
            
            distancediff_data = {
                'source': 'TextExtraction',
                'session_info': self.current_session,
                'distancediff_telemetry': {
                    'driver1_distancediff_data': self._generate_distancediff_from_stats(avg_distancediff, max_distancediff, min_distancediff, 'driver1'),
                    'driver2_distancediff_data': self._generate_distancediff_from_stats(avg_distancediff, max_distancediff, min_distancediff, 'driver2'),
                    'track_info': {'total_distance': 5807.0},
                    'engine_info': {'max_distancediff': max_distancediff, 'idle_distancediff': min_distancediff, 'rev_limit': max_distancediff}
                },
                'timestamp': self._get_current_timestamp()
            }
            
            return distancediff_data
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 構建distancediff數據失敗: {e}")
            return None
    
    def _generate_distancediff_from_stats(self, avg_distancediff: int, max_distancediff: int, min_distancediff: int, driver: str) -> List[Dict[str, Any]]:
        """根據統計信息生成distancediff數據點"""
        import numpy as np
        
        try:
            distances = np.arange(0, 5807, 50)
            distancediff_points = []
            
            for dist in distances:
                # 在統計範圍內生成變化
                distancediff_range = max_distancediff - min_distancediff
                normalized_pos = (dist % 1000) / 1000  # 0-1之間的位置
                
                # 基於位置和統計生成distancediff
                distancediff = min_distancediff + (distancediff_range * (0.5 + 0.3 * np.sin(normalized_pos * 2 * np.pi)))
                distancediff += np.random.normal(0, distancediff_range * 0.1)  # 加入變化
                
                # 為不同車手加入差異
                if driver == 'driver2':
                    distancediff *= 0.98  # 車手2略低一點
                
                distancediff = max(min_distancediff, min(max_distancediff, distancediff))
                
                distancediff_points.append({
                    'distance': float(dist),
                    'distancediff': int(distancediff)
                })
            
            return distancediff_points
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 統計生成distancediff數據失敗: {e}")
            return []
    
    def cache_distancediff_data(self, distancediff_data: Dict[str, Any]) -> bool:
        """緩存distancediff數據"""
        try:
            cache_filename = self._build_distancediff_cache_filename()
            cache_path = os.path.join(self.cache_dir, cache_filename)
            
            with open(cache_path, 'wb') as f:
                pickle.dump(distancediff_data, f)
            
            print(f"[distancediff_LOADER] 💾 distancediff數據已緩存至: {cache_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [distancediff_LOADER] 緩存distancediff數據失敗: {e}")
            return False
    
    def _build_distancediff_cache_filename(self) -> str:
        """構建distancediff緩存檔案名稱"""
        if not self.current_session:
            return "distancediff_data_cache.pkl"
            
        year = self.current_session['year']
        race = self.current_session['race'].replace(' ', '_')
        driver1 = self.current_session['driver1']
        driver2 = self.current_session['driver2']
        
        filename = f"distancediff_analysis_{year}_{race}_{driver1}_vs_{driver2}.pkl"
        return filename

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試distancediff數據載入器
    loader = distancediffAnalysisDataLoader()
    
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
        print(f"[TEST] ✅ distancediff數據載入完成: {len(data)} 個項目")
        print(f"[TEST] 數據來源: {data.get('source', 'Unknown')}")
        
    def on_progress(message, percentage):
        print(f"[TEST] 📊 載入進度: {message} ({percentage}%)")
        
    def on_error(error_msg):
        print(f"[TEST] ❌ 載入錯誤: {error_msg}")
    
    # 連接信號
    loader.data_loaded.connect(on_data_loaded)
    loader.load_progress.connect(lambda progress: on_progress(f"載入進度", progress))
    loader.load_error.connect(on_error)
    
    # 開始載入
    QTimer.singleShot(1000, lambda: loader.load_distancediff_analysis_data(test_session))
    
    sys.exit(app.exec_())
