# -*- coding: utf-8 -*-
"""
DriverMappingLoader - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class DriverMappingLoader:
    """從 f1t_gui_main.py 提取的 _load_driver_team_mapping_from_standings 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _load_driver_team_mapping_from_standings(self, year: int) -> None:
        """從本地 Driver Standings JSON 載入車手車隊映射"""
        import glob
        import json
        
        try:
            json_dir = Path("json")
            if not json_dir.exists():
                logger.debug("[INIT] ⚠️ json 目錄不存在，跳過車隊映射載入")
                return
            
            # 搜索最新的 championship_standings JSON
            patterns = [
                f"championship_standings_{year}_R*_*.json",
                f"championship_standings_{year}.json",
            ]
            
            latest_file = None
            latest_time = 0
            
            for pattern in patterns:
                for filepath in json_dir.glob(pattern):
                    mtime = filepath.stat().st_mtime
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = filepath
            
            if not latest_file:
                logger.debug(f"[INIT] ⚠️ 找不到 {year} 年的 Driver Standings JSON，使用預設車隊映射")
                return
            
            # 載入並解析 JSON
            with open(latest_file, 'r', encoding='utf-8') as f:
                standings_data = json.load(f)
            
            count = self.main_window._color_palette_provider.update_driver_teams_from_standings(standings_data)
            logger.debug(f"[INIT] 🏎️ 從 {latest_file.name} 載入 {count} 位車手的車隊映射")
            
        except Exception as exc:
            logger.warning(f"[INIT] ⚠️ 載入車隊映射失敗: {exc}")
