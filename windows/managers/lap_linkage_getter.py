# -*- coding: utf-8 -*-
"""
LapLinkageGetter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class LapLinkageGetter:
    """從 f1t_gui_main.py 提取的 get_lap_linkage_enabled 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_lap_linkage_enabled(self):
        """獲取圈速分析連動總開關狀態"""
        if hasattr(self, 'lap_linkage_action'):
            return self.main_window.lap_linkage_action.isChecked()
        return True  # 預設啟用
        logger.debug(f"[LINKAGE_MASTER] 🔗 圈速分析連動總開關: {'啟用' if checked else '停用'}")
        
        # 更新全域連動狀態
        if hasattr(global_signals, 'lap_analysis_linkage_master_enabled'):
            global_signals.lap_analysis_linkage_master_enabled = checked
        else:
            # 如果沒有這個屬性，添加它
            global_signals.lap_analysis_linkage_master_enabled = checked
        
        # 通知所有圈速分析模組總開關狀態變更
        updated_count = 0
        for analysis_module in self.main_window.lap_analysis_windows:
            try:
                # 檢查模組是否有連動控制方法
                if hasattr(analysis_module, 'set_master_linkage_enabled'):
                    analysis_module.set_master_linkage_enabled(checked)
                    updated_count += 1
                    logger.debug(f"[LINKAGE_MASTER] ✅ 已更新 {type(analysis_module).__name__} 總開關狀態")
                elif hasattr(analysis_module, 'speed_chart_widget'):
                    # 速度分析模組
                    if hasattr(analysis_module.speed_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.speed_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        logger.debug(f"[LINKAGE_MASTER] ✅ 已更新速度分析模組總開關狀態")
                elif hasattr(analysis_module, 'rpm_chart_widget'):
                    # RPM分析模組
                    if hasattr(analysis_module.rpm_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.rpm_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        logger.debug(f"[LINKAGE_MASTER] ✅ 已更新RPM分析模組總開關狀態")
                elif hasattr(analysis_module, 'throttle_chart_widget'):
                    # 油門分析模組
                    if hasattr(analysis_module.throttle_chart_widget, 'set_master_linkage_enabled'):
                        analysis_module.throttle_chart_widget.set_master_linkage_enabled(checked)
                        updated_count += 1
                        logger.debug(f"[LINKAGE_MASTER] ✅ 已更新油門分析模組總開關狀態")
                else:
                    logger.debug(f"[LINKAGE_MASTER] ⚠️ {type(analysis_module).__name__} 不支援連動控制")
                    
            except Exception as e:
                logger.debug(f"[LINKAGE_MASTER] ❌ 更新 {type(analysis_module).__name__} 總開關狀態失敗: {e}")
        
        logger.debug(f"[LINKAGE_MASTER] 📊 總開關狀態更新完成: {updated_count}/{len(self.main_window.lap_analysis_windows)} 個模組")
