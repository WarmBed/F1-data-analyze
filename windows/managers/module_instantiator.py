# -*- coding: utf-8 -*-
"""
ModuleInstantiator - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import Dict, Optional, Any
from windows.workers.cli_workers import MainWindowParameterProvider
import importlib

logger = get_logger(__name__)


class ModuleInstantiator:
    """從 f1t_gui_main.py 提取的 _instantiate_module_from_state 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _instantiate_module_from_state(self, module_state: Optional[Dict[str, Any]]):
        """依據快照資訊建立分析模組實例"""
        if not isinstance(module_state, dict):
            return None

        module = None
        module_type = module_state.get("factory_type")

        if module_type:
            module = self.main_window._create_analysis_module(module_type, module_type_hint=module_type)

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
