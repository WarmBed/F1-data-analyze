# -*- coding: utf-8 -*-
"""
ColorPaletteInitializer - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
import datetime

from core.logger import get_logger

logger = get_logger(__name__)


class ColorPaletteInitializer:
    """從 f1t_gui_main.py 提取的 _initialize_color_palette 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _initialize_color_palette(self) -> None:
        """Fetch the colour palette from the API (or fall back to defaults)."""
        target_year = datetime.datetime.now().year
        try:
            self.main_window._color_palette_provider.ensure_loaded(year=target_year)
        except ColorPaletteError as exc:
            logger.debug(f"[INIT] ❌ 顏色配置載入失敗 (已禁用預設色票): {exc}")
            self.main_window._show_palette_error_message(str(exc))
            return
        except Exception as exc:
            update_health_state('offline', str(exc))
            logger.debug(f"[INIT] ❌ 顏色配置載入失敗: {exc}")
            self.main_window._show_palette_error_message(str(exc))
            return

        error = self.main_window._color_palette_provider.last_error()
        if error:
            # ✅ 改善訊息：這不是錯誤，是正常的後備機制
            logger.debug(f"[INIT] 💡 API 顏色資料不完整，已套用內建顏色配置")
            logger.debug(f"[INIT] 📋 詳情: {error}")
        else:
            logger.debug(f"[INIT] 🎨 顏色配置載入完成 (year={target_year})")
        
        # ✅ 新增：從 Driver Standings JSON 載入車手車隊映射 (2025-12-14)
        self.main_window._load_driver_team_mapping_from_standings(target_year)
