"""Throttle Line Chart (Single Driver) 模組套件匯出。

在組件尚未完整實作前，允許部分導入失敗而不中止套件載入，
以便撰寫與執行單獨元件的測試（例如資料載入器）。
"""

import importlib
from typing import Optional

from .throttle_line_chart_data_loader import ThrottleLineChartDataLoader


def _optional_import(module_name: str, symbol: str) -> Optional[object]:  # pragma: no cover - 動態匯入供快速測試
    try:
        module = importlib.import_module(module_name, package=__name__)
        return getattr(module, symbol, None)
    except Exception:
        return None


ThrottleLineChartMDI = _optional_import(".throttle_line_chart_mdi", "ThrottleLineChartMDI")
ThrottleLineChartModule = _optional_import(".throttle_line_chart_module", "ThrottleLineChartModule")
create_throttle_line_chart_module = _optional_import(
    ".throttle_line_chart_module", "create_throttle_line_chart_module"
)

__all__ = ["ThrottleLineChartDataLoader"]
if ThrottleLineChartMDI is not None:
    __all__.append("ThrottleLineChartMDI")
if ThrottleLineChartModule is not None:
    __all__.extend(["ThrottleLineChartModule", "create_throttle_line_chart_module"])
