# -*- coding: utf-8 -*-
"""
LinkageIntegrator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LinkageIntegrator:
    """從 f1t_gui_main.py 提取的 integrate_linkage_manager 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def integrate_linkage_manager(self):
        """整合新的連動管理器到主程式"""
        try:
            # 將現有的全域信號與新連動管理器連接
            if hasattr(global_signals, 'lap_analysis_master_linkage_changed'):
                global_signals.lap_analysis_master_linkage_changed.connect(
                    linkage_manager.set_master_linkage_enabled
                )
                logger.debug("[LINKAGE_INTEGRATION] ✅ 全域信號已連接到連動管理器")
            
            # 確保主開關狀態同步
            if hasattr(self, 'lap_linkage_action'):
                current_state = self.main_window.lap_linkage_action.isChecked()
                linkage_manager.set_master_linkage_enabled(current_state)
                logger.debug(f"[LINKAGE_INTEGRATION] ✅ 主開關狀態已同步: {'啟用' if current_state else '停用'}")
            
            # 設置連動管理器的信號回調
            linkage_manager.master_linkage_changed.connect(self.main_window.on_linkage_manager_state_changed)
            
            logger.debug("[LINKAGE_INTEGRATION] ✅ 連動管理器整合完成")
            
        except Exception as e:
            logger.error(f"[ERROR] [LINKAGE_INTEGRATION] 連動管理器整合失敗: {e}")
