# -*- coding: utf-8 -*-
"""
ModuleStateCollector - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import Dict
from typing import Optional

from core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class ModuleStateCollector:
    """從 f1t_gui_main.py 提取的 _collect_module_state 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _collect_module_state(self, module) -> Optional[Dict[str, Any]]:
        """收集分析模組狀態，便於日後重新建立"""
        try:
            module_state: Dict[str, Any] = {
                "module_path": module.__class__.__module__,
                "class_name": module.__class__.__name__,
            }

            factory_type = getattr(module, "_factory_module_type", None)
            if factory_type:
                module_state["factory_type"] = factory_type

            analysis_type = getattr(module, "analysis_type", None)
            if analysis_type:
                module_state["analysis_type"] = analysis_type

            display_name = getattr(module, "display_name", None)
            if display_name:
                module_state["display_name"] = display_name

            module_name = getattr(module, "module_name", None)
            if module_name:
                module_state["module_name"] = module_name

            parameters: Dict[str, Any] = {}
            for attr in ("current_year", "current_race", "current_session", "driver1", "driver2", "lap1", "lap2"):
                if hasattr(module, attr):
                    value = getattr(module, attr)
                    if value is not None:
                        parameters[attr] = value

            if parameters:
                module_state["parameters"] = parameters

            return module_state
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to collect module state: %s", exc)
            return None
