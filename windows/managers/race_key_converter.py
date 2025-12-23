# -*- coding: utf-8 -*-
"""
RaceKeyConverter - 從 f1t_gui_main.py 提取
"""



from core.logger import get_logger

logger = get_logger(__name__)


class RaceKeyConverter:
    """從 f1t_gui_main.py 提取的 _get_race_key_from_display 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_race_key_from_display(self, race_display: str) -> str:
        """
        從顯示文字獲取正規的 race_key，移除日期後綴
        
        範例:
            "Japan (2025-04-06)" → "Japan"
            "Italy" → "Italy"
            "Italian Grand Prix (2025-09-01)" → "Italian Grand Prix"
        
        Args:
            race_display: 從 race_combo 獲取的顯示文字（可能包含日期）
            
        Returns:
            清理後的賽事名稱（移除日期後綴）
        """
        if not race_display:
            return race_display
        
        # 優先使用 _display_to_race_key 映射表（最準確）
        if hasattr(self, '_display_to_race_key') and race_display in self.main_window._display_to_race_key:
            race_key = self.main_window._display_to_race_key[race_display]
            return race_key
        
        # 後備方案: 使用正則表達式移除 " (YYYY-MM-DD)" 格式的日期後綴
        import re
        clean_name = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)\s*$', '', race_display)
        return clean_name.strip()
