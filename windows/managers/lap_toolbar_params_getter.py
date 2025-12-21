# -*- coding: utf-8 -*-
"""
LapToolbarParamsGetter - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger
from typing import Dict
from typing import Optional

from core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class LapToolbarParamsGetter:
    """從 f1t_gui_main.py 提取的 get_current_lap_toolbar_parameters 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_current_lap_toolbar_parameters(self) -> Dict[str, Any]:
        """回傳工具欄上的圈速分析參數設定"""
        driver1: str = "VER"
        driver2: Optional[str] = "LEC"
        lap1_number: int = 1
        lap2_number: Optional[int] = 1
        lap_type: str = tr("specific_lap", "Specific Lap")
        is_fastest_lap: bool = False
        use_time_axis: bool = False

        try:
            # 🔧 修復：使用 hasattr(self.main_window, ...) 而非 hasattr(self, ...)
            if hasattr(self.main_window, 'driver1_combo') and self.main_window.driver1_combo.count() > 0:
                data = self.main_window.driver1_combo.currentData()
                text = self.main_window.driver1_combo.currentText()
                candidate = data if data else text
                if isinstance(candidate, str) and candidate.strip():
                    driver1 = candidate.strip()
                logger.debug(f"[LAP_TOOLBAR] 讀取 Driver1: {driver1}")

            if hasattr(self.main_window, 'driver2_combo') and self.main_window.driver2_combo.count() > 0:
                data2 = self.main_window.driver2_combo.currentData()
                if data2 is None:
                    driver2 = None
                else:
                    text2 = self.main_window.driver2_combo.currentText()
                    candidate2 = data2 if data2 else text2
                    if isinstance(candidate2, str) and candidate2.strip():
                        driver2 = candidate2.strip()
                logger.debug(f"[LAP_TOOLBAR] 讀取 Driver2: {driver2}")
            else:
                driver2 = None

            if hasattr(self.main_window, 'lap1_spinbox'):
                lap1_number = int(self.main_window.lap1_spinbox.value())
                logger.debug(f"[LAP_TOOLBAR] 讀取 Lap1: {lap1_number}")

            if hasattr(self.main_window, 'lap2_spinbox'):
                lap2_number = int(self.main_window.lap2_spinbox.value())
                logger.debug(f"[LAP_TOOLBAR] 讀取 Lap2: {lap2_number}")

            if hasattr(self.main_window, 'fastest_lap_checkbox'):
                is_fastest_lap = bool(self.main_window.fastest_lap_checkbox.isChecked())
                logger.debug(f"[LAP_TOOLBAR] 讀取 FastestLap: {is_fastest_lap}")

            if hasattr(self.main_window, 'use_time_axis_checkbox'):
                use_time_axis = bool(self.main_window.use_time_axis_checkbox.isChecked())

            if is_fastest_lap:
                lap1_number = 99
                lap2_number = 99 if driver2 else None
                lap_type = tr("fastest_lap_type", "Fastest Lap")
            else:
                lap_type = tr("specific_lap", "Specific Lap")
                if driver2 is None:
                    lap2_number = None
            
            logger.debug(f"[LAP_TOOLBAR] 最終參數: driver1={driver1}, driver2={driver2}, lap1={lap1_number}, lap2={lap2_number}, fastest={is_fastest_lap}")

        except Exception as exc:
            logger.debug(f"[LAP_CONTROL] [DEBUG]   ⚠️ 無法讀取圈速工具欄參數: {exc}")

        return {
            "driver1": driver1,
            "driver2": driver2,
            "lap1_number": lap1_number,
            "lap2_number": lap2_number,
            "lap_type": lap_type,
            "is_fastest_lap": is_fastest_lap,
            "use_time_axis": use_time_axis,
        }
