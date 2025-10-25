#!/usr/bin/env python3
"""
UniversalDataLoader - F1T 通用數據載入器基類
==============================================

這個模組提供了所有 F1T 分析模組共用的數據載入邏輯，
支援多種分析類型（遙測分析、降雨分析、事故分析等）。

支援的分析類型：
- telemetry: 遙測分析（速度、RPM、檔位、油門、煞車等）
- rain: 降雨分析（天氣數據、降雨強度等）
- accident: 事故分析（事故數據、時間線等）
- pitstop: 進站分析（進站策略、時間等）
- driver: 車手分析（表現統計等）
- track: 賽道分析（圈速、路線等）

設計原則：
1. 統一的載入邏輯，消除代碼重複
2. 支援多種數據源（JSON、CSV、API、實時數據等）
3. 模組化設計，支援新增分析類型
4. 統一的錯誤處理和監控機制
5. 異步載入和進度追蹤
6. 智能緩存和檔案搜尋

Author: F1T Team
Date: 2025-09-09
Version: 1.0.0
"""

import sys
import os
import json
import glob
import pickle
import time
from datetime import datetime
import threading
import subprocess
from typing import Dict, List, Any, Optional, Tuple, Callable
from abc import ABC
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QThread


class AnalysisConfig:
    """分析類型配置類"""
    
    def __init__(self, display_name: str, debug_prefix: str, 
                 data_source: str = "json", cli_function: str = None,
                 file_patterns: List[str] = None, **kwargs):
        """
        初始化分析配置
        
        Args:
            display_name: 顯示名稱
            debug_prefix: 除錯前綴
            data_source: 數據源類型 (json/csv/api/realtime)
            cli_function: CLI 功能編號或命令
            file_patterns: 檔案搜尋模式
            **kwargs: 額外的配置參數
        """
        self.display_name = display_name
        self.debug_prefix = debug_prefix
        self.data_source = data_source
        self.cli_function = cli_function
        self.file_patterns = file_patterns or []
        
        # 儲存額外配置
        for key, value in kwargs.items():
            setattr(self, key, value)


class CliAnalysisWorker(QThread):
    """背景執行 CLI 分析的工作執行緒
    
    統一的 CLI 調用模組，提供標準的編碼處理和信號機制。
    支援所有分析類型的 CLI 調用。
    """
    
    # 定義信號
    progress_updated = pyqtSignal(str)  # 進度更新信號
    analysis_completed = pyqtSignal(bool, str)  # 分析完成信號 (成功/失敗, 訊息)
    output_received = pyqtSignal(str)  # 輸出信號
    
    def __init__(self, year, race, session, force_mode=1, parent=None):
        super().__init__(parent)
        self.year = year
        self.race = race
        self.session = session
        self.force_mode = force_mode
        self.process = None
        self.should_stop = False
        
    def run(self):
        """
        [已禁用] 執行 CLI 分析
        
        ⚠️ API-ONLY 模式: CliAnalysisWorker 已完全禁用
        系統只允許通過 REST API 獲取數據
        """
        print("[CLI_WORKER] ⚠️  [API-ONLY] CliAnalysisWorker 已禁用")
        print("[CLI_WORKER] 💡 提示: 請使用 API 或手動執行 CLI 獲取數據")
        self.progress_updated.emit("⚠️ CLI 調用已禁用 - 請使用 API")
        self.analysis_completed.emit(False, "API-ONLY 模式: CLI 調用已禁用")
    
    def stop(self):
        """停止分析"""
        pass  # CliAnalysisWorker 已禁用,無需執行任何操作


class UniversalDataLoaderMeta(type(QObject), type(ABC)):
    """解決 QObject 和 ABC 的 metaclass 衝突"""
    pass


