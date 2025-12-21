# -*- coding: utf-8 -*-
"""
YearChangeHandler - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class YearChangeHandler:
    """從 f1t_gui_main.py 提取的 on_year_changed 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def on_year_changed(self, year):
        """處理年份變更事件"""
        # ✅ 調試點 1: 方法入口
        logger.info(f"🔵 [DEBUG]    on_year_changed 被調用: year={year}")
        logger.debug(f"🔵 [DEBUG]    on_year_changed 被調用: year={year}")
        
        try:
            previous_race = self.main_window.get_selected_race_key()
            previous_session = self.main_window.get_selected_session_code()
        except Exception:
            previous_race = None
            previous_session = None

        try:
            year_int = int(year)
        except Exception:
            year_int = self.main_window.get_selected_year()

        logger.debug(f"[CALENDAR] 切換至 {year_int} 年賽季日曆")
        logger.info(f"[CALENDAR] 切換至 {year_int} 年賽季日曆")

        self.main_window._refresh_calendar_for_year(
            year_int,
            preserve_race_key=previous_race,
            preserve_session_code=previous_session,
        )

        self.main_window.update_status_bar()
        
        # 🔧 更新 Welcome 頁面的 Season Progress
        # Note: 只更新 Season Progress，因為 Constructor/Driver Standings 
        # 會通過 sync_to_all_mdi_subwindows 自動更新（如果它們實現了 update_parameters 方法）
        print(f"[DEBUG] 檢查 welcome_season_progress...")
        has_attr = hasattr(self.main_window, 'welcome_season_progress')
        print(f"[DEBUG] hasattr welcome_season_progress: {has_attr}")
        
        if has_attr:
            sp = self.main_window.welcome_season_progress
            print(f"[DEBUG] welcome_season_progress 類型: {type(sp).__name__}")
            print(f"[DEBUG] welcome_season_progress 當前年份: {sp.year}")
            has_method = hasattr(sp, 'update_year')
            print(f"[DEBUG] has update_year method: {has_method}")
            
            if has_method:
                print(f"[DEBUG] 調用 update_year({year_int})...")
                try:
                    sp.update_year(str(year_int))
                    print(f"[DEBUG] update_year 調用成功")
                except Exception as e:
                    print(f"[DEBUG] update_year 調用失敗: {e}")
                    logger.error(f"[YEAR_CHANGE] 更新 Season Progress 失敗: {e}")
        else:
            print(f"[DEBUG] welcome_season_progress 不存在!")
        
        # Debounced parameter broadcast for main window year change
        logger.info("🔵 [DEBUG]    on_main_year_changed - scheduling parameter broadcast")
        logger.debug("🔵 [DEBUG]    on_main_year_changed - scheduling parameter broadcast")
        self.main_window._schedule_parameter_broadcast("main_year_changed")

        
        # 保留原有同步邏輯（用於單獨通知）
        self.main_window.sync_to_all_mdi_subwindows('year', str(year_int))
