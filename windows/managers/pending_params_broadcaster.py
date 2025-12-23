# -*- coding: utf-8 -*-
"""
PendingParamsBroadcaster - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from core.api_runtime_state import clear_pending_update

from core.logger import get_logger

logger = get_logger(__name__)


class PendingParamsBroadcaster:
    """從 f1t_gui_main.py 提取的 _broadcast_pending_parameters 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _broadcast_pending_parameters(self) -> None:
        """Execute the consolidated parameter update for all listening modules."""
        logger.info("[BROADCAST_DEBUG] _broadcast_pending_parameters 被調用")
        
        payload = self.main_window._pending_parameter_payload or {}
        self.main_window._pending_parameter_payload = None
        clear_pending_update()

        logger.info("[BROADCAST_DEBUG] 執行 payload: %s", payload)

        try:
            logger.info("[PARAMS] Executing parameter broadcast: %s", payload)
            
            # 🔧 修復：更新 Welcome Screen 的固定視窗
            current_year = self.main_window.year_combo.currentText() if hasattr(self, 'year_combo') else '2025'
            logger.debug(f"🔍 [BROADCAST] 檢查 Welcome Screen 視窗更新: year={current_year}")
            
            # 更新 Season Progress
            if hasattr(self, 'welcome_season_progress') and self.main_window.welcome_season_progress:
                try:
                    logger.debug(f"🔍 [BROADCAST] 更新 Season Progress: {current_year}")
                    self.main_window.welcome_season_progress.update_year(current_year)
                except Exception as e:
                    logger.debug(f"❌ [BROADCAST] Season Progress 更新失敗: {e}")
            
            # 更新 Constructor Standings
            if hasattr(self, 'welcome_constructor_standings') and self.main_window.welcome_constructor_standings:
                try:
                    logger.debug(f"🔍 [BROADCAST] 更新 Constructor Standings: {current_year}")
                    if hasattr(self.main_window.welcome_constructor_standings, 'update_year'):
                        self.main_window.welcome_constructor_standings.update_year(current_year)
                except Exception as e:
                    logger.debug(f"❌ [BROADCAST] Constructor Standings 更新失敗: {e}")
            
            # 更新 Driver Standings
            if hasattr(self, 'welcome_driver_standings') and self.main_window.welcome_driver_standings:
                try:
                    logger.debug(f"🔍 [BROADCAST] 更新 Driver Standings: {current_year}")
                    if hasattr(self.main_window.welcome_driver_standings, 'update_year'):
                        self.main_window.welcome_driver_standings.update_year(current_year)
                except Exception as e:
                    logger.debug(f"❌ [BROADCAST] Driver Standings 更新失敗: {e}")
            
            logger.info("[BROADCAST_DEBUG] 調用 on_race_parameters_changed()")
            self.main_window.on_race_parameters_changed()
            logger.info("[BROADCAST_DEBUG] on_race_parameters_changed() 完成")
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("[BROADCAST_DEBUG] 錯誤: %s", exc)
            # 🔴 關鍵修復：移除 exc_info=True 避免 logging 持有 frame chain
            logger.error("Failed to broadcast parameter update: %s", exc)
            exc = None  # 🔴 立即釋放異常對象
