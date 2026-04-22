# -*- coding: utf-8 -*-
"""
F1T GUI - CLI Workers
======================

背景執行 CLI 分析的工作執行緒和管理器。

從 f1t_gui_main.py 提取 (原始行號: 1259-1586, 328 行)
提取日期: 2025-06-14
"""

# LOCAL_ONLY_REFACTOR:
# This file contains a disabled GUI-to-CLI subprocess path followed by
# unreachable legacy code. Do not add new work here. The replacement path should
# be a shared local task runner calling core.local_analysis_executor.

import os
import sys
import subprocess
import logging
import uuid
import glob
import json

from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from core.gui_i18n import tr

# 設定日誌
logger = logging.getLogger(__name__)


class CliAnalysisWorker(QThread):
    """背景執行 CLI 分析的工作執行緒"""
    
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
        """執行 CLI 分析"""
        try:
            disabled_message = tr("cli_disabled", "API-ONLY 模式：CLI 調用已禁用")
            logger.warning("[CLI_WORKER] %s", disabled_message)
            self.progress_updated.emit(disabled_message)
            self.analysis_completed.emit(False, disabled_message)
            return
            # 構建CLI命令
            cmd = [
                sys.executable,
                "f1_analysis_modular_main.py",
                "-f", str(self.force_mode),  # 使用指定的 force_mode
                "-y", str(self.year),
                "-r", self.race,
                "-s", self.session
            ]
            
            logger.debug(f"[DEBUG]    [CLI_WORKER] 準備執行命令: {' '.join(cmd)}")
            logger.debug(f"[DEBUG]    [CLI_WORKER] 工作目錄: {os.getcwd()}")
            
            self.progress_updated.emit(f"啟動 CLI 分析: {self.year} {self.race} {self.session}")
            
            # 設置環境變數以確保正確的編碼
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONLEGACYWINDOWSFS'] = '0'
            
            logger.debug(f"[DEBUG]    [CLI_WORKER] 環境變數已設置: PYTHONIOENCODING=utf-8")
            
            # 啟動進程，使用 UTF-8 編碼避免編碼問題
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',  # 遇到無法解碼的字符時替換為 ?
                env=env,  # 使用自定義環境變數
                cwd=os.getcwd(),
                bufsize=1,
                universal_newlines=True
            )
            
            logger.debug(f"[DEBUG]    [CLI_WORKER] 進程已啟動，PID: {self.process.pid}")
            self.progress_updated.emit(f"CLI 分析已啟動 (PID: {self.process.pid})")
            
            # 即時讀取輸出
            while True:
                if self.should_stop:
                    if self.process:
                        self.process.terminate()
                    break
                    
                # 檢查進程是否完成
                if self.process.poll() is not None:
                    break
                    
                # 讀取輸出，處理編碼問題
                try:
                    output = self.process.stdout.readline()
                    if output:
                        self.output_received.emit(output.strip())
                except UnicodeDecodeError as e:
                    # 如果遇到編碼錯誤，記錄但不中斷
                    self.output_received.emit(f"[編碼錯誤] 無法解碼部分輸出: {str(e)}")
                    
                # 短暫休息避免CPU占用過高
                self.msleep(100)
            
            # 獲取最終結果
            if not self.should_stop:
                return_code = self.process.wait()
                logger.debug(f"[DEBUG]    [CLI_WORKER] 進程結束，返回碼: {return_code}")
                
                if return_code == 0:
                    logger.debug(f"[DEBUG]    [CLI_WORKER] CLI 分析成功完成")
                    self.analysis_completed.emit(True, "CLI 分析成功完成")
                else:
                    logger.debug(f"[DEBUG]    [CLI_WORKER] CLI 分析失敗，返回碼: {return_code}")
                    try:
                        stderr_output = self.process.stderr.read()
                        logger.debug(f"[DEBUG]    [CLI_WORKER] 錯誤輸出: {stderr_output}")
                        self.analysis_completed.emit(False, f"CLI 分析失敗: {stderr_output}")
                    except UnicodeDecodeError as e:
                        logger.debug(f"[DEBUG]    [CLI_WORKER] 錯誤輸出編碼問題: {str(e)}")
                        self.analysis_completed.emit(False, f"CLI 分析失敗 (編碼錯誤): {str(e)}")
            else:
                logger.debug(f"[DEBUG]    [CLI_WORKER] 分析被用戶取消")
                self.analysis_completed.emit(False, "分析被用戶取消")
                
        except Exception as e:
            self.analysis_completed.emit(False, f"CLI 分析錯誤: {str(e)}")
    
    def stop(self):
        """停止分析"""
        self.should_stop = True
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # 等待進程結束，如果沒有回應則強制終止
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


