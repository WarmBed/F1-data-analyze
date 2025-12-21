# -*- coding: utf-8 -*-
"""
AnalysisStopper - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class AnalysisStopper:
    """從 f1t_gui_main.py 提取的 stop_all_analyses 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def stop_all_analyses(self):
        """停止所有正在執行的分析"""
        try:
            # 清理全域 CLI 分析管理器
            cli_analysis_manager.cleanup_all()
            
            # 停止所有子視窗中的 CLI 分析
            for mdi_area in self.main_window.mdi_areas:
                subwindows = mdi_area.subWindowList()
                
                for sub_window in subwindows:
                    widget = sub_window.widget()
                    if hasattr(widget, 'stop_cli_analysis'):
                        widget.stop_cli_analysis()
            
            # 清理追蹤列表
            if hasattr(self, 'active_subwindows'):
                self.main_window.active_subwindows.clear()
            
            # 停止當前視窗的分析（如果有的話）
            if hasattr(self, 'stop_cli_analysis'):
                self.main_window.stop_cli_analysis()
                
        except Exception as e:
            pass
