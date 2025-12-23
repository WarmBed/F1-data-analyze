"""油門分析模組封裝
======================

重新匯出 `ThrottleAnalysisModule` 以維持既有匯入路徑，實際功能定義於
`Throttle_analysis.throttle_analysis_mdi` 模組中。
"""

from .Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule

__all__ = ["ThrottleAnalysisModule"]

