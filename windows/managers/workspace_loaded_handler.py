# -*- coding: utf-8 -*-
"""
WorkspaceLoadedHandler - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from typing import Dict

from core.logger import get_logger

logger = get_logger(__name__)


class WorkspaceLoadedHandler:
    """從 f1t_gui_main.py 提取的 _on_workspace_loaded 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _on_workspace_loaded(self, workspace_id: int, config: Dict):
        """Workspace 載入的回調 - 重建所有分頁和視窗"""
        logger.debug(f"[WORKSPACE] 🔄 開始載入 Workspace: ID={workspace_id}")
        
        try:
            # 調用 deserialize_workspace 重建 GUI 狀態
            success = self.main_window.workspace_serializer.deserialize_workspace(config)
            
            if success:
                total_tabs = len(config.get('tabs', []))
                total_windows = sum(len(tab.get('mdi_windows', [])) for tab in config.get('tabs', []))
                
                # ✅ 不再自動平鋪，保持保存時的視窗位置
                # 原本：QTimer.singleShot(500, self.main_window._tile_all_workspace_windows_delayed)
                logger.debug(f"[WORKSPACE] ✅ 保持保存時的視窗位置（不自動平鋪）")
                
                # ✅ 更新所有分頁的滾動範圍（確保超出範圍的視窗可透過滾動條訪問）
                QTimer.singleShot(300, self.main_window._update_all_mdi_scroll_areas)
                
                QMessageBox.information(
                    self.main_window,
                    tr('workspace_load_success_title'),
                    tr('workspace_load_success_message').format(
                        tabs=total_tabs,
                        windows=total_windows
                    )
                )
            else:
                QMessageBox.warning(
                    self.main_window,
                    tr('workspace_load_failed_title'),
                    tr('workspace_load_failed_message')
                )
            
        except Exception as e:
            logger.exception("Failed to load workspace", exc_info=e)
            QMessageBox.critical(
                self.main_window,
                tr('workspace_load_error_title'),
                tr('workspace_load_error_message').format(error=str(e))
            )
