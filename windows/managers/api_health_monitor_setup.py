# -*- coding: utf-8 -*-
"""
ApiHealthMonitorSetup - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ApiHealthMonitorSetup:
    """從 f1t_gui_main.py 提取的 setup_api_health_monitor 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_api_health_monitor(self) -> None:
        """Initialise the periodic API health checks and kick off the first probe.
        
        ⏰ 調整頻率：初始化時檢查一次 + 每 5 分鐘檢查一次（避免過度頻繁）
        """
        try:
            self.main_window.api_base_url = self.main_window._determine_api_base_url()
            self.main_window._api_last_state = 'unknown'
            self.main_window.api_mode_enabled = False
            if self.main_window.api_status_label:
                self.main_window.api_status_label.setText('[API] CHECKING...')
                self.main_window.api_status_label.setStyleSheet('color: #f1c40f; font-weight: bold;')
                self.main_window.api_status_label.setToolTip(f'API Base: {self.main_window.api_base_url}\nChecking...')
            if self.main_window.ready_label:
                self.main_window.ready_label.setText('[READY] INITIALIZING')
            if self.main_window.api_health_timer:
                self.main_window.api_health_timer.stop()
            self.main_window.api_health_timer = QTimer(self.main_window)
            # ✅ 修復：從 60 秒改為 5 分鐘 (300,000 毫秒)
            self.main_window.api_health_timer.setInterval(300_000)
            self.main_window.api_health_timer.timeout.connect(self.main_window.trigger_api_health_check)
            # ✅ 初始化時檢查一次
            QTimer.singleShot(200, self.main_window.trigger_api_health_check)
            self.main_window.api_health_timer.start()
            # ⚠️ 已停用：不再透過 GUI 輪詢 CLI 執行狀態
            # self.main_window.setup_api_runtime_monitor()
        except Exception as exc:
            logger.error('Failed to setup API health monitor: %s', exc)
            if self.main_window.api_status_label:
                self.main_window.api_status_label.setText('[API] ERROR')
                self.main_window.api_status_label.setStyleSheet('color: #e74c3c; font-weight: bold;')
                self.main_window.api_status_label.setToolTip(str(exc))
            if self.main_window.cli_status_label:
                self.main_window.cli_status_label.setText('[CLI] UNKNOWN')
                self.main_window.cli_status_label.setStyleSheet('color: #c0392b; font-weight: bold;')
                self.main_window.cli_status_label.setToolTip(str(exc))
