# -*- coding: utf-8 -*-
"""
LapWindowCloseHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapWindowCloseHandler:
    """從 f1t_gui_main.py 提取的 on_lap_analysis_window_closed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_lap_analysis_window_closed(self, window_object):
        """遙測分析視窗關閉時調用"""
        
        # � 強制刷新日誌
        import sys
        
        logger.debug(f"\n[LAP_CONTROL] [SET_DEBUG] START on_lap_analysis_window_closed", flush=True)
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] window_object: {window_object}", flush=True)
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] window_object id: {id(window_object)}", flush=True)
        sys.stdout.flush()
        
        # 第一步：斷開信號連接，釋放 partial 函數引用
        if hasattr(window_object, '_sub_window'):
            sub_window = window_object._sub_window
            if sub_window and hasattr(sub_window, 'window_closed'):
                try:
                    # 斷開所有 window_closed 信號連接
                    sub_window.window_closed.disconnect()
                    logger.debug(f"[LAP_CONTROL] SIGNAL_DISCONNECT: Success", flush=True)
                except Exception as e:
                    logger.debug(f"[LAP_CONTROL] SIGNAL_DISCONNECT: Failed ({e})", flush=True)
        
        # 從追蹤集合中移除
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] BEFORE discard: size={len(self.main_window.lap_analysis_windows)}", flush=True)
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] Object to remove: {window_object}", flush=True)
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] Object in set: {window_object in self.main_window.lap_analysis_windows}", flush=True)
        sys.stdout.flush()
        
        self.main_window.lap_analysis_windows.discard(window_object)
        
        logger.debug(f"[LAP_CONTROL] [SET_DEBUG] AFTER discard: size={len(self.main_window.lap_analysis_windows)}", flush=True)
        sys.stdout.flush()
        
        # 獲取視窗標題用於日誌
        window_title = window_object.windowTitle() if hasattr(window_object, 'windowTitle') else str(window_object)
        logger.debug(f"[LAP_CONTROL] Window closed: {window_title}", flush=True)
        
        # ✅ 修復：調用模組的清理方法（如果存在）
        if hasattr(window_object, 'cleanup'):
            try:
                logger.debug(f"[LAP_CONTROL] [DEBUG]   🧹 調用模組清理方法: {window_title}")
                window_object.cleanup()
                logger.debug(f"[LAP_CONTROL] [DEBUG]   ✅ 模組清理成功: {window_title}")
            except Exception as e:
                # 🔴 簡化錯誤日誌避免 traceback 持有 frame 引用
                logger.error(f"[ERROR] [LAP_CONTROL] [DEBUG]   模組清理失敗: {e}")
                # 調試時可以取消註解：
                # import traceback
                # traceback.print_exc()
        
        # 如果是分析模組，確保清理相關引用
        if hasattr(window_object, '_sub_window'):
            sub_window = window_object._sub_window
            # 從 MDI 區域中移除子視窗
            if sub_window and sub_window.parent():
                mdi_area = sub_window.parent()
                if hasattr(mdi_area, 'removeSubWindow'):
                    mdi_area.removeSubWindow(sub_window)
                    logger.debug(f"[LAP_CONTROL] [DEBUG]   🗑️ 已從 MDI 區域移除子視窗: {window_title}")
            
            # 🔴 清理模組對子視窗的引用
            window_object._sub_window = None
            sub_window = None
            logger.debug(f"[LAP_CONTROL] [DEBUG]   🗑️ 已清理模組的子視窗引用")
        
        logger.debug(f"[LAP_CONTROL] [DEBUG]   📊 當前活動視窗數: {len(self.main_window.lap_analysis_windows)}")
        
        # 如果沒有活動視窗，隱藏圈速控件
        if len(self.main_window.lap_analysis_windows) == 0:
            self.main_window.hide_lap_controls()
        
        # 🔴 強制清理局部變量和 frame 引用
        window_object = None
        window_title = None
        sub_window = None
        
        # 🔴 清理異常緩存（Python 可能保留最近的異常信息）
        import sys
        sys.exc_clear() if hasattr(sys, 'exc_clear') else None
        
        # 🔴 強制垃圾回收，清理 frame 緩存
        import gc
        collected = gc.collect()
        logger.debug(f"[LAP_CONTROL] [DEBUG]   🗑️ 垃圾回收完成，回收了 {collected} 個對象", flush=True)
        logger.debug(f"[LAP_CONTROL] [DEBUG]   ========== on_lap_analysis_window_closed 完成 ==========\n", flush=True)
        sys.stdout.flush()
