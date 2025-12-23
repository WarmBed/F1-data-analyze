# -*- coding: utf-8 -*-
"""
LiveTimingOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from windows.widgets.popout_subwindow import PopoutSubWindow

from core.logger import get_logger

logger = get_logger(__name__)


class LiveTimingOpener:
    """從 f1t_gui_main.py 提取的 _open_live_timing_module 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _open_live_timing_module(self, module_name: str):
        """
        統一的 Live Timing 模組開啟入口
        
        所有 Live Timing 模組都通過 LiveTimingModuleFactory 創建，
        並使用 PopoutSubWindow 包裝，與標準分析模組 UI 風格一致。
        
        Args:
            module_name: 模組名稱（支援多語言）
        """
        from modules.gui.live_timing import LiveTimingModuleFactory
        
        factory = LiveTimingModuleFactory.get_instance()
        
        # 檢查模組是否已實現
        if not factory.is_implemented(module_name):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self.main_window,
                "Module Not Implemented",
                f"The module '{module_name}' is not yet implemented.\n"
                "Please check back in a future update."
            )
            return
        
        # 創建模組實例
        module_instance = factory.create_module(module_name, self.main_window)
        if module_instance is None:
            logger.debug(f"[LIVE_TIMING] Failed to create module: {module_name}")
            return
        
        # 獲取當前 MDI 區域（使用正確的方法）
        current_mdi_area = self.main_window.get_current_mdi_area(auto_create_tab=True)
        if current_mdi_area is None:
            logger.debug(f"[LIVE_TIMING] No MDI area available for module: {module_name}")
            return
        
        # 獲取模組標題
        window_title = module_instance.windowTitle() or module_name
        logger.debug(f"[LIVE_TIMING] Creating PopoutSubWindow with title: {window_title}")
        
        # 使用 PopoutSubWindow 包裝模組（與標準分析模組一致）
        # 注意：Live Timing 模組不需要同步功能（sync_enabled=False）
        sub_window = PopoutSubWindow(
            window_title, 
            current_mdi_area, 
            analysis_module=None,  # Live Timing 模組不是標準分析模組
            sync_enabled=False
        )
        
        # 設置模組 widget 為內容
        sub_window.setWidget(module_instance)
        
        # 設置預設尺寸（使用模組的建議尺寸）
        if hasattr(module_instance, 'minimumSize'):
            min_size = module_instance.minimumSize()
            if min_size.width() > 0 and min_size.height() > 0:
                sub_window.resize(min_size.width() + 50, min_size.height() + 50)
            else:
                sub_window.resize(500, 500)  # 預設尺寸
        else:
            sub_window.resize(500, 500)
        
        # 添加到 MDI 區域
        current_mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        # 自動顯示 Live Timing Control Dock
        self.main_window._on_live_timing_module_opened()
        
        # 連接子視窗關閉信號
        sub_window.destroyed.connect(self.main_window._on_live_timing_module_closed)
        
        logger.debug(f"[LIVE_TIMING] Module opened via factory with PopoutSubWindow: {module_name}")
