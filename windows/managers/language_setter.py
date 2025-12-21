# -*- coding: utf-8 -*-
"""
LanguageSetter - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from core.gui_i18n import set_gui_language

logger = get_logger(__name__)


class LanguageSetter:
    """從 f1t_gui_main.py 提取的 set_interface_language 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def set_interface_language(self, language):
        """設定介面語言"""
        try:
            # 設定語言
            set_gui_language(language)
            
            # 更新選單狀態
            if language == 'en':
                self.main_window.english_action.setChecked(True)
                self.main_window.chinese_action.setChecked(False)
                self.main_window.japanese_action.setChecked(False)
                message = "Interface language switched to English. Please restart the application for full effect."
            elif language == 'ja':
                self.main_window.english_action.setChecked(False)
                self.main_window.chinese_action.setChecked(False)
                self.main_window.japanese_action.setChecked(True)
                message = "インターフェース言語が日本語に切り替わりました。完全に有効にするには、アプリケーションを再起動してください。"
            else:
                self.main_window.english_action.setChecked(False)
                self.main_window.chinese_action.setChecked(True)
                self.main_window.japanese_action.setChecked(False)
                message = "介面語言已切換為中文。請重新啟動應用程式以獲得完整效果。"
            
            # 更新功能表文字
            self.main_window.refresh_menu_text()
            
            # 顯示提示訊息
            QMessageBox.information(self.main_window, "Language / 語言 / 言語", message)
            
            logger.debug(f"[LANGUAGE] 介面語言已切換為: {language}")
            
        except Exception as e:
            logger.error(f"[ERROR] 語言切換失敗: {e}")
