# -*- coding: utf-8 -*-
"""
PaletteErrorShower - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger

logger = get_logger(__name__)


class PaletteErrorShower:
    """從 f1t_gui_main.py 提取的 _show_palette_error_message 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _show_palette_error_message(self, message: str) -> None:
        try:
            QMessageBox.warning(self.main_window, "Color Palette Error", message)
        except Exception:
            logger.debug(f"[INIT] ⚠️ 顏色錯誤提示失敗: {message}")
