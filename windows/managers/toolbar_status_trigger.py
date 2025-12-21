# -*- coding: utf-8 -*-
"""
ToolbarStatusTrigger - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ToolbarStatusTrigger:
    """從 f1t_gui_main.py 提取的 _trigger_toolbar_status_for_lap_analysis 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _trigger_toolbar_status_for_lap_analysis(self, analysis_type, window_object):
        """統一觸發工具欄狀態更新 - 任何遙測分析模組都會觸發"""
        try:
            logger.debug(f"[TOOLBAR_TRIGGER] 🎯 開始為 {analysis_type} 分析模組觸發工具欄狀態更新")
            
            # 根據分析類型設定模組名稱
            module_name_mapping = {
                "speed_analysis": "Speed Analysis",
                "rpm": "RPM Analysis", 
                "brake": "Brake Analysis",
                "throttle": "Throttle Analysis",
                "steering": "Steering Analysis",
                "gear": "Gear Analysis",
                "acceleration": "Acceleration Analysis",
                "speed_diff": "Speed Difference Analysis",
                "distancediff": "Distance Difference Analysis"
            }
            
            module_name = module_name_mapping.get(analysis_type, f"{analysis_type}分析")
            
            # 獲取當前遙測分析設置
            driver1 = self.main_window.driver1_combo.currentText() if hasattr(self, 'driver1_combo') else "VER"
            driver2 = self.main_window.driver2_combo.currentText() if hasattr(self, 'driver2_combo') else "LEC"
            lap1 = self.main_window.lap1_spinbox.value() if hasattr(self, 'lap1_spinbox') else 1
            lap2 = self.main_window.lap2_spinbox.value() if hasattr(self, 'lap2_spinbox') else 1
            
            # 處理單車手模式
            if driver2 == "無":
                driver2 = None
            
            # 構建圈數信息
            if driver2:
                lap_numbers = f"{driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈"
            else:
                lap_numbers = f"{driver1} 第{lap1}圈"
            
            # 構建狀態信息（初始值，等數據載入後會更新更詳細的信息）
            lap_time = "載入中..."
            tyre_compound = "分析中..."
            
            # 觸發工具欄狀態更新
            self.main_window.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            logger.debug(f"[TOOLBAR_TRIGGER] ✅ 已觸發工具欄狀態更新: {module_name} | {lap_numbers}")
            
        except Exception as e:
            # 🔴 簡化錯誤日誌避免 traceback 持有 frame（包含 window_object 參數）
            logger.error(f"[ERROR] [TOOLBAR_TRIGGER] 觸發工具欄狀態更新失敗: {e}")
            # 調試時可以取消註解：
            # import traceback
            # traceback.print_exc()
