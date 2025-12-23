# -*- coding: utf-8 -*-
"""
ApiHealthTrigger - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from windows.workers.api_workers import ApiHealthWorker

logger = get_logger(__name__)


class ApiHealthTrigger:
    """從 f1t_gui_main.py 提取的 trigger_api_health_check 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def trigger_api_health_check(self, manual: bool = False) -> None:
        """Launch a background API health check.
        
        ✅ 新架構：使用單例 Worker，避免頻繁創建銷毀導致的洩漏
        """
        if not self.main_window.api_base_url:
            self.main_window.api_base_url = self.main_window._determine_api_base_url()
        
        # ⚠️ 關鍵修復：檢查 worker 是否正在運行
        if self.main_window._api_health_worker is not None and self.main_window._api_health_worker.isRunning():
            if manual:
                QMessageBox.information(self.main_window, 'API Check', 'API health check is already running. Please wait.')
            return
        
        # ✅ 首次創建或重新創建 worker
        if self.main_window._api_health_worker is None:
            try:
                self.main_window._api_health_worker = ApiHealthWorker(
                    self.main_window.api_base_url, manual=manual, parent=self.main_window
                )
                # ✅ 使用 Qt.UniqueConnection 確保信號只連接一次
                self.main_window._api_health_worker.result_ready.connect(
                    self.main_window.on_api_health_result, Qt.UniqueConnection
                )
                self.main_window._api_health_worker.finished.connect(
                    self.main_window.on_api_health_finished, Qt.UniqueConnection
                )
            except Exception as exc:
                logger.error('Failed to create API health worker: %s', exc)
                if self.main_window.api_status_label:
                    self.main_window.api_status_label.setText('[API] ERROR')
                    self.main_window.api_status_label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                    self.main_window.api_status_label.setToolTip(f'Failed to create health worker: {exc}')
                return
        else:
            # ✅ Worker 已存在，更新參數
            self.main_window._api_health_worker.update_params(base_url=self.main_window.api_base_url, manual=manual)
        
        # ✅ 啟動 worker
        try:
            self.main_window._api_health_worker_active = True
            self.main_window._api_health_manual_request = manual
            if self.main_window.api_status_label:
                self.main_window.api_status_label.setText('[API] CHECKING...')
                self.main_window.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
                self.main_window.api_status_label.setToolTip(f'API Base: {self.main_window.api_base_url}\nChecking...')
            if self.main_window.check_api_action:
                self.main_window.check_api_action.setEnabled(False)
            logger.info('Starting API health check (manual=%s, base=%s)', manual, self.main_window.api_base_url)
            
            if not self.main_window._api_health_worker.isRunning():
                self.main_window._api_health_worker.start()
        except Exception as exc:
            logger.error('Failed to start API health worker: %s', exc)
            self.main_window._api_health_worker_active = False
            if self.main_window.check_api_action:
                self.main_window.check_api_action.setEnabled(True)
            if self.main_window.api_status_label:
                self.main_window.api_status_label.setText('[API] ERROR')
                self.main_window.api_status_label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                self.main_window.api_status_label.setToolTip(f'Failed to start health check: {exc}')
