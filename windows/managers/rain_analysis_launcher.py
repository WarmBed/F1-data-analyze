# -*- coding: utf-8 -*-
"""
RainAnalysisLauncher - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class RainAnalysisLauncher:
    """從 f1t_gui_main.py 提取的 rain_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def rain_analysis(self):
        """開啟降雨分析 - 使用通用圖表系統"""
        try:
            # 移除歡迎頁面（如果存在）
            self.main_window.remove_welcome_tab()
            
            params = self.main_window.get_current_parameters()
            logger.debug(f"[RAIN] {params['year']} {params['race']} {params['session']}")
            
            # 導入新的雨量分析模組 (使用 Universal MDI 架構)
            from modules.gui.race_analysis.rain.rain_analysis_mdi import RainAnalysisUniversal
            
            # 創建雨量分析模組
            rain_widget = RainAnalysisUniversal(
                year=params['year'],
                race=params['race'], 
                session=params['session']
            )
            
            # [TOOL] 修正：使用新的標題格式
            tab_title = f"Rain Analysis_{params['year']}_{params['race']}_{params['session']}"
            
            # 添加到主分頁控件 (使用空字串隱藏標題)
            tab_index = self.main_window.tab_widget.addTab(rain_widget, "")
            self.main_window.tab_widget.setCurrentIndex(tab_index)
            
            # 添加到活動分頁列表
            self.main_window.active_analysis_tabs.append(tab_title)
            
            logger.debug(f"[OK] 降雨分析頁面已開啟: {tab_title} (使用通用圖表系統)")
            
        except ImportError as e:
            logger.error(f"[ERROR] 降雨分析組件導入失敗: {e}")
            self.main_window.show_error_message("模組錯誤", f"無法載入降雨分析組件: {e}")
        except Exception as e:
            logger.error(f"[ERROR] 降雨分析開啟失敗: {e}")
            import traceback
            traceback.print_exc()
            self.main_window.show_error_message("降雨分析錯誤", f"開啟降雨分析時發生錯誤: {e}")
