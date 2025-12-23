# -*- coding: utf-8 -*-
"""
SeasonProgressOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class SeasonProgressOpener:
    """從 f1t_gui_main.py 提取的 open_season_progress 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_season_progress(self):
        """Open Season Progress MDI window"""
        try:
            from modules.gui.season_progress import SeasonProgressMDI
            
            # Get current year from year combo
            current_year = self.main_window.year_combo.currentText() if hasattr(self.main_window, 'year_combo') else "2024"
            
            # Create MDI window
            progress_mdi = SeasonProgressMDI(year=current_year)
            progress_sub = QMdiSubWindow()
            progress_sub.setWidget(progress_mdi)
            progress_sub.setWindowTitle(tr('season_progress_title', 'Season Progress - {year}').format(year=current_year))
            progress_sub.resize(800, 500)
            
            # Add to MDI area
            if hasattr(self, 'mdi_area'):
                self.main_window.mdi_area.addSubWindow(progress_sub)
                progress_sub.show()
                logger.debug(f"[MENU] Opened Season Progress (year={current_year})")
        except Exception as e:
            logger.debug(f"[MENU] Failed to open Season Progress: {e}")
            import traceback
            traceback.print_exc()