class CliAnalysisManager(QObject):
    """統一的 CLI 分析管理器 - 業務服務層"""
    
    # 定義信號
    analysis_started = pyqtSignal(str, str, str, str)  # (request_id, year, race, session)
    analysis_progress = pyqtSignal(str, str)  # (request_id, message)
    analysis_output = pyqtSignal(str, str)  # (request_id, output)
    analysis_completed = pyqtSignal(str, bool, str)  # (request_id, success, message)
    json_ready = pyqtSignal(str, dict)  # (request_id, json_data)
    
    def __init__(self):
        super().__init__()
        self.active_requests = {}  # 存儲活動的請求
        self.worker_threads = {}   # 存儲工作線程
        
    def request_analysis(self, year, race, session, force_mode=1, requester_id=None):
        """請求 CLI 分析"""
        request_id = str(uuid.uuid4())
        
        # 記錄請求者
        self.active_requests[request_id] = {
            'year': year,
            'race': race, 
            'session': session,
            'requester_id': requester_id,
            'status': 'starting'
        }
        
        disabled_message = tr("cli_disabled", "API-ONLY 模式：CLI 調用已禁用")
        self.analysis_started.emit(request_id, year, race, session)
        self.analysis_progress.emit(request_id, disabled_message)
        self.analysis_completed.emit(request_id, False, disabled_message)
        logger.debug(f"[START] CLI分析請求已被禁用: {request_id} ({year} {race} {session})")
        return request_id
    
    def cancel_analysis(self, request_id):
        """取消分析"""
        if request_id in self.worker_threads:
            worker = self.worker_threads[request_id]
            if worker.isRunning():
                worker.stop()
                worker.wait(5000)
            del self.worker_threads[request_id]
            
        if request_id in self.active_requests:
            del self.active_requests[request_id]
            
        logger.debug(f"[STOP] CLI分析已取消: {request_id}")
    
    def _on_analysis_completed(self, request_id, success, message):
        """處理分析完成"""
        self.analysis_completed.emit(request_id, success, message)
        
        # 清理線程
        if request_id in self.worker_threads:
            del self.worker_threads[request_id]
            
        logger.debug(f"[OK] CLI分析完成: {request_id}, 成功: {success}")
    
    def _start_json_monitoring(self, request_id, year, race, session):
        """開始監控 JSON 文件產生"""
        if request_id not in self.active_requests:
            return
            
        # 創建計時器監控 JSON 文件
        timer = QTimer()
        timer.timeout.connect(lambda: self._check_json_ready(request_id, year, race, session, timer))
        timer.start(3000)  # 每3秒檢查一次
        
        # 保存計時器引用
        self.active_requests[request_id]['json_timer'] = timer
        
        # 設置超時 (120秒)
        timeout_timer = QTimer()
        timeout_timer.setSingleShot(True)
        timeout_timer.timeout.connect(lambda: self._on_json_timeout(request_id, timer, timeout_timer))
        timeout_timer.start(120000)
        
        self.active_requests[request_id]['timeout_timer'] = timeout_timer
    
    def _check_json_ready(self, request_id, year, race, session, timer):
        """檢查 JSON 是否準備好"""
        if request_id not in self.active_requests:
            timer.stop()
            return
            
        # 嘗試載入 JSON
        json_data = self._try_load_json(year, race, session)
        if json_data:
            # JSON 已產生
            timer.stop()
            if 'timeout_timer' in self.active_requests[request_id]:
                self.active_requests[request_id]['timeout_timer'].stop()
            
            self.json_ready.emit(request_id, json_data)
            logger.debug(f"JSON已準備好: {request_id}")
            
            # 清理請求
            if request_id in self.active_requests:
                del self.active_requests[request_id]
    
    def _on_json_timeout(self, request_id, timer, timeout_timer):
        """JSON 等待超時"""
        timer.stop()
        timeout_timer.stop()
        
        self.analysis_completed.emit(request_id, False, "JSON等待超時")
        
        if request_id in self.active_requests:
            del self.active_requests[request_id]
        
        logger.debug(f"[TIME] JSON等待超時: {request_id}")
    
    def _try_load_json(self, year, race, session):
        """嘗試載入 JSON 檔案"""
        # 搜尋模式與原有邏輯保持一致
        json_patterns = [
            f"json/temp_analysis_{year}_{race}_{session}.json",
            f"json/*{year}*{race}*{session}*.json",
            f"json_exports/*{year}*{race}*{session}*.json", 
            f"cache/*{year}*{race}*{session}*.json"
        ]
        
        for pattern in json_patterns:
            if '*' in pattern:
                json_files = glob.glob(pattern)
                if json_files:
                    pattern = json_files[0]  # 使用第一個匹配的文件
            
            if os.path.exists(pattern):
                try:
                    with open(pattern, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"[ERROR] JSON載入錯誤 {pattern}: {e}")
        
        return None
    
    def cleanup_all(self):
        """清理所有活動的分析"""
        logger.debug(f"[CLEANUP] 檢查活動的分析請求: {len(self.active_requests)} 個")
        
        if not self.active_requests:
            logger.debug("[CLEANUP] 沒有活動的分析請求需要清理")
        else:
            logger.debug(f"[CLEANUP] 開始清理 {len(self.active_requests)} 個活動請求...")
            
        for i, request_id in enumerate(list(self.active_requests.keys())):
            logger.debug(f"[CLEANUP] 正在取消分析請求 {i+1}/{len(self.active_requests)}: {request_id}")
            self.cancel_analysis(request_id)
            logger.debug(f"[CLEANUP] 分析請求已取消: {request_id}")
            
        logger.debug("[CLEANUP] CLI分析管理器已清理所有資源")


