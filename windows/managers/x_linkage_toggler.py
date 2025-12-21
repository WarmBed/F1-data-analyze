# -*- coding: utf-8 -*-
"""
XLinkageToggler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class XLinkageToggler:
    """從 f1t_gui_main.py 提取的 toggle_lap_analysis_x_linkage 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def toggle_lap_analysis_x_linkage(self, checked):
        """切換圈速分析X軸連動功能（保留舊版相容性）"""
        logger.debug(f"[連動] 圈速分析X軸連動功能: {'啟用' if checked else '停用'}")
        
        # 更新所有活躍的圖表組件的連動狀態
        mdi_windows = self.main_window.mdi_area.subWindowList()
        for window in mdi_windows:
            widget = window.widget()
            
            # 檢查是否為速度分析MDI
            if hasattr(widget, 'speed_chart_widget') and widget.speed_chart_widget:
                # 直接訪問SpeedAnalysisChartWidget的chart_widget
                if hasattr(widget.speed_chart_widget, 'chart_widget'):
                    widget.speed_chart_widget.chart_widget.set_linkage_enabled(checked)
            
            # 檢查是否為RPM分析MDI
            elif hasattr(widget, 'rpm_chart_widget') and widget.rpm_chart_widget:
                # 直接訪問RPMAnalysisChartWidget的chart_widget
                if hasattr(widget.rpm_chart_widget, 'chart_widget'):
                    widget.rpm_chart_widget.chart_widget.set_linkage_enabled(checked)
        
        # 如果停用連動，發送清除信號
        if not checked:
            global_signals.lap_analysis_x_clear.emit()
