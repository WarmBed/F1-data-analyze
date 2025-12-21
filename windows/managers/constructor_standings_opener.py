# -*- coding: utf-8 -*-
"""
ConstructorStandingsOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ConstructorStandingsOpener:
    """從 f1t_gui_main.py 提取的 open_constructor_standings 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_constructor_standings(self):
        """Open Constructor Standings MDI window"""
        try:
            from modules.gui.constructor_standings import ConstructorStandingsMDI
            
            # Get current year from year combo
            current_year = self.main_window.year_combo.currentText() if hasattr(self.main_window, 'year_combo') else "2024"
            
            # Create MDI window
            constructor_mdi = ConstructorStandingsMDI(year=current_year)
            constructor_sub = QMdiSubWindow()
            constructor_sub.setWidget(constructor_mdi)
            constructor_sub.setWindowTitle(tr('menu_constructor_standings', 'Constructor Standings'))
            constructor_sub.resize(700, 400)
            
            # Add to MDI area
            if hasattr(self, 'mdi_area'):
                self.main_window.mdi_area.addSubWindow(constructor_sub)
                constructor_sub.show()
                logger.debug(f"[MENU] Opened Constructor Standings (year={current_year})")
        except Exception as e:
            logger.debug(f"[MENU] Failed to open Constructor Standings: {e}")
            import traceback
            traceback.print_exc()