class MainWindowParameterProvider:
    """主視窗參數提供者 - 實現 IParameterProvider 介面"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def get_current_year(self) -> str:
        """從主視窗獲取當前年份"""
        try:
            if hasattr(self.main_window, 'get_selected_year'):
                return str(self.main_window.get_selected_year())
            if hasattr(self.main_window, 'year_combo') and self.main_window.year_combo:
                return self.main_window.year_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [PARAM_PROVIDER] 獲取年份失敗: {e}")
        return "2025"  # 預設值
    
    def get_current_race(self) -> str:
        """從主視窗獲取當前賽事"""
        try:
            if hasattr(self.main_window, 'get_selected_race_key'):
                return self.main_window.get_selected_race_key()
            if hasattr(self.main_window, 'race_combo') and self.main_window.race_combo:
                return self.main_window.race_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [PARAM_PROVIDER] 獲取賽事失敗: {e}")
        return "Japan"  # 預設值
    
    def get_current_session(self) -> str:
        """從主視窗獲取當前賽段"""
        try:
            if hasattr(self.main_window, 'get_selected_session_code'):
                return self.main_window.get_selected_session_code()
            if hasattr(self.main_window, 'session_combo') and self.main_window.session_combo:
                return self.main_window.session_combo.currentText()
        except Exception as e:
            logger.warning(f"[WARNING] [PARAM_PROVIDER] 獲取賽段失敗: {e}")
        return "R"  # 預設值


# 創建全域 CLI 分析管理器實例
cli_analysis_manager = CliAnalysisManager()
