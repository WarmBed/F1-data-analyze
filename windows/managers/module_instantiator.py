# -*- coding: utf-8 -*-
"""
ModuleInstantiator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import Dict, Optional, Any
from windows.workers.cli_workers import MainWindowParameterProvider
import importlib

logger = get_logger(__name__)

# Live Timing 模組類型列表 (用於識別)
LIVE_TIMING_MODULE_TYPES = {
    'pedal_behavior_live',
    'live_traffic_timeline',
    'track_map',
    'circle_map',
    'live_ranking',
    'tyre_strategy',
    'driver_strategy',
    'lap_distribution',
    'race_control_messages',
    'speed_trace',
    'track_weather',
    'pit_window',
    'chase_strategy',
    'lap_history_lap_time',
    'throttle_history',
    'top_speed_history',
}


class ModuleInstantiator:
    """從 f1t_gui_main.py 提取的 _instantiate_module_from_state 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _instantiate_module_from_state(self, module_state: Optional[Dict[str, Any]]):
        """依據快照資訊建立分析模組實例"""
        if not isinstance(module_state, dict):
            return None

        module = None
        
        # 優先使用 factory_type，其次使用 analysis_type
        module_type = module_state.get("factory_type")
        analysis_type = module_state.get("analysis_type")
        module_name = module_state.get("module_name")
        
        # ✅ 檢查是否為 Live Timing 模組 (2025-01-13)
        is_live_timing = (
            (analysis_type and analysis_type in LIVE_TIMING_MODULE_TYPES) or
            (module_type and module_type in LIVE_TIMING_MODULE_TYPES) or
            (module_name and module_name in LIVE_TIMING_MODULE_TYPES)
        )
        
        if is_live_timing:
            # Live Timing 模組使用專門的工廠創建
            live_timing_key = analysis_type or module_type or module_name
            logger.debug(f"[MODULE_INSTANTIATOR] 識別為 Live Timing 模組: {live_timing_key}")
            module = self._create_live_timing_module(live_timing_key)
            if module:
                return module
        
        # 嘗試使用 factory_type 創建
        if module_type:
            logger.debug(f"[MODULE_INSTANTIATOR] 嘗試使用 factory_type 創建模組: {module_type}")
            module = self.main_window._create_analysis_module(module_type, module_type_hint=module_type)
        
        # 如果 factory_type 失敗，嘗試使用 analysis_type
        if module is None and analysis_type and analysis_type != module_type:
            logger.debug(f"[MODULE_INSTANTIATOR] factory_type 失敗，嘗試使用 analysis_type: {analysis_type}")
            module = self.main_window._create_analysis_module(analysis_type, module_type_hint=analysis_type)

        if module is None:
            module_path = module_state.get("module_path")
            class_name = module_state.get("class_name")
            if module_path and class_name:
                try:
                    module_cls = getattr(importlib.import_module(module_path), class_name)
                    module = module_cls()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to import module %s.%s: %s", module_path, class_name, exc)
                    module = None

            if module and hasattr(module, "parameter_provider"):
                module.parameter_provider = MainWindowParameterProvider(self.main_window)
                initialize_module = getattr(module, "initialize_module", None)
                if callable(initialize_module):
                    try:
                        initialize_module()
                    except Exception as exc:  # noqa: BLE001
                        logger.warning("Module initialization failed: %s", exc)

        if module and module_type and not getattr(module, "_factory_module_type", None):
            setattr(module, "_factory_module_type", module_type)

        return module

    def _create_live_timing_module(self, module_key: str):
        """
        使用 LiveTimingModuleFactory 創建 Live Timing 模組
        
        Args:
            module_key: 模組識別鍵 (如 'pedal_behavior_live', 'live_traffic_timeline')
        
        Returns:
            模組實例或 None
        """
        try:
            from modules.gui.live_timing import LiveTimingModuleFactory
            
            factory = LiveTimingModuleFactory.get_instance()
            
            # 將 analysis_type 轉換為 factory 識別的模組名稱
            # LiveTimingModuleFactory 使用顯示名稱或特定的 key
            module_name_map = {
                'pedal_behavior_live': 'Pedal Behavior',
                'live_traffic_timeline': 'Traffic Timeline',
                'track_map': 'Track Map',
                'circle_map': 'Circle Map',
                'live_ranking': 'Ranking Tower',
                'tyre_strategy': 'Tyre Strategy',
                'driver_strategy': 'Driver Strategy',
                'lap_distribution': 'Lap Time Distribution',
                'race_control_messages': 'Race Control Messages',
                'speed_trace': 'Speed Trace',
                'track_weather': 'Track & Weather',
                'pit_window': 'Pit Window',
                'chase_strategy': 'Chase Strategy',
                'lap_history_lap_time': 'Lap History - Lap Time',
                'throttle_history': 'Throttle 95% History',
                'top_speed_history': 'Top Speed History',
            }
            
            display_name = module_name_map.get(module_key, module_key)
            logger.debug(f"[MODULE_INSTANTIATOR] 創建 Live Timing 模組: key={module_key}, display_name={display_name}")
            
            # 檢查模組是否已實現
            if not factory.is_implemented(display_name):
                logger.warning(f"[MODULE_INSTANTIATOR] Live Timing 模組未實現: {display_name}")
                return None
            
            # 創建模組實例
            module = factory.create_module(display_name, self.main_window)
            if module:
                logger.debug(f"[MODULE_INSTANTIATOR] Live Timing 模組創建成功: {display_name}")
                # 設置 factory type
                setattr(module, "_factory_module_type", module_key)
            return module
            
        except Exception as e:
            logger.exception(f"[MODULE_INSTANTIATOR] 創建 Live Timing 模組失敗: {module_key}, error={e}")
            return None
