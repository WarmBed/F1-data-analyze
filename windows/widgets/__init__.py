# -*- coding: utf-8 -*-
"""
F1T GUI - Windows Widgets Package
================================

此套件包含從 f1t_gui_main.py 提取的獨立 UI 元件。
"""

from windows.widgets.telemetry_chart_widget import TelemetryChartWidget
from windows.widgets.draggable_title_bar import DraggableTitleBar
from windows.widgets.custom_mdi_area import (
    SnapZone,
    MODULE_SIZE_HINTS,
    SnapPreviewOverlay,
    CustomMdiArea
)
from windows.widgets.context_menu_tree_widget import ContextMenuTreeWidget
from windows.widgets.standalone_windows import (
    ResizableStandaloneWindow,
    TabStandaloneWindow
)
from windows.widgets.popout_subwindow import PopoutSubWindow

__all__ = [
    'TelemetryChartWidget',
    'DraggableTitleBar',
    'SnapZone',
    'MODULE_SIZE_HINTS',
    'SnapPreviewOverlay',
    'CustomMdiArea', 
    'ContextMenuTreeWidget',
    'ResizableStandaloneWindow',
    'TabStandaloneWindow',
    'PopoutSubWindow',
]
