# -*- coding: utf-8 -*-
"""
DriverStandingsOpener - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMdiSubWindow
from core.gui_i18n import tr
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class DriverStandingsOpener:
    """從 f1t_gui_main.py 提取的 open_driver_standings 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def open_driver_standings(self):
        """Open Driver Standings MDI window"""
        try:
            from modules.gui.driver_standings import DriverStandingsMDI
            
            # Get current year from year combo
            current_year = self.main_window.year_combo.currentText() if hasattr(self.main_window, 'year_combo') else "2024"
            
            # Create MDI window
            driver_mdi = DriverStandingsMDI(year=current_year)
            driver_sub = QMdiSubWindow()
            driver_sub.setWidget(driver_mdi)
            driver_sub.setWindowTitle(tr('menu_driver_standings', 'Driver Standings'))
            driver_sub.resize(900, 600)
            
            # Add to MDI area
            if hasattr(self, 'mdi_area'):
                self.main_window.mdi_area.addSubWindow(driver_sub)
                driver_sub.show()
                logger.debug(f"[MENU] Opened Driver Standings (year={current_year})")
        except Exception as e:
            logger.debug(f"[MENU] Failed to open Driver Standings: {e}")
            import traceback
            traceback.print_exc()
