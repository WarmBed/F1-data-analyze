# -*- coding: utf-8 -*-
"""
ModuleParamsApplier - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger
from typing import Dict
from typing import Optional

from core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class ModuleParamsApplier:
    """從 f1t_gui_main.py 提取的 _apply_module_parameters 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _apply_module_parameters(self, module, parameters: Optional[Dict[str, Any]]) -> None:
        """將快照中的參數套用到分析模組"""
        if not module or not isinstance(parameters, dict):
            return

        year_value = parameters.get("current_year") or parameters.get("year")
        race_value = parameters.get("current_race") or parameters.get("race")
        session_value = parameters.get("current_session") or parameters.get("session")

        update_kwargs: Dict[str, Any] = {}
        if year_value is not None:
            try:
                update_kwargs["year"] = int(year_value)
            except (TypeError, ValueError):  # noqa: BLE001
                update_kwargs["year"] = year_value
        if race_value is not None:
            update_kwargs["race"] = race_value
        if session_value is not None:
            update_kwargs["session"] = session_value

        update_parameters = getattr(module, "update_parameters", None)
        if callable(update_parameters) and update_kwargs:
            try:
                update_parameters(**update_kwargs)
            except TypeError:
                try:
                    update_parameters(
                        update_kwargs.get("year"),
                        update_kwargs.get("race"),
                        update_kwargs.get("session"),
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Module parameter update failed: %s", exc)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Module parameter update failed: %s", exc)

        for attr in ("driver1", "driver2", "lap1", "lap2"):
            if attr in parameters and hasattr(module, attr):
                try:
                    setattr(module, attr, parameters[attr])
                except Exception as exc:  # noqa: BLE001
                    logger.debug("Unable to set module attribute %s: %s", attr, exc)

        load_data = getattr(module, "load_data", None)
        if callable(load_data):
            load_kwargs = {k: v for k, v in update_kwargs.items() if v is not None}
            for attr in ("driver1", "driver2", "lap1", "lap2"):
                if attr in parameters and parameters[attr] is not None:
                    load_kwargs[attr] = parameters[attr]
            try:
                load_data(**load_kwargs)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Module data load skipped: %s", exc)
