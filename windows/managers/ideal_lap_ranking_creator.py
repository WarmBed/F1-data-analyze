# -*- coding: utf-8 -*-
"""
IdealLapRankingCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QMessageBox
from core.logger import get_logger
from functools import partial
from windows.widgets.popout_subwindow import PopoutSubWindow

logger = get_logger(__name__)


class IdealLapRankingCreator:
    """從 f1t_gui_main.py 提取的 _create_ideal_lap_ranking_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_ideal_lap_ranking_window(self, mdi_area, year, race, session):
        """建立理想圈排名表格視窗並加入 MDI"""
        try:
            logger.debug(f"[IDEAL_LAP_RANKING] 🚀 啟動理想圈排名表格模組...")
            from modules.gui.lap_analysis.ideal_lap.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
            logger.debug(f"[IDEAL_LAP_RANKING] ✅ 模組導入成功")
        except ImportError as exc:
            message = f"無法載入理想圈排名表格模組: {exc}"
            logger.debug(f"[IDEAL_LAP_RANKING] ❌ {message}")
            QMessageBox.critical(self.main_window, "模組載入失敗", message)
            import traceback
            traceback.print_exc()
            return None

        try:
            logger.debug(f"[IDEAL_LAP_RANKING] 🔧 創建模組實例...")
            # 創建模組實例
            analysis_module = IdealLapRankingTableModule(
                parent=self.main_window,
                year=year,
                race=race,
                session=session
            )
            logger.debug(f"[IDEAL_LAP_RANKING] ✅ 模組實例創建成功")
            
            # 初始化模組
            logger.debug(f"[IDEAL_LAP_RANKING] 🚀 初始化模組...")
            if not analysis_module.initialize_module(parent_widget=self.main_window):
                raise RuntimeError("Module initialization failed")
            logger.debug(f"[IDEAL_LAP_RANKING] ✅ 模組初始化成功！")
            
            # 獲取模組標題
            window_title = analysis_module.get_title()
            logger.debug(f"[IDEAL_LAP_RANKING] 📝 視窗標題: {window_title}")
            
            # 創建子視窗
            logger.debug(f"[IDEAL_LAP_RANKING] 🖼️ 創建 MDI 子視窗...")
            sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            sub_window.setWidget(analysis_module.get_widget())
            
            # 設置視窗尺寸
            width, height = analysis_module.get_default_size()
            sub_window.resize(width, height)
            logger.debug(f"[IDEAL_LAP_RANKING] 📐 設置視窗尺寸: {width}x{height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            logger.debug(f"[IDEAL_LAP_RANKING] ✅ 已添加到 MDI 區域")
            
            # 連接關閉信號
            if hasattr(sub_window, 'window_closed'):
                # 🔴 使用 partial 避免 lambda 閉包洩漏

                sub_window.window_closed.connect(

                    partial(self.main_window.on_subwindow_closed, sub_window)

                )
            
            # 添加到追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.main_window.active_subwindows.append(sub_window)
            
            # 顯示視窗
            sub_window.show()
            logger.debug(f"[IDEAL_LAP_RANKING] 🎉 理想圈排名表格視窗創建完成！")
            
            # 載入資料
            logger.debug(f"[IDEAL_LAP_RANKING] 📊 開始載入資料...")
            analysis_module.load_data()
            
            return sub_window
            
        except Exception as exc:
            message = f"建立理想圈排名表格視窗時發生錯誤: {exc}"
            logger.debug(f"[IDEAL_LAP_RANKING] ❌ {message}")
            QMessageBox.critical(self.main_window, "創建失敗", message)
            import traceback
            traceback.print_exc()
            return None
