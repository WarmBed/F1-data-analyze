# -*- coding: utf-8 -*-
"""
CurrentMdiGetter - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QWidget
from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class CurrentMdiGetter:
    """從 f1t_gui_main.py 提取的 get_current_mdi_area 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_current_mdi_area(self, auto_create_tab=False):
        """
        獲取當前分頁的 MDI 區域
        
        Args:
            auto_create_tab: 是否在主頁時自動創建分頁一（默認 False）
                            只有在用戶主動操作（如點擊模組）時才應設為 True
        """
        try:
            # 獲取當前分頁
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[ERROR] 無法獲取當前分頁")
                return None
            
            # [深度調試] 輸出當前分頁資訊
            current_index = self.main_window.tab_widget.currentIndex()
            logger.debug(f"[MDI_AREA_DEBUG] ===== 查找 MDI 區域 =====")
            logger.debug(f"[MDI_AREA_DEBUG] 當前分頁索引: {current_index}")
            logger.debug(f"[MDI_AREA_DEBUG] 當前分頁 ObjectName: {current_tab.objectName()}")
            logger.debug(f"[MDI_AREA_DEBUG] 當前分頁類型: {type(current_tab).__name__}")
            
            # 檢查是否為主頁（歡迎頁）
            is_welcome_tab = (current_index == 0 and current_tab.objectName() == "welcome_tab")
            logger.debug(f"[MDI_AREA_DEBUG] 是否為歡迎頁: {is_welcome_tab}")
            
            # ✅ 只有明確要求時才自動創建分頁（避免初始化時誤觸發）
            if is_welcome_tab and auto_create_tab:
                logger.debug("[TAB] 💡 檢測到在主頁，自動創建 '分頁一' 避免 toolbar 衝突")
                self.main_window.add_new_tab()  # 創建 "分頁一"
                # 重新獲取當前分頁（已切換到新分頁）
                current_tab = self.main_window.tab_widget.currentWidget()
            elif is_welcome_tab:
                # 主頁沒有 MDI 區域，直接返回 None
                logger.debug("[TAB] 💡 當前在主頁，無 MDI 區域（未自動創建分頁）")
                return None
            
            # [深度調試] 首先檢查 current_tab 本身是否就是 CustomMdiArea
            logger.debug(f"[MDI_AREA_DEBUG] 檢查 current_tab 是否為 CustomMdiArea: {isinstance(current_tab, CustomMdiArea)}")
            logger.debug(f"[MDI_AREA_DEBUG] current_tab 類別物件 ID: {id(type(current_tab))}")
            logger.debug(f"[MDI_AREA_DEBUG] CustomMdiArea 類別 ID: {id(CustomMdiArea)}")
            logger.debug(f"[MDI_AREA_DEBUG] 兩者是否相同類別: {type(current_tab) is CustomMdiArea}")
            
            if isinstance(current_tab, CustomMdiArea):
                logger.debug(f"[MDI_AREA_DEBUG] ✅ current_tab 本身就是 CustomMdiArea！")
                logger.debug(f"[MDI_AREA_DEBUG] MDI ObjectName: {current_tab.objectName()}")
                logger.debug(f"[MDI_AREA_DEBUG] MDI 子視窗數量: {len(current_tab.subWindowList())}")
                logger.debug(f"[MDI_AREA_DEBUG] ================================")
                return current_tab
            
            # 在當前分頁中查找 CustomMdiArea
            def find_mdi_area(widget):
                if isinstance(widget, CustomMdiArea):
                    return widget
                
                # 遞歸查找子元件
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            result = find_mdi_area(child)
                            if result:
                                return result
                return None
            
            logger.debug(f"[MDI_AREA_DEBUG] current_tab 不是 CustomMdiArea，開始遞歸查找...")
            mdi_area = find_mdi_area(current_tab)
            
            if not mdi_area:
                logger.debug(f"[MDI_AREA_DEBUG] ❌ 遞歸查找失敗")
                logger.error(f"[ERROR] 在當前分頁中未找到 MDI 區域: {current_tab.objectName()}")
                logger.debug(f"[MDI_AREA_DEBUG] ================================")
                return None
            
            logger.debug(f"[MDI_AREA_DEBUG] ✅ 遞歸查找成功")
            logger.debug(f"[MDI_AREA_DEBUG] MDI ObjectName: {mdi_area.objectName()}")
            logger.debug(f"[MDI_AREA_DEBUG] MDI 子視窗數量: {len(mdi_area.subWindowList())}")
            logger.debug(f"[OK] 找到當前 MDI 區域: {mdi_area.objectName()}")
            logger.debug(f"[MDI_AREA_DEBUG] ================================")
            return mdi_area
            
        except Exception as e:
            logger.error(f"[ERROR] 獲取當前 MDI 區域失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
