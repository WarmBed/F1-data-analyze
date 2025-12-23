# -*- coding: utf-8 -*-
"""
AllDataShower - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

logger = get_logger(__name__)


class AllDataShower:
    """從 f1t_gui_main.py 提取的 show_all_data_in_current_tab 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def show_all_data_in_current_tab(self, *args, **kwargs):
        """顯示當前分頁的所有數據（全局工具列按鈕）- 重置所有已開啟視窗的 XY 軸視圖"""
        try:
            current_mdi_area = self.main_window.get_current_mdi_area()
            if not current_mdi_area:
                logger.debug("[GLOBAL_TOOLBAR] ⚠️  當前分頁沒有 MDI 區域")
                return
            
            # 🔧 獲取所有 MDI 子窗口（不只是 active 的）
            all_sub_windows = current_mdi_area.subWindowList()
            if not all_sub_windows:
                logger.debug("[GLOBAL_TOOLBAR] ⚠️  當前分頁沒有任何分析窗口")
                return
            
            logger.debug(f"[GLOBAL_TOOLBAR] 🔄 準備重置 {len(all_sub_windows)} 個視窗的 XY 軸...")
            
            # 遍歷所有子窗口
            reset_count = 0
            for sub_window in all_sub_windows:
                try:
                    # 嘗試從子窗口獲取模組實例
                    analysis_module = None
                    if hasattr(sub_window, 'analysis_module'):
                        analysis_module = sub_window.analysis_module
                        logger.debug(f"[GLOBAL_TOOLBAR]   ✅ 找到模組: {analysis_module.__class__.__name__}")
                    
                    # 如果沒有模組實例，嘗試獲取 widget
                    if not analysis_module:
                        analysis_widget = sub_window.widget()
                        if not analysis_widget:
                            logger.debug(f"[GLOBAL_TOOLBAR]   ⚠️  無法獲取 widget，跳過此視窗")
                            continue
                        
                        # 檢查 widget 本身是否有 reset_chart_view()
                        if hasattr(analysis_widget, 'reset_chart_view'):
                            logger.debug(f"[GLOBAL_TOOLBAR]   ✅ Widget 有 reset_chart_view(): {analysis_widget.__class__.__name__}")
                            analysis_widget.reset_chart_view()
                            reset_count += 1
                            continue
                        
                        # 檢查 widget 是否有 analysis_module 屬性
                        if hasattr(analysis_widget, 'analysis_module'):
                            analysis_module = analysis_widget.analysis_module
                            logger.debug(f"[GLOBAL_TOOLBAR]   ✅ 從 widget 找到模組: {analysis_module.__class__.__name__}")
                        else:
                            # 最後嘗試直接調用 chart_widget.reset_view()
                            if hasattr(analysis_widget, 'chart_widget') and hasattr(analysis_widget.chart_widget, 'reset_view'):
                                logger.debug(f"[GLOBAL_TOOLBAR]   ✅ 直接調用 chart_widget.reset_view()")
                                analysis_widget.chart_widget.reset_view()
                                reset_count += 1
                            else:
                                logger.debug(f"[GLOBAL_TOOLBAR]   ⚠️  {analysis_widget.__class__.__name__} 無重置方法，跳過")
                            continue
                    
                    # 調用模組的 reset_chart_view() 方法
                    if analysis_module and hasattr(analysis_module, 'reset_chart_view'):
                        logger.debug(f"[GLOBAL_TOOLBAR]   ✅ 調用 {analysis_module.__class__.__name__}.reset_chart_view()")
                        analysis_module.reset_chart_view()
                        reset_count += 1
                    else:
                        logger.debug(f"[GLOBAL_TOOLBAR]   ⚠️  模組沒有 reset_chart_view()，跳過")
                
                except Exception as e:
                    logger.debug(f"[GLOBAL_TOOLBAR]   ❌ 處理視窗時發生錯誤: {e}")
                    continue
            
            logger.debug(f"[GLOBAL_TOOLBAR] ✅ 完成！成功重置 {reset_count}/{len(all_sub_windows)} 個視窗")
            
        except Exception as e:
            logger.debug(f"[GLOBAL_TOOLBAR] ❌ 重置視圖失敗: {e}")
            import traceback
            traceback.print_exc()
