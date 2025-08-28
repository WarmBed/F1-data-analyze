"""
TrackDataLoader - 賽道數據載入器
===============================

這個模組負責載入和解析 F1 賽道位置數據，支援 JSON 格式的數據文件。

功能特色：
1. JSON 格式賽道數據載入
2. 數據格式驗證與錯誤處理
3. 進度追蹤與異步載入支援
4. 快取機制提升載入效率

支援的數據格式：
- raw_data_track_position_*.json (來自 json_exports 目錄)

Author: F1T Team  
Date: 2025-08-28
Version: 1.0.0
"""

import json
import os
import glob
import subprocess
import sys
from typing import Dict, Any, Optional, List
from PyQt5.QtCore import QObject, pyqtSignal, QThread, QTimer


class TrackDataLoader(QObject):
    """
    賽道數據載入器
    
    負責從 JSON 檔案載入賽道位置數據，並提供數據驗證功能。
    """
    
    # 信號定義
    data_loaded = pyqtSignal(dict)      # 數據載入完成
    load_progress = pyqtSignal(int)     # 載入進度 (0-100)
    load_error = pyqtSignal(str)        # 載入錯誤
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 基本設定
        self._base_path = "json_exports"  # JSON 檔案目錄
        self._current_data = None
        self._is_loading = False
        
        # 支援的賽段代碼映射
        self._session_mapping = {
            'R': 'R',
            'Q': 'Q', 
            'FP1': 'FP1',
            'FP2': 'FP2',
            'FP3': 'FP3',
            'S': 'S'  # Sprint
        }
        
    def load_track_data(self, year: int, race: str, session: str, **kwargs) -> bool:
        """
        載入賽道數據
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
            **kwargs: 額外參數
            
        Returns:
            bool: 載入請求是否成功提交
        """
        try:
            print(f"[FOLDER] [DATA_LOADER] 開始載入賽道數據: {year} {race} {session}")
            
            if self._is_loading:
                self.load_error.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.load_progress.emit(0)
            
            # 尋找對應的 JSON 檔案
            json_file = self._find_track_data_file(year, race, session)
            print(f"[FOLDER] [DATA_LOADER] 搜尋到的檔案: {json_file}")
            
            if not json_file:
                print(f"[FOLDER] [DATA_LOADER] 找不到現有 JSON，開始生成: {year} {race} {session}")
                # 呼叫 CLI 生成 JSON (異步)
                self._start_cli_generation(year, race, session)
                return True  # 返回 True 表示已啟動生成流程
                    
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            return True
            
        except Exception as e:
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
            
    def _find_track_data_file(self, year: int, race: str, session: str) -> Optional[str]:
        """
        尋找對應的賽道數據檔案
        
        Args:
            year: 年份
            race: 賽事名稱  
            session: 賽段代碼
            
        Returns:
            str: 檔案路徑，如果找不到則返回 None
        """
        try:
            # 賽事全名映射（與track_position_analysis.py保持一致）
            race_full_names = {
                "Bahrain": "Bahrain Grand Prix",
                "Saudi Arabia": "Saudi Arabian Grand Prix", 
                "Australia": "Australian Grand Prix",
                "Japan": "Japanese Grand Prix",
                "China": "Chinese Grand Prix",
                "Miami": "Miami Grand Prix",
                "Emilia Romagna": "Emilia Romagna Grand Prix",
                "Monaco": "Monaco Grand Prix",
                "Canada": "Canadian Grand Prix",
                "Spain": "Spanish Grand Prix", 
                "Austria": "Austrian Grand Prix",
                "Great Britain": "British Grand Prix",
                "Hungary": "Hungarian Grand Prix",
                "Belgium": "Belgian Grand Prix",
                "Netherlands": "Dutch Grand Prix",
                "Italy": "Italian Grand Prix",
                "Azerbaijan": "Azerbaijan Grand Prix",
                "Singapore": "Singapore Grand Prix",
                "United States": "United States Grand Prix",
                "Mexico": "Mexican Grand Prix",
                "Brazil": "Brazilian Grand Prix",
                "Las Vegas": "Las Vegas Grand Prix",
                "Qatar": "Qatar Grand Prix",
                "Abu Dhabi": "Abu Dhabi Grand Prix"
            }
            
            # 標準化賽事名稱 (移除空格，轉為底線)
            race_normalized = race.replace(' ', '_').replace("'", "")
            race_full = race_full_names.get(race, race)  # 獲取完整賽事名稱
            race_full_normalized = race_full.replace(' ', '_').replace("'", "")
            
            # 可能的檔案名稱模式（新格式：使用完整賽事名稱）
            patterns = [
                f"raw_data_track_position_{year}_{race_full}.json",              # 新格式：完整賽事名稱
                f"raw_data_track_position_{year}_{race_full_normalized}.json",   # 新格式：完整標準化名稱
                f"raw_data_track_position_{year}_{race}.json",                   # 新格式：簡短賽事名稱
                f"raw_data_track_position_{year}_{race_normalized}.json",        # 新格式：簡短標準化名稱
                f"raw_data_track_position_{year}_{race}_{session}.json",         # 舊格式：包含賽段
                f"raw_data_track_position_{year}_{race_normalized}_{session}.json", # 舊格式：標準化+賽段
                f"track_position_{year}_{race}.json",                           # 其他格式
                f"track_position_{year}_{race_normalized}.json"
            ]
            
            # 搜尋多個目錄
            search_dirs = ["json_exports", "json"]
            
            for search_dir in search_dirs:
                for pattern in patterns:
                    search_path = os.path.join(search_dir, pattern)
                    files = glob.glob(search_path)
                    if files:
                        print(f"[FOLDER] [DATA_LOADER] 找到檔案: {files[0]}")
                        return files[0]  # 返回第一個匹配的檔案
                    
            # 如果精確匹配失敗，嘗試模糊搜尋
            for search_dir in search_dirs:
                fuzzy_patterns = [
                    f"*track_position*{year}*{session}*.json",
                    f"*track_position*{year}*.json"
                ]
                
                for fuzzy_pattern in fuzzy_patterns:
                    search_path = os.path.join(search_dir, fuzzy_pattern)
                    files = glob.glob(search_path)
                    
                    # 動態生成賽事關鍵字（包含完整賽事名稱）
                    race_keywords = []
                    if race:
                        race_normalized = race.lower().replace(' ', '_').replace("'", "")
                        race_full = race_full_names.get(race, race)  # 獲取完整賽事名稱
                        race_full_lower = race_full.lower()
                        
                        race_keywords.extend([
                            race.lower(),                    # 原始簡短名稱
                            race_normalized,                 # 標準化簡短名稱
                            race.lower().replace(' ', ''),   # 移除空格
                            race.split()[0].lower() if ' ' in race else race.lower(),  # 第一個單詞
                            race_full_lower,                 # 完整賽事名稱
                            race_full_lower.replace(' ', '_'),  # 完整標準化名稱
                            race_full_lower.replace(' ', ''),   # 完整移除空格
                            race_full.split()[0].lower() if ' ' in race_full else race_full_lower  # 完整第一個單詞
                        ])
                    
                    print(f"[FOLDER] [DATA_LOADER] 模糊搜尋關鍵字: {race_keywords}")
                    
                    for file_path in files:
                        file_name_lower = os.path.basename(file_path).lower()
                        if any(keyword in file_name_lower for keyword in race_keywords):
                            print(f"[FOLDER] [DATA_LOADER] 模糊搜尋找到: {file_path}")
                            return file_path
                    
            return None
            
        except Exception as e:
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
            
    def _load_json_file(self, file_path: str) -> None:
        """
        載入 JSON 檔案
        
        Args:
            file_path: JSON 檔案路徑
        """
        try:
            print(f"[FOLDER] [DATA_LOADER] 開始載入檔案: {file_path}")
            self.load_progress.emit(25)
            
            # 檢查檔案是否存在
            if not os.path.exists(file_path):
                self.load_error.emit(f"檔案不存在: {file_path}")
                self._is_loading = False
                return
                
            self.load_progress.emit(50)
            
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"[FOLDER] [DATA_LOADER] JSON 載入成功，數據類型: {type(data)}")
            
            self.load_progress.emit(75)
            
            # 驗證數據格式
            if not self._validate_data_format(data):
                self.load_error.emit("數據格式驗證失敗")
                self._is_loading = False
                return
                
            print(f"[FOLDER] [DATA_LOADER] 數據格式驗證通過")
            
            self.load_progress.emit(90)
            
            # 處理數據
            processed_data = self._process_track_data(data, file_path)
            
            records_count = len(processed_data.get('detailed_position_records', []))
            print(f"[FOLDER] [DATA_LOADER] 數據處理完成，位置記錄: {records_count} 個")
            
            self.load_progress.emit(100)
            
            # 儲存數據並發出信號
            self._current_data = processed_data
            self.data_loaded.emit(processed_data)
            
            self._is_loading = False
            
        except json.JSONDecodeError as e:
            self.load_error.emit(f"JSON 格式錯誤: {str(e)}")
            self._is_loading = False
        except Exception as e:
            self.load_error.emit(f"載入檔案失敗: {str(e)}")
            self._is_loading = False
            
    def _validate_data_format(self, data: Dict[str, Any]) -> bool:
        """
        驗證數據格式
        
        Args:
            data: 載入的數據
            
        Returns:
            bool: 數據格式是否正確
        """
        try:
            # 檢查必要的欄位
            required_fields = ['detailed_position_records']
            for field in required_fields:
                if field not in data:
                    return False
                    
            # 檢查位置記錄格式
            records = data['detailed_position_records']
            if not isinstance(records, list) or len(records) == 0:
                return False
                
            # 檢查第一個記錄的格式
            first_record = records[0]
            required_record_fields = ['position_x', 'position_y']  # 修正欄位名稱
            for field in required_record_fields:
                if field not in first_record:
                    print(f"[FOLDER] [DATA_LOADER] 驗證失敗：缺少欄位 {field}")
                    print(f"[FOLDER] [DATA_LOADER] 可用欄位：{list(first_record.keys())}")
                    return False
                    
            print(f"[FOLDER] [DATA_LOADER] 數據欄位驗證通過，記錄數量：{len(records)}")
            return True
            
        except Exception:
            return False
            
    def _process_track_data(self, data: Dict[str, Any], file_path: str) -> Dict[str, Any]:
        """
        處理賽道數據
        
        Args:
            data: 原始數據
            file_path: 檔案路徑
            
        Returns:
            Dict[str, Any]: 處理後的數據
        """
        try:
            processed_data = data.copy()
            
            # 添加元數據
            processed_data['metadata'] = {
                'source_file': os.path.basename(file_path),
                'file_path': file_path,
                'loaded_at': self._get_current_timestamp(),
                'total_points': len(data.get('detailed_position_records', [])),
                'loader_version': '1.0.0'
            }
            
            # 處理位置記錄
            records = data.get('detailed_position_records', [])
            if records:
                print(f"[FOLDER] [DATA_LOADER] 開始處理 {len(records)} 個位置記錄")
                
                # 確保數據類型正確並標準化欄位名稱
                for record in records:
                    # 從 position_x/position_y 轉換為 x/y 
                    record['x'] = float(record.get('position_x', record.get('x', 0)))
                    record['y'] = float(record.get('position_y', record.get('y', 0)))
                    record['distance'] = float(record.get('distance_m', record.get('distance', 0)))
                    record['time'] = float(record.get('time', 0))
                    
                print(f"[FOLDER] [DATA_LOADER] 樣本數據: {records[:3]}")
                
                # 計算邊界
                x_coords = [r['x'] for r in records]
                y_coords = [r['y'] for r in records]
                
                print(f"[FOLDER] [DATA_LOADER] X座標範圍: {min(x_coords)} ~ {max(x_coords)}")
                print(f"[FOLDER] [DATA_LOADER] Y座標範圍: {min(y_coords)} ~ {max(y_coords)}")
                
                processed_data['bounds'] = {
                    'x_min': min(x_coords),
                    'x_max': max(x_coords),
                    'y_min': min(y_coords),
                    'y_max': max(y_coords),
                    'center_x': sum(x_coords) / len(x_coords),
                    'center_y': sum(y_coords) / len(y_coords)
                }
                
            return processed_data
            
        except Exception as e:
            self.load_error.emit(f"數據處理失敗: {str(e)}")
            return data
            
    def _get_current_timestamp(self) -> str:
        """獲取當前時間戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前載入的數據"""
        return self._current_data
        
    def clear_data(self) -> None:
        """清除當前數據"""
        self._current_data = None
        
    def is_loading(self) -> bool:
        """檢查是否正在載入"""
        return self._is_loading
        
    def get_available_files(self, year: Optional[int] = None, race: Optional[str] = None) -> List[str]:
        """
        獲取可用的數據檔案列表
        
        Args:
            year: 篩選年份 (可選)
            race: 篩選賽事 (可選)
            
        Returns:
            List[str]: 可用檔案列表
        """
        try:
            pattern = "raw_data_track_position_*.json"
            search_path = os.path.join(self._base_path, pattern)
            files = glob.glob(search_path)
            
            # 過濾條件
            filtered_files = []
            for file_path in files:
                file_name = os.path.basename(file_path)
                
                # 年份過濾
                if year and str(year) not in file_name:
                    continue
                    
                # 賽事過濾
                if race and race.lower() not in file_name.lower():
                    continue
                    
                filtered_files.append(file_path)
                
            return sorted(filtered_files)
            
        except Exception:
            return []
    
    def _start_cli_generation(self, year: int, race: str, session: str):
        """
        啟動 CLI 生成流程 - 非阻塞方式
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
        """
        try:
            # 儲存參數供後續使用
            self._generation_params = (year, race, session)
            
            # 啟動 CLI 生成
            success = self._generate_track_data_via_cli(year, race, session)
            
            if success:
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring(year, race, session)
            else:
                self.load_error.emit(f"啟動 CLI 生成失敗: {year} {race} {session}")
                self._is_loading = False
                
        except Exception as e:
            print(f"[ERROR] [CLI_GEN] 啟動生成時發生錯誤: {e}")
            self.load_error.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    def _start_generation_monitoring(self, year: int, race: str, session: str):
        """
        開始監控檔案生成進度
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
        """
        print(f"⏱️ [CLI_GEN] 開始監控檔案生成: {year} {race} {session}")
        
        # 創建檢查計時器
        if not hasattr(self, '_generation_timer'):
            self._generation_timer = QTimer()
            self._generation_timer.timeout.connect(self._check_generation_progress)
        
        # 創建超時計時器
        if not hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer = QTimer()
            self._generation_timeout_timer.setSingleShot(True)
            self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._generation_timer.start(5000)
        self._generation_timeout_timer.start(180000)
        
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        if hasattr(self, '_generation_params'):
            year, race, session = self._generation_params
            
            # 檢查是否有新檔案生成
            json_file = self._find_track_data_file(year, race, session)
            
            if json_file:
                print(f"[OK] [CLI_GEN] 檔案生成完成: {json_file}")
                
                # 停止監控
                self._stop_generation_monitoring()
                
                # 載入新生成的檔案
                QTimer.singleShot(10, lambda: self._load_json_file(json_file))
            else:
                print(f"⏳ [CLI_GEN] 繼續等待檔案生成...")
                
    def _on_generation_timeout(self):
        """處理生成超時"""
        print(f"[TIME] [CLI_GEN] 檔案生成超時")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或稍後重試")
        self._is_loading = False
        
    def _stop_generation_monitoring(self):
        """停止生成監控"""
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
    
    def _generate_track_data_via_cli(self, year: int, race: str, session: str) -> bool:
        """
        透過 CLI 工具生成賽道數據 - 使用非阻塞方式
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段代碼
            
        Returns:
            bool: 請求是否成功提交（注意：不是生成是否成功）
        """
        try:
            # 導入全域 CLI 分析管理器
            from f1t_gui_main import cli_analysis_manager
            
            print(f"[TOOL] [CLI_GEN] 開始生成賽道數據: {year} {race} {session}")
            
            # 使用 force_mode=2 對應原有的 -f 2 參數
            request_id = cli_analysis_manager.request_analysis(
                year=str(year),
                race=race,
                session=session,
                force_mode=2,
                requester_id=f"track_loader_{id(self)}"
            )
            
            # 連接信號來接收結果
            cli_analysis_manager.json_ready.connect(self._on_cli_json_ready)
            cli_analysis_manager.analysis_completed.connect(self._on_cli_analysis_completed)
            
            # 保存請求 ID 以便後續識別
            self._current_cli_request = request_id
            
            print(f"[START] [CLI_GEN] CLI 分析請求已提交: {request_id}")
            return True  # 返回請求提交成功
                
        except Exception as e:
            print(f"[ERROR] [CLI_GEN] 提交 CLI 請求失敗: {str(e)}")
            return False
    
    def _on_cli_json_ready(self, request_id: str, json_data: dict):
        """處理 CLI 分析完成後的 JSON 數據"""
        if hasattr(self, '_current_cli_request') and self._current_cli_request == request_id:
            print(f"[OK] [CLI_GEN] JSON 數據已準備好: {request_id}")
            
            # 驗證並載入數據
            if self._validate_track_data(json_data):
                self._current_data = json_data
                self.data_loaded.emit(json_data)
                print(f"📄 [CLI_GEN] 數據載入完成")
            else:
                self.load_error.emit("CLI 生成的數據格式無效")
            
            # 清理
            self._cleanup_cli_request()
    
    def _on_cli_analysis_completed(self, request_id: str, success: bool, message: str):
        """處理 CLI 分析完成事件"""
        if hasattr(self, '_current_cli_request') and self._current_cli_request == request_id:
            if not success:
                print(f"[ERROR] [CLI_GEN] CLI 分析失敗: {message}")
                self.load_error.emit(f"CLI 分析失敗: {message}")
                self._cleanup_cli_request()
    
    def _cleanup_cli_request(self):
        """清理 CLI 請求相關資源"""
        if hasattr(self, '_current_cli_request'):
            delattr(self, '_current_cli_request')
        
        # 斷開信號連接以避免內存洩漏
        try:
            from f1t_gui_main import cli_analysis_manager
            cli_analysis_manager.json_ready.disconnect(self._on_cli_json_ready)
            cli_analysis_manager.analysis_completed.disconnect(self._on_cli_analysis_completed)
        except:
            pass  # 忽略斷開連接時的錯誤
    
    def _validate_track_data(self, json_data: dict) -> bool:
        """驗證 JSON 數據是否包含有效的賽道數據
        
        Args:
            json_data: 要驗證的 JSON 數據
            
        Returns:
            bool: 數據是否有效
        """
        try:
            # 檢查基本結構
            if not isinstance(json_data, dict):
                print(f"[ERROR] [VALIDATE] JSON 數據不是字典格式")
                return False
            
            # 檢查是否包含賽道位置數據
            required_fields = ['track_positions', 'race_info']
            for field in required_fields:
                if field not in json_data:
                    print(f"[WARNING] [VALIDATE] 缺少必要欄位: {field}")
                    # 不是嚴格要求，可能有其他格式的數據
            
            # 如果有 track_positions，檢查其格式
            if 'track_positions' in json_data:
                positions = json_data['track_positions']
                if not isinstance(positions, (list, dict)):
                    print(f"[WARNING] [VALIDATE] track_positions 格式不正確")
                    return False
                
                if isinstance(positions, list) and len(positions) > 0:
                    # 檢查第一個項目是否有基本欄位
                    first_item = positions[0]
                    if isinstance(first_item, dict):
                        expected_keys = ['Time', 'DriverNumber', 'X', 'Y']
                        missing_keys = [key for key in expected_keys if key not in first_item]
                        if missing_keys:
                            print(f"[WARNING] [VALIDATE] 位置數據缺少欄位: {missing_keys}")
            
            # 檢查數據大小（避免空數據）
            data_size = len(str(json_data))
            if data_size < 100:  # 小於 100 字符可能是空數據
                print(f"[WARNING] [VALIDATE] 數據太小，可能無效: {data_size} 字符")
                return False
            
            print(f"[OK] [VALIDATE] 數據驗證通過，大小: {data_size} 字符")
            return True
            
        except Exception as e:
            print(f"[ERROR] [VALIDATE] 數據驗證時發生錯誤: {str(e)}")
            return False
