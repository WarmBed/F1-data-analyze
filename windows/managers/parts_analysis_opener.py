# -*- coding: utf-8 -*-
"""
PartsAnalysisOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class PartsAnalysisOpener:
    """從 f1t_gui_main.py 提取的 open_parts_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_parts_analysis(self):
        """Open FIA Parts Analysis MDI window"""
        try:
            from modules.gui.partupdated_analysis import PartsAnalysisMDI
            
            # Get current year from year combo
            current_year = self.main_window.year_combo.currentText() if hasattr(self, 'year_combo') else "2025"
            
            # Create MDI window
            parts_mdi = PartsAnalysisMDI(year=current_year)
            parts_sub = QMdiSubWindow()
            parts_sub.setWidget(parts_mdi)
            parts_sub.setWindowTitle(tr('menu_parts_analysis', 'Vehicle Parts Changes'))
            parts_sub.resize(1200, 700)  # 較大視窗以容納 10 欄位表格
            
            # Add to MDI area
            if hasattr(self, 'mdi_area'):
                self.main_window.mdi_area.addSubWindow(parts_sub)
                parts_sub.show()
                logger.debug(f"[MENU] Opened FIA Parts Analysis (year={current_year})")
        except Exception as e:
            logger.debug(f"[MENU] Failed to open FIA Parts Analysis: {e}")
            import traceback
            traceback.print_exc()
