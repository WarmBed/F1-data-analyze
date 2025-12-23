# -*- coding: utf-8 -*-
"""
WorkspaceLoader - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceLoader:
    """從 f1t_gui_main.py 提取的 load_workspace 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def load_workspace(self, *, source_path: Optional[str] = None):
        """載入工作區設定（使用 Workspace Manager）"""
        try:
            from windows.load_workspace_dialog import LoadWorkspaceDialog
            
            # 創建並顯示載入對話框
            dialog = LoadWorkspaceDialog(
                workspace_database=self.main_window.workspace_db,
                parent=self.main_window
            )
            
            # 連接信號
            dialog.workspace_selected.connect(self.main_window._on_workspace_loaded)
            
            # 顯示對話框
            dialog.exec_()
            
        except Exception as e:
            logger.exception("Failed to open load workspace dialog", exc_info=e)
            QMessageBox.critical(
                self.main_window,
                tr('load_workspace_error', '載入工作區失敗'),
                f"{tr('error_details', '詳細資訊')}: {e}"
            )
