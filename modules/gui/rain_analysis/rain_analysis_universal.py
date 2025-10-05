"""降雨分析模組封裝
======================

為了維持與舊版程式碼的相容性，提供 `RainAnalysisModule` 的快捷匯入點。
實際實作位於 `rain_analysis_module.RainAnalysisModule`，此處僅重新匯出
該類別，讓外部模組仍可透過 `rain_analysis_universal` 取得主模組。
"""

from .rain_analysis_module import RainAnalysisModule

__all__ = ["RainAnalysisModule"]

