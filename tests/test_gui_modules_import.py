"""Import smoke tests for GUI core modules."""

from __future__ import annotations

import importlib

import pytest


GUI_MODULE_IMPORTS = [
    "modules.gui.base.universal_analysis_mdi_base",
    "modules.gui.lap_analysis.speed_analysis_module",
    "modules.gui.lap_analysis.brake_analysis_module",
    "modules.gui.lap_analysis.throttle_analysis_module",
    "modules.gui.shared.season_calendar_provider",
    "modules.gui.themes.color_palette_provider",
    "windows.workers.local_task_worker",
]


@pytest.mark.parametrize("module_name", GUI_MODULE_IMPORTS)
def test_gui_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None
