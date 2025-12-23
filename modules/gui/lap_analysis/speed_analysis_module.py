"""速度分析模組封裝
=================================

這個模組作為 `modules.gui.lap_analysis.speed_analysis` 套件的友善入口，
提供 `SpeedAnalysisModule` 類別的簡單匯入路徑，確保現有程式碼與測試
可以透過 `modules.gui.lap_analysis.speed_analysis_module` 取得主模組類別。

實際的 GUI 與資料邏輯實現在 `speed_analysis.speed_analysis_mdi` 中，
此檔案僅負責重新匯出對應的類別以維持向後相容性。
"""

from .speed_analysis.speed_analysis_mdi import SpeedAnalysisModule

__all__ = ["SpeedAnalysisModule"]

