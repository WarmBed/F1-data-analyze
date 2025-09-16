#!/usr/bin/env python3
"""
F1T 進站分析 MDI 模組
基於開發設計文檔實現的車手最快進站時間排行榜 GUI 模組
使用統一CLI管理器避免編碼問題
"""

import sys
import os
import json
import datetime
import traceback
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame,
    QTabWidget, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 導入翻譯函數
from core.gui_i18n import tr

# 導入分析模組介面
from ..interfaces.analysis_module import IAnalysisModule

# 導入基礎類別
# from f1t_gui_main import PopoutSubWindow  # 不再直接繼承PopoutSubWindow

class PitstopDataManager(QObject):
    """進站數據管理器 - 負責JSON緩存和CLI備援 - 採用檔案系統監控機制"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    team_data_loaded = pyqtSignal(dict)  # 新增車隊數據載入完成信號
    team_data_reload_requested = pyqtSignal()  # 新增車隊數據重新載入請求信號
    driver_detailed_loaded = pyqtSignal(dict)  # 新增車手詳細數據載入完成信號
    driver_detailed_reload_requested = pyqtSignal()  # 新增車手詳細數據重新載入請求信號
    error_occurred = pyqtSignal(str)
    loading_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cache_dir = os.path.join(os.getcwd(), "cache")
        self.current_year = None  # 修正：初始化為 None，等待同步
        self.current_race = None  # 修正：初始化為 None，等待同步
        self.current_session = None  # 修正：初始化為 None，等待同步
        self.loading = False
        self._is_loading = False  # 載入狀態標誌
        self._generation_params = None  # 生成參數
        
        # 檔案生成監控定時器（類似賽道分析）
        self._generation_timer = QTimer()
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer()
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
    # check_json_cache 方法已移除，改用 _find_pitstop_data_file
    
    def _find_pitstop_data_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋進站數據檔案（類似賽道分析模組的 _find_track_data_file）"""
        try:
            print(f"[FOLDER] [PITSTOP] 搜尋進站數據檔案: {year} {race} {session}")
            
            # 修正：優先檢查 json/ 和 json_exports/ 目錄下的完整JSON檔案，使用正確的賽事名稱
            search_dirs = ["json", "json_exports"]  # 擴大搜尋範圍，與賽道分析一致
            
            # 構建賽事的完整名稱（加上 Grand Prix）
            race_full_names = {
                "Japan": "Japanese_Grand_Prix",
                "China": "Chinese_Grand_Prix", 
                "Belgium": "Belgian_Grand_Prix",
                "Bahrain": "Bahrain_Grand_Prix",
                "Saudi Arabia": "Saudi_Arabian_Grand_Prix",
                "Australia": "Australian_Grand_Prix",
                "Miami": "Miami_Grand_Prix",
                "Emilia Romagna": "Emilia_Romagna_Grand_Prix",
                "Monaco": "Monaco_Grand_Prix",
                "Canada": "Canadian_Grand_Prix",
                "Spain": "Spanish_Grand_Prix",
                "Austria": "Austrian_Grand_Prix",
                "Great Britain": "British_Grand_Prix",
                "Hungary": "Hungarian_Grand_Prix",
                "Netherlands": "Dutch_Grand_Prix",
                "Italy": "Italian_Grand_Prix",
                "Azerbaijan": "Azerbaijan_Grand_Prix",
                "Singapore": "Singapore_Grand_Prix",
                "United States": "United_States_Grand_Prix",
                "Mexico": "Mexican_Grand_Prix",
                "Brazil": "Brazilian_Grand_Prix",
                "Las Vegas": "Las_Vegas_Grand_Prix",
                "Qatar": "Qatar_Grand_Prix",
                "Abu Dhabi": "Abu_Dhabi_Grand_Prix"
            }
            
            # 獲取完整賽事名稱
            race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
            
            # 精確匹配模式（多種檔案命名格式）
            patterns = [
                f"driver_fastest_pitstop_ranking_{year}_{race_full_name}.json",
                f"driver_fastest_pitstop_ranking_{year}_{race.replace(' ', '_')}_Grand_Prix.json",
                f"driver_fastest_pitstop_{year}_{race_full_name}.json",
                f"driver_fastest_pitstop_{year}_{race.replace(' ', '_')}.json",
                f"pitstop_ranking_{year}_{race_full_name}.json",
                f"pitstop_ranking_{year}_{race.replace(' ', '_')}.json"
            ]
            
            # 搜尋多個目錄中的精確匹配
            for search_dir in search_dirs:
                for pattern in patterns:
                    import glob
                    search_path = os.path.join(search_dir, pattern)
                    files = glob.glob(search_path)
                    if files:
                        print(f"[FOLDER] [PITSTOP] 找到檔案: {files[0]}")
                        return files[0]  # 返回第一個匹配的檔案
            
            # 如果精確匹配失敗，嘗試模糊搜尋（類似賽道分析）
            print(f"[FOLDER] [PITSTOP] 精確搜尋失敗，嘗試模糊搜尋...")
            
            for search_dir in search_dirs:
                # 使用通配符搜尋
                import glob
                fuzzy_patterns = [
                    f"*pitstop*{year}*{session}*.json",
                    f"*pitstop*{year}*.json"
                ]
                
                for fuzzy_pattern in fuzzy_patterns:
                    search_path = os.path.join(search_dir, fuzzy_pattern)
                    files = glob.glob(search_path)
                    
                    # 動態生成賽事關鍵字
                    race_keywords = []
                    if race:
                        race_normalized = race.lower().replace(' ', '_').replace("'", "")
                        race_full = race_full_names.get(race, race)
                        race_full_lower = race_full.lower() if isinstance(race_full, str) else race.lower()
                        
                        race_keywords.extend([
                            race.lower(),
                            race_normalized,
                            race.lower().replace(' ', ''),
                            race.split()[0].lower() if ' ' in race else race.lower(),
                            race_full_lower,
                            race_full_lower.replace(' ', '_'),
                            race_full_lower.replace(' ', ''),
                        ])
                    
                    print(f"[FOLDER] [PITSTOP] 模糊搜尋關鍵字: {race_keywords}")
                    
                    # 檢查檔案是否匹配賽事關鍵字
                    for file_path in files:
                        file_name_lower = os.path.basename(file_path).lower()
                        
                        for keyword in race_keywords:
                            if keyword in file_name_lower:
                                print(f"[FOLDER] [PITSTOP] 模糊搜尋找到: {file_path}")
                                return file_path
            
            # 最後檢查cache目錄的PKL檔案
            cache_pattern = f"driver_fastest_pitstop_{year}_{race.replace(' ', '_')}_Grand_Prix.pkl"
            cache_path = os.path.join(self.cache_dir, cache_pattern)
            if os.path.exists(cache_path):
                print(f"[FOLDER] [PITSTOP] 找到PKL緩存: {cache_path}")
                return cache_path
            
            print(f"[FOLDER] [PITSTOP] 找不到檔案: {year} {race} {session}")
            return None
                
        except Exception as e:
            print(f"[ERROR] [PITSTOP] 搜尋檔案時發生錯誤: {str(e)}")
            self.error_occurred.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
    
    def _start_cli_generation(self, year: str, race: str, session: str):
        """
        啟動 CLI 生成流程 - 非阻塞方式（類似賽道分析模組）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
        """
        try:
            # 儲存參數供後續使用
            self._generation_params = (year, race, session)
            
            # 啟動 CLI 生成
            success = self._generate_pitstop_data_via_cli(year, race, session)
            
            if success:
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring(year, race, session)
            else:
                self.error_occurred.emit(f"啟動 CLI 生成失敗: {year} {race} {session}")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [CLI_GEN] 啟動生成時發生錯誤: {e}")
            self.error_occurred.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    def _start_generation_monitoring(self, year: str, race: str, session: str):
        """
        啟動檔案生成監控（類似賽道分析模組）
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段代碼
        """
        # 確保定時器存在
        if not hasattr(self, '_generation_timer'):
            self._generation_timer = QTimer()
            self._generation_timer.timeout.connect(self._check_generation_progress)
        
        if not hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer = QTimer()
            self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)
        
    def _check_generation_progress(self):
        """檢查檔案生成進度（類似賽道分析模組）"""
        if hasattr(self, '_generation_params'):
            year, race, session = self._generation_params
            
            # 檢查是否有新檔案生成
            json_file = self._find_pitstop_data_file(year, race, session)
            
            if json_file:
                print(f"[OK] [CLI_GEN] 檔案生成完成: {json_file}")
                
                # 停止監控
                self._stop_generation_monitoring()
                
                # 載入新生成的檔案
                QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            else:
                print(f"⏳ [CLI_GEN] 繼續等待檔案生成...")
                
    def _on_generation_timeout(self):
        """處理生成超時（類似賽道分析模組）"""
        print(f"[TIME] [CLI_GEN] 檔案生成超時")
        self._stop_generation_monitoring()
        self.error_occurred.emit("數據生成超時，請檢查網路連線或稍後重試")
        self._is_loading = False
        
    def _stop_generation_monitoring(self):
        """停止生成監控（類似賽道分析模組）"""
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
    
    def _generate_pitstop_data_via_cli(self, year: str, race: str, session: str) -> bool:
        """
        透過 CLI 工具生成進站數據 - 使用非阻塞方式（類似賽道分析模組）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
            
        Returns:
            bool: 請求是否成功提交（注意：不是生成是否成功）
        """
        try:
            print(f"[CLI] [GENERATE] 開始生成進站數據: {year} {race} {session}")
            
            # 直接調用 CLI 分析腳本
            import subprocess
            import threading
            
            # 構建命令
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "3",  # 功能3: 車手最快進站時間排行榜
                "-y", str(year),
                "-r", race,
                "-s", session
            ]
            
            print(f"[CLI] [GENERATE] 執行命令: {' '.join(command)}")
            
            # 非阻塞執行
            def run_cli():
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        print(f"[OK] [CLI_GEN] CLI 執行成功")
                    else:
                        print(f"[ERROR] [CLI_GEN] CLI 執行失敗: {stderr}")
                        
                except Exception as e:
                    print(f"[ERROR] [CLI_GEN] CLI 執行異常: {e}")
            
            # 在後台執行 CLI
            thread = threading.Thread(target=run_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [CLI_GEN] 啟動 CLI 失敗: {e}")
            return False
    
    def _load_json_file(self, file_path: str) -> None:
        """
        載入 JSON 檔案（類似賽道分析模組）
        
        Args:
            file_path: JSON 檔案路徑
        """
        try:
            print(f"[LOAD] [JSON] 開始載入檔案: {file_path}")
            self.loading_progress.emit(90)
            
            # 判斷檔案類型並載入
            if file_path.endswith('.pkl'):
                import pickle
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # 驗證數據格式
            if self._validate_pitstop_data(data):
                self.loading_progress.emit(100)
                self.status_changed.emit("數據載入完成")
                self.data_loaded.emit(data)
                print(f"[OK] [JSON] 檔案載入完成: {file_path}")
            else:
                self.error_occurred.emit("載入的數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] [JSON] 檔案載入失敗: {e}")
            self.error_occurred.emit(f"檔案載入失敗: {str(e)}")
        
        finally:
            self._is_loading = False
    
    def _validate_pitstop_data(self, data: dict) -> bool:
        """
        驗證進站數據格式（類似賽道分析模組）
        
        Args:
            data: 要驗證的數據
            
        Returns:
            bool: 數據是否有效
        """
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                print(f"[ERROR] [VALIDATE] 數據不是字典格式")
                return False
                
            # 檢查不同可能的數據格式
            records = None
            
            # 格式1: 新的標準格式 - data 陣列
            if 'data' in data:
                records_data = data['data']
                print(f"[INFO] [VALIDATE] 檢測到標準格式：data 欄位")
                
                # 檢查 data 是陣列還是物件
                if isinstance(records_data, list):
                    records = records_data
                    print(f"[INFO] [VALIDATE] data 是陣列格式")
                elif isinstance(records_data, dict):
                    # 新格式：data 是物件，車手代碼作為鍵值
                    print(f"[INFO] [VALIDATE] data 是物件格式，車手鍵值：{list(records_data.keys())[:5]}...")
                    # 將所有車手的進站記錄合併成一個陣列
                    records = []
                    for driver_code, driver_records in records_data.items():
                        if isinstance(driver_records, list):
                            for record in driver_records:
                                # 確保每個記錄都有 driver 欄位
                                if 'driver' not in record and 'driver_code' not in record:
                                    record['driver'] = driver_code
                                records.append(record)
                    print(f"[INFO] [VALIDATE] 合併後的進站記錄數量：{len(records)}")
                else:
                    print(f"[ERROR] [VALIDATE] data 欄位格式不支援：{type(records_data)}")
                    return False
            # 格式2: 舊格式 - driver_fastest_pitstops
            elif 'driver_fastest_pitstops' in data:
                records = data['driver_fastest_pitstops']
                print(f"[INFO] [VALIDATE] 檢測到舊格式：driver_fastest_pitstops")
            # 格式3: 其他格式 - pitstop_ranking
            elif 'pitstop_ranking' in data:
                records = data['pitstop_ranking']
                print(f"[INFO] [VALIDATE] 檢測到其他格式：pitstop_ranking")
            # 格式4: 直接是陣列
            elif isinstance(data, list):
                records = data
                print(f"[INFO] [VALIDATE] 檢測到直接陣列格式")
            else:
                print(f"[ERROR] [VALIDATE] 找不到進站數據記錄，可用欄位：{list(data.keys())}")
                return False
                
            if not records:
                print(f"[ERROR] [VALIDATE] 進站數據記錄為空")
                return False
                
            if not isinstance(records, list):
                print(f"[ERROR] [VALIDATE] 進站數據不是陣列格式")
                return False
                
            # 驗證第一筆記錄的欄位
            first_record = records[0]
            print(f"[INFO] [VALIDATE] 第一筆記錄欄位：{list(first_record.keys())}")
            
            # 檢查不同可能的欄位名稱
            driver_field = None
            time_field = None
            
            # 檢查車手欄位
            for field in ['driver', 'driver_code', 'driver_name']:
                if field in first_record:
                    driver_field = field
                    break
                    
            # 檢查時間欄位  
            for field in ['fastest_time', 'fastest_pitstop_time', 'pitstop_time', 'time', 'pit_duration']:
                if field in first_record:
                    time_field = field
                    break
            
            if not driver_field:
                print(f"[ERROR] [VALIDATE] 找不到車手欄位，可用欄位：{list(first_record.keys())}")
                return False
                
            if not time_field:
                print(f"[ERROR] [VALIDATE] 找不到時間欄位，可用欄位：{list(first_record.keys())}")
                return False
                    
            print(f"[OK] [VALIDATE] 進站數據驗證通過，記錄數量：{len(records)}")
            print(f"[OK] [VALIDATE] 車手欄位：{driver_field}，時間欄位：{time_field}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 數據驗證異常: {e}")
            return False
    
    # 舊的統一CLI管理器方法已移除，改用檔案系統監控機制
    
    def load_data(self, year: str, race: str, session: str):
        """載入數據的主要方法（類似賽道分析模組）"""
        try:
            print(f"[FOLDER] [DATA_MANAGER] 開始載入進站數據: {year} {race} {session}")
            
            if self._is_loading:
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            
            # 儲存當前參數
            self.current_year = year
            self.current_race = race
            self.current_session = session
            
            # 尋找對應的 JSON 檔案
            json_file = self._find_pitstop_data_file(year, race, session)
            print(f"[FOLDER] [DATA_MANAGER] 搜尋到的檔案: {json_file}")
            
            if not json_file:
                print(f"[FOLDER] [DATA_MANAGER] 找不到現有 JSON，開始生成: {year} {race} {session}")
                # 呼叫 CLI 生成 JSON (異步)
                self._start_cli_generation(year, race, session)
                return True  # 返回 True 表示已啟動生成流程
                    
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
    
    def _find_team_pitstop_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋車隊進站數據檔案"""
        try:
            print(f"[FOLDER] [TEAM_PITSTOP] 搜尋車隊進站數據檔案: {year} {race} {session}")
            
            # 搜尋目錄
            search_dirs = ["json", "json_exports", "cache"]
            
            # 構建賽事的完整名稱
            race_full_names = {
                "Japan": "Japanese_Grand_Prix",
                "China": "Chinese_Grand_Prix", 
                "Belgium": "Belgian_Grand_Prix",
                "Bahrain": "Bahrain_Grand_Prix",
                "Saudi Arabia": "Saudi_Arabian_Grand_Prix",
                "Australia": "Australian_Grand_Prix",
                "Miami": "Miami_Grand_Prix",
                "Emilia Romagna": "Emilia_Romagna_Grand_Prix",
                "Monaco": "Monaco_Grand_Prix",
                "Canada": "Canadian_Grand_Prix",
                "Spain": "Spanish_Grand_Prix",
                "Austria": "Austrian_Grand_Prix",
                "Great Britain": "British_Grand_Prix",
                "Hungary": "Hungarian_Grand_Prix",
                "Netherlands": "Dutch_Grand_Prix",
                "Italy": "Italian_Grand_Prix",
                "Azerbaijan": "Azerbaijan_Grand_Prix",
                "Singapore": "Singapore_Grand_Prix",
                "United States": "United_States_Grand_Prix",
                "Mexico": "Mexican_Grand_Prix",
                "Brazil": "Brazilian_Grand_Prix",
                "Las Vegas": "Las_Vegas_Grand_Prix",
                "Qatar": "Qatar_Grand_Prix",
                "Abu Dhabi": "Abu_Dhabi_Grand_Prix"
            }
            
            # 獲取完整賽事名稱
            race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
            
            # 精確匹配模式
            patterns = [
                f"team_pitstop_ranking_{year}_{race_full_name}.json",
                f"team_pitstop_{year}_{race_full_name}.json",
                f"team_pitstop_ranking_{year}_{race.replace(' ', '_')}.json",
            ]
            
            # 搜尋多個目錄中的精確匹配
            for search_dir in search_dirs:
                for pattern in patterns:
                    search_path = os.path.join(search_dir, pattern)
                    if os.path.exists(search_path):
                        print(f"[FOLDER] [TEAM_PITSTOP] 找到車隊檔案: {search_path}")
                        return search_path
            
            print(f"[FOLDER] [TEAM_PITSTOP] 找不到車隊檔案: {year} {race} {session}")
            return None
                
        except Exception as e:
            print(f"[ERROR] [TEAM_PITSTOP] 搜尋車隊檔案時發生錯誤: {str(e)}")
            return None
    
    def load_team_data(self, year: str, race: str, session: str):
        """載入車隊數據"""
        try:
            print(f"[FOLDER] [TEAM_DATA_MANAGER] 開始載入車隊進站數據: {year} {race} {session}")
            
            # 尋找車隊 JSON 檔案
            json_file = self._find_team_pitstop_file(year, race, session)
            print(f"[FOLDER] [TEAM_DATA_MANAGER] 搜尋到的車隊檔案: {json_file}")
            
            if json_file:
                # 載入現有 JSON
                QTimer.singleShot(10, lambda: self._load_team_json_file(json_file))
            else:
                # 🔧 修正：如果找不到車隊檔案，自動呼叫CLI生成
                print(f"[CLI] [TEAM_GENERATE] 找不到車隊JSON檔案，嘗試生成: {year} {race} {session}")
                success = self._generate_team_data_via_cli(year, race, session)
                if not success:
                    self.error_occurred.emit("找不到車隊進站數據檔案，且CLI生成失敗")
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"車隊數據載入失敗: {str(e)}")
            return False
    
    def _load_team_json_file(self, file_path: str):
        """載入車隊 JSON 檔案"""
        try:
            print(f"[LOAD] [TEAM_JSON] 載入車隊 JSON 檔案: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證車隊數據
            if self._validate_team_pitstop_data(data):
                print(f"[OK] [TEAM_JSON] 車隊 JSON 載入成功")
                self.team_data_loaded.emit(data)
            else:
                self.error_occurred.emit("車隊進站數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] [TEAM_JSON] 車隊 JSON 載入失敗: {e}")
            self.error_occurred.emit(f"車隊 JSON 載入失敗: {str(e)}")
    
    def _validate_team_pitstop_data(self, data: Dict[str, Any]) -> bool:
        """驗證車隊進站數據格式"""
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                return False
            
            # 檢查 function_id 是否為 4 (車隊進站分析)
            if data.get("function_id") != 4:
                print(f"[ERROR] [VALIDATE] 車隊數據 function_id 不匹配: {data.get('function_id')}")
                return False
            
            # 提取記錄
            records = data.get("data", [])
            if not records or not isinstance(records, list):
                return False
                
            # 驗證第一筆記錄的欄位
            first_record = records[0]
            required_fields = ["team", "fastest_time", "average_time", "pitstop_count"]
            
            for field in required_fields:
                if field not in first_record:
                    print(f"[ERROR] [VALIDATE] 車隊數據缺少必要欄位: {field}")
                    return False
                    
            print(f"[OK] [VALIDATE] 車隊數據驗證通過，記錄數量：{len(records)}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 車隊數據驗證異常: {e}")
            return False
    
    def _generate_team_data_via_cli(self, year: str, race: str, session: str) -> bool:
        """透過CLI生成車隊進站數據"""
        try:
            import subprocess
            import threading
            
            # 建構CLI命令 - 功能4: 車隊進站時間排行榜
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "4",  # 功能4: 車隊進站時間排行榜
                "-y", str(year),
                "-r", race,
                "-s", session
            ]
            
            print(f"[CLI] [TEAM_GENERATE] 執行車隊數據生成命令: {' '.join(command)}")
            
            # 非阻塞執行
            def run_team_cli():
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        print(f"[OK] [TEAM_CLI_GEN] 車隊CLI 執行成功")
                        # 🔧 修正：CLI執行成功後，通知主模組刷新
                        # 使用信號機制，在主執行緒中處理
                        print(f"[RELOAD] [TEAM_CLI_GEN] 發送車隊數據重新載入信號")
                        self.team_data_reload_requested.emit()
                    else:
                        print(f"[ERROR] [TEAM_CLI_GEN] 車隊CLI 執行失敗: {stderr}")
                        self.error_occurred.emit(f"車隊CLI生成失敗: {stderr}")
                        
                except Exception as e:
                    print(f"[ERROR] [TEAM_CLI_GEN] 車隊CLI 執行異常: {e}")
                    self.error_occurred.emit(f"車隊CLI執行異常: {str(e)}")
            
            # 在後台執行車隊 CLI
            thread = threading.Thread(target=run_team_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [TEAM_CLI_GEN] 啟動車隊CLI失敗: {e}")
            return False
    
    def _trigger_reload_signal(self):
        """觸發重新載入信號給主模組"""
        print(f"[SIGNAL] [TEAM_RELOAD] 發送車隊數據重新載入信號")
        self.team_data_reload_requested.emit()

    # === 車手進站詳細記錄支援 ===
    
    def _find_driver_detailed_file(self, year: str, race: str, session: str) -> Optional[str]:
        """搜尋車手進站詳細數據檔案（支援多格式匹配）"""
        try:
            print(f"[FOLDER] [DRIVER_DETAILED] 搜尋車手詳細檔案: {year} {race} {session}")
            
            search_dirs = ["json", "json_exports", "cache"]
            
            # 賽事名稱映射
            race_full_names = {
                "Japan": "Japanese_Grand_Prix",
                "China": "Chinese_Grand_Prix", 
                "Belgium": "Belgian_Grand_Prix",
                "Miami": "Miami_Grand_Prix",
                "Bahrain": "Bahrain_Grand_Prix",
                "Saudi Arabia": "Saudi_Arabian_Grand_Prix",
                "Australia": "Australian_Grand_Prix",
                "Emilia Romagna": "Emilia_Romagna_Grand_Prix",
                "Monaco": "Monaco_Grand_Prix",
                "Canada": "Canadian_Grand_Prix",
                "Spain": "Spanish_Grand_Prix",
                "Austria": "Austrian_Grand_Prix",
                "Great Britain": "British_Grand_Prix",
                "Hungary": "Hungarian_Grand_Prix",
                "Netherlands": "Dutch_Grand_Prix",
                "Italy": "Italian_Grand_Prix",
                "Azerbaijan": "Azerbaijan_Grand_Prix",
                "Singapore": "Singapore_Grand_Prix",
                "United States": "United_States_Grand_Prix",
                "Mexico": "Mexican_Grand_Prix",
                "Brazil": "Brazilian_Grand_Prix",
                "Las Vegas": "Las_Vegas_Grand_Prix",
                "Qatar": "Qatar_Grand_Prix",
                "Abu Dhabi": "Abu_Dhabi_Grand_Prix"
            }
            
            race_full_name = race_full_names.get(race, f"{race.replace(' ', '_')}_Grand_Prix")
            
            patterns = [
                f"driver_detailed_pitstop_records_{year}_{race_full_name}.json",
                f"driver_detailed_pitstops_{year}_{race_full_name}.json",
                f"driver_detailed_pitstop_records_{year}_{race.replace(' ', '_')}.json",
                f"driver_detailed_pitstop_records_{year}_{race}_{session}.json",  # 新增：支援 _R 格式
                f"driver_detailed_pitstops_{year}_{race}_{session}.json",
            ]
            
            # 搜尋多個目錄中的精確匹配
            for search_dir in search_dirs:
                for pattern in patterns:
                    import glob
                    search_path = os.path.join(search_dir, pattern)
                    files = glob.glob(search_path)
                    if files:
                        print(f"[FOLDER] [DRIVER_DETAILED] 找到檔案: {files[0]}")
                        return files[0]
            
            print(f"[FOLDER] [DRIVER_DETAILED] 找不到檔案: {year} {race} {session}")
            return None
                
        except Exception as e:
            print(f"[ERROR] [DRIVER_DETAILED] 搜尋檔案時發生錯誤: {str(e)}")
            return None

    def load_driver_detailed_data(self, year: str, race: str, session: str):
        """載入車手進站詳細數據 - 支援JSON優先+CLI後備"""
        try:
            print(f"[FOLDER] [DRIVER_DETAILED_MANAGER] 開始載入車手詳細數據: {year} {race} {session}")
            
            # 檢查現有JSON檔案
            json_file = self._find_driver_detailed_file(year, race, session)
            print(f"[FOLDER] [DRIVER_DETAILED_MANAGER] 搜尋到的檔案: {json_file}")
            
            if json_file:
                # 載入現有JSON
                QTimer.singleShot(10, lambda: self._load_driver_detailed_json(json_file))
            else:
                # 自動觸發CLI生成
                print(f"[CLI] [DRIVER_DETAILED_GENERATE] 找不到JSON檔案，嘗試生成: {year} {race} {session}")
                success = self._generate_driver_detailed_via_cli(year, race, session)
                if not success:
                    self.error_occurred.emit("找不到車手詳細進站數據檔案，且CLI生成失敗")
            
            return True
            
        except Exception as e:
            self.error_occurred.emit(f"車手詳細數據載入失敗: {str(e)}")
            return False

    def _load_driver_detailed_json(self, file_path: str):
        """載入車手詳細JSON檔案"""
        try:
            print(f"[LOAD] [DRIVER_DETAILED_JSON] 載入車手詳細 JSON 檔案: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 驗證車手詳細數據
            if self._validate_driver_detailed_data(data):
                print(f"[OK] [DRIVER_DETAILED_JSON] 車手詳細 JSON 載入成功")
                self.driver_detailed_loaded.emit(data)
            else:
                self.error_occurred.emit("車手詳細進站數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] [DRIVER_DETAILED_JSON] 車手詳細 JSON 載入失敗: {e}")
            self.error_occurred.emit(f"車手詳細 JSON 載入失敗: {str(e)}")

    def _validate_driver_detailed_data(self, data: Dict[str, Any]) -> bool:
        """驗證車手詳細進站數據格式"""
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                return False
            
            # 檢查新格式：{ "success": true, "data": {...} }
            if data.get("success") is True and "data" in data:
                records = data["data"]
                print(f"[INFO] [VALIDATE] 檢測到新格式車手詳細數據")
            # 檢查舊格式：{ "function_id": 5, "data": {...} }
            elif data.get("function_id") == 5:
                records = data.get("data", {})
                print(f"[INFO] [VALIDATE] 檢測到舊格式車手詳細數據")
            else:
                print(f"[ERROR] [VALIDATE] 車手詳細數據格式不匹配")
                return False
            
            # 驗證 data 部分是否為物件（車手代碼為鍵值）
            if not records or not isinstance(records, dict):
                print(f"[ERROR] [VALIDATE] 車手詳細數據不是物件格式")
                return False
                
            # 驗證第一個車手記錄的欄位
            for driver, pitstops in records.items():
                if not isinstance(pitstops, list) or not pitstops:
                    continue
                    
                first_pitstop = pitstops[0]
                required_fields = ["pitstop_number", "lap_number", "pit_duration", "team"]
                
                for field in required_fields:
                    if field not in first_pitstop:
                        print(f"[ERROR] [VALIDATE] 車手詳細數據缺少必要欄位: {field}")
                        return False
                
                print(f"[OK] [VALIDATE] 車手詳細數據驗證通過，記錄數量：{len(records)}")
                return True
                
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 車手詳細數據驗證失敗: {e}")
            return False

    def _generate_driver_detailed_via_cli(self, year: str, race: str, session: str) -> bool:
        """透過CLI生成車手進站詳細數據（後台執行）"""
        try:
            import subprocess
            import threading
            
            # 建構CLI命令 - 功能5: 車手進站詳細記錄
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "5",  # 功能5: 車手進站詳細記錄
                "-y", str(year),
                "-r", race,
                "-s", session
            ]
            
            print(f"[CLI] [DRIVER_DETAILED_GENERATE] 執行車手詳細數據生成命令: {' '.join(command)}")
            
            # 非阻塞執行
            def run_driver_detailed_cli():
                try:
                    process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding='utf-8',
                        cwd=os.getcwd()
                    )
                    
                    stdout, stderr = process.communicate()
                    
                    if process.returncode == 0:
                        print(f"[OK] [DRIVER_DETAILED_CLI_GEN] 車手詳細CLI 執行成功")
                        # 使用信號機制，在主執行緒中處理
                        print(f"[RELOAD] [DRIVER_DETAILED_CLI_GEN] 發送車手詳細數據重新載入信號")
                        self.driver_detailed_reload_requested.emit()
                    else:
                        print(f"[ERROR] [DRIVER_DETAILED_CLI_GEN] 車手詳細CLI 執行失敗: {stderr}")
                        self.error_occurred.emit(f"車手詳細CLI生成失敗: {stderr}")
                        
                except Exception as e:
                    print(f"[ERROR] [DRIVER_DETAILED_CLI_GEN] 車手詳細CLI 執行異常: {e}")
                    self.error_occurred.emit(f"車手詳細CLI執行異常: {str(e)}")
            
            # 在後台執行車手詳細 CLI
            thread = threading.Thread(target=run_driver_detailed_cli, daemon=True)
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"[ERROR] [DRIVER_DETAILED_CLI_GEN] 啟動車手詳細CLI失敗: {e}")
            return False

class PitstopRankingWidget(QWidget):
    """進站排行榜主要內容Widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ranking_data = []
        self.current_data = {}  # 儲存當前數據，用於導出功能
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 控制面板 - 隱藏
        # control_panel = self.create_control_panel()
        # layout.addWidget(control_panel)
        
        # 主要表格
        self.table_widget = self.create_ranking_table()
        layout.addWidget(self.table_widget)
        
        # 狀態面板 - 隱藏
        # status_panel = self.create_status_panel()
        # layout.addWidget(status_panel)
        
        # 創建隱藏的控制組件但不顯示（保持功能性）
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        
        self.status_label = QLabel()
        self.status_label.setVisible(False)
        
        self.data_source_label = QLabel()
        self.data_source_label.setVisible(False)
        
        self.update_time_label = QLabel()
        self.update_time_label.setVisible(False)
    
    def create_control_panel(self) -> QWidget:
        """創建控制面板"""
        panel = QFrame()
        panel.setObjectName("ControlPanel")
        panel.setFixedHeight(40)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 刷新按鈕
        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setToolTip("重新載入進站排行榜數據")
        layout.addWidget(self.refresh_btn)
        
        # 匯出按鈕
        self.export_btn = QPushButton("📤 匯出")
        self.export_btn.setToolTip("匯出進站排行榜數據")
        layout.addWidget(self.export_btn)
        
        # 設定按鈕
        self.settings_btn = QPushButton("⚙️ 設定")
        self.settings_btn.setToolTip("顯示設定對話框")
        layout.addWidget(self.settings_btn)
        
        layout.addStretch()  # 推送按鈕到左側
        
        # 載入進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(200)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def create_ranking_table(self) -> QTableWidget:
        """創建排行榜表格"""
        table = QTableWidget()
        table.setObjectName("PitstopRankingTable")
        
        # 設置表格欄位 (根據設計文檔，已移除進站類型和輪胎類型)
        headers = ["Rank", "Driver Code", "Driver Name", "Fastest Time", "Gap to 1st", "Pit Lap"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        
        # 設置表格屬性
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setSortingEnabled(True)
        
        # 設置欄位寬度 - 響應式設計，適應小視窗
        header = table.horizontalHeader()
        
        # 設定初始寬度
        table.setColumnWidth(0, 30)   # 排名
        table.setColumnWidth(1, 45)   # 車手代碼
        table.setColumnWidth(2, 100)  # 車手全名
        table.setColumnWidth(3, 60)   # 最快時間
        table.setColumnWidth(4, 65)   # 與第一名差距
        table.setColumnWidth(5, 40)   # 進站圈數
        
        # 所有欄位都設為可手動調整
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
        # 🔧 新增：響應式調整功能已移除，改為手動調整
        
        return table
    
    def create_status_panel(self) -> QWidget:
        """創建狀態面板"""
        panel = QFrame()
        panel.setObjectName("StatusPanel")
        panel.setFixedHeight(30)
        
        layout = QHBoxLayout(panel)
        layout.setContentsMargins(5, 2, 5, 2)
        
        # 數據來源標籤
        self.data_source_label = QLabel("📄 數據來源: 未載入")
        layout.addWidget(self.data_source_label)
        
        layout.addStretch()
        
        # 載入狀態標籤
        self.status_label = QLabel("📊 狀態: 等待載入")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # 更新時間標籤
        self.update_time_label = QLabel("⏱️ 更新: 未更新")
        layout.addWidget(self.update_time_label)
        
        return panel
    
    def update_ranking_data(self, data: Dict[str, Any]):
        """更新排行榜數據"""
        try:
            print(f"[RANK] 開始更新排行榜數據...")
            print(f"[DEBUG] 收到數據鍵: {list(data.keys()) if isinstance(data, dict) else 'not_dict'}")
            
            # 儲存當前數據
            self.current_data = data
            
            # 清空現有數據
            self.table_widget.setRowCount(0)
            
            # 檢查數據格式 - 添加更詳細的檢查
            if not data:
                print(f"[WARNING] 數據為空")
                self.show_no_data_message()
                return
                
            if not isinstance(data, dict):
                print(f"[WARNING] 數據不是字典格式: {type(data)}")
                self.show_no_data_message()
                return
            
            if 'data' not in data:
                print(f"[WARNING] 數據中缺少 'data' 鍵，可用鍵: {list(data.keys())}")
                self.show_no_data_message()
                return
            
            ranking_data = data['data']
            if not ranking_data:
                print(f"[WARNING] 無排行榜數據")
                self.show_no_data_message()
                return
            
            # 解析並顯示數據
            self.ranking_data = ranking_data
            self.populate_table(ranking_data)
            
            # 更新狀態信息
            self.update_status_info(data)
            
            print(f"[OK] 排行榜數據更新完成，共 {len(ranking_data)} 筆記錄")
            
        except Exception as e:
            print(f"[ERROR] 更新排行榜數據失敗: {str(e)}")
            self.show_error_message(f"數據更新失敗: {str(e)}")
    
    def populate_table(self, ranking_data: List[Dict[str, Any]]):
        """填充表格數據"""
        try:
            row_count = len(ranking_data)
            self.table_widget.setRowCount(row_count)
            
            # 車手代碼到全名的映射
            driver_names = {
                'HAM': 'Lewis Hamilton', 'VER': 'Max Verstappen', 'LEC': 'Charles Leclerc',
                'RUS': 'George Russell', 'NOR': 'Lando Norris', 'PIA': 'Oscar Piastri',
                'SAI': 'Carlos Sainz', 'PER': 'Sergio Perez', 'ALO': 'Fernando Alonso',
                'STR': 'Lance Stroll', 'TSU': 'Yuki Tsunoda', 'RIC': 'Daniel Ricciardo',
                'HUL': 'Nico Hulkenberg', 'MAG': 'Kevin Magnussen', 'GAS': 'Pierre Gasly',
                'OCO': 'Esteban Ocon', 'ALB': 'Alexander Albon', 'SAR': 'Logan Sargeant',
                'ZHO': 'Zhou Guanyu', 'BOT': 'Valtteri Bottas', 'DOO': 'Jack Doohan'
            }
            
            # 計算第一名時間，用於計算差距
            first_time = None
            if ranking_data and len(ranking_data) > 0:
                first_time = ranking_data[0].get('fastest_time', None)
            
            for row, driver_data in enumerate(ranking_data):
                # 排名
                rank_item = QTableWidgetItem(str(row + 1))
                rank_item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 0, rank_item)
                
                # 車手代碼 - 修正：使用 'driver' 而不是 'driver_abbreviation'
                driver_code = driver_data.get('driver', driver_data.get('driver_abbreviation', 'N/A'))
                code_item = QTableWidgetItem(driver_code)
                code_item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 1, code_item)
                
                # 車手全名 - 修正：從映射表獲取全名
                driver_name = driver_names.get(driver_code, f'{driver_code} (Unknown)')
                name_item = QTableWidgetItem(driver_name)
                self.table_widget.setItem(row, 2, name_item)
                
                # 最快時間 - 修正：使用 'fastest_time' 而不是 'fastest_pitstop_time'
                fastest_time = driver_data.get('fastest_time', driver_data.get('fastest_pitstop_time', 'N/A'))
                if fastest_time != 'N/A':
                    time_text = f"{fastest_time:.1f}s"
                else:
                    time_text = 'N/A'
                time_item = QTableWidgetItem(time_text)
                time_item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 3, time_item)
                
                # 與第一名差距 - 修正：自動計算差距
                if row == 0:
                    gap_text = "-"
                else:
                    if first_time is not None and fastest_time != 'N/A' and fastest_time is not None:
                        try:
                            gap = float(fastest_time) - float(first_time)
                            gap_text = f"+{gap:.1f}s"
                        except (ValueError, TypeError):
                            gap_text = 'N/A'
                    else:
                        gap_text = 'N/A'
                gap_item = QTableWidgetItem(gap_text)
                gap_item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row, 4, gap_item)
                
                # 進站圈數
                lap_number = driver_data.get('lap_number', 'N/A')
                lap_item = QTableWidgetItem(str(lap_number))
                lap_item.setTextAlignment(Qt.AlignCenter)
                lap_item.setForeground(QColor(0, 100, 200))  # 設置為藍色
                self.table_widget.setItem(row, 5, lap_item)
                
                # 設置第一名的特殊樣式
                if row == 0:
                    for col in range(self.table_widget.columnCount()):
                        item = self.table_widget.item(row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                            item.setBackground(QColor(255, 215, 0, 50))  # 淡金色背景
            
        except Exception as e:
            print(f"[ERROR] 填充表格失敗: {str(e)}")
            raise
    
    def update_status_info(self, data: Dict[str, Any]):
        """更新狀態信息"""
        try:
            # 隱藏狀態更新，只在控制台輸出
            cache_used = data.get('cache_used', False)
            source_text = "JSON緩存" if cache_used else "CLI分析"
            driver_count = len(data.get('data', []))
            current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            print(f"[STATUS] 數據來源: {source_text}, 車手數: {driver_count}, 更新時間: {current_time}")
            
            # 原本的UI更新代碼已隱藏
            # self.data_source_label.setText(f"📄 數據來源: {source_text}")
            # self.status_label.setText(f"📊 總共 {driver_count} 位車手")
            # self.update_time_label.setText(f"⏱️ 更新: {current_time}")
            
        except Exception as e:
            print(f"[ERROR] 更新狀態信息失敗: {str(e)}")
    
    def show_no_data_message(self):
        """顯示無數據訊息"""
        self.table_widget.setRowCount(1)
        no_data_item = QTableWidgetItem("無可用數據")
        no_data_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, no_data_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
        
        # 隱藏狀態標籤更新
        # self.status_label.setText("📊 狀態: 無數據")
    
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        self.table_widget.setRowCount(1)
        error_item = QTableWidgetItem(f"載入失敗: {message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, error_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
        
        self.status_label.setText("📊 狀態: 錯誤")
    
    def show_loading_state(self):
        """顯示載入中狀態"""
        # 隱藏進度條，只在表格中顯示載入狀態
        # self.progress_bar.setVisible(True)
        # self.progress_bar.setValue(0)
        
        self.table_widget.setRowCount(1)
        loading_item = QTableWidgetItem("⏳ 正在載入數據...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, loading_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
        
        # 隱藏狀態標籤更新
        # self.status_label.setText("📊 狀態: 載入中")
    
    def hide_loading_state(self):
        """隱藏載入中狀態"""
        # 隱藏進度條（已經隱藏）
        # self.progress_bar.setVisible(False)
        pass
    
    def clear_table(self):
        """清空表格數據"""
        self.table_widget.setRowCount(0)
        self.ranking_data = []
        self.current_data = {}
        # 隱藏狀態標籤更新
        # self.status_label.setText("📊 狀態: 已清空")
        print(f"[CLEAR] [RANKING_WIDGET] 表格數據已清空")

class PitstopAnalysisModule(IAnalysisModule):
    """進站分析模組 - 實現IAnalysisModule介面，提供進站時間排行榜功能"""
    
    # 信號定義
    parameter_update_received = pyqtSignal(str, str, str)  # year, race, session
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "PitstopAnalysis"
        self._display_name = "進站分析"
        self._version = "1.0.0"
        self._description = "F1 車手最快進站時間排行榜"
        
        # 參數
        self.current_year = None  # 修正：初始化為 None，等待同步
        self.current_race = None  # 修正：初始化為 None，等待同步
        self.current_session = None  # 修正：初始化為 None，等待同步
        
        # 同步設定
        self.sync_enabled = True  # 預設啟用同步
        
        # UI 組件
        self._main_widget = None
        self.tab_widget = None
        self.ranking_widget = None
        self.team_ranking_widget = None  # 新增車隊排行榜控件
        self.detailed_widget = None      # 新增車手詳細記錄控件
        
        # 初始化數據管理器
        self.data_manager = PitstopDataManager(self)
        self.setup_connections()
    
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return self._module_name
        
    @property
    def display_name(self) -> str:
        """返回顯示名稱"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return self._version
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return self._description
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父級 widget (PopoutSubWindow)
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 創建主要 Widget
            self._main_widget = QWidget(parent_widget)
            
            # 設置UI
            self.setup_ui()
            
            # 修正：不立即載入數據，等待同步觸發
            # self.load_data()  # 移除立即載入
            
            print(f"✅ [PITSTOP_MODULE] 模組已初始化，等待參數同步...")
            
            self.set_initialized(True)
            return True
            
        except Exception as e:
            self.module_error.emit(f"模組初始化失敗: {str(e)}")
            return False
    
    def get_widget(self):
        """返回模組的主要 Widget - 必需的介面方法"""
        return self._main_widget
    
    def get_title(self) -> str:
        """返回模組標題 - 模組工廠需要的方法"""
        # 修正：處理 None 參數，提供預設值
        year = self.current_year or "2025"
        race = self.current_race or "Unknown"
        session = self.current_session or "R"
        return f"進站分析_{year}_{race}_{session}"
    
    def get_window_title(self, year: str, race: str, session: str) -> str:
        """Generate window title"""
        from core.gui_i18n import tr, get_gui_language
        language = get_gui_language()
        if language == 'zh':
            return f"{tr('pitstop_analysis')}_{year}_{race}_{session}"
        else:
            return f"Pitstop Analysis_{year}_{race}_{session}"
    
    def get_default_size(self):
        """獲取預設視窗大小 - GUI系統要求的方法"""
        return (800, 600)  # 寬度, 高度
    
    def validate_parameters(self, year: int, race: str, session: str) -> bool:
        """驗證分析參數"""
        try:
            # 驗證年份
            if not isinstance(year, (int, str)) or int(year) < 2020 or int(year) > 2030:
                return False
            
            # 驗證賽段
            if session not in ["FP1", "FP2", "FP3", "Q", "S", "R"]:
                return False
                
            return True
        except:
            return False
    
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 驗證參數
            if not self.validate_parameters(year, race, session):
                self.module_error.emit(f"無效的參數: {year}, {race}, {session}")
                return False
                
            # 檢查參數是否有變化（處理初始 None 值）
            params_changed = (
                self.current_year is None or str(self.current_year) != str(year) or 
                self.current_race is None or self.current_race != race or 
                self.current_session is None or self.current_session != session
            )
            
            # 更新內部參數
            self.current_year = str(year)
            self.current_race = race  
            self.current_session = session
            
            # 如果參數有變化，重新載入數據
            if params_changed:
                print(f"🔄 [PITSTOP_MODULE] 參數變更觸發數據重載: {year} {race} {session}")
                
                # 發出參數更新信號
                params = {
                    'year': year,
                    'race': race,
                    'session': session,
                    'module': self.module_name
                }
                self.emit_parameters_updated(params)
                
                # 確保 UI 已經設置完成再載入數據
                if self.ranking_widget is not None:
                    # 立即載入數據，但有短暫延遲確保UI完全準備好
                    QTimer.singleShot(100, self.load_data)
                    print(f"📅 [PITSTOP_MODULE] 已安排數據載入任務: {year} {race} {session}")
                else:
                    # UI 還沒準備好，稍後再試
                    print(f"🔄 [PITSTOP_MODULE] UI 未準備好，延遲載入: {year} {race} {session}")
                    QTimer.singleShot(500, self.load_data)
                
            return True
            
        except Exception as e:
            self.module_error.emit(f"更新參數失敗: {str(e)}")
            return False
    
    def load_data(self):
        """載入數據"""
        if self.data_manager:
            # 修正：檢查參數完整性，類似賽道分析模組
            if not all([self.current_year, self.current_race, self.current_session]):
                error_msg = f"缺少必要參數，無法載入數據: year={self.current_year}, race={self.current_race}, session={self.current_session}"
                print(f"[WARNING] [PITSTOP_MODULE] {error_msg}")
                # 不要發出錯誤信號，只是記錄警告，避免在初始化時阻斷流程
                # self.emit_error(error_msg)
                return False
                
            print(f"🔄 [PITSTOP_MODULE] 載入數據: {self.current_year} {self.current_race} {self.current_session}")
            self.data_manager.current_year = self.current_year
            self.data_manager.current_race = self.current_race
            self.data_manager.current_session = self.current_session
            # 修正：調用正確的方法名稱
            self.data_manager.load_data(self.current_year, self.current_race, self.current_session)
            return True
        return False
    
    def clear_data(self):
        """清除數據 - IAnalysisModule 必需方法"""
        if self.ranking_widget:
            self.ranking_widget.clear_table()
        if self.team_ranking_widget:
            self.team_ranking_widget.clear_table()
        if self.detailed_widget:
            self.detailed_widget.clear_table()
        print(f"[CLEAR] [PITSTOP_MODULE] 數據已清除")
    
    def export_data(self, format_type: str = "json") -> bool:
        """導出數據 - IAnalysisModule 必需方法"""
        try:
            if self.ranking_widget and hasattr(self.ranking_widget, 'current_data'):
                data = self.ranking_widget.current_data
                if data:
                    filename = f"pitstop_analysis_{self.current_year}_{self.current_race}_{self.current_session}.{format_type}"
                    filepath = os.path.join(os.getcwd(), "json_exports", filename)
                    
                    # 確保目錄存在
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    
                    if format_type.lower() == "json":
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    
                    print(f"[EXPORT] [PITSTOP_MODULE] 數據已導出: {filepath}")
                    return True
            
            print(f"[WARNING] [PITSTOP_MODULE] 無數據可導出")
            return False
            
        except Exception as e:
            print(f"[ERROR] [PITSTOP_MODULE] 導出失敗: {e}")
            return False
    
    def get_current_data(self) -> dict:
        """獲取當前數據 - IAnalysisModule 必需方法"""
        if self.ranking_widget and hasattr(self.ranking_widget, 'current_data'):
            return self.ranking_widget.current_data or {}
        return {}
    
    def refresh_analysis(self) -> bool:
        """刷新分析 - IAnalysisModule 必需方法"""
        try:
            self.load_data()
            print(f"[REFRESH] [PITSTOP_MODULE] 分析已刷新")
            return True
        except Exception as e:
            print(f"[ERROR] [PITSTOP_MODULE] 刷新失敗: {e}")
            return False
    
    def setup_ui(self):
        """設置使用者界面"""
        if not self._main_widget:
            return
            
        layout = QVBoxLayout(self._main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 創建分頁容器
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("PitstopAnalysisTabWidget")
        
        # 分頁1: 車手最快進站排行榜 (已實現)
        self.ranking_widget = PitstopRankingWidget(self._main_widget)
        self.tab_widget.addTab(self.ranking_widget, tr("driver_fastest_pitstop_ranking", "🏆 車手最快進站排行榜"))
        
        # 分頁2: 車隊進站時間排行榜 (新實現)
        self.team_ranking_widget = TeamPitstopRankingWidget(self._main_widget)
        self.tab_widget.addTab(self.team_ranking_widget, tr("team_pitstop_statistics", "🏁 車隊進站統計"))
        
        # 分頁3: 車手進站詳細記錄 (新實現)
        self.detailed_widget = DriverDetailedPitstopWidget(self._main_widget)
        self.tab_widget.addTab(self.detailed_widget, tr("detailed_records", "📋 詳細記錄"))
        
        layout.addWidget(self.tab_widget)
        
        print(f"[UI] [PITSTOP_MODULE] UI 設置完成，tab_widget已添加到主layout")
        
        # UI設置完成後，檢查是否有有效參數需要載入數據
        if all([self.current_year, self.current_race, self.current_session]):
            print(f"[UI] [PITSTOP_MODULE] UI設置完成，發現有效參數，開始載入數據: {self.current_year} {self.current_race} {self.current_session}")
            QTimer.singleShot(200, self.load_data)
    
    def setup_connections(self):
        """設置信號連接"""
        # 數據管理器信號連接
        self.data_manager.data_loaded.connect(self.on_data_loaded)
        self.data_manager.team_data_loaded.connect(self.on_team_data_loaded)  # 新增車隊數據信號連接
        self.data_manager.team_data_reload_requested.connect(self.on_team_data_reload_requested)  # 新增車隊重新載入信號連接
        self.data_manager.driver_detailed_loaded.connect(self.on_driver_detailed_loaded)  # 新增車手詳細數據信號連接
        self.data_manager.driver_detailed_reload_requested.connect(self.on_driver_detailed_reload_requested)  # 新增車手詳細重新載入信號連接
        self.data_manager.error_occurred.connect(self.on_error_occurred)
        self.data_manager.loading_progress.connect(self.on_loading_progress)
        self.data_manager.status_changed.connect(self.on_status_changed)
    
    def load_data(self):
        """載入數據"""
        print(f"[LOAD] 載入進站分析數據: {self.current_year} {self.current_race} {self.current_session}")
        
        # 顯示載入狀態
        if self.ranking_widget:
            self.ranking_widget.show_loading_state()
        if self.team_ranking_widget:
            self.team_ranking_widget.show_loading_state()
        if self.detailed_widget:
            self.detailed_widget.show_loading_state()
        
        # 同時啟動車手排行榜、車隊排行榜和車手詳細記錄數據載入
        self.data_manager.load_data(self.current_year, self.current_race, self.current_session)
        self.data_manager.load_team_data(self.current_year, self.current_race, self.current_session)
        self.data_manager.load_driver_detailed_data(self.current_year, self.current_race, self.current_session)
    
    def on_data_loaded(self, data: Dict[str, Any]):
        """處理數據載入完成"""
        print(f"[OK] 數據載入完成")
        
        # 隱藏載入狀態
        if self.ranking_widget:
            self.ranking_widget.hide_loading_state()
            # 更新排行榜數據
            self.ranking_widget.update_ranking_data(data)
    
    def on_team_data_loaded(self, data: Dict[str, Any]):
        """處理車隊數據載入完成"""
        print(f"[OK] 車隊數據載入完成")
        
        # 隱藏載入狀態
        if self.team_ranking_widget:
            self.team_ranking_widget.hide_loading_state()
            # 更新車隊排行榜數據
            self.team_ranking_widget.update_ranking_data(data)
    
    def on_team_data_reload_requested(self):
        """處理車隊數據重新載入請求"""
        print(f"[RELOAD] [MAIN_MODULE] 收到車隊數據重新載入請求")
        
        # 🔧 修正：使用整體刷新機制，確保車手和車隊數據同步載入
        # 延遲刷新，確保JSON檔案已完全生成
        QTimer.singleShot(2000, self.refresh_analysis)
    
    def on_driver_detailed_loaded(self, data: Dict[str, Any]):
        """處理車手詳細數據載入完成"""
        print(f"[OK] 車手詳細數據載入完成")
        
        # 隱藏載入狀態
        if self.detailed_widget:
            self.detailed_widget.hide_loading_state()
            # 更新車手詳細記錄數據
            self.detailed_widget.update_detailed_data(data)
    
    def on_driver_detailed_reload_requested(self):
        """處理車手詳細數據重新載入請求"""
        print(f"[RELOAD] [MAIN_MODULE] 收到車手詳細數據重新載入請求")
        
        # 延遲刷新，確保JSON檔案已完全生成
        QTimer.singleShot(2000, lambda: self.data_manager.load_driver_detailed_data(
            self.current_year, self.current_race, self.current_session))
    
    def on_error_occurred(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] 載入錯誤: {error_message}")
        
        # 隱藏載入狀態
        if self.ranking_widget:
            self.ranking_widget.hide_loading_state()
            # 顯示錯誤訊息
            self.ranking_widget.show_error_message(error_message)
        
        if self.team_ranking_widget:
            self.team_ranking_widget.hide_loading_state()
        
        if self.detailed_widget:
            self.detailed_widget.hide_loading_state()
            # 顯示錯誤訊息
            self.detailed_widget.show_error_message(error_message)
    
    def on_loading_progress(self, progress: int):
        """處理載入進度"""
        # 隱藏進度條更新，只在控制台輸出
        print(f"[PROGRESS] 載入進度: {progress}%")
        # if self.ranking_widget:
        #     self.ranking_widget.progress_bar.setValue(progress)
    
    def on_status_changed(self, status: str):
        """處理狀態變更"""
        # 隱藏狀態標籤更新，只在控制台輸出
        print(f"[STATUS] 狀態變更: {status}")
        # if self.ranking_widget:
        #     self.ranking_widget.status_label.setText(f"📊 狀態: {status}")
    
    def refresh_data(self):
        """刷新數據"""
        print(f"[REFRESH] 手動刷新數據")
        self.load_data()
    
    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數變更通知"""
        print(f"[ANNOUNCE] [NOTIFICATION] 進站分析模組收到主視窗更新通知: {param_type}={value}")
        
        # 檢查同步狀態 - 假設總是啟用同步
        sync_enabled = True
        
        # 方法1: 檢查 sync_enabled 屬性
        if hasattr(self, 'sync_enabled'):
            sync_enabled = self.sync_enabled
            print(f"[SEARCH] [NOTIFICATION] 進站分析模組使用屬性檢查同步狀態: {sync_enabled}")
        else:
            print(f"[SEARCH] [NOTIFICATION] 進站分析模組預設啟用同步")
        
        # 如果未啟用同步，直接返回
        if not sync_enabled:
            print(f"🔴 [NOTIFICATION] 進站分析模組同步已停用，忽略更新通知")
            return
        
        print(f"[GREEN] [NOTIFICATION] 進站分析模組同步已啟用，處理參數更新")
        
        # [TOOL] 更新本地參數（同步模式）
        if param_type == 'year':
            self.current_year = str(value)
            print(f"[UPDATE] 年份更新為: {self.current_year}")
        elif param_type == 'race':
            self.current_race = str(value)
            print(f"[UPDATE] 賽事更新為: {self.current_race}")
        elif param_type == 'session':
            self.current_session = str(value)
            print(f"[UPDATE] 場次更新為: {self.current_session}")
        
        # [TOOL] 更新窗口標題（如果有父窗口）
        if hasattr(self, 'parent') and hasattr(self.parent(), 'setWindowTitle'):
            title = f"進站分析 - {self.current_year} {self.current_race} {self.current_session}"
            self.parent().setWindowTitle(title)
            print(f"[TITLE] 窗口標題更新為: {title}")
        
        # [TOOL] 立即刷新數據
        try:
            self.load_data()
            print(f"[OK] [NOTIFICATION] 進站分析模組內容更新成功")
        except Exception as e:
            print(f"[ERROR] [NOTIFICATION] 進站分析模組內容更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def refresh_team_data(self):
        """刷新車隊數據 - 供車隊排行榜控件調用"""
        print(f"[REFRESH] 手動刷新車隊數據")
        if self.team_ranking_widget:
            self.team_ranking_widget.show_loading_state()
        self.data_manager.load_team_data(self.current_year, self.current_race, self.current_session)

class TeamPitstopRankingWidget(QWidget):
    """車隊進站排行榜 Widget - 顯示車隊進站統計與排行"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ranking_data = []           # 車隊排行榜數據
        self.current_data = {}           # 儲存當前數據，用於導出功能
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 🔧 修正：隱藏工具列（保留代碼但不添加到佈局）
        # 工具列（隱藏）
        toolbar_layout = QHBoxLayout()
        
        # 刷新按鈕（隱藏）
        self.refresh_button = QPushButton("🔄 刷新數據")
        self.refresh_button.clicked.connect(self.refresh_data)
        self.refresh_button.setVisible(False)  # 隱藏按鈕
        # toolbar_layout.addWidget(self.refresh_button)  # 不添加到佈局
        
        # 匯出按鈕（隱藏）
        self.export_button = QPushButton("📤 匯出CSV")
        self.export_button.clicked.connect(self.export_to_csv)
        self.export_button.setVisible(False)  # 隱藏按鈕
        # toolbar_layout.addWidget(self.export_button)  # 不添加到佈局
        
        # toolbar_layout.addStretch()
        # layout.addLayout(toolbar_layout)  # 不添加工具列到主佈局
        
        # 主要表格
        self.table_widget = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table_widget)
        
    def setup_table(self):
        """設置表格結構"""
        # 🔧 修正：設置列數和標題，添加最慢時間欄位
        headers = ["Rank", "Team Name", "Fastest Time", "Slowest Time", "Pit Count", "Consistency Score"]
        self.table_widget.setColumnCount(len(headers))
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 設置表格屬性
        self.table_widget.setAlternatingRowColors(True)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.setSortingEnabled(True)
        
        # 響應式列寬設定 - 允許手動調整
        header = self.table_widget.horizontalHeader()
        
        # 設定初始寬度
        self.table_widget.setColumnWidth(0, 35)   # 排名
        self.table_widget.setColumnWidth(1, 100)  # 車隊名稱
        self.table_widget.setColumnWidth(2, 60)   # 最快時間
        self.table_widget.setColumnWidth(3, 60)   # 最慢時間
        self.table_widget.setColumnWidth(4, 50)   # 進站次數
        self.table_widget.setColumnWidth(5, 80)   # 一致性分數
        
        # 所有欄位都設為可手動調整
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
    def update_ranking_data(self, data: Dict[str, Any]):
        """更新車隊排行榜數據"""
        try:
            print(f"[DEBUG] 開始更新車隊排行榜數據")
            
            # 驗證數據格式
            if not self.validate_team_data(data):
                self.show_error_message("無效的車隊進站數據格式")
                return
            
            # 儲存完整數據
            self.current_data = data
            
            # 提取排行榜數據
            if "data" in data:
                self.ranking_data = data["data"]
            else:
                self.ranking_data = data if isinstance(data, list) else []
            
            # 🔧 修正：添加數據檢查
            if not self.ranking_data:
                print("[WARNING] 車隊排行榜數據為空")
                return
            
            # 🔧 修正：按最快時間排序數據
            self.ranking_data = sorted(self.ranking_data, key=lambda x: x.get("fastest_time", float('inf')))
            print(f"[OK] [TEAM_RANKING] 車隊數據已按最快時間排序，首位: {self.ranking_data[0].get('team', 'Unknown')} - {self.ranking_data[0].get('fastest_time', 0):.3f}s")
            
            # 🔧 修正：延遲更新表格，確保UI準備完成
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(100, self.populate_table)
            
            print(f"[OK] [TEAM_RANKING] 車隊排行榜數據更新完成，{len(self.ranking_data)} 支車隊")
            
        except Exception as e:
            self.show_error_message(f"更新車隊排行榜數據失敗: {str(e)}")
            print(f"[ERROR] [TEAM_RANKING] 數據更新失敗: {e}")
    
    def populate_table(self):
        """填充表格數據"""
        # 🔧 修正：更徹底的表格清理
        self.table_widget.clearContents()  # 清空內容但保留表頭
        self.table_widget.setRowCount(0)   # 先設為0行
        self.table_widget.setRowCount(len(self.ranking_data))  # 再設置正確行數
        
        # 🔧 修正：確保表頭正確設置（添加最慢時間欄位）
        headers = ["Rank", "Team Name", "Fastest Time", "Slowest Time", "Pit Count", "Consistency Score"]
        self.table_widget.setHorizontalHeaderLabels(headers)
        
        # 🔧 修正：添加防護檢查
        if not self.ranking_data:
            print("[WARNING] 車隊排行榜數據為空")
            return
        
        for row, team_data in enumerate(self.ranking_data):
            # 排名
            rank_item = QTableWidgetItem()
            if row == 0:
                rank_item.setText("🥇1")
            elif row == 1:
                rank_item.setText("🥈2")
            elif row == 2:
                rank_item.setText("🥉3")
            else:
                rank_item.setText(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 0, rank_item)
            
            # 車隊名稱
            team_name = team_data.get("team", "Unknown")
            team_item = QTableWidgetItem(team_name)
            team_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 1, team_item)
            
            # 🔧 修正：最快時間（格式為SS.0s）
            fastest_time = team_data.get("fastest_time", 0)
            fastest_item = QTableWidgetItem(f"{fastest_time:.1f}s")
            fastest_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 2, fastest_item)
            
            # 🔧 新增：最慢時間（格式為SS.0s）
            # 假設最慢時間從數據中獲取，如果沒有則計算
            slowest_time = team_data.get("slowest_time")
            if slowest_time is None:
                # 如果JSON中沒有最慢時間，使用最快時間加上標準差作為估算
                std_dev = team_data.get("std_deviation", 0)
                slowest_time = fastest_time + (std_dev * 2)  # 估算最慢時間
            
            slowest_item = QTableWidgetItem(f"{slowest_time:.1f}s")
            slowest_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 3, slowest_item)
            
            # 🔧 修正：進站次數（欄位索引調整為4）
            pitstop_count = team_data.get("pitstop_count", 0)
            count_item = QTableWidgetItem(str(pitstop_count))
            count_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 4, count_item)
            
            # 🔧 修正：一致性分數（欄位索引調整為5）
            consistency = team_data.get("consistency_score", 0)
            consistency_item = QTableWidgetItem(f"{consistency:.2f}%")
            consistency_item.setTextAlignment(Qt.AlignCenter)
            self.table_widget.setItem(row, 5, consistency_item)
        
    def validate_team_data(self, data: Dict[str, Any]) -> bool:
        """驗證車隊進站數據格式"""
        try:
            # 檢查基本結構
            if not isinstance(data, dict):
                return False
            
            # 提取記錄
            records = None
            if "data" in data:
                records = data["data"]
            elif isinstance(data, list):
                records = data
            else:
                return False
                
            if not records or not isinstance(records, list):
                return False
                
            # 驗證第一筆記錄的欄位
            first_record = records[0]
            required_fields = ["team", "fastest_time", "average_time", "pitstop_count"]
            
            for field in required_fields:
                if field not in first_record:
                    print(f"[ERROR] [VALIDATE] 缺少必要欄位: {field}")
                    return False
                    
            print(f"[OK] [VALIDATE] 車隊數據驗證通過，記錄數量：{len(records)}")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 車隊數據驗證異常: {e}")
            return False
    
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        self.table_widget.setRowCount(1)
        error_item = QTableWidgetItem(f"❌ 錯誤: {message}")
        error_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, error_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
    
    def show_loading_state(self):
        """顯示載入中狀態"""
        self.table_widget.setRowCount(1)
        loading_item = QTableWidgetItem("⏳ 正在載入車隊數據...")
        loading_item.setTextAlignment(Qt.AlignCenter)
        self.table_widget.setItem(0, 0, loading_item)
        self.table_widget.setSpan(0, 0, 1, self.table_widget.columnCount())
    
    def hide_loading_state(self):
        """隱藏載入中狀態"""
        pass
    
    def clear_table(self):
        """清空表格數據"""
        self.table_widget.setRowCount(0)
        self.ranking_data = []
        self.current_data = {}
        print(f"[CLEAR] [TEAM_RANKING] 車隊表格數據已清空")
    
    def refresh_data(self):
        """刷新數據 - 委託給父模組"""
        if hasattr(self.parent(), 'refresh_team_data'):
            self.parent().refresh_team_data()
    
    def export_to_csv(self):
        """匯出CSV功能 (預留實現)"""
        print(f"[EXPORT] 車隊進站排行榜匯出功能 (開發中)")
        # TODO: 實現CSV匯出功能


class DriverDetailedPitstopWidget(QWidget):
    """車手進站詳細記錄 Widget - 統一匯總表格顯示所有車手進站記錄"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detailed_data = {}          # 車手詳細記錄數據
        self.max_pitstops = 0            # 最大進站次數
        self.summary_table = None        # 統一匯總表格
        self.current_data = {}           # 儲存當前數據
        self.setup_ui()
        
    def setup_ui(self):
        """設置使用者界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # 隱藏工具列，保持與車隊排行榜一致的設計
        
        # 統一匯總表格 (支援水平滾動) - 590px測試模式
        self.table_scroll = QScrollArea()
        self.table_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # 🎯 設定滾動區域的最小尺寸以適應590px表格
        self.table_scroll.setMinimumWidth(600)  # 稍微大於590px以容納滾動條
        self.table_scroll.setMinimumHeight(300) # 增加高度以顯示更多行
        
        layout.addWidget(self.table_scroll)
        
        # 狀態列
        self.status_layout = QHBoxLayout()
        layout.addLayout(self.status_layout)
        
        print(f"[UI_SETUP] 車手詳細記錄UI設置完成 - 滾動區域最小尺寸: 600x300")
        
    def setup_summary_table(self):
        """設置統一匯總表格"""
        # 計算最大進站次數
        self.calculate_max_pitstops()
        
        # 創建動態表格標題
        headers = self.create_dynamic_headers()
        
        # 建立QTableWidget
        self.summary_table = QTableWidget()
        self.summary_table.setColumnCount(len(headers))
        self.summary_table.setHorizontalHeaderLabels(headers)
        
        # 設置表格樣式和欄位寬度
        self.configure_table_style()
        
    def create_dynamic_headers(self):
        """根據最大進站次數創建動態表格標題"""
        headers = ["Driver", "Team", "Total Pitstops"]
        
        # 動態添加進站次數欄位
        for i in range(1, self.max_pitstops + 1):
            headers.extend([f"#{i} Time", f"#{i} Lap"])
        
        # 添加統計欄位
        headers.extend(["Fastest Time", "Slowest Time"])
        return headers
        
    def calculate_max_pitstops(self):
        """計算所有車手中的最大進站次數"""
        if not self.detailed_data:
            self.max_pitstops = 0
            return
            
        max_stops = 0
        for driver_data in self.detailed_data.values():
            if isinstance(driver_data, list):
                max_stops = max(max_stops, len(driver_data))
        self.max_pitstops = max_stops
        
    def update_detailed_data(self, data: Dict[str, Any]):
        """更新車手詳細記錄數據"""
        try:
            # 儲存完整數據
            self.current_data = data
            
            if "data" in data:
                self.detailed_data = data["data"]
                # 延遲更新UI確保數據準備完成
                QTimer.singleShot(100, self.populate_summary_table)
            else:
                self.show_error_message("車手詳細數據格式無效")
                
        except Exception as e:
            print(f"[ERROR] 更新車手詳細數據失敗: {e}")
            self.show_error_message(f"更新車手詳細數據失敗: {str(e)}")
        
    def populate_summary_table(self):
        """填充統一匯總表格"""
        try:
            if not self.detailed_data:
                print("[WARNING] 車手詳細數據為空")
                return
                
            # 重新設置表格結構
            self.setup_summary_table()
            
            # 按車手代碼排序
            sorted_drivers = sorted(self.detailed_data.keys())
            self.summary_table.setRowCount(len(sorted_drivers))
            
            for row, driver in enumerate(sorted_drivers):
                pitstops = self.detailed_data[driver]
                if not pitstops or not isinstance(pitstops, list):
                    continue
                    
                # 填充基本信息
                self.summary_table.setItem(row, 0, QTableWidgetItem(driver))
                self.summary_table.setItem(row, 1, QTableWidgetItem(pitstops[0].get("team", "Unknown")))
                self.summary_table.setItem(row, 2, QTableWidgetItem(str(len(pitstops))))
                
                # 填充每次進站詳細信息
                col_index = 3
                for i in range(self.max_pitstops):
                    if i < len(pitstops):
                        # 填充實際進站數據
                        pit_time = self.format_time_display(pitstops[i].get("pit_duration", 0))
                        lap_num = str(pitstops[i].get("lap_number", 0))
                        
                        self.summary_table.setItem(row, col_index, QTableWidgetItem(pit_time))
                        # 設置圈數為藍色
                        lap_item = QTableWidgetItem(lap_num)
                        lap_item.setForeground(QColor(0, 100, 200))  # 設置為藍色
                        self.summary_table.setItem(row, col_index + 1, lap_item)
                    else:
                        # 填充空白欄位
                        self.summary_table.setItem(row, col_index, QTableWidgetItem("-"))
                        self.summary_table.setItem(row, col_index + 1, QTableWidgetItem("-"))
                    
                    col_index += 2
                
                # 計算並填充統計信息
                stats = self.calculate_driver_stats(pitstops)
                self.summary_table.setItem(row, col_index, QTableWidgetItem(stats["fastest"]))
                self.summary_table.setItem(row, col_index + 1, QTableWidgetItem(stats["slowest"]))
            
            # 設置表格到滾動區域
            self.table_scroll.setWidget(self.summary_table)
            
            # 🎯 強制調整表格大小以適應內容
            self.adjust_table_size()
            
            # 更新狀態列
            self.update_status_bar()
            
            print(f"[OK] 車手詳細記錄表格更新完成: {len(sorted_drivers)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] 填充車手詳細表格失敗: {e}")
            self.show_error_message(f"填充車手詳細表格失敗: {str(e)}")
        
    def calculate_driver_stats(self, pitstops):
        """計算單一車手的統計數據"""
        if not pitstops:
            return {"fastest": "-", "slowest": "-"}
            
        times = [pit.get("pit_duration", 0) for pit in pitstops if pit.get("pit_duration", 0) > 0]
        
        if not times:
            return {"fastest": "-", "slowest": "-"}
            
        return {
            "fastest": self.format_time_display(min(times)),
            "slowest": self.format_time_display(max(times))
        }
        
    def format_time_display(self, seconds):
        """格式化時間顯示為SS.0s格式"""
        if seconds <= 0:
            return "-"
        return f"{seconds:.1f}s"
        
    def configure_table_style(self):
        """設置表格樣式和欄位寬度 - 響應式設計 (預設590px寬度)"""
        if not self.summary_table:
            return
            
        # 🎯 預設590px寬度配置 - 測試模式
        total_columns = self.summary_table.columnCount()
        
        # 基本列寬度設定 - 針對590px優化
        self.summary_table.setColumnWidth(0, 50)   # 車手 - 增加寬度
        self.summary_table.setColumnWidth(1, 100)  # 車隊 - 增加寬度  
        self.summary_table.setColumnWidth(2, 60)   # 總進站次數 - 增加寬度
        
        # 動態欄位寬度 - 進站記錄使用更寬的設定
        for i in range(3, total_columns - 2):
            self.summary_table.setColumnWidth(i, 70)  # 進站時間和圈數使用70px
            
        # 統計欄位寬度 - 加寬模式
        if total_columns >= 2:
            self.summary_table.setColumnWidth(total_columns - 2, 80)  # 最快時間
            self.summary_table.setColumnWidth(total_columns - 1, 80)  # 最慢時間
        
        # 🎯 設置響應式拉伸策略 - 所有欄位可手動調整
        header = self.summary_table.horizontalHeader()
        
        # 所有欄位都設為可手動調整
        for col in range(total_columns):
            header.setSectionResizeMode(col, QHeaderView.Interactive)
        
        # 表格樣式設置
        self.summary_table.setAlternatingRowColors(True)
        self.summary_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        print(f"[TABLE_CONFIG] 表格配置完成 - 欄數:{total_columns}, 預設總寬度:~590px")
        
    def adjust_table_size(self):
        """調整表格大小以適應內容和容器"""
        if not self.summary_table:
            return
            
        # 計算表格應有的寬度
        total_column_width = 0
        for i in range(self.summary_table.columnCount()):
            total_column_width += self.summary_table.columnWidth(i)
        
        # 考慮垂直滾動條的寬度（約20px）
        required_width = total_column_width + 25
        
        # 獲取滾動區域的可用寬度
        scroll_width = self.table_scroll.width()
        
        # 設置表格寬度以填滿滾動區域
        table_width = max(required_width, scroll_width - 20)  # 留20px邊距和滾動條
        
        print(f"[TABLE_SIZE_DEBUG] 表格大小調整:")
        print(f"[TABLE_SIZE_DEBUG] - 計算的欄位總寬度: {total_column_width}px")
        print(f"[TABLE_SIZE_DEBUG] - 建議表格寬度: {required_width}px")
        print(f"[TABLE_SIZE_DEBUG] - 滾動區域寬度: {scroll_width}px")
        print(f"[TABLE_SIZE_DEBUG] - 最終設定表格寬度: {table_width}px")
        
        # 設置表格大小策略為擴展
        from PyQt5.QtWidgets import QSizePolicy
        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.summary_table.setSizePolicy(size_policy)
        
        # 設置表格寬度以填滿滾動區域，高度自動適應內容
        self.summary_table.setFixedWidth(table_width)
        
        # 計算表格應有的高度（根據行數）
        header_height = self.summary_table.horizontalHeader().height()
        row_count = self.summary_table.rowCount()
        row_height = self.summary_table.rowHeight(0) if row_count > 0 else 30
        total_height = header_height + (row_count * row_height) + 10  # 加10px邊距
        
        # 獲取滾動區域的可用高度
        scroll_height = self.table_scroll.height()
        table_height = min(total_height, scroll_height - 20)  # 最大不超過滾動區域
        
        print(f"[TABLE_SIZE_DEBUG] 高度計算:")
        print(f"[TABLE_SIZE_DEBUG] - 表頭高度: {header_height}px")
        print(f"[TABLE_SIZE_DEBUG] - 行數: {row_count}, 每行高度: {row_height}px")
        print(f"[TABLE_SIZE_DEBUG] - 計算總高度: {total_height}px")
        print(f"[TABLE_SIZE_DEBUG] - 滾動區域高度: {scroll_height}px")
        print(f"[TABLE_SIZE_DEBUG] - 最終表格高度: {table_height}px")
        
        # 設置表格高度
        self.summary_table.setFixedHeight(table_height)
        
        # 強制重新計算佈局
        self.summary_table.updateGeometry()
        self.table_scroll.updateGeometry()
        
    def update_status_bar(self):
        """更新狀態列信息"""
        try:
            # 清理現有狀態
            for i in reversed(range(self.status_layout.count())):
                item = self.status_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setParent(None)
            
            # 計算統計信息
            total_drivers = len(self.detailed_data)
            fastest_overall, slowest_overall = self.calculate_overall_stats()
            
            # 添加狀態標籤
            status_items = [
                f"📊 共 {total_drivers} 位車手",
                "📄 來源: JSON",
                f"⏱️ 更新: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"🎯 最快進站: {fastest_overall}",
                f"🐌 最慢進站: {slowest_overall}",
                "🤖 智能生成: 開啟"
            ]
            
            for item in status_items:
                label = QLabel(item)
                self.status_layout.addWidget(label)
                
            self.status_layout.addStretch()
            
        except Exception as e:
            print(f"[ERROR] 更新狀態列失敗: {e}")
            
    def calculate_overall_stats(self):
        """計算全域最快/最慢進站時間"""
        all_times = []
        
        for driver_data in self.detailed_data.values():
            if isinstance(driver_data, list):
                for pit in driver_data:
                    duration = pit.get("pit_duration", 0)
                    if duration > 0:
                        all_times.append(duration)
        
        if not all_times:
            return "-", "-"
            
        fastest = min(all_times)
        slowest = max(all_times)
        
        return self.format_time_display(fastest), self.format_time_display(slowest)
    
    def show_loading_state(self):
        """顯示載入狀態"""
        # 創建簡單的載入提示
        loading_widget = QLabel("🔄 載入車手詳細記錄中...")
        loading_widget.setAlignment(Qt.AlignCenter)
        loading_widget.setStyleSheet("color: #666; font-size: 14px; padding: 20px;")
        self.table_scroll.setWidget(loading_widget)
    
    def hide_loading_state(self):
        """隱藏載入狀態"""
        # 載入狀態會在populate_summary_table中被替換
        pass
    
    def show_error_message(self, message: str):
        """顯示錯誤訊息"""
        error_widget = QLabel(f"❌ {message}")
        error_widget.setAlignment(Qt.AlignCenter)
        error_widget.setStyleSheet("color: #d32f2f; font-size: 14px; padding: 20px;")
        self.table_scroll.setWidget(error_widget)
    
    def resizeEvent(self, event):
        """監控視窗大小變化"""
        super().resizeEvent(event)
        
        # 獲取新的視窗大小
        new_size = event.size()
        widget_width = new_size.width()
        widget_height = new_size.height()
        
        print(f"[RESIZE_DEBUG] DriverDetailedPitstopWidget 視窗大小變化:")
        print(f"[RESIZE_DEBUG] - Widget 寬度: {widget_width}px")
        print(f"[RESIZE_DEBUG] - Widget 高度: {widget_height}px")
        
        # 如果存在滾動區域，也列印其大小
        if hasattr(self, 'table_scroll') and self.table_scroll:
            scroll_size = self.table_scroll.size()
            print(f"[RESIZE_DEBUG] - QScrollArea 寬度: {scroll_size.width()}px")
            print(f"[RESIZE_DEBUG] - QScrollArea 高度: {scroll_size.height()}px")
            
            # 如果存在表格，也列印表格大小
            if hasattr(self, 'summary_table') and self.summary_table:
                table_size = self.summary_table.size()
                table_width = self.summary_table.width()
                column_count = self.summary_table.columnCount()
                print(f"[RESIZE_DEBUG] - QTableWidget 寬度: {table_width}px")
                print(f"[RESIZE_DEBUG] - QTableWidget 高度: {table_size.height()}px")
                print(f"[RESIZE_DEBUG] - 表格欄數: {column_count}")
                
                # 檢查每個欄位的寬度
                if column_count > 0:
                    column_widths = []
                    total_column_width = 0
                    for i in range(column_count):
                        width = self.summary_table.columnWidth(i)
                        column_widths.append(width)
                        total_column_width += width
                    print(f"[RESIZE_DEBUG] - 欄位寬度: {column_widths}")
                    print(f"[RESIZE_DEBUG] - 總欄位寬度: {total_column_width}px")
                
                # 重新調整表格大小以適應新的視窗大小
                self.adjust_table_size()
        
        print(f"[RESIZE_DEBUG] ===== 視窗大小變化監控結束 =====")
    
    def clear_table(self):
        """清空表格"""
        if self.summary_table:
            self.summary_table.setRowCount(0)
        self.detailed_data = {}
        self.current_data = {}
        print(f"[CLEAR] 車手詳細記錄表格數據已清空")

# 導出模組的主要類別
__all__ = ['PitstopAnalysisModule', 'PitstopRankingWidget', 'PitstopDataManager', 'TeamPitstopRankingWidget', 'DriverDetailedPitstopWidget']

# 註冊模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.PITSTOP_ANALYSIS, PitstopAnalysisModule)
    print(f"[OK] [MODULE_FACTORY] 進站分析模組已註冊")
except ImportError as e:
    print(f"[WARNING] [MODULE_FACTORY] 進站分析模組註冊失敗: {e}")
