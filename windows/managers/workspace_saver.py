# -*- coding: utf-8 -*-
"""
WorkspaceSaver - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from typing import Optional

from core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceSaver:
    """從 f1t_gui_main.py 提取的 save_workspace 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def save_workspace(self, *, default_path: Optional[str] = None):
        """儲存目前的工作區設定（使用 Workspace Manager）"""
        try:
            from windows.save_workspace_dialog import SaveWorkspaceDialog
            
            # 創建並顯示儲存對話框
            dialog = SaveWorkspaceDialog(
                workspace_serializer=self.main_window.workspace_serializer,
                workspace_database=self.main_window.workspace_db,
                parent=self
            )
            
            # 連接信號（如果需要額外處理）
            dialog.workspace_saved.connect(self.main_window._on_workspace_saved)
            
            # 顯示對話框
            dialog.exec_()
            
        except Exception as e:
            logger.exception("Failed to open save workspace dialog", exc_info=e)
            QMessageBox.critical(
                self,
                tr('save_workspace_error', '儲存工作區失敗'),
                f"{tr('error_details', '詳細資訊')}: {e}"
            )
