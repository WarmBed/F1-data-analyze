# -*- coding: utf-8 -*-
"""
AboutDialogShower - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


class AboutDialogShower:
    """從 f1t_gui_main.py 提取的 show_about_dialog 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def show_about_dialog(self):
        """顯示關於對話框"""
        about_message = tr(
            'about_message',
            (
                "F1 TelemetryStation Pro\n"
                "版本：0.0 (API-ONLY 模式)\n\n"
                "本系統整合 FastF1 與 OpenF1 API，提供專業賽車遙測分析。\n"
                "GUI 模組僅透過 REST API 或既有 JSON 讀取資料，遵守 2025-10-03 API-ONLY 政策。\n\n"
                "專案維護：Telemetry Station 核心團隊\n"
                "GitHub：WarmBed / F1-data-analyze"
            ),
        )
        QMessageBox.information(self.main_window, tr('about_action', '關於 PITWALL'), about_message)
    
    # ===========================================
    # F1TV Authentication Methods
    # ===========================================
