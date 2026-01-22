#!/usr/bin/env python3
"""
FiaSeasonStatsOpener - FIA 賽季統計模組開啟器

從 f1t_gui_main.py 提取的視窗開啟邏輯

作者: F1T Team
日期: 2026-01-22
"""

from PyQt5.QtWidgets import QMdiSubWindow, QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class FiaSeasonStatsOpener:
    """FIA 賽季統計模組開啟器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def open_fia_season_stats_module(self):
        """開啟 FIA 賽季統計 MDI 視窗"""
        try:
            logger.info("[FIA_STATS_OPENER] Opening module...")
            
            # 檢查是否為首次使用分析功能
            self.main_window.check_and_remove_welcome_page()
            
            # 獲取當前 MDI 區域
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[FIA_STATS_OPENER] No current tab")
                return
            
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if mdi_area is None:
                logger.error("[FIA_STATS_OPENER] Cannot find MDI area")
                return
            
            # 獲取當前年份
            current_year = self.main_window.get_selected_year()
            
            logger.info(f"[FIA_STATS_OPENER] Year: {current_year}")
            
            # 導入並創建模組
            from modules.gui.multi_season.fia_season_stats import FiaSeasonStatsAnalysis
            
            # 創建模組實例
            module = FiaSeasonStatsAnalysis(year=current_year)
            
            # 驗證模組是否初始化成功
            if not hasattr(module, 'main_widget') or module.main_widget is None:
                logger.error("[FIA_STATS_OPENER] Module has no main_widget")
                QMessageBox.critical(
                    self.main_window,
                    tr("error", "Error"),
                    tr("module_init_failed", "Failed to initialize module")
                )
                return
            
            # 創建 MDI 子視窗
            title = f"{tr('fia_season_stats', 'FIA Season Statistics')} - {current_year}"
            sub_window = PopoutSubWindow(title, mdi_area, module)
            sub_window.setWidget(module.get_widget())
            
            # 設置預設大小
            default_size = module.get_default_size()
            sub_window.resize(default_size[0], default_size[1])
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 觸發數據載入
            module.update_lap_parameters(year=str(current_year))
            
            logger.info("[FIA_STATS_OPENER] Module opened successfully")
            
        except ImportError as e:
            logger.exception(f"[FIA_STATS_OPENER] Import error: {e}")
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                tr("module_import_failed", f"Failed to import module: {e}")
            )
        except Exception as e:
            logger.exception(f"[FIA_STATS_OPENER] Error opening module: {e}")
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                tr("module_open_failed", f"Failed to open module: {e}")
            )
