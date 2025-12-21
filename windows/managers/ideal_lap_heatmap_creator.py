# -*- coding: utf-8 -*-
"""
IdealLapHeatmapCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from functools import partial
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class IdealLapHeatmapCreator:
    """從 f1t_gui_main.py 提取的 _create_ideal_lap_heatmap_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_ideal_lap_heatmap_window(self, mdi_area, year, race, session):
        """建立理想圈分段熱力圖視窗"""
        try:
            logger.debug(f"[IDEAL_LAP_HEATMAP] 🚀 啟動理想圈分段熱力圖模組...")
            from modules.gui.lap_analysis.ideal_lap.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_module import IdealLapSectorHeatmapModule
            logger.debug(f"[IDEAL_LAP_HEATMAP] ✅ 模組導入成功")
        except ImportError as exc:
            message = f"無法載入理想圈分段熱力圖模組: {exc}"
            logger.debug(f"[IDEAL_LAP_HEATMAP] ❌ {message}")
            QMessageBox.critical(self.main_window, "模組載入失敗", message)
            import traceback
            traceback.print_exc()
            return None

        try:
            module = IdealLapSectorHeatmapModule(parent=self.main_window, year=year, race=race, session=session)
            logger.debug(f"[IDEAL_LAP_HEATMAP] 🔧 創建模組實例...")

            if not module.initialize_module(parent_widget=self.main_window):
                raise RuntimeError("Module initialization failed")
            logger.debug(f"[IDEAL_LAP_HEATMAP] ✅ 模組初始化完成")

            get_title = getattr(module, "get_title", None)
            if callable(get_title):
                window_title = get_title()
            else:
                window_title = module.get_window_title(int(year), race, session)
            logger.debug(f"[IDEAL_LAP_HEATMAP] 📛 視窗標題: {window_title}")

            sub_window = PopoutSubWindow(window_title, mdi_area, module)
            sub_window.setWidget(module.get_widget())

            if hasattr(module, "set_parent_window"):
                module.set_parent_window(sub_window)

            if hasattr(module, "get_default_size"):
                width, height = module.get_default_size()
                sub_window.resize(width, height)
                logger.debug(f"[IDEAL_LAP_HEATMAP] 📐 視窗尺寸: {width}x{height}")

            mdi_area.addSubWindow(sub_window)
            logger.debug(f"[IDEAL_LAP_HEATMAP] ✅ 已加入 MDI")

            if hasattr(sub_window, 'window_closed'):
                # 🔴 使用 partial 避免 lambda 閉包洩漏

                sub_window.window_closed.connect(

                    partial(self.main_window.on_subwindow_closed, sub_window)

                )
            if hasattr(self, 'active_subwindows'):
                self.main_window.active_subwindows.append(sub_window)

            sub_window.show()
            self.main_window._position_subwindow(mdi_area, sub_window)

            module.load_data()
            logger.debug(f"[IDEAL_LAP_HEATMAP] 📊 資料載入觸發完成")
            return sub_window

        except Exception as exc:
            message = f"建立理想圈分段熱力圖視窗時發生錯誤: {exc}"
            logger.debug(f"[IDEAL_LAP_HEATMAP] ❌ {message}")
            QMessageBox.critical(self.main_window, "創建失敗", message)
            import traceback
            traceback.print_exc()
            return None
