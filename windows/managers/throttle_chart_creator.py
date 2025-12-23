# -*- coding: utf-8 -*-
"""
ThrottleChartCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea
from windows.workers.cli_workers import MainWindowParameterProvider

logger = get_logger(__name__)


class ThrottleChartCreator:
    """從 f1t_gui_main.py 提取的 _create_throttle_line_chart_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_throttle_line_chart_window(self):
        """創建油門折線圖分析視窗"""
        logger.debug("[THROTTLE_LINE] 開始創建油門折線圖視窗...")
        
        # 獲取當前參數
        current_tab = self.main_window.tab_widget.currentWidget()
        if current_tab is None:
            logger.debug("[THROTTLE_LINE] 錯誤: 無活動分頁")
            QMessageBox.warning(self.main_window, "錯誤", "無活動分頁")
            return

        # 🔧 修復：使用 MainWindowParameterProvider 獲取參數（參考其他模組）
        parameter_provider = MainWindowParameterProvider(self.main_window)
        current_year = parameter_provider.get_current_year()
        current_race = parameter_provider.get_current_race()
        current_session = parameter_provider.get_current_session()

        if not all([current_year, current_race, current_session]):
            logger.debug(f"[THROTTLE_LINE] 錯誤: 參數不完整 Year={current_year}, Race={current_race}, Session={current_session}")
            QMessageBox.warning(
                self.main_window,
                "參數錯誤",
                "無法獲取當前年份、賽事或會話資訊\n請先選擇賽事資料"
            )
            return

        logger.debug(f"[THROTTLE_LINE] 參數: {current_year} {current_race} {current_session}")

        # 獲取 MDI 區域
        mdi_area = None
        if isinstance(current_tab, CustomMdiArea):
            mdi_area = current_tab
        else:
            for child in current_tab.findChildren(CustomMdiArea):
                mdi_area = child
                break

        if mdi_area is None:
            logger.debug("[THROTTLE_LINE] 錯誤: 找不到MDI區域")
            QMessageBox.warning(self.main_window, "錯誤", "找不到MDI區域")
            return

        logger.debug("[THROTTLE_LINE] 開始創建油門折線圖模組...")

        try:
            from modules.gui.lap_analysis.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module import (
                ThrottleLineChartModule,
            )

            # 設置當前參數
            try:
                year_int = int(current_year)
            except (TypeError, ValueError):
                year_int = current_year

            logger.debug(f"[THROTTLE_LINE] 模組參數: {year_int} {current_race} {current_session}")

            # 創建模組實例（直接傳入參數）
            module = ThrottleLineChartModule(
                parent=self.main_window,
                year=year_int,
                race=current_race,
                session=current_session
            )
            
            # 設置參數提供者
            module.parameter_provider = parameter_provider

            # 獲取 widget
            widget = module.get_widget()

            if widget:
                logger.debug("[THROTTLE_LINE] ✅ 模組初始化成功")
                
                # 獲取視窗標題
                window_title = module.get_window_title()
                
                # 創建 MDI 子視窗
                sub_window = PopoutSubWindow(window_title, mdi_area, module)
                sub_window.setWidget(widget)
                
                # 設置模組的父視窗引用
                module.set_parent_window(sub_window)
                
                # 設置視窗大小
                width, height = module.get_default_size()
                sub_window.resize(width, height)
                
                # 添加到 MDI 區域
                mdi_area.addSubWindow(sub_window)
                sub_window.show()
                
                logger.debug(f"[THROTTLE_LINE] ✅ 油門折線圖視窗已創建: {window_title}")
                
            else:
                logger.debug("[THROTTLE_LINE] ❌ 模組初始化失敗")
                QMessageBox.warning(
                    self,
                    "初始化失敗",
                    "油門折線圖模組初始化失敗\n請檢查日誌"
                )

        except Exception as e:
            logger.debug(f"[THROTTLE_LINE] ❌ 創建失敗: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "創建失敗",
                f"創建油門折線圖視窗時發生錯誤:\n{str(e)}"
            )
