#!/usr/bin/env python3
"""
PitLossTableOpener - 進站時間損失表模組開啟器

從各賽道載入並顯示進站時間損失數據

作者: F1T Team
日期: 2025-10-13
"""

from PyQt5.QtWidgets import QMdiSubWindow, QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class PitLossTableOpener:
    """進站時間損失表模組開啟器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def open_pit_loss_table_module(self):
        """開啟進站時間損失表 MDI 視窗"""
        try:
            logger.info("[PIT_LOSS_TABLE_OPENER] Opening module...")
            
            # 檢查是否為首次使用分析功能
            self.main_window.check_and_remove_welcome_page()
            
            # 獲取當前 MDI 區域
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[PIT_LOSS_TABLE_OPENER] No current tab")
                return
            
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if mdi_area is None:
                logger.error("[PIT_LOSS_TABLE_OPENER] Cannot find MDI area")
                return
            
            logger.info("[PIT_LOSS_TABLE_OPENER] Importing module...")
            
            # 導入並創建模組
            from modules.gui.multi_season.pit_loss_table import PitLossTableMDI
            
            # 創建模組實例
            module = PitLossTableMDI()
            
            # 驗證模組初始化成功
            if module.get_widget() is None:
                logger.error("[PIT_LOSS_TABLE_OPENER] Module widget is None")
                QMessageBox.critical(
                    self.main_window,
                    tr("error", "Error"),
                    tr("module_init_failed", "Failed to initialize module")
                )
                return
            
            # 創建 MDI 子視窗
            title = module.get_window_title()
            sub_window = PopoutSubWindow(title, mdi_area, module)
            sub_window.setWidget(module.get_widget())
            
            # 設置預設大小
            default_size = module.get_default_size()
            sub_window.resize(default_size[0], default_size[1])
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 註冊到分析模組管理器
            try:
                from modules.gui.lap_analysis.analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                module_id = f"pit_loss_table_{id(module)}"
                manager.register_module(module_id, module, sub_window)
                logger.info(f"[PIT_LOSS_TABLE_OPENER] Registered module: {module_id}")
            except Exception as e:
                logger.warning(f"[PIT_LOSS_TABLE_OPENER] Failed to register module: {e}")
            
            logger.info("[PIT_LOSS_TABLE_OPENER] Module opened successfully")
            
        except Exception as e:
            logger.exception(f"[PIT_LOSS_TABLE_OPENER] Error opening module: {e}")
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                tr("module_open_error", "Failed to open module: {error}").format(error=str(e))
            )
