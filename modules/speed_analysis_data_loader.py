#!/usr/bin/env python3
"""
速度分析數據載入器模組
基於進站分析模組的成熟架構實現
支援雙車手速度對比和單車手速度分析
"""

import sys
import os
import glob
import json
import pickle
import time
from datetime import datetime
import pandas as pd
import fastf1
import subprocess
import threading
from typing import Dict, List, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal, QTimer

class SpeedAnalysisDataLoader(QObject):
    """速度分析數據載入器 - 基於進站分析模組架構"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    load_progress = pyqtSignal(int)
    load_error = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._base_path = "json"
        self._current_data = None
        self._is_loading = False
        self._generation_params = None
        
        # 檔案生成監控定時器
        self._generation_timer = QTimer()
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer()
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
    def load_speed_data(self, year: int, race: str, session: str, 
                       driver1: str, driver2: str = None, 
                       lap1: int = 1, lap2: int = 1, 
                       is_fastest_lap: bool = False) -> bool:
        """載入速度對比數據"""
        try:
            print(f"[SPEED DEBUG] ========== 開始載入速度數據 ==========")
            print(f"[SPEED DEBUG] 載入速度數據: {driver1} vs {driver2 or '單車手'}")
            print(f"[SPEED DEBUG] 詳細參數:")
            print(f"[SPEED DEBUG]   年份: {year}")
            print(f"[SPEED DEBUG]   賽站: {race}")
            print(f"[SPEED DEBUG]   賽段: {session}")
            print(f"[SPEED DEBUG]   車手1: {driver1}, 圈數: {lap1}")
            print(f"[SPEED DEBUG]   車手2: {driver2}, 圈數: {lap2}")
            print(f"[SPEED DEBUG]   最快圈: {is_fastest_lap}")
            
            # 檢測同車手同圈數的特殊情況
            if driver2 and driver1 == driver2 and lap1 == lap2:
                print(f"[SPEED DEBUG] 🔍 檢測到同車手同圈數特殊情況: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
                print(f"[SPEED DEBUG] ⚠️ 注意：這種情況 CLI -f13 會生成 comparison_type: 'same_driver' 的特殊JSON格式")
            elif driver2 and driver1 == driver2:
                print(f"[SPEED DEBUG] 🔍 檢測到同車手不同圈數情況: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            elif driver2:
                print(f"[SPEED DEBUG] 🔍 標準雙車手比較: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            else:
                print(f"[SPEED DEBUG] 🔍 單車手分析: {driver1} 第{lap1}圈")
            
            if self._is_loading:
                self.load_error.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.load_progress.emit(0)
            self.status_changed.emit(f"正在載入速度數據...")
            
            # 儲存當前參數
            self._current_params = {
                'year': year,
                'race': race,
                'session': session,
                'driver1': driver1,
                'driver2': driver2,
                'lap1': lap1,
                'lap2': lap2,
                'is_fastest_lap': is_fastest_lap
            }
            
            # 尋找對應的 JSON 檔案
            json_file = self._find_speed_data_file(year, race, session, driver1, driver2, lap1, lap2)
            print(f"[SPEED DEBUG] 搜尋結果: {json_file}")
            
            if not json_file:
                print(f"[SPEED DEBUG] ❌ 找不到現有 JSON，開始生成新檔案")
                print(f"[SPEED DEBUG] 呼叫 CLI 生成: {year} {race} {session}")
                # 呼叫 CLI 生成 JSON (異步)
                self._start_cli_generation(year, race, session, driver1, driver2, lap1, lap2)
                return True  # 返回 True 表示已啟動生成流程
            else:
                print(f"[SPEED DEBUG] ✅ 找到現有檔案，準備載入")
                
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            return True
            
        except Exception as e:
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
    
    def _find_speed_data_file(self, year: int, race: str, session: str, 
                             driver1: str, driver2: str = None, 
                             lap1: int = 1, lap2: int = 1) -> Optional[str]:
        """搜尋速度分析數據檔案"""
        try:
            print(f"[JSON_SEARCH] ========== 搜尋速度分析檔案 ==========")
            print(f"[JSON_SEARCH] 🔍 搜尋條件:")
            print(f"[JSON_SEARCH]   📅 年份: {year}")
            print(f"[JSON_SEARCH]   🏁 賽事: {race}")
            print(f"[JSON_SEARCH]   🏁 賽段: {session}")
            print(f"[JSON_SEARCH]   🏎️ 車手1: {driver1} (第{lap1}圈)")
            print(f"[JSON_SEARCH]   🏎️ 車手2: {driver2} (第{lap2}圈)")
            
            # 搜尋目錄
            search_dirs = ["json", "json_exports", "cache"]
            print(f"[JSON_SEARCH] 📂 搜尋目錄: {search_dirs}")
            
            # 構建檔案名稱搜尋模式
            if driver2:
                # 雙車手對比檔案 - 只允許精確搜尋模式，避免誤判
                filename_patterns = [
                    f"comparison_telemetry_{driver1}_{driver2}_{year}_{race}_{session}_Lap{lap1}_Lap{lap2}.json"   # 只允許模式1：精確匹配
                ]
                print(f"[JSON_SEARCH] 🔄 雙車手檔案搜尋模式（僅精確搜尋）:")
                for i, pattern in enumerate(filename_patterns, 1):
                    print(f"[JSON_SEARCH]   {i}. {pattern}")
                print(f"[JSON_SEARCH] ⚠️ 注意：雙車手模式僅使用精確搜尋，避免檔案誤判")
            else:
                # 單車手檔案
                filename_patterns = [
                    f"speed_telemetry_{driver1}_{year}_{race}_{session}_Lap{lap1}.json",
                    f"speed_telemetry_{driver1}_{year}_{race}_{session}_Lap*.json"
                ]
                print(f"[JSON_SEARCH] 👤 單車手檔案搜尋模式:")
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
            print(f"[ERROR] [SPEED] 搜尋檔案時發生錯誤: {str(e)}")
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
    
    def _start_cli_generation(self, year: int, race: str, session: str,
                             driver1: str, driver2: str = None,
                             lap1: int = 1, lap2: int = 1):
        """啟動 CLI 生成流程"""
        try:
            print(f"[SPEED DEBUG] ========== 啟動 CLI 生成流程 ==========")
            print(f"[SPEED DEBUG] 生成參數:")
            print(f"[SPEED DEBUG]   年份: {year}")
            print(f"[SPEED DEBUG]   賽站: {race}")
            print(f"[SPEED DEBUG]   賽段: {session}")
            print(f"[SPEED DEBUG]   車手1: {driver1}, 圈數: {lap1}")
            print(f"[SPEED DEBUG]   車手2: {driver2}, 圈數: {lap2}")
            
            # 儲存參數供後續使用
            self._generation_params = (year, race, session, driver1, driver2, lap1, lap2)
            
            # 啟動 CLI 生成
            success = self._generate_speed_data_via_cli(year, race, session, driver1, driver2, lap1, lap2)
            
            if success:
                print(f"[SPEED DEBUG] ✅ CLI 啟動成功，開始監控檔案生成")
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring()
            else:
                print(f"[SPEED DEBUG] ❌ CLI 啟動失敗")
                self.load_error.emit(f"啟動 CLI 生成失敗: {year} {race} {session}")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [SPEED DEBUG] 啟動生成時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    def _generate_speed_data_via_cli(self, year: int, race: str, session: str,
                                   driver1: str, driver2: str = None,
                                   lap1: int = 1, lap2: int = 1) -> bool:
        """透過 CLI 工具生成速度數據"""
        try:
            print(f"[SPEED DEBUG] ========== CLI 命令生成 ==========")
            print(f"[SPEED DEBUG] 生成速度數據: {year} {race} {session}")
            
            # 構建命令
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
                print(f"[SPEED DEBUG] 雙車手模式: {driver1} vs {driver2}")
            else:
                print(f"[SPEED DEBUG] 單車手模式: {driver1}")
            
            # 添加圈數參數
            if driver2:
                # 雙車手模式：使用 lap1 和 lap2 參數
                command.extend(["--lap1", str(lap1), "--lap2", str(lap2)])
                print(f"[SPEED DEBUG] 雙車手模式圈數設定: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
            else:
                # 單車手模式：使用 lap1 參數（車手與自己比較）
                command.extend(["--lap1", str(lap1)])
                print(f"[SPEED DEBUG] 單車手模式圈數設定: {driver1} 第{lap1}圈")
            
            print(f"[SPEED DEBUG] 完整 CLI 命令: {' '.join(command)}")
            self.status_changed.emit(f"正在生成速度數據...")
            
            # 非阻塞執行
            def run_cli():
                try:
                    print(f"[SPEED DEBUG] 🚀 開始執行 CLI 命令...")
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
                        print(f"[OK] [SPEED] CLI 執行成功")
                    else:
                        print(f"[ERROR] [SPEED] CLI 執行失敗: {stderr}")
                        
                except Exception as e:
                    print(f"[ERROR] [SPEED] CLI 執行異常: {e}")
            
            # 在背景執行緒中執行CLI
            thread = threading.Thread(target=run_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [SPEED] 啟動 CLI 失敗: {e}")
            return False
    
    def _start_generation_monitoring(self):
        """啟動檔案生成監控"""
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)
        self.status_changed.emit("正在生成數據，請稍候...")
        
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        if hasattr(self, '_generation_params'):
            year, race, session, driver1, driver2, lap1, lap2 = self._generation_params
            
            # 檢查是否有新檔案生成
            json_file = self._find_speed_data_file(year, race, session, driver1, driver2, lap1, lap2)
            
            if json_file:
                print(f"[OK] [SPEED] 檔案生成完成: {json_file}")
                
                # 停止監控
                self._stop_generation_monitoring()
                
                # 載入新生成的檔案
                QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            else:
                print(f"⏳ [SPEED] 繼續等待檔案生成...")
                
    def _on_generation_timeout(self):
        """處理生成超時"""
        print(f"[TIME] [SPEED] 檔案生成超時")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或稍後重試")
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
            print(f"[SPEED DEBUG] ========== JSON 檔案載入 ==========")
            print(f"[SPEED DEBUG] 載入檔案: {file_path}")
            
            # 檢查檔案狀態
            if not os.path.exists(file_path):
                print(f"[SPEED DEBUG] ❌ 檔案不存在: {file_path}")
                self.load_error.emit(f"檔案不存在: {file_path}")
                return
                
            file_size = os.path.getsize(file_path)
            print(f"[SPEED DEBUG] 檔案大小: {file_size} bytes")
            
            self.load_progress.emit(90)
            self.status_changed.emit("正在處理數據...")
            
            # 載入JSON檔案
            print(f"[SPEED DEBUG] 開始讀取 JSON 內容...")
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            
            print(f"[SPEED DEBUG] JSON 載入成功")
            print(f"[SPEED DEBUG] 頂層鍵值: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
            
            # 驗證數據格式
            print(f"[SPEED DEBUG] 開始驗證數據格式...")
            if self._validate_speed_data(raw_data):
                print(f"[SPEED DEBUG] ✅ 數據格式驗證通過")
                # 處理為速度分析格式
                processed_data = self._process_speed_data(raw_data)
                
                print(f"[SPEED DEBUG] ========== 即將發送數據 ==========")
                print(f"[SPEED DEBUG] 處理後數據類型: {type(processed_data)}")
                print(f"[SPEED DEBUG] 處理後數據鍵值: {list(processed_data.keys()) if isinstance(processed_data, dict) else 'Not a dict'}")
                
                if 'speed_data' in processed_data:
                    speed_data = processed_data['speed_data']
                    print(f"[SPEED DEBUG] 速度數據鍵值: {list(speed_data.keys())}")
                    print(f"[SPEED DEBUG] 距離數據點數: {len(speed_data.get('distance', []))}")
                    print(f"[SPEED DEBUG] 車手1速度點數: {len(speed_data.get('driver1_speed', []))}")
                    print(f"[SPEED DEBUG] 車手2速度點數: {len(speed_data.get('driver2_speed', []))}")
                
                self.load_progress.emit(100)
                self.status_changed.emit("數據載入完成")
                self._current_data = processed_data
                
                print(f"[SPEED DEBUG] 🚀 即將發送 data_loaded 信號...")
                self.data_loaded.emit(processed_data)
                print(f"[SPEED DEBUG] ✅ data_loaded 信號已發送")
                print(f"[OK] [SPEED DEBUG] 檔案載入並處理完成: {file_path}")
            else:
                print(f"[SPEED DEBUG] ❌ 數據格式驗證失敗")
                self.load_error.emit("載入的數據格式無效")
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] [SPEED DEBUG] JSON 解析錯誤: {e}")
            self.load_error.emit(f"JSON 解析錯誤: {str(e)}")
        except Exception as e:
            print(f"[ERROR] [SPEED DEBUG] 檔案載入失敗: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"檔案載入失敗: {str(e)}")
        
        finally:
            self._is_loading = False
    
    def _validate_speed_data(self, data: dict) -> bool:
        """驗證速度數據格式 - 支援新舊兩種格式"""
        try:
            print(f"[SPEED DEBUG] ========== 數據格式驗證 ==========")
            print(f"[SPEED DEBUG] 數據類型: {type(data)}")
            
            if not isinstance(data, dict):
                print(f"[SPEED DEBUG] ❌ 數據不是字典格式")
                return False
                
            print(f"[SPEED DEBUG] 數據鍵值: {list(data.keys())}")
            
            # 檢查數據格式類型
            if 'analysis_type' in data and data.get('analysis_type') == 'two_driver_telemetry_comparison':
                # 新格式：comparison_telemetry JSON
                print(f"[SPEED DEBUG] 📊 檢測到新格式：遙測比較數據")
                required_fields = ['analysis_type', 'metadata', 'results']
                
                for field in required_fields:
                    if field not in data:
                        print(f"[SPEED DEBUG] ❌ 缺少必要欄位: {field}")
                        return False
                    else:
                        print(f"[SPEED DEBUG] ✅ 找到欄位: {field}")
                
                # 檢查 results 結構
                results = data.get('results', {})
                if 'telemetry_comparison' not in results:
                    print(f"[SPEED DEBUG] ❌ 缺少遙測比較數據")
                    return False
                
                telemetry_data = results.get('telemetry_comparison', {})
                if 'Speed' not in telemetry_data:
                    print(f"[SPEED DEBUG] ❌ 缺少速度數據")
                    return False
                    
                print(f"[SPEED DEBUG] ✅ 新格式驗證通過")
                return True
                
            else:
                # 舊格式：function 13 直接輸出
                print(f"[SPEED DEBUG] 📊 檢測到舊格式：功能13輸出")
                required_fields = ['function_id', 'analysis_type', 'data']
                
                for field in required_fields:
                    if field not in data:
                        print(f"[SPEED DEBUG] ❌ 缺少必要欄位: {field}")
                        return False
                    else:
                        print(f"[SPEED DEBUG] ✅ 找到欄位: {field}")
                
                # 檢查功能ID
                function_id = data.get('function_id')
                print(f"[SPEED DEBUG] 功能ID: {function_id}")
                if function_id != 13:
                    print(f"[SPEED DEBUG] ❌ 功能ID不正確，期望: 13, 實際: {function_id}")
                    return False
                
                # 檢查分析類型
                analysis_type = data.get('analysis_type')
                print(f"[SPEED DEBUG] 分析類型: {analysis_type}")
                
                # 檢查數據結構
                data_section = data.get('data', {})
                print(f"[SPEED DEBUG] 數據段鍵值: {list(data_section.keys()) if isinstance(data_section, dict) else 'Not a dict'}")
                
                print(f"[SPEED DEBUG] ✅ 舊格式驗證通過")
                return True
            
        except Exception as e:
            print(f"[ERROR] [SPEED DEBUG] 數據驗證異常: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _process_speed_data(self, raw_data: dict) -> dict:
        """處理原始數據為速度分析格式 - 支援新舊兩種格式"""
        try:
            print(f"[SPEED DEBUG] ========== 數據處理 ==========")
            print(f"[SPEED DEBUG] 開始處理原始數據...")
            
            # 檢查數據格式類型
            if raw_data.get('analysis_type') == 'two_driver_telemetry_comparison':
                # 新格式：comparison_telemetry JSON
                print(f"[SPEED DEBUG] 📊 處理新格式數據")
                return self._process_new_format_data(raw_data)
            else:
                # 舊格式：function 13 直接輸出
                print(f"[SPEED DEBUG] 📊 處理舊格式數據")
                return self._process_old_format_data(raw_data)
                
        except Exception as e:
            print(f"[ERROR] 數據處理失敗: {str(e)}")
            raise
    
    def _process_new_format_data(self, raw_data: dict) -> dict:
        """處理新格式的遙測比較數據"""
        try:
            print(f"[SPEED DEBUG] ========== 解析新格式遙測數據 ==========")
            
            metadata = raw_data.get('metadata', {})
            results = raw_data.get('results', {})
            comparison_info = results.get('comparison_info', {})
            telemetry_comparison = results.get('telemetry_comparison', {})
            
            print(f"[SPEED DEBUG] 元數據: {metadata}")
            print(f"[SPEED DEBUG] 比較信息: {comparison_info}")
            print(f"[SPEED DEBUG] 遙測比較鍵值: {list(telemetry_comparison.keys())}")
            
            # 提取速度數據
            speed_data = telemetry_comparison.get('Speed', {})
            driver1_speed = speed_data.get('driver1_data', [])
            driver2_speed = speed_data.get('driver2_data', [])
            distance_data = speed_data.get('distance', [])
            
            print(f"[SPEED DEBUG] 車手1速度數據點數: {len(driver1_speed)}")
            print(f"[SPEED DEBUG] 車手2速度數據點數: {len(driver2_speed)}")
            print(f"[SPEED DEBUG] 距離數據點數: {len(distance_data)}")
            
            # 顯示一些樣本數據
            if driver1_speed:
                print(f"[SPEED DEBUG] 車手1速度樣本: {driver1_speed[:5]} ... {driver1_speed[-5:]}")
            if driver2_speed:
                print(f"[SPEED DEBUG] 車手2速度樣本: {driver2_speed[:5]} ... {driver2_speed[-5:]}")
            if distance_data:
                print(f"[SPEED DEBUG] 距離樣本: {distance_data[:5]} ... {distance_data[-5:]}")
            
            # 構建處理後的數據結構
            processed = {
                'metadata': {
                    'analysis_type': 'speed_comparison',
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
                'speed_data': {
                    'distance': distance_data,
                    'driver1_speed': driver1_speed,
                    'driver2_speed': driver2_speed,
                    'driver1_name': comparison_info.get('driver1', 'Driver 1'),
                    'driver2_name': comparison_info.get('driver2', 'Driver 2')
                },
                'statistics': self._calculate_speed_statistics_new(driver1_speed, driver2_speed, distance_data),
                'raw_data': raw_data
            }
            
            print(f"[SPEED DEBUG] ========== 處理結果摘要 ==========")
            print(f"[SPEED DEBUG] 處理後數據鍵值: {list(processed.keys())}")
            print(f"[SPEED DEBUG] 速度數據鍵值: {list(processed['speed_data'].keys())}")
            print(f"[SPEED DEBUG] 車手1名稱: {processed['speed_data']['driver1_name']}")
            print(f"[SPEED DEBUG] 車手2名稱: {processed['speed_data']['driver2_name']}")
            print(f"[SPEED DEBUG] ✅ 新格式數據處理完成")
            
            return processed
            
        except Exception as e:
            print(f"[ERROR] 新格式數據處理失敗: {str(e)}")
            raise
    
    def _process_old_format_data(self, raw_data: dict) -> dict:
        """處理舊格式的功能13輸出數據"""
        try:
            print(f"[SPEED DEBUG] 解析舊格式數據...")
            
            # 從現有JSON結構提取基本信息
            data_section = raw_data.get('data', {})
            analysis_result = data_section.get('analysis_result', {})
            driver_comparison = analysis_result.get('driver_comparison', {})
            
            print(f"[SPEED DEBUG] 數據段結構:")
            print(f"[SPEED DEBUG]   data 鍵值: {list(data_section.keys()) if isinstance(data_section, dict) else 'Not a dict'}")
            print(f"[SPEED DEBUG]   analysis_result 鍵值: {list(analysis_result.keys()) if isinstance(analysis_result, dict) else 'Not a dict'}")
            print(f"[SPEED DEBUG]   driver_comparison 鍵值: {list(driver_comparison.keys()) if isinstance(driver_comparison, dict) else 'Not a dict'}")
            
            # 提取車手資訊
            drivers_info = []
            if 'drivers' in driver_comparison:
                drivers_info = driver_comparison['drivers']
                print(f"[SPEED DEBUG] 找到車手資訊: {len(drivers_info)} 位車手")
            else:
                print(f"[SPEED DEBUG] ⚠️ 未找到車手資訊，使用預設值")
            
            # 生成處理後的數據結構
            processed = {
                'metadata': {
                    'analysis_type': 'speed_comparison',
                    'drivers': drivers_info,
                    'track_length': 5807.0,  # 預設賽道長度(可根據賽道調整)
                    'sectors': [
                        {'sector': 1, 'start_distance': 0.0, 'end_distance': 1935.0},
                        {'sector': 2, 'start_distance': 1935.0, 'end_distance': 4129.0},
                        {'sector': 3, 'start_distance': 4129.0, 'end_distance': 5807.0}
                    ]
                },
                'speed_data': self._generate_mock_speed_data(driver_comparison),
                'statistics': self._calculate_speed_statistics(driver_comparison),
                'raw_data': raw_data  # 保留原始數據供參考
            }
            
            # 填入車手信息
            if 'driver1' in driver_comparison:
                processed['metadata']['drivers'].append(
                    driver_comparison['driver1'].get('driver_code', 'Unknown')
                )
            if 'driver2' in driver_comparison:
                processed['metadata']['drivers'].append(
                    driver_comparison['driver2'].get('driver_code', 'Unknown')
                )
            
            return processed
            
        except Exception as e:
            print(f"[ERROR] [SPEED] 處理速度數據失敗: {str(e)}")
            return {}
    
    def _generate_mock_speed_data(self, driver_comparison: dict) -> dict:
        """生成模擬速度數據 (開發階段使用)"""
        try:
            import numpy as np
            
            # 生成距離點 (每50米一個點)
            distances = np.arange(0, 5807, 50)
            
            # 生成模擬速度曲線
            def generate_speed_curve(base_speed=250, variation=0):
                speeds = []
                for dist in distances:
                    # 模擬賽道特性: 直線高速、彎道低速
                    if 0 <= dist < 800:  # 起/終點直線
                        speed = base_speed + (dist / 800) * 70 + variation
                    elif 800 <= dist < 1200:  # 第一彎角區
                        speed = base_speed - 80 + np.sin((dist - 800) / 100) * 20 + variation
                    elif 1200 <= dist < 2800:  # 中段高速區
                        speed = base_speed + 60 + np.sin(dist / 200) * 15 + variation
                    elif 2800 <= dist < 3500:  # 複合彎角
                        speed = base_speed - 60 + np.cos(dist / 150) * 25 + variation
                    elif 3500 <= dist < 4800:  # 高速直線
                        speed = base_speed + 80 + (dist - 3500) / 1300 * 20 + variation
                    else:  # 最終區間
                        speed = base_speed - 40 + np.sin(dist / 100) * 30 + variation
                    
                    # 添加隨機變化
                    speed += np.random.normal(0, 3)
                    speeds.append(max(120, min(350, speed)))  # 限制在合理範圍
                
                return [{'distance': float(d), 'speed': float(s)} 
                       for d, s in zip(distances, speeds)]
            
            driver1_code = driver_comparison.get('driver1', {}).get('driver_code', 'VER')
            driver2_code = driver_comparison.get('driver2', {}).get('driver_code', 'LEC')
            
            result = {
                'driver1': {
                    'driver_code': driver1_code,
                    'speed_data': generate_speed_curve(248, 2)  # 稍快的基準速度
                }
            }
            
            # 如果有第二位車手
            if 'driver2' in driver_comparison:
                result['driver2'] = {
                    'driver_code': driver2_code,
                    'speed_data': generate_speed_curve(246, -1)  # 稍慢的基準速度
                }
            
            return result
            
        except Exception as e:
            print(f"[ERROR] [SPEED] 生成模擬數據失敗: {e}")
            return {}
    
    def _calculate_speed_statistics(self, driver_comparison: dict) -> dict:
        """計算速度統計信息"""
        try:
            # 基於模擬數據的統計計算
            stats = {
                'driver1_stats': {
                    'max_speed': 318.2,
                    'avg_speed': 246.8,
                    'min_speed': 142.3,
                    'sector_avg': {
                        'S1': 198.5,
                        'S2': 267.8,
                        'S3': 201.4
                    }
                }
            }
            
            # 如果有第二位車手
            if 'driver2' in driver_comparison:
                stats['driver2_stats'] = {
                    'max_speed': 315.7,
                    'avg_speed': 244.3,
                    'min_speed': 145.1,
                    'sector_avg': {
                        'S1': 196.8,
                        'S2': 265.2,
                        'S3': 203.1
                    }
                }
                
                stats['comparison'] = {
                    'speed_advantage': 'driver1',
                    'max_speed_diff': 2.5,
                    'avg_speed_diff': 2.5,
                    'sector_diff': {
                        'S1': 1.7,
                        'S2': 2.6,
                        'S3': -1.7
                    }
                }
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] [SPEED] 計算統計信息失敗: {e}")
            return {}
    
    def _generate_sector_data(self, distance_data: list) -> list:
        """根據距離數據生成賽道分段信息"""
        try:
            if not distance_data:
                # 預設分段（日本鈴鹿賽道）
                return [
                    {'sector': 1, 'start_distance': 0.0, 'end_distance': 1935.0},
                    {'sector': 2, 'start_distance': 1935.0, 'end_distance': 4129.0},
                    {'sector': 3, 'start_distance': 4129.0, 'end_distance': 5807.0}
                ]
            
            track_length = max(distance_data)
            return [
                {'sector': 1, 'start_distance': 0.0, 'end_distance': track_length / 3},
                {'sector': 2, 'start_distance': track_length / 3, 'end_distance': 2 * track_length / 3},
                {'sector': 3, 'start_distance': 2 * track_length / 3, 'end_distance': track_length}
            ]
        except Exception as e:
            print(f"[ERROR] 生成分段數據失敗: {e}")
            return []
    
    def _calculate_speed_statistics_new(self, driver1_speed: list, driver2_speed: list, distance_data: list = None) -> dict:
        """計算新格式速度統計信息，包含分段統計"""
        try:
            if not driver1_speed or not driver2_speed:
                return {}
            
            stats = {
                'driver1_stats': {
                    'max_speed': max(driver1_speed),
                    'min_speed': min(driver1_speed),
                    'avg_speed': sum(driver1_speed) / len(driver1_speed)
                },
                'driver2_stats': {
                    'max_speed': max(driver2_speed),
                    'min_speed': min(driver2_speed),
                    'avg_speed': sum(driver2_speed) / len(driver2_speed)
                }
            }
            
            # 計算差值
            stats['comparison'] = {
                'max_speed_diff': stats['driver1_stats']['max_speed'] - stats['driver2_stats']['max_speed'],
                'avg_speed_diff': stats['driver1_stats']['avg_speed'] - stats['driver2_stats']['avg_speed']
            }
            
            # 計算分段統計
            if distance_data and len(distance_data) == len(driver1_speed) == len(driver2_speed):
                sector_stats = self._calculate_sector_statistics(distance_data, driver1_speed, driver2_speed)
                if sector_stats:
                    stats['sector_stats'] = sector_stats
            
            return stats
            
        except Exception as e:
            print(f"[ERROR] 計算新格式統計信息失敗: {e}")
            return {}
    
    def _calculate_sector_statistics(self, distance_data: list, driver1_speed: list, driver2_speed: list) -> dict:
        """計算分段統計信息"""
        try:
            if not distance_data or not driver1_speed or not driver2_speed:
                return {}
            
            max_distance = max(distance_data)
            
            # 定義分段邊界（大約等分三段）
            sector_boundaries = [
                max_distance * 0.33,  # S1 結束
                max_distance * 0.67,  # S2 結束
                max_distance          # S3 結束
            ]
            
            sector_stats = {}
            
            for sector_num in range(1, 4):
                # 確定分段範圍
                start_dist = sector_boundaries[sector_num - 2] if sector_num > 1 else 0
                end_dist = sector_boundaries[sector_num - 1]
                
                # 找到該分段內的數據點
                sector_indices = [
                    i for i, dist in enumerate(distance_data)
                    if start_dist <= dist <= end_dist
                ]
                
                if sector_indices:
                    # 提取該分段的速度數據
                    sector_driver1_speeds = [driver1_speed[i] for i in sector_indices]
                    sector_driver2_speeds = [driver2_speed[i] for i in sector_indices]
                    
                    # 計算該分段統計
                    sector_stats[f'sector_{sector_num}'] = {
                        'driver1_max_speed': max(sector_driver1_speeds),
                        'driver1_avg_speed': sum(sector_driver1_speeds) / len(sector_driver1_speeds),
                        'driver2_max_speed': max(sector_driver2_speeds),
                        'driver2_avg_speed': sum(sector_driver2_speeds) / len(sector_driver2_speeds),
                        'start_distance': start_dist,
                        'end_distance': end_dist,
                        'data_points': len(sector_indices)
                    }
                    
                    print(f"[DEBUG] S{sector_num} 統計: 車手1最高={sector_stats[f'sector_{sector_num}']['driver1_max_speed']:.1f}, 車手2最高={sector_stats[f'sector_{sector_num}']['driver2_max_speed']:.1f}")
            
            return sector_stats
            
        except Exception as e:
            print(f"[ERROR] 計算分段統計失敗: {e}")
            return {}
