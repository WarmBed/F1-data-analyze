#!/usr/bin/env python3
"""
PoleDefenseOpener - 桿位防守統計模組開啟器

從 f1t_gui_main.py 提取的視窗開啟邏輯

作者: F1T Team
日期: 2025-12-22
"""

from PyQt5.QtWidgets import QMdiSubWindow, QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class PoleDefenseOpener:
    """桿位防守統計模組開啟器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def open_pole_defense_module(self):
        """開啟桿位防守統計 MDI 視窗"""
        try:
            logger.info("[POLE_DEFENSE_OPENER] Opening module...")
            
            # 檢查是否為首次使用分析功能
            self.main_window.check_and_remove_welcome_page()
            
            # 獲取當前 MDI 區域
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[POLE_DEFENSE_OPENER] No current tab")
                return
            
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if mdi_area is None:
                logger.error("[POLE_DEFENSE_OPENER] Cannot find MDI area")
                return
            
            # 獲取當前年份
            current_year = self.main_window.get_selected_year()
            
            logger.info(f"[POLE_DEFENSE_OPENER] Year: {current_year}")
            
            # 導入並創建模組
            from modules.gui.multi_season.pole_defense import PoleDefenseAnalysis
            
            # 創建模組實例 (initialization happens in __init__)
            module = PoleDefenseAnalysis(year=current_year)
            
            # Verify module was initialized successfully
            if not hasattr(module, 'main_widget') or module.main_widget is None:
                logger.error("[POLE_DEFENSE_OPENER] Module has no main_widget")
                QMessageBox.critical(
                    self.main_window,
                    tr("error", "Error"),
                    tr("module_init_failed", "Failed to initialize module")
                )
                return
            
            # 創建 MDI 子視窗
            title = f"{tr('pole_defense_statistics', 'Pole Defense Statistics')} - {current_year}"
            sub_window = PopoutSubWindow(title, mdi_area, module)
            sub_window.setWidget(module.get_widget())
            
            # 設置預設大小
            default_size = module.get_default_size()
            sub_window.resize(default_size[0], default_size[1])
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 載入數據
            try:
                if hasattr(module, 'update_lap_parameters'):
                    module.update_lap_parameters(year=str(current_year))
                elif hasattr(module, 'data_manager') and module.data_manager:
                    module.data_manager.load_data(year=current_year)
                logger.info("[POLE_DEFENSE_OPENER] Data load triggered")
            except Exception as e:
                logger.warning(f"[POLE_DEFENSE_OPENER] Data load error: {e}")
            
            # 註冊到分析模組管理器
            try:
                from modules.gui.lap_analysis.analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                module_id = f"pole_defense_{id(module)}"
                manager.register_module(module_id, module, sub_window)
                logger.info(f"[POLE_DEFENSE_OPENER] Registered module: {module_id}")
            except Exception as e:
                logger.warning(f"[POLE_DEFENSE_OPENER] Failed to register module: {e}")
            
            logger.info("[POLE_DEFENSE_OPENER] Module opened successfully")
            
        except Exception as e:
            logger.exception(f"[POLE_DEFENSE_OPENER] Error opening module: {e}")
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                tr("module_open_error", "Failed to open module: {error}").format(error=str(e))
            )