class UniversalDataLoader(QObject, ABC, metaclass=UniversalDataLoaderMeta):
    """
    通用數據載入器基類
    
    所有 F1T 分析模組的共用載入器，提供統一的數據載入、
    檔案搜尋、CLI生成和監控機制。
    """
    
    # 標準信號定義 (所有分析模組共用)
    data_loaded = pyqtSignal(dict)      # 數據載入完成
    load_progress = pyqtSignal(int)     # 載入進度 (0-100)
    load_error = pyqtSignal(str)        # 載入錯誤
    status_changed = pyqtSignal(str)    # 狀態變更
    
    # 支援的分析類型註冊表
    ANALYSIS_TYPES = {}
    
    @classmethod
    def register_analysis_type(cls, analysis_type: str, config: AnalysisConfig):
        """註冊新的分析類型"""
        cls.ANALYSIS_TYPES[analysis_type] = config
    
    def __init__(self, analysis_type: str, parent=None):
        """
        初始化通用數據載入器
        
        Args:
            analysis_type: 分析類型 ('telemetry', 'rain', 'accident', 等)
            parent: 父級 QObject
        """
        super().__init__(parent)
        
        # 驗證分析類型，必要時建立臨時配置以確保測試可以進行
        if analysis_type not in self.ANALYSIS_TYPES:
            fallback_display = f"{analysis_type} Analysis" if analysis_type else "Generic Analysis"
            fallback_prefix = (analysis_type or "GENERIC").upper()
            fallback_config = AnalysisConfig(
                display_name=fallback_display,
                debug_prefix=fallback_prefix,
                data_source='json',
                file_patterns=[f"{analysis_type}_*.json"] if analysis_type else ["*.json"],
            )
            self.ANALYSIS_TYPES[analysis_type] = fallback_config
            print(f"[UNIVERSAL_LOADER] ⚠️ 未註冊的分析類型 '{analysis_type}'，已建立臨時配置以維持相容性")
            
        self.analysis_type = analysis_type
        self.config = self.ANALYSIS_TYPES[analysis_type]
        # 強制 API-ONLY 模式：預設禁止本地 JSON/CLI 回退
        # 若要在開發環境啟用本地回退，可在子類或測試中顯式設定
        self._allow_local_fallback = False
        self._debug("📡 API-ONLY 模式已啟用：本地 JSON 回退與 CLI 自動生成已停用")
        
        # 狀態變數
        self._base_paths = ["json", "json_exports", "cache"]
        self._is_loading = False
        self._current_data = None
        self.current_session = None
        self._generation_params = None
        
        # 監控定時器 - 設置 parent 防止被垃圾回收
        self._generation_timer = QTimer(self)
        self._generation_timer.timeout.connect(self._check_generation_progress)
        
        self._generation_timeout_timer = QTimer(self)
        self._generation_timeout_timer.timeout.connect(self._on_generation_timeout)
        
        self._debug(f"初始化 {self.config.display_name} 載入器")

    # ========== 本地儲存策略工具 ==========

    def _local_storage_enabled(self) -> bool:
        """檢查是否允許使用本地 JSON/快取資料夾。"""
        allowed = getattr(self, "_allow_local_fallback", None)
        if allowed is None:
            return True
        return bool(allowed)

    def _get_search_directories(self) -> List[str]:
        """回傳實際要搜尋的資料夾清單。"""
        if not self._local_storage_enabled():
            return []

        unique_paths: List[str] = []
        for path in self._base_paths:
            if not path:
                continue
            if path not in unique_paths:
                unique_paths.append(path)
        return unique_paths
    
    def _debug(self, message: str):
        """統一的除錯輸出"""
        prefix = self.config.debug_prefix
        print(f"[{prefix} DEBUG] {message}")
    
    def _error(self, message: str):
        """統一的錯誤輸出"""
        prefix = self.config.debug_prefix
        print(f"[ERROR] [{prefix}] {message}")
    
    # ========== 公開API方法 ==========
    
    def load_data(self, **kwargs) -> bool:
        """
        載入分析數據 - 通用載入方法
        
        Args:
            **kwargs: 載入參數，根據分析類型而定
            
        Returns:
            bool: 載入是否成功啟動
        """
        try:
            self._debug("========== 數據載入 ==========")
            self._debug(f"類型: {self.config.display_name}")
            self._debug(f"參數: {kwargs}")
            
            if self._is_loading:
                self._debug("已在載入中，忽略重複請求")
                return False
                
            self._is_loading = True
            self.load_progress.emit(10)
            
            # 儲存當前會話資訊
            self.current_session = kwargs
            
            # 驗證載入參數
            if not self._validate_load_parameters(kwargs):
                self._error("載入參數驗證失敗")
                self.load_error.emit("載入參數不正確")
                self._is_loading = False
                return False
            
            # 尋找對應的數據檔案
            data_file = self._find_data_file(**kwargs)
            self._debug(f"搜尋結果: {data_file}")
            
            if not data_file:
                self._debug("❌ 找不到現有數據檔案")
                self._debug("⚠️  [API-ONLY 模式] 禁止呼叫 CLI 生成數據")
                self._debug("💡 提示: 請透過 API 獲取數據或手動執行 CLI 生成檔案")
                # ✅ 修正：靜默處理，不彈出錯誤視窗，讓用戶使用 API 獲取數據
                self._debug("📡 建議: 使用 API 獲取數據或確保已預先生成 JSON 檔案")
                self._is_loading = False
                # 不發送錯誤信號，避免彈出錯誤視窗
                return False
            else:
                self._debug("✅ 找到現有檔案，準備載入")
                
            # 使用 QTimer 模擬異步載入
            QTimer.singleShot(10, lambda: self._load_data_file(data_file))
            return True
            
        except Exception as e:
            self._error(f"載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前載入的數據"""
        return self._current_data
    
    def is_loading(self) -> bool:
        """檢查是否正在載入"""
        return self._is_loading
    
    def get_analysis_type(self) -> str:
        """獲取分析類型"""
        return self.analysis_type
    
    def get_display_name(self) -> str:
        """獲取顯示名稱"""
        return self.config.display_name
    
    def create_cli_worker(self, year: int, race: str, session: str, force_mode: int = 1) -> CliAnalysisWorker:
        """
        創建 CLI 分析工作執行緒
        
        統一的 CLI 調用入口，提供標準的編碼處理和信號機制。
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段類型
            force_mode: 功能編號 (預設為 1)
            
        Returns:
            CliAnalysisWorker: 配置好的工作執行緒
            
        Example:
            # 創建降雨分析工作執行緒
            worker = self.create_cli_worker(2025, "Japan", "R", 1)
            worker.analysis_completed.connect(self.on_analysis_completed)
            worker.output_received.connect(self.on_output_received)
            worker.start()
        """
        return CliAnalysisWorker(year, race, session, force_mode, parent=self)
    
    # ========== 抽象方法 - 子類必須實現 ==========
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        Args:
            params: 載入參數
            
        Returns:
            bool: 參數是否有效
        """
        # 預設允許載入，具體載入器可自行覆寫
        return True
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """
        構建檔案名稱搜尋模式
        
        Args:
            **kwargs: 搜尋參數
            
        Returns:
            List[str]: 檔案名稱模式列表
        """
        # 預設不提供特定模式，由子類覆寫；提供通配避免空列表導致搜尋器異常
        return ["*.json"]
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        透過 CLI 工具生成數據
        
        Args:
            **kwargs: 生成參數
            
        Returns:
            bool: 是否成功啟動生成
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已在基類中禁用")
        self._debug("💡 提示: 請透過 API 或手動生成數據檔案")
        return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """
        驗證數據格式
        
        Args:
            raw_data: 原始數據
            
        Returns:
            bool: 數據格式是否正確
        """
        # 預設接受任何字典資料，子類可覆寫進行嚴格驗證
        return isinstance(raw_data, (dict, list)) or raw_data is None
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """
        處理數據為標準格式
        
        Args:
            raw_data: 原始數據
            
        Returns:
            Dict[str, Any]: 處理後的標準數據格式
        """
        if isinstance(raw_data, dict):
            return raw_data
        if raw_data is None:
            return {}
        return {"raw_data": raw_data}
    
    # ========== 通用檔案搜尋邏輯 ==========
    
    def _find_data_file(self, **kwargs) -> Optional[str]:
        """搜尋分析數據檔案 - 通用搜尋邏輯"""
        try:
            self._debug("========== 搜尋數據檔案 ==========")
            self._debug(f"🔍 搜尋條件: {kwargs}")
            
            # 搜尋目錄
            search_directories = self._get_search_directories()
            if not search_directories:
                self._debug("🚫 本地 JSON 後備已停用，跳過檔案搜尋流程")
                return None

            self._debug(f"📂 搜尋目錄: {search_directories}")
            
            # 構建檔案名稱搜尋模式
            filename_patterns = self._build_filename_patterns(**kwargs)
            
            # 精確搜尋
            self._debug("🔍 開始精確搜尋...")
            found_file = None
            
            for search_dir in search_directories:
                self._debug(f"📂 搜尋目錄: {search_dir}")
                
                if not os.path.exists(search_dir):
                    self._debug(f"   ❌ 目錄不存在: {search_dir}")
                    continue
                
                for i, filename_pattern in enumerate(filename_patterns, 1):
                    search_pattern = os.path.join(search_dir, filename_pattern)
                    self._debug(f"   🔍 模式 {i}: {search_pattern}")
                    matches = glob.glob(search_pattern)
                    
                    if matches:
                        # 如果有多個匹配，選擇最新的
                        found_file = max(matches, key=os.path.getmtime)
                        self._debug(f"✅ 找到檔案: {found_file}")
                        self._debug(f"📊 匹配檔案數量: {len(matches)}")
                        if len(matches) > 1:
                            self._debug("📋 所有匹配檔案:")
                            for match in matches:
                                self._debug(f"     - {match}")
                        break
                    else:
                        self._debug(f"   ❌ 模式 {i} 無匹配")
                
                # 如果找到檔案就跳出目錄循環
                if found_file:
                    break
                
                self._debug(f"❌ 目錄 {search_dir} 無匹配檔案")
            
            if found_file:
                self._debug(f"✅ 搜尋成功: {found_file}")
                return found_file
            
            # 精確搜尋失敗，需要生成新檔案
            self._debug("❌ 未找到符合的數據檔案，需要生成新檔案")
            return None
            
        except Exception as e:
            self._error(f"搜尋檔案時發生錯誤: {str(e)}")
            self.load_error.emit(f"搜尋檔案時發生錯誤: {str(e)}")
            return None
    
    # ========== 通用數據生成邏輯 ==========
    
    def _start_data_generation(self, **kwargs):
        """啟動數據生成流程"""
        try:
            self._debug("========== 啟動數據生成流程 ==========")
            self._debug(f"生成參數: {kwargs}")
            
            # 儲存參數供後續使用
            self._generation_params = kwargs
            
            # 啟動數據生成
            success = self._generate_data_via_cli(**kwargs)
            
            if success:
                self._debug("✅ 數據生成啟動成功，開始監控檔案生成")
                # 啟動定時器檢查檔案是否生成完成
                self._start_generation_monitoring()
            else:
                self._debug("❌ 數據生成啟動失敗")
                self.load_error.emit(f"啟動數據生成失敗")
                self._is_loading = False
                
        except Exception as e:
            self._error(f"啟動生成時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.load_error.emit(f"啟動生成時發生錯誤: {str(e)}")
            self._is_loading = False
    
    # ========== 通用監控系統 ==========
    
    def _start_generation_monitoring(self):
        """啟動檔案生成監控"""
        self._debug("========== 啟動監控系統 ==========")
        self._debug(f"生成參數: {self._generation_params}")
        
        # 檢查預期生成的檔案路徑
        if self._generation_params:
            expected_patterns = []
            for pattern in self.config.file_patterns:
                try:
                    # 嘗試使用現有參數格式化
                    formatted_pattern = pattern.format(**self._generation_params)
                    expected_patterns.append(formatted_pattern)
                except KeyError as e:
                    # 如果缺少參數，使用自定義的檔案名稱模式生成方法
                    self._debug(f"⚠️ 檔案模式缺少參數 {e}，使用自定義格式化方法")
                    try:
                        custom_patterns = self._build_filename_patterns(**self._generation_params)
                        expected_patterns.extend(custom_patterns)
                        break  # 使用自定義方法後跳出循環
                    except Exception as custom_error:
                        self._debug(f"❌ 自定義格式化也失敗: {custom_error}")
                        expected_patterns.append(f"<格式化失敗: {pattern}>")
            
            if expected_patterns:
                self._debug(f"📋 預期檔案模式: {expected_patterns}")
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._debug("啟動主監控計時器 (每5秒檢查)")
        self._generation_timer.start(5000)
        
        self._debug("啟動超時計時器 (180秒)")
        self._generation_timeout_timer.start(180000)
        
        self._debug("✅ 監控系統已啟動")
        self.status_changed.emit("正在生成數據，請稍候...")
        
        # 立即執行一次檢查
        self._debug("🧪 執行立即測試檢查...")
        QTimer.singleShot(1000, self._check_generation_progress)
    
    def _check_generation_progress(self):
        """檢查檔案生成進度"""
        try:
            self._debug("========== 監控檢查觸發 ==========")
            self._debug(f"時間: {datetime.now().strftime('%H:%M:%S')}")
            
            if self._generation_params:
                self._debug(f"檢查參數: {self._generation_params}")
                
                # 檢查是否有新檔案生成
                self._debug("開始搜尋檔案...")
                data_file = self._find_data_file(**self._generation_params)
                
                if data_file:
                    self._debug(f"檔案生成完成: {data_file}")
                    self._debug("停止監控並載入檔案")
                    
                    # 停止監控
                    self._stop_generation_monitoring()
                    
                    # 載入新生成的檔案
                    QTimer.singleShot(10, lambda: self._load_data_file(data_file))
                else:
                    self._debug("繼續等待檔案生成...")
                    self._debug("下次檢查將在5秒後進行")
            else:
                self._debug("❌ 缺少 _generation_params 參數")
                self._debug("停止監控")
                self._stop_generation_monitoring()
                
        except Exception as e:
            self._error(f"監控檢查異常: {e}")
            import traceback
            traceback.print_exc()
            self._debug("嘗試繼續監控...")
    
    def _on_generation_timeout(self):
        """處理生成超時"""
        self._debug("========== 監控超時 ==========")
        self._debug("檔案生成超時 (180秒)")
        self._debug("停止監控系統")
        self._stop_generation_monitoring()
        self.load_error.emit("數據生成超時，請檢查網路連線或重試")
        self._is_loading = False
    
    def _stop_generation_monitoring(self):
        """停止檔案生成監控"""
        self._debug("========== 停止監控系統 ==========")
        if hasattr(self, '_generation_timer'):
            self._generation_timer.stop()
            self._debug("主監控計時器已停止")
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.stop()
            self._debug("超時計時器已停止")
        self._debug("✅ 監控系統已完全停止")
    
    # ========== 通用檔案載入和處理 ==========
    
    def _load_data_file(self, file_path: str):
        """載入數據檔案"""
        try:
            self._debug("========== 數據檔案載入 ==========")
            self._debug(f"載入檔案: {file_path}")
            
            # 檢查檔案狀態
            if not os.path.exists(file_path):
                self._debug(f"❌ 檔案不存在: {file_path}")
                self.load_error.emit(f"檔案不存在: {file_path}")
                return
                
            file_size = os.path.getsize(file_path)
            self._debug(f"檔案大小: {file_size} bytes")
            
            self.load_progress.emit(90)
            self.status_changed.emit("正在處理數據...")
            
            # 根據檔案類型載入數據
            raw_data = self._load_file_by_type(file_path)
            
            if raw_data is None:
                self._debug("❌ 檔案載入失敗")
                self.load_error.emit("檔案載入失敗")
                self._is_loading = False
                return
            
            self._debug("數據載入成功")
            
            # 驗證數據格式
            self._debug("開始驗證數據格式...")
            if self._validate_data_format(raw_data):
                self._debug("✅ 數據格式驗證通過")
                # 處理為標準分析格式
                processed_data = self._process_data(raw_data)
                
                self._debug("========== 即將發送數據 ==========")
                self._debug(f"處理後數據類型: {type(processed_data)}")
                
                self.load_progress.emit(100)
                self.status_changed.emit("數據載入完成")
                self._current_data = processed_data
                self._is_loading = False
                
                self._debug("🚀 即將發送 data_loaded 信號...")
                self.data_loaded.emit(processed_data)
                self._debug("✅ data_loaded 信號已發送")
                
            else:
                self._debug("❌ 數據格式驗證失敗")
                self.load_error.emit("數據格式驗證失敗")
                self._is_loading = False
                
        except Exception as e:
            self._error(f"數據檔案載入失敗: {str(e)}")
            self.load_error.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
    
    def _load_file_by_type(self, file_path: str) -> Any:
        """根據檔案類型載入數據"""
        try:
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.json':
                self._debug("載入 JSON 檔案...")
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
                    
            elif file_ext == '.csv':
                self._debug("載入 CSV 檔案...")
                import pandas as pd
                return pd.read_csv(file_path)
                
            elif file_ext == '.pkl':
                self._debug("載入 Pickle 檔案...")
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
                    
            else:
                self._error(f"不支援的檔案類型: {file_ext}")
                return None
                
        except Exception as e:
            self._error(f"載入檔案失敗: {e}")
            return None
    
    # ========== 工具方法 ==========
    
    # ========== 清理 ==========
    def cleanup(self) -> None:
        """停止計時器並斷開訊號，避免物件被計時器/連線保活。"""
        try:
            try:
                if hasattr(self, '_generation_timer') and self._generation_timer:
                    self._generation_timer.stop()
            except Exception:
                pass
            try:
                if hasattr(self, '_generation_timeout_timer') and self._generation_timeout_timer:
                    self._generation_timeout_timer.stop()
            except Exception:
                pass
            for sig in (self.data_loaded, self.load_error, self.status_changed, self.load_progress):
                try:
                    sig.disconnect()
                except Exception:
                    pass
            self._is_loading = False
            self.current_session = None
        except Exception:
            pass

    def calculate_statistics(self, data: List[float]) -> Dict[str, float]:
        """計算統計數據"""
        if not data:
            return {"max": 0, "min": 0, "avg": 0, "count": 0}
        
        return {
            "max": max(data),
            "min": min(data),
            "avg": sum(data) / len(data),
            "count": len(data)
        }


# ========== 預設分析類型註冊 ==========

# 註冊遙測分析類型
UniversalDataLoader.register_analysis_type(
    'telemetry',
    AnalysisConfig(
        display_name='遙測分析',
        debug_prefix='TELEMETRY',
        data_source='json',
        cli_function='13',  # 功能13: 車手比較分析
        file_patterns=['comparison_telemetry_*.json']
    )
)

# 註冊降雨分析類型
UniversalDataLoader.register_analysis_type(
    'rain',
    AnalysisConfig(
        display_name='降雨分析',
        debug_prefix='RAIN',
        data_source='json',
        cli_function='rain_intensity',  # 降雨強度分析
        file_patterns=['rain_analysis_*.json', 'rain_intensity_*.json']
    )
)

# 註冊事故分析類型
from core.gui_i18n import tr
UniversalDataLoader.register_analysis_type(
    'accident',
    AnalysisConfig(
        display_name=tr('accident_analysis', 'Accident Analysis'),
        debug_prefix='ACCIDENT',
        data_source='json',
        cli_function='accident',
        file_patterns=['accident_analysis_*.json', 'incidents_*.json']
    )
)

# 註冊進站分析類型
UniversalDataLoader.register_analysis_type(
    'pitstop',
    AnalysisConfig(
        display_name='進站分析',
        debug_prefix='PITSTOP',
        data_source='json',
        cli_function='pitstop',
        file_patterns=['pitstop_analysis_*.json', 'pit_strategy_*.json']
    )
)

# 註冊車手積分榜類型
UniversalDataLoader.register_analysis_type(
    'driver_standings',
    AnalysisConfig(
        display_name='車手積分榜',
        debug_prefix='DRIVER_STANDINGS',
        data_source='json',
        cli_function='97',  # 功能97: 賽季積分查詢
        file_patterns=['championship_standings_*.json']
    )
)

# 註冊車隊積分榜類型
UniversalDataLoader.register_analysis_type(
    'constructor_standings',
    AnalysisConfig(
        display_name='車隊積分榜',
        debug_prefix='CONSTRUCTOR_STANDINGS',
        data_source='json',
        cli_function='97',  # 功能97: 賽季積分查詢
        file_patterns=['championship_standings_*.json']
    )
)


# ========== 工廠函數 ==========

def create_data_loader(analysis_type: str, parent=None) -> UniversalDataLoader:
    """
    創建數據載入器的工廠函數
    
    Args:
        analysis_type: 分析類型
        parent: 父級 QObject
        
    Returns:
        UniversalDataLoader: 數據載入器實例
        
    Note:
        這是一個抽象基類的工廠函數，實際使用時需要具體的實現類
    """
    # 這裡返回基類，實際使用時應該返回具體的實現類
    # 例如：TelemetryDataLoader, RainDataLoader 等
    if analysis_type not in UniversalDataLoader.ANALYSIS_TYPES:
        raise ValueError(f"不支援的分析類型: {analysis_type}")
    
    # 實際實現中，這裡應該根據 analysis_type 返回對應的具體實現類
    # 目前先返回基類以保持向後兼容
    class ConcreteDataLoader(UniversalDataLoader):
        def _validate_load_parameters(self, params): return True
        def _build_filename_patterns(self, **kwargs): return ["*.json"]
        # 明確禁止 CLI 路徑
        def _generate_data_via_cli(self, **kwargs): return False
        def _validate_data_format(self, raw_data): return True
        def _process_data(self, raw_data): return raw_data
    
    return ConcreteDataLoader(analysis_type, parent)
