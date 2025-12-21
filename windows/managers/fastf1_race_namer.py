# -*- coding: utf-8 -*-
"""
Fastf1RaceNamer - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class Fastf1RaceNamer:
    """從 f1t_gui_main.py 提取的 get_fastf1_race_name 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def get_fastf1_race_name(self, display_name):
        """將顯示名稱轉換為 FastF1 API 期望的名稱"""
        if not display_name:
            return "Unknown"

        name = display_name.strip()
        override = self.main_window._fastf1_overrides.get(name)
        if override:
            return override

        # 優先使用季賽日曆映射
        mapped_key = self.main_window._display_to_race_key.get(name)
        if not mapped_key:
            mapped_key = self.main_window._display_to_race_key.get(self.main_window._strip_race_display(name))

        return mapped_key or name
