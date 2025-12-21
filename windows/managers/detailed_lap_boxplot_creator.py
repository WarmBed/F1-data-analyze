# -*- coding: utf-8 -*-
"""
DetailedLapBoxplotCreator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class DetailedLapBoxplotCreator:
    """從 f1t_gui_main.py 提取的 _create_detailed_lap_boxplot_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_detailed_lap_boxplot_window(self, mdi_area, year, race, session):
        """建立圈速箱型圖視窗並加入 MDI (✅ 使用 module_factory 模式 - 2025-11-13 重構)。"""
        try:
            logger.debug(f"[BOXPLOT] 🚀 使用 module_factory 創建圈速箱型圖模組...")
            
            # ✅ 使用 module_factory 創建包裝器模組
            analysis_module = self.main_window.create_module_from_factory(
                function_name="Lap Time Box Plot",
                module_type_hint="laptime_box_plot"
            )
            
            if not analysis_module:
                raise RuntimeError("Module factory 創建失敗")
            
            logger.debug(f"[BOXPLOT] ✅ 模組工廠創建成功")
            
            # 設置當前參數
            analysis_module.current_year = str(year)
            analysis_module.current_race = race
            analysis_module.current_session = session
            logger.debug(f"[BOXPLOT] ✅ 基本參數設置完成: {year} {race} {session}")
            
            # 更新參數（觸發數據載入）
            logger.debug(f"[BOXPLOT] 🚀 更新模組參數...")
            if hasattr(analysis_module, 'update_parameters'):
                analysis_module.update_parameters(int(year), race, session)
            logger.debug(f"[BOXPLOT] ✅ 參數更新成功！")
            
            # 獲取模組標題
            window_title = analysis_module.get_window_title(
                year=year,
                race=race,
                session=session
            )
            logger.debug(f"[BOXPLOT] 📝 視窗標題: {window_title}")
            
            # 創建子視窗
            logger.debug(f"[BOXPLOT] 🖼️ 創建 MDI 子視窗...")
            sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            sub_window.setWidget(analysis_module.get_widget())
            
            # 設置模組的父視窗引用（如果 MDI 支持）
            if hasattr(analysis_module, '_laptime_boxplot_core') and hasattr(analysis_module._laptime_boxplot_core, 'set_parent_window'):
                analysis_module._laptime_boxplot_core.set_parent_window(sub_window)
            
            # 設置視窗尺寸
            width, height = analysis_module.get_default_size()
            sub_window.resize(width, height)
            logger.debug(f"[BOXPLOT] 📐 設置視窗尺寸: {width}x{height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            logger.debug(f"[BOXPLOT] ✅ 已添加到 MDI 區域")
            
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
            logger.debug(f"[BOXPLOT] 🎉 圈速箱型圖視窗創建完成（使用包裝器架構）！")
            
            return sub_window
            
        except Exception as exc:
            message = f"建立圈速箱型圖視窗時發生錯誤: {exc}"
            logger.debug(f"[BOXPLOT] ❌ {message}")
            self.main_window.show_error_message("Lap Time Box Plot", message)
            import traceback
            traceback.print_exc()
            return None
