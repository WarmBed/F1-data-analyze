# -*- coding: utf-8 -*-
"""
SingleWindowRestorer - 從 f1t_gui_main.py 提取
"""

from typing import Dict

from core.logger import get_logger
from typing import Any

logger = get_logger(__name__)


class SingleWindowRestorer:
    """從 f1t_gui_main.py 提取的 _restore_single_window 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _restore_single_window(self, window_state: Dict[str, Any]) -> None:
        """根據快照資訊重建單一分析視窗"""
        if not isinstance(window_state, dict):
            return

        module_state = window_state.get("module")
        analysis_module = self.main_window._instantiate_module_from_state(module_state)
        if not analysis_module:
            return

        mdi_area = self.main_window._find_mdi_area_by_name(window_state.get("mdi_area"))
        if mdi_area is None and getattr(self, "mdi_areas", None):
            mdi_area = self.main_window.mdi_areas[0]
        if mdi_area is None:
            return

        sync_enabled = bool(window_state.get("sync_enabled", True))
        window_title = window_state.get("title")
        if not window_title and hasattr(analysis_module, "display_name"):
            window_title = getattr(analysis_module, "display_name")
        if not window_title:
            window_title = "Analysis Window"

        sub_window = PopoutSubWindow(window_title, mdi_area, analysis_module, sync_enabled=sync_enabled)
        content_widget = analysis_module.get_widget()
        sub_window.setWidget(content_widget)
        mdi_area.addSubWindow(sub_window)

        geometry = window_state.get("geometry") or {}
        try:
            width = int(geometry.get("width")) if geometry.get("width") is not None else None
            height = int(geometry.get("height")) if geometry.get("height") is not None else None
            pos_x = int(geometry.get("x")) if geometry.get("x") is not None else None
            pos_y = int(geometry.get("y")) if geometry.get("y") is not None else None
        except (TypeError, ValueError):  # noqa: BLE001
            width = height = pos_x = pos_y = None

        if width and height:
            sub_window.resize(width, height)

        if hasattr(sub_window, 'title_bar'):
            sub_window.title_bar.sync_btn.setChecked(sync_enabled)
            sub_window.toggle_x_sync()

        local_params = window_state.get("local_parameters") or {}
        if local_params.get("year") is not None:
            sub_window.local_year = str(local_params.get("year"))
        if local_params.get("race") is not None:
            sub_window.local_race = local_params.get("race")
        if local_params.get("session") is not None:
            sub_window.local_session = local_params.get("session")

        module_params = module_state.get("parameters") if isinstance(module_state, dict) else None
        self.main_window._apply_module_parameters(analysis_module, module_params)

        sub_window.update_window_title()
        sub_window.show()

        window_state_flag = window_state.get("window_state")
        if window_state_flag == "maximized":
            sub_window.showMaximized()
        elif window_state_flag == "minimized":
            sub_window.showMinimized()
        else:
            if pos_x is not None and pos_y is not None:
                sub_window.move(pos_x, pos_y)

        if hasattr(self, "active_subwindows"):
            self.main_window.active_subwindows.append(sub_window)
