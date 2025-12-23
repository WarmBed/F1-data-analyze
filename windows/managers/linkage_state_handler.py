# -*- coding: utf-8 -*-
"""
LinkageStateHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LinkageStateHandler:
    """從 f1t_gui_main.py 提取的 on_linkage_manager_state_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_linkage_manager_state_changed(self, enabled: bool):
        """處理連動管理器狀態變更"""
        try:
            # 更新主視窗的連動按鈕狀態
            if hasattr(self, 'lap_linkage_action'):
                self.main_window.lap_linkage_action.setChecked(enabled)
            
            # 獲取連動管理器統計
            stats = linkage_manager.get_module_stats()
            logger.debug(f"[LINKAGE_MANAGER] 狀態更新: {'啟用' if enabled else '停用'}")
            logger.debug(f"[LINKAGE_MANAGER] 已註冊模組: {stats['total_modules']} 個")
            logger.debug(f"[LINKAGE_MANAGER] 模組類型: {stats['module_types']}")
            
        except Exception as e:
            logger.error(f"[ERROR] [LINKAGE_MANAGER] 狀態變更處理失敗: {e}")
