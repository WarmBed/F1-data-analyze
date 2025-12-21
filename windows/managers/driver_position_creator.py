# -*- coding: utf-8 -*-
"""
DriverPositionCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.gui_i18n import tr
from core.logger import get_logger
from functools import partial
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class DriverPositionCreator:
    """從 f1t_gui_main.py 提取的 _create_driver_position_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_driver_position_window(self, mdi_area, year, race, session):
        """建立車手比賽排名分析視窗並加入 MDI"""
        try:
            logger.debug(f"[DRIVER_POSITION] 🚀 啟動車手比賽排名分析模組...")
            from modules.gui.race_analysis.position.driver_position_analysis_module import DriverPositionAnalysisModule
            logger.debug(f"[DRIVER_POSITION] ✅ 模組導入成功")
        except ImportError as exc:
            message = f"無法載入車手比賽排名分析模組: {exc}"
            logger.debug(f"[DRIVER_POSITION] ❌ {message}")
            QMessageBox.critical(self.main_window, tr("module_load_failed", "模組載入失敗"), message)
            import traceback
            traceback.print_exc()
            return None

        try:
            logger.debug(f"[DRIVER_POSITION] 🔧 創建模組實例...")
            # 創建模組實例
            analysis_module = DriverPositionAnalysisModule(
                parent=self.main_window,
                year=year,
                race=race,
                session=session
            )
            logger.debug(f"[DRIVER_POSITION] ✅ 模組實例創建成功")
            
            # 初始化模組
            logger.debug(f"[DRIVER_POSITION] 🚀 初始化模組...")
            if not analysis_module.initialize_module(parent_widget=self.main_window):
                raise RuntimeError("Module initialization failed")
            logger.debug(f"[DRIVER_POSITION] ✅ 模組初始化成功！")
            
            # 獲取模組標題
            window_title = analysis_module.get_title()
            logger.debug(f"[DRIVER_POSITION] 📝 視窗標題: {window_title}")
            
            # 創建子視窗
            logger.debug(f"[DRIVER_POSITION] 🖼️ 創建 MDI 子視窗...")
            sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            sub_window.setWidget(analysis_module.get_widget())
            
            # 設置視窗尺寸
            width, height = analysis_module.get_default_size()
            sub_window.resize(width, height)
            logger.debug(f"[DRIVER_POSITION] 📐 設置視窗尺寸: {width}x{height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            logger.debug(f"[DRIVER_POSITION] ✅ 已添加到 MDI 區域")
            
            # 連接關閉信號
            if hasattr(sub_window, 'window_closed'):
                sub_window.window_closed.connect(
                    partial(self.main_window.on_subwindow_closed, sub_window)
                )
            
            # 添加到追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.main_window.active_subwindows.append(sub_window)
            
            # 顯示視窗
            sub_window.show()
            logger.debug(f"[DRIVER_POSITION] 🎉 車手比賽排名分析視窗創建完成！")
            
            # 載入資料
            logger.debug(f"[DRIVER_POSITION] 📊 開始載入資料...")
            analysis_module.load_data()
            
            return sub_window
            
        except Exception as exc:
            message = f"建立車手比賽排名分析視窗時發生錯誤: {exc}"
            logger.debug(f"[DRIVER_POSITION] ❌ {message}")
            QMessageBox.critical(self.main_window, tr("creation_failed", "創建失敗"), message)
            import traceback
            traceback.print_exc()
            return None
