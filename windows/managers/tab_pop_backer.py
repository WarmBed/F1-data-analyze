# -*- coding: utf-8 -*-
"""
TabPopBacker - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class TabPopBacker:
    """從 f1t_gui_main.py 提取的 pop_back_in_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def pop_back_in_tab(self, tab_index):
        """將彈出的分頁返回主視窗"""
        try:
            # ✅ 修復：檢查分頁是否已彈出（避免重複調用導致 KeyError）
            if tab_index not in self.main_window.popped_out_tabs:
                logger.debug(f"[TAB_POPOUT] {tr('tab_not_popped').format(index=tab_index)}")
                return
            
            logger.debug(f"[TAB_POPOUT] {tr('tab_starting_return').format(index=tab_index)}")
            
            # 獲取彈出信息
            popout_info = self.main_window.popped_out_tabs[tab_index]
            standalone_window = popout_info['standalone_window']
            mdi_area = popout_info['original_widget']
            placeholder = popout_info['placeholder']
            tab_name = popout_info['tab_name']
            
            logger.debug(f"[TAB_POPOUT] 📊 返回時 MDI 子視窗數量: {len(mdi_area.subWindowList())}")
            
            # ✅ 關鍵修復：先從字典移除（避免 closeEvent 重複調用）
            del self.main_window.popped_out_tabs[tab_index]
            logger.debug(f"[TAB_POPOUT] 🗑️ 已從追蹤字典移除分頁 {tab_index}")
            
            # ✅ 關鍵修復：從獨立視窗取出 MDI 區域（避免關閉時刪除）
            standalone_window.takeCentralWidget()
            
            # ✅ 關鍵修復：移除佔位符，恢復 MDI 工作區
            self.main_window.tab_widget.removeTab(tab_index)
            self.main_window.tab_widget.insertTab(tab_index, mdi_area, tab_name)
            self.main_window.tab_widget.setCurrentIndex(tab_index)
            
            # 清理佔位符
            placeholder.deleteLater()
            
            # 恢復分頁標籤正常樣式
            self.main_window._update_tab_appearance(tab_index, is_popped_out=False)
            
            # 關閉獨立視窗（不會刪除 MDI 區域，因為已經 takeCentralWidget）
            standalone_window.close()
            
            logger.debug(f"[TAB_POPOUT] {tr('tab_return_success').format(index=tab_index)}")
            logger.debug(f"[TAB_POPOUT] Current popped out tabs: {len(self.main_window.popped_out_tabs)}")
            
        except KeyError:
            # ✅ 修復：KeyError 表示分頁已返回，這是正常情況（closeEvent 重複調用）
            logger.debug(f"[TAB_POPOUT] Tab {tab_index} already returned (skip duplicate return)")
        except Exception as e:
            # 其他真正的錯誤
            logger.debug(f"[TAB_POPOUT] Return failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
