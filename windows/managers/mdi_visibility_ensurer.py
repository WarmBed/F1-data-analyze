# -*- coding: utf-8 -*-
"""
MdiVisibilityEnsurer - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class MdiVisibilityEnsurer:
    """從 f1t_gui_main.py 提取的 _ensure_mdi_visible 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _ensure_mdi_visible(self, mdi_area):
        """確保 MDI 區域可見（延遲檢查）"""
        try:
            if not mdi_area:
                return
            
            # 檢查 MDI 區域的可見性
            is_visible = mdi_area.isVisible()
            geometry = mdi_area.geometry()
            sub_count = len(mdi_area.subWindowList())
            
            logger.debug(f"[TAB_POPOUT] 🔍 MDI 可見性檢查:")
            logger.debug(f"[TAB_POPOUT]   - 可見: {is_visible}")
            logger.debug(f"[TAB_POPOUT]   - 幾何: {geometry.width()}x{geometry.height()}")
            logger.debug(f"[TAB_POPOUT]   - 子視窗: {sub_count}")
            
            # 如果不可見或大小為 0，強制顯示
            if not is_visible or geometry.width() == 0 or geometry.height() == 0:
                logger.debug(f"[TAB_POPOUT] ⚠️ MDI 區域異常，嘗試修復...")
                mdi_area.setVisible(True)
                mdi_area.show()
                mdi_area.update()
                
                # 強制設置合理的大小
                if geometry.width() == 0 or geometry.height() == 0:
                    mdi_area.resize(800, 600)
                    logger.debug(f"[TAB_POPOUT] 🔧 已設置 MDI 區域大小為 800x600")
            
            # 確保所有子視窗可見
            for sub_win in mdi_area.subWindowList():
                if not sub_win.isVisible():
                    logger.debug(f"[TAB_POPOUT] 🔧 顯示隱藏的子視窗: {sub_win.windowTitle()}")
                    sub_win.setVisible(True)
                    sub_win.show()
                    
        except Exception as e:
            logger.debug(f"[TAB_POPOUT] ❌ MDI 可見性檢查失敗: {e}")
    
    # ==================== 分頁彈出功能結束 ====================
