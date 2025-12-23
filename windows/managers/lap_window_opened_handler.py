# -*- coding: utf-8 -*-
"""
LapWindowOpenedHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapWindowOpenedHandler:
    """從 f1t_gui_main.py 提取的 on_lap_analysis_window_opened 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_lap_analysis_window_opened(self, window_object, analysis_type):
        """遙測分析視窗開啟時調用"""
        window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
        logger.debug(f"[LAP_CONTROL] [DEBUG]   � on_lap_analysis_window_opened 被調用")
        logger.debug(f"[LAP_CONTROL] [DEBUG]   參數: window_title='{window_title}', analysis_type='{analysis_type}'")
        
        # 🔴 移除 traceback 代碼避免 frame 引用洩漏
        # 調試時可以取消註解以下代碼：
        # import traceback
        # stack = traceback.format_stack()
        # print("[LAP_CONTROL] [DEBUG]   調用堆疊:")
        # for frame in stack[-5:]:
        #     print(f"[LAP_CONTROL] [DEBUG]     {frame.strip()}")
        
        # 為視窗對象添加分析類型標記（用於後續過濾）
        if not hasattr(window_object, '_analysis_type'):
            window_object._analysis_type = analysis_type
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🏷️ 為視窗添加類型標記: {analysis_type}")
        
        # 存儲視窗對象而不是標題字符串
        self.main_window.lap_analysis_windows.add(window_object)
        logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 圈速分析視窗已開啟: {window_title} ({analysis_type})")
        logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 當前活動視窗數: {len(self.main_window.lap_analysis_windows)}")
        
        # 顯示圈速控件
        logger.debug("[LAP_CONTROL] [DEBUG]   🎯 即將調用 show_lap_controls()...")
        self.main_window.show_lap_controls()
        
        # 🎯 新增: 統一觸發工具欄狀態更新 - 任何遙測分析模組都會觸發
        logger.debug(f"[TOOLBAR_TRIGGER] 🚀 圈速分析模組開啟，觸發工具欄狀態更新: {analysis_type}")
        self.main_window._trigger_toolbar_status_for_lap_analysis(analysis_type, window_object)
