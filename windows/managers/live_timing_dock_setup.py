# -*- coding: utf-8 -*-
"""
LiveTimingDockSetup - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingDockSetup:
    """從 f1t_gui_main.py 提取的 _setup_live_timing_dock 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _setup_live_timing_dock(self):
        """
        設置 Live Timing 控制面板 Dock Widget
        
        - 預設隱藏
        - 開啟任一 Live Timing 模組時自動顯示
        - 放置在視窗頂部
        """
        from modules.gui.live_timing.live_timing_modules.control_dock import LiveTimingControlDock
        
        # 創建 Dock Widget
        self.main_window.live_timing_dock = LiveTimingControlDock(self.main_window)
        
        # 添加到頂部
        self.main_window.addDockWidget(Qt.TopDockWidgetArea, self.main_window.live_timing_dock)
        
        # 預設隱藏
        self.main_window.live_timing_dock.hide()
        
        # 初始化時傳遞 F1TV 認證狀態
        if hasattr(self.main_window, 'f1tv_auth_manager') and self.main_window.f1tv_auth_manager:
            is_authenticated = self.main_window.f1tv_auth_manager.is_authenticated()
            self.main_window.live_timing_dock.set_f1tv_authenticated(is_authenticated)
            logger.debug(f"[INIT] F1TV auth state passed to Control Dock: {is_authenticated}")
        
        # 追蹤已開啟的 Live Timing 模組數量
        self.main_window._live_timing_module_count = 0
        
        logger.debug("[INIT] Live Timing Control Dock initialized (hidden)")
