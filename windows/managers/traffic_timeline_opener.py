#!/usr/bin/env python3
"""
TrafficTimelineOpener - Traffic Timeline 模組開啟器

從樹狀圖開啟 Traffic Timeline 視覺化 MDI 視窗

Author: F1T Team
Date: 2025-12-23
"""

from PyQt5.QtWidgets import QMdiSubWindow, QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class TrafficTimelineOpener:
    """Traffic Timeline 模組開啟器"""
    
    def __init__(self, main_window):
        self.main_window = main_window
    
    def open_traffic_timeline_module(self):
        """開啟 Traffic Timeline MDI 視窗"""
        try:
            logger.info("[TRAFFIC_TIMELINE_OPENER] Opening module...")
            
            # 檢查是否為首次使用分析功能
            self.main_window.check_and_remove_welcome_page()
            
            # 獲取當前 MDI 區域
            current_tab = self.main_window.tab_widget.currentWidget()
            if not current_tab:
                logger.error("[TRAFFIC_TIMELINE_OPENER] No current tab")
                return
            
            mdi_area = None
            if isinstance(current_tab, CustomMdiArea):
                mdi_area = current_tab
            else:
                for child in current_tab.findChildren(CustomMdiArea):
                    mdi_area = child
                    break
            
            if mdi_area is None:
                logger.error("[TRAFFIC_TIMELINE_OPENER] Cannot find MDI area")
                return
            
            # 獲取當前參數 (使用正確的方法名稱)
            current_year = self.main_window.get_selected_year()
            current_race = self.main_window.get_selected_race_key()
            current_session = self.main_window.get_selected_session_code()
            
            logger.info(f"[TRAFFIC_TIMELINE_OPENER] Year: {current_year}, Race: {current_race}, Session: {current_session}")
            
            # 導入並創建模組
            from modules.gui.lap_analysis.traffic_timeline_analysis import TrafficTimelineAnalysis
            
            # 創建模組實例
            module = TrafficTimelineAnalysis(
                year=current_year,
                race=current_race,
                session=current_session,
            )
            
            # 驗證模組初始化成功
            if not hasattr(module, 'main_widget') or module.main_widget is None:
                logger.error("[TRAFFIC_TIMELINE_OPENER] Module has no main_widget")
                QMessageBox.critical(
                    self.main_window,
                    tr("error", "Error"),
                    tr("module_init_failed", "Failed to initialize module")
                )
                return
            
            # 創建 MDI 子視窗
            title = f"{tr('traffic_timeline', 'Traffic Timeline')} - {current_year} {current_race} {current_session}"
            sub_window = PopoutSubWindow(title, mdi_area, module)
            sub_window.setWidget(module.get_widget())
            
            # 設置預設大小
            default_size = module.get_default_size()
            sub_window.resize(default_size[0], default_size[1])
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 載入數據 (與 Season Start Reaction 一致的模式)
            try:
                if hasattr(module, 'update_lap_parameters'):
                    module.update_lap_parameters(
                        year=str(current_year),
                        race=current_race,
                        session=current_session,
                    )
                elif hasattr(module, 'data_manager') and module.data_manager:
                    module.data_manager.load_data(
                        year=current_year,
                        race=current_race,
                        session=current_session,
                    )
                logger.info("[TRAFFIC_TIMELINE_OPENER] Data load triggered")
            except Exception as e:
                logger.warning(f"[TRAFFIC_TIMELINE_OPENER] Data load error: {e}")
            
            # 註冊到分析模組管理器 (與 Season Start Reaction 一致的模式)
            try:
                from modules.gui.lap_analysis.analysis_module_manager import get_analysis_module_manager
                manager = get_analysis_module_manager()
                module_id = f"traffic_timeline_{id(module)}"
                manager.register_module(module_id, module, "traffic_timeline")
                logger.debug(f"[TRAFFIC_TIMELINE_OPENER] Registered module: {module_id}")
            except Exception as e:
                logger.warning(f"[TRAFFIC_TIMELINE_OPENER] Failed to register to manager: {e}")
            
            # ✅ 註冊到 lap_analysis_windows 以支援參數同步
            # 這確保當主視窗 Year/Race/Session 變更時，此模組會自動更新
            try:
                self.main_window.on_lap_analysis_window_opened(module, "traffic_timeline")
                logger.info("[TRAFFIC_TIMELINE_OPENER] Registered to lap_analysis_windows for sync")
            except Exception as e:
                logger.warning(f"[TRAFFIC_TIMELINE_OPENER] Failed to register for sync: {e}")
            
            logger.info("[TRAFFIC_TIMELINE_OPENER] Module opened successfully")
            
        except ImportError as e:
            logger.error(f"[TRAFFIC_TIMELINE_OPENER] Import error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                f"{tr('module_import_failed', 'Failed to import module')}: {e}"
            )
        except Exception as e:
            logger.error(f"[TRAFFIC_TIMELINE_OPENER] Error: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self.main_window,
                tr("error", "Error"),
                f"{tr('module_open_failed', 'Failed to open module')}: {e}"
            )
