# -*- coding: utf-8 -*-
"""
TabMdiCloser - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

logger = get_logger(__name__)


class TabMdiCloser:
    """從 f1t_gui_main.py 提取的 close_all_mdi_windows_in_current_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def close_all_mdi_windows_in_current_tab(self, *args, **kwargs):
        """關閉當前分頁的所有 MDI 視窗（全局工具列按鈕）"""
        try:
            logger.debug(f"[CLOSE_ALL_DEBUG] ===== 開始關閉所有視窗 =====")
            
            current_mdi_area = self.main_window.get_current_mdi_area()
            if not current_mdi_area:
                logger.debug("[GLOBAL_TOOLBAR] ⚠️  當前分頁沒有 MDI 區域")
                logger.debug(f"[CLOSE_ALL_DEBUG] ================================")
                return
            
            logger.debug(f"[CLOSE_ALL_DEBUG] 找到 MDI 區域: {current_mdi_area.objectName()}")
            
            # 獲取所有子視窗
            all_subwindows = current_mdi_area.subWindowList()
            logger.debug(f"[CLOSE_ALL_DEBUG] MDI 區域有 {len(all_subwindows)} 個子視窗")
            
            for i, sw in enumerate(all_subwindows):
                logger.debug(f"[CLOSE_ALL_DEBUG]   子視窗 {i}: {sw.windowTitle()}, 可見={sw.isVisible()}")
            
            # 關閉所有子視窗
            logger.debug(f"[CLOSE_ALL_DEBUG] 調用 closeAllSubWindows()...")
            current_mdi_area.closeAllSubWindows()
            
            # 驗證關閉結果
            remaining = current_mdi_area.subWindowList()
            logger.debug(f"[CLOSE_ALL_DEBUG] 關閉後剩餘 {len(remaining)} 個子視窗")
            logger.debug("[GLOBAL_TOOLBAR] ✅ 已關閉當前分頁的所有 MDI 視窗")
            logger.debug(f"[CLOSE_ALL_DEBUG] ================================")
            
        except Exception as e:
            logger.debug(f"[GLOBAL_TOOLBAR] ❌ 關閉 MDI 視窗失敗: {e}")
            import traceback
            traceback.print_exc()
