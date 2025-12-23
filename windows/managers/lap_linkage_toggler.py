# -*- coding: utf-8 -*-
"""
LapLinkageToggler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from modules.gui.lap_analysis.linkage.linkage_manager import linkage_manager
from windows.managers.signal_manager import global_signals

logger = get_logger(__name__)


class LapLinkageToggler:
    """從 f1t_gui_main.py 提取的 toggle_lap_analysis_linkage 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def toggle_lap_analysis_linkage(self, checked):
        """切換圈速分析連動功能總開關"""
        try:
            logger.debug(f"[LAP_LINKAGE] 圈速分析連動總開關: {'啟用' if checked else '停用'}")
            
            # 優先使用新的連動管理器
            linkage_manager.set_master_linkage_enabled(checked)
            
            # 🔧 修復：獲取連動管理器統計資訊並顯示詳細狀態
            stats = linkage_manager.get_module_stats()
            logger.debug(f"[LAP_LINKAGE] 連動管理器統計: {stats['total_modules']} 個模組已註冊")
            logger.debug(f"[LAP_LINKAGE] 模組類型分佈: {stats['module_types']}")
            
            # 更新全域信號管理器的連動狀態（向後相容）
            if hasattr(global_signals, 'set_lap_linkage_enabled'):
                global_signals.set_lap_linkage_enabled(checked)
            stats = linkage_manager.get_module_stats()
            logger.debug(f"[LAP_LINKAGE] 連動管理器統計: {stats['total_modules']} 個模組已註冊")
            
            # 兼容舊系統：通知現有的分析模組（在它們遷移到新系統之前）
            for analysis_module in self.main_window.lap_analysis_windows:
                try:
                    if hasattr(analysis_module, 'speed_chart_widget') and analysis_module.speed_chart_widget:
                        analysis_module.speed_chart_widget.set_master_linkage_enabled(checked)
                    elif hasattr(analysis_module, 'rpm_chart_widget') and analysis_module.rpm_chart_widget:
                        analysis_module.rpm_chart_widget.set_master_linkage_enabled(checked)
                    elif hasattr(analysis_module, 'throttle_chart_widget') and analysis_module.throttle_chart_widget:
                        analysis_module.throttle_chart_widget.set_master_linkage_enabled(checked)
                    
                    logger.debug(f"[LAP_LINKAGE] 已通知模組 {type(analysis_module).__name__} 更新連動狀態")
                except Exception as e:
                    logger.error(f"[ERROR] [LAP_LINKAGE] 通知模組時發生錯誤: {e}")
            
            # 通知所有MDI子視窗的個別連動按鈕更新狀態
            current_mdi_area = self.main_window.get_current_mdi_area()
            if current_mdi_area:
                mdi_windows = current_mdi_area.subWindowList()
                for window in mdi_windows:
                    # 檢查是否為圈速分析相關的MDI子視窗
                    widget = window.widget()
                    if hasattr(widget, 'windowTitle') and any(analysis_type in widget.windowTitle() 
                        for analysis_type in ['速度分析', 'RPM分析', '油門分析']):
                        # 獲取MDI子視窗的標題欄
                        if hasattr(window, 'title_bar_widget') and hasattr(window.title_bar_widget, 'set_linkage_button_state'):
                            window.title_bar_widget.set_linkage_button_state(checked)
                            logger.debug(f"[LAP_LINKAGE] 已通知MDI子視窗 '{widget.windowTitle()}' 更新個別連動按鈕狀態")
            else:
                logger.debug(f"[LAP_LINKAGE] ⚠️ 未找到當前MDI區域，跳過MDI視窗連動按鈕更新")
            
        except Exception as e:
            logger.error(f"[ERROR] [LAP_LINKAGE] 切換連動總開關失敗: {e}")
