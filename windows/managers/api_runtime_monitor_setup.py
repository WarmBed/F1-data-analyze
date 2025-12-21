# -*- coding: utf-8 -*-
"""
ApiRuntimeMonitorSetup - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ApiRuntimeMonitorSetup:
    """從 f1t_gui_main.py 提取的 setup_api_runtime_monitor 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def setup_api_runtime_monitor(self) -> None:
        """Initialise the periodic polling of the CLI runtime status.
        
        ⚠️ 已停用：不再透過 GUI 輪詢 CLI 執行狀態（2025-10-11）
        保留此方法以備未來需要時重新啟用
        """
        logger.info("⚠️  API Runtime Monitor 已停用，不再輪詢 CLI 狀態")
        return  # ✅ 直接返回，不執行任何操作
        
        # 以下代碼已停用，保留以備未來使用
        try:
            if not self.main_window.api_base_url:
                return
            if self.main_window.api_runtime_timer:
                self.main_window.api_runtime_timer.stop()
                self.main_window.api_runtime_timer.deleteLater()
            self.main_window.api_runtime_timer = QTimer(self.main_window)
            # ✅ 修復：從 5 秒改為 30 秒 (30,000 毫秒)
            self.main_window.api_runtime_timer.setInterval(30_000)
            self.main_window.api_runtime_timer.timeout.connect(self.main_window.trigger_api_runtime_poll)
            # ✅ 初始化時檢查一次
            QTimer.singleShot(500, self.main_window.trigger_api_runtime_poll)
            self.main_window.api_runtime_timer.start()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning('Failed to setup API runtime monitor: %s', exc)
