"""
Windows Managers Package

此套件包含從 f1t_gui_main.py 中拆分出來的管理器類別。
每個管理器負責單一職責，遵循 SOLID 原則。

管理器列表：
- LiveTimingManager: Live Timing 模組管理 (Phase 1) ✅
- TabManager: 分頁管理 (Phase 2) ✅
- MDIManager: MDI 視窗管理 (Phase 3) ✅
- ParameterSyncManager: 參數同步管理 (Phase 4.1) ✅
- LapAnalysisManager: 圈速分析管理 (Phase 4.3) ✅
- PopoutChartUpdater: 圖表更新處理器 (Phase 5.1) ✅
- PopoutCliHandler: CLI 分析處理器 (Phase 5.2) ✅
- PopoutResizeHandler: 視窗調整大小處理器 (Phase 5.3) ✅
- DriverLapSettingsHelper: 車手與圈數設定輔助類別 (Phase 5.4.1) ✅
- DialogSeasonHelper: 對話框季節日曆輔助類別 (Phase 5.4.2) ✅
"""

from .live_timing_manager import LiveTimingManager
from .tab_manager import TabManager
from .mdi_manager import MDIManager
from .parameter_sync_manager import ParameterSyncManager
from .lap_analysis_manager import LapAnalysisManager
from .popout_chart_updater import PopoutChartUpdater
from .popout_cli_handler import PopoutCliHandler
from .popout_resize_handler import PopoutResizeHandler
from .driver_lap_settings_helper import DriverLapSettingsHelper
from .dialog_season_helper import DialogSeasonHelper

__all__ = [
    'LiveTimingManager',
    'TabManager',
    'MDIManager',
    'ParameterSyncManager',
    'LapAnalysisManager',
    'PopoutChartUpdater',
    'PopoutCliHandler',
    'PopoutResizeHandler',
    'DriverLapSettingsHelper',
    'DialogSeasonHelper',
]
