# -*- coding: utf-8 -*-
"""
SubwindowStateCollector - 從 f1t_gui_main.py 提取
"""

from typing import Dict
from typing import Optional

from core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class SubwindowStateCollector:
    """從 f1t_gui_main.py 提取的 _collect_subwindow_state 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _collect_subwindow_state(self, subwindow: 'PopoutSubWindow') -> Optional[Dict[str, Any]]:
        """產生單一子視窗的序列化狀態"""
        if getattr(subwindow, "is_popped_out", False):
            # 目前僅支援還原在 MDI 內的視窗
            return None

        module = getattr(subwindow, "analysis_module", None)
        if module is None:
            return None

        mdi_area = subwindow.mdiArea()
        geometry = subwindow.geometry()
        geometry_state = {
            "x": int(geometry.x()),
            "y": int(geometry.y()),
            "width": int(geometry.width()),
            "height": int(geometry.height()),
        }

        window_state = "normal"
        if subwindow.isMaximized():
            window_state = "maximized"
        elif subwindow.isMinimized():
            window_state = "minimized"

        subwindow_state: Dict[str, Any] = {
            "title": subwindow.windowTitle(),
            "mdi_area": mdi_area.objectName() if mdi_area else None,
            "geometry": geometry_state,
            "window_state": window_state,
            "sync_enabled": bool(getattr(subwindow, "sync_enabled", True)),
            "local_parameters": {
                "year": getattr(subwindow, "local_year", None),
                "race": getattr(subwindow, "local_race", None),
                "session": getattr(subwindow, "local_session", None),
            },
            "module": self.main_window._collect_module_state(module),
        }

        return subwindow_state
