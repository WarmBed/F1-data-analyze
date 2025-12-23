"""溫度分析模組封裝
======================

為了維持與舊版程式碼的相容性，提供 `TempAnalysisModule` 的快捷匯入點。
實際實作位於 `temp_analysis_module.TempAnalysisModule`，此處僅重新匯出
該類別，讓外部模組仍可透過 `temp_analysis_universal` 取得主模組。
"""

from .temp_analysis_module import TempAnalysisModule

__all__ = ["TempAnalysisModule"]

