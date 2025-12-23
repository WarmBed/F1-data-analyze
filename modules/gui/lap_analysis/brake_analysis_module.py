"""煞車分析模組封裝
======================

提供 `BrakeAnalysisModule` 類別的向後相容匯入口，讓外部模組可以透過
`modules.gui.lap_analysis.brake_analysis_module` 取得主 GUI 模組實作。

真正的模組邏輯定義在 `brake_analysis.brake_analysis_mdi`，此處僅重新匯出。
"""

from .brake_analysis.brake_analysis_mdi import BrakeAnalysisModule

__all__ = ["BrakeAnalysisModule"]

