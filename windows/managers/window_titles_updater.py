# -*- coding: utf-8 -*-
"""
WindowTitlesUpdater - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class WindowTitlesUpdater:
    """從 f1t_gui_main.py 提取的 update_all_window_titles 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def update_all_window_titles(self):
        """更新所有子窗口的標題為新格式"""
        try:
            # 查找所有 MDI 區域
            for child in self.main_window.findChildren(CustomMdiArea):
                if child:
                    # 遍歷所有子窗口
                    for subwindow in child.subWindowList():
                        if isinstance(subwindow, PopoutSubWindow):
                            # 從當前標題提取模組名稱 (簡化提取邏輯)
                            current_title = subwindow.windowTitle()
                            if current_title and '_' in current_title:
                                # 如果已經是新格式，提取模組名稱
                                module_name = current_title.split('_')[0]
                            elif current_title:
                                # 如果是舊格式，直接使用
                                module_name = current_title.replace(' - 分析', '')
                            else:
                                # 如果沒有標題，跳過
                                continue
                            
                            # 生成新標題並更新
                            new_title = self.main_window.format_window_title(module_name)
                            subwindow.setWindowTitle(new_title)
                            
                            # 如果有自定義標題欄，也更新它
                            if hasattr(subwindow, 'title_bar') and subwindow.title_bar:
                                subwindow.title_bar.update_title(new_title)
                            
                            logger.debug(f"[TITLE] 更新子窗口標題: {module_name} -> {new_title}")
        except Exception as e:
            logger.error(f"[ERROR] 更新標題時發生錯誤: {e}")
