# -*- coding: utf-8 -*-
"""
WindowTitlePatternGetter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class WindowTitlePatternGetter:
    """從 f1t_gui_main.py 提取的 _get_expected_window_title_pattern 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_expected_window_title_pattern(self, function_name, year, race, session):
        """
        根據功能名稱和參數生成預期的視窗標題模式
        
        參數:
            function_name: str - 功能名稱（可能是多語言）
            year: str - 年份
            race: str - 賽事名稱
            session: str - 賽段
        
        返回:
            list[str] - 可能的視窗標題模式（支援萬用字元）
        """
        # 清理 race 參數（移除日期後綴）
        race_clean = self.main_window._get_race_key_from_display(race)
        
        # 模組名稱映射表（支援多語言）
        module_mapping = {
            "Pitstop Analysis": ["Pitstop Analysis", "ピットストップ分析", "進站分析"],
            "Accident Analysis": ["Accident Analysis", "事故分析"],
            "Track Analysis": ["Track Analysis", "トラック分析", "賽道分析"],
            "Rain Analysis": ["Rain Analysis", "降雨分析", "雨況分析", "Rain Weather Analysis"],
            "Tire Analysis": ["Tire Analysis", "タイヤ分析", "輪胎分析"],
            "Speed Analysis": ["Speed Analysis", "速度分析"],
            "Brake Analysis": ["Brake Analysis", "ブレーキ分析", "煞車分析"],
            "Throttle Analysis": ["Throttle Analysis", "スロットル分析", "油門分析"],
            "Gear Analysis": ["Gear Analysis", "ギア分析", "檔位分析"],
            "RPM Analysis": ["RPM Analysis", "RPM分析"],
            "Acceleration Analysis": ["Acceleration Analysis", "アクセラレーション分析", "加速度分析"],
        }
        
        # 查找匹配的模組類型
        for key, aliases in module_mapping.items():
            for alias in aliases:
                if alias in function_name:
                    # 🔧 [FIX] 生成所有可能的標題格式（使用萬用字元匹配日期變化）
                    patterns = []
                    for name_variant in aliases:
                        # 格式1: "ModuleName_YYYY_Race*_Session" (包含空格和括號的日期)
                        patterns.append(f"{name_variant}_{year}_{race_clean}*_{session}")
                        # 格式2: "ModuleName - YYYY Race*Session" (包含空格)
                        patterns.append(f"{name_variant} - {year} {race_clean}*{session}")
                        # 格式3: "ModuleName_YYYY_Race (YYYY-MM-DD)_Session" (實際格式)
                        patterns.append(f"{name_variant}_{year}_{race_clean} *_{session}")
                        # 格式4: 只匹配核心部分，忽略日期細節
                        patterns.append(f"{name_variant}_{year}_{race_clean}*")
                    
                    logger.debug(f"[PATTERN_GEN] 為 '{function_name}' 生成 {len(patterns)} 個標題模式")
                    logger.debug(f"[PATTERN_GEN] 模式範例: {patterns[0]}")
                    return patterns
        
        # 無法判斷模組類型，返回基於功能名稱的通用模式
        logger.debug(f"[PATTERN_GEN] 無法匹配模組類型，使用通用模式: {function_name}")
        return [f"{function_name}*{year}*{race_clean}*{session}"]
