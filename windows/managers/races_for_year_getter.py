# -*- coding: utf-8 -*-
"""
RacesForYearGetter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class RacesForYearGetter:
    """從 f1t_gui_main.py 提取的 get_races_for_year 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_races_for_year(self, year):
        """根據年份獲取可用的賽事列表（使用與CLI相同的race_options）"""
        try:
            year_int = int(year)
            events = self.main_window._get_calendar_events(year_int)
            if events:
                race_keys = [event.race_key for event in events]
                logger.debug(f"[RACE_OPTIONS] 從季賽日曆載入 {year_int} 年賽事: {len(race_keys)}")
                return race_keys
            logger.debug(f"[RACE_OPTIONS] 無法取得 {year_int} 年的季賽日曆資料")
            return []
        except Exception as e:
            logger.error(f"[ERROR] 獲取賽事列表時出錯: {e}")
            # 回退到基本列表
            return ["Japan", "Great Britain", "Monaco"]
