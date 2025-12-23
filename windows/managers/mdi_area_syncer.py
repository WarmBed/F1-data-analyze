# -*- coding: utf-8 -*-
"""
MdiAreaSyncer - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MdiAreaSyncer:
    """從 f1t_gui_main.py 提取的 sync_to_mdi_area 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def sync_to_mdi_area(self, mdi_area, param_type, value):
        """通知MDI區域內所有子視窗主頁面參數變更"""
        if not mdi_area:
            logger.warning(f"[WARNING] [SYNC] MDI區域為空，跳過通知")
            return 0
            
        notified_count = 0
        subwindow_list = mdi_area.subWindowList()
        logger.debug(f"[TEST] [SYNC] 向MDI區域 {mdi_area.objectName()} 的 {len(subwindow_list)} 個子視窗發送參數變更通知")
        
        for subwindow in subwindow_list:
            window_title = subwindow.windowTitle() if subwindow else "未知視窗"
            logger.debug(f"[TEST] [SYNC] 發送通知到子視窗: {window_title} ({param_type}={value})")
            
            # 總是發送通知，讓子視窗自己決定是否響應
            if hasattr(subwindow, 'receive_main_window_update_notification'):
                try:
                    subwindow.receive_main_window_update_notification(param_type, value)
                    notified_count += 1
                    logger.debug(f"[OK] [SYNC] 已發送通知到: {window_title}")
                except Exception as e:
                    logger.error(f"[ERROR] [SYNC] 發送通知失敗: {window_title}, 錯誤: {e}")
            else:
                logger.warning(f"[WARNING] [SYNC] 子視窗 {window_title} 不支援通知機制")
        
        logger.debug(f"[STATS] [SYNC] MDI區域 {mdi_area.objectName()} 通知完成，共發送 {notified_count} 個通知")
        return notified_count
    
    # ==================== 同步功能實現結束 ====================
