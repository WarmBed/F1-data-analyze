# -*- coding: utf-8 -*-
"""
ChartInfoGetter - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class ChartInfoGetter:
    """從 f1t_gui_main.py 提取的 get_chart_info 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_chart_info(self, chart_type):
        """獲取圖表類型的資訊"""
        chart_info_map = {
            'speed_analysis': {'name': '速度分析', 'icon': '⚡'},  # 新增速度分析
            # 'speed': {'name': '速度圖表', 'icon': '🏃'},  # 移除速度圖表
            'brake': {'name': '煞車圖表', 'icon': '🛑'},
            'throttle': {'name': '油門圖表', 'icon': '⚡'},
            'steering': {'name': '轉向圖表', 'icon': '🎯'},
            'gear': {'name': '檔位圖表', 'icon': '⚙️'},
            'rpm': {'name': '轉速圖表', 'icon': '🔄'},
            'acceleration': {'name': '加速度圖表', 'icon': '📈'},
            'speed_diff': {'name': '速度差圖表', 'icon': '📊'},
            'distancediff': {'name': '累積距離差圖表', 'icon': '📏'}
        }
        
        return chart_info_map.get(chart_type, {'name': '未知圖表', 'icon': '❓'})
