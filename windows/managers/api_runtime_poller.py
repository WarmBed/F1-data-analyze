# -*- coding: utf-8 -*-
"""
ApiRuntimePoller - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from core.logger import get_logger
from windows.workers.api_workers import ApiRuntimeWorker

logger = get_logger(__name__)


class ApiRuntimePoller:
    """從 f1t_gui_main.py 提取的 trigger_api_runtime_poll 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def trigger_api_runtime_poll(self) -> None:
        """Kick off a single runtime poll if no worker is currently running.
        
        ✅ 新架構：使用單例 Worker，避免頻繁創建銷毀導致的洩漏
        """
        if not self.main_window.api_base_url:
            return
        
        # ⚠️ 關鍵修復：檢查 worker 是否正在運行，而不是只檢查標誌
        if self.main_window._api_runtime_worker is not None and self.main_window._api_runtime_worker.isRunning():
            return  # Worker 還在執行，跳過此次輪詢

        # ✅ 首次創建或重新創建 worker
        if self.main_window._api_runtime_worker is None:
            try:
                self.main_window._api_runtime_worker = ApiRuntimeWorker(self.main_window.api_base_url, parent=self.main_window)
                # ✅ 使用 Qt.UniqueConnection 確保信號只連接一次
                self.main_window._api_runtime_worker.result_ready.connect(
                    self.main_window.on_api_runtime_result, Qt.UniqueConnection
                )
                self.main_window._api_runtime_worker.finished.connect(
                    self.main_window.on_api_runtime_finished, Qt.UniqueConnection
                )
            except Exception as exc:
                logger.error('Failed to create API runtime worker: %s', exc)
                return
        
        # ✅ 啟動 worker（如果已經完成，可以重新啟動）
        try:
            if not self.main_window._api_runtime_worker.isRunning():
                self.main_window._api_runtime_worker_active = True
                self.main_window._api_runtime_worker.start()
        except Exception as exc:
            logger.error('Failed to start API runtime worker: %s', exc)
            self.main_window._api_runtime_worker_active = False
