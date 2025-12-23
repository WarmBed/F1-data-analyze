#!/usr/bin/env python3
"""
F1T GUI 主程式 - 專業賽車分析工作站
F1T GUI Main - Professional Racing Analysis Workstation
集成的F1分析GUI系統，提供完整的賽車數據分析功能
"""

# ========== 強制 UTF-8 編碼（最優先設定，必須在任何 print 之前）==========
# 這段代碼必須在所有其他 import 之前執行
import sys
import io
import os

class _NullWriter:
    """靜默輸出器，永不關閉，避免 I/O operation on closed file"""
    def write(self, text):
        pass
    def flush(self):
        pass
    def close(self):
        pass  # 永不真正關閉
    def isatty(self):
        return False
    @property
    def closed(self):
        return False  # 永遠回報未關閉
    @property
    def encoding(self):
        return 'utf-8'  # 返回 UTF-8 編碼避免 AttributeError
    @property
    def errors(self):
        return 'replace'  # 錯誤處理策略

def _setup_safe_stdout():
    """
    設定安全的 stdout/stderr，處理以下情況：
    1. PyInstaller GUI 模式 (console=False): sys.stdout 可能是 None
    2. 被重定向的情況: 確保不會崩潰
    
    注意：UTF-8 編碼由環境變數 PYTHONIOENCODING=utf-8 設定（在 tasks.json 中）
    不再使用 TextIOWrapper 包裝，避免 closed file 問題
    """
    # 情況 1: PyInstaller GUI 模式，stdout/stderr 是 None
    if sys.stdout is None or sys.stderr is None:
        sys.stdout = _NullWriter()
        sys.stderr = _NullWriter()
        return
    
    # 情況 2: 測試 stdout 是否正常運作
    try:
        sys.stdout.write('')
        sys.stdout.flush()
    except Exception:
        sys.stdout = _NullWriter()
        sys.stderr = _NullWriter()

# 立即執行
_setup_safe_stdout()

import math
import time
import warnings

# ========== 抑制執行緒清理時的無害警告 ==========
# 抑制 Python 3.13+ 在解釋器關閉時的 DummyThread 警告
# 這些警告是無害的，發生在程序正常關閉時
warnings.filterwarnings('ignore', category=RuntimeWarning, module='threading')

# 重定向 stderr 以抑制 __del__ 方法中的異常（僅在程序關閉時）
import threading
original_threading_excepthook = threading.excepthook

def silent_threading_excepthook(args):
    """靜默執行緒異常處理，僅在關閉時抑制 DummyThread 錯誤"""
    # 僅抑制 _DeleteDummyThreadOnDel 的 TypeError
    if args.exc_type == TypeError and '_DeleteDummyThreadOnDel' in str(args.exc_traceback):
        return  # 靜默處理
    # 其他異常正常輸出
    original_threading_excepthook(args)

threading.excepthook = silent_threading_excepthook

from functools import partial
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QComboBox, QCheckBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QMdiArea, QMdiSubWindow, QTableWidget, QTableWidgetItem,
    QSplitter, QLineEdit, QStatusBar, QLabel, QProgressBar, QGroupBox,
    QFrame, QToolBar, QAction, QMenuBar, QMenu, QGridLayout, QLCDNumber,
    QTextEdit, QScrollArea, QHeaderView, QDialog, QDialogButtonBox, QMessageBox,
    QListWidget, QListWidgetItem, QSpinBox, QSizePolicy, QFileDialog, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QPoint, QObject, QRect, QThread
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPainter, QPen, QBrush, QMouseEvent
import json
import datetime
import traceback
import subprocess
import importlib
from pathlib import Path
from enum import Enum, auto

# ✅ 導入集中管理的版本號
from config.version import APP_VERSION, APP_FULL_TITLE
from typing import Any, Dict, List, Optional
import requests

import core.dependency_guard  # noqa: F401  # 確保可選依賴存在

from core.logger import setup_logging, get_logger

# 🔧 日誌系統配置：
# - 開發模式 (Python): level="INFO" (詳細日誌)
# - EXE 模式 (PyInstaller): level="INFO" (預設啟用日誌，方便除錯)
#   * 可設置環境變數 F1T_EXE_DISABLE_LOG=1 來禁用 EXE 日誌（節省效能）
# - console_level=None : 已停用終端機輸出（在 logger.py 中移除 console handler）
# - 日誌檔案：logs/f1_gui_YYYY-MM-DD.log（依日期自動切換，保留 30 天）

# 檢測是否為 PyInstaller 打包的 EXE
IS_EXE_MODE = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
LOG_LEVEL = "INFO"  # 統一使用 INFO 級別（開發模式和 EXE 模式）

# ✅ EXE 模式：設定 SSL 證書路徑（API HTTPS 請求必須）
if IS_EXE_MODE:
    import certifi
    # 優先使用打包的證書，否則用 certifi 內建證書
    bundled_cert = os.path.join(sys._MEIPASS, 'certifi', 'cacert.pem')
    if os.path.exists(bundled_cert):
        os.environ['REQUESTS_CA_BUNDLE'] = bundled_cert
        os.environ['SSL_CERT_FILE'] = bundled_cert
    else:
        os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
        os.environ['SSL_CERT_FILE'] = certifi.where()

def get_resource_path(relative_path):
    """獲取資源文件的絕對路徑（支援 EXE 模式）
    
    在開發模式下，返回相對於專案根目錄的路徑
    在 EXE 模式下，返回 PyInstaller 打包的臨時目錄路徑
    """
    if IS_EXE_MODE:
        # EXE 模式：使用 PyInstaller 的臨時資源目錄
        base_path = Path(sys._MEIPASS)
    else:
        # 開發模式：使用當前工作目錄
        base_path = Path.cwd()
    
    return base_path / relative_path

setup_logging(component="gui", level=LOG_LEVEL, console_level=None)
logger = get_logger("main", component="gui")
logger.info(f"F1T GUI 控制台初始化完成 - 日誌系統已啟用 ({LOG_LEVEL} level, {'EXE 模式' if IS_EXE_MODE else '開發模式'})")

# 導入連動管理器
from modules.gui.lap_analysis.linkage import linkage_manager

# 導入 GUI 國際化模組
from core.api_base_url import resolve_api_base_url
from core.gui_i18n import tr, set_gui_language, get_gui_language, get_telemetry_option_text
from core.gui_help_catalog import get_gui_help_message
from core.gui_settings_manager import gui_settings_manager
from core.runtime_status_resolver import (
    RuntimeStatusResolver,
    RuntimeStatusState,
    RuntimeStatusView,
)
from core.api_runtime_state import (
    clear_pending_update,
    set_pending_update,
    update_health_state,
    update_runtime_view,
)
from modules.gui.shared.season_calendar_provider import (
    SeasonCalendarError,
    SeasonCalendarProvider,
    SeasonEvent,
)
from modules.gui.themes import ColorPaletteError, color_palette_provider

# ========== 從 windows 套件導入已提取的類別 ==========
from windows.widgets import (
    TelemetryChartWidget,
    DraggableTitleBar,
    SnapZone,
    MODULE_SIZE_HINTS,
    SnapPreviewOverlay,
    CustomMdiArea,
    ContextMenuTreeWidget,
    ResizableStandaloneWindow,
    TabStandaloneWindow,
    PopoutSubWindow,
)
from windows.workers import (
    CliAnalysisWorker,
    CliAnalysisManager,
    MainWindowParameterProvider,
    cli_analysis_manager,
    ApiHealthWorker,
    ApiRuntimeWorker,
)
from windows.dialogs import WindowSettingsDialog, LapAnalysisOptionsDialog
from windows.managers.signal_manager import GlobalSignalManager, global_signals


def select_preferred_event(
    completed_events: List[SeasonEvent],
    upcoming_events: List[SeasonEvent],
) -> Optional[SeasonEvent]:
    """Return the preferred event for default selection.

    Prioritise the most recent completed race and fall back to the next
    upcoming race when no completed race is available.
    """

    if completed_events:
        return completed_events[-1]
    if upcoming_events:
        return upcoming_events[0]
    return None


# ========== 以下類別已提取到 windows/ 套件 ==========
# SnapZone, SnapPreviewOverlay, CustomMdiArea → windows/widgets/custom_mdi_area.py
# TelemetryChartWidget → windows/widgets/telemetry_chart_widget.py  
# DraggableTitleBar → windows/widgets/draggable_title_bar.py
# ContextMenuTreeWidget → windows/widgets/context_menu_tree_widget.py
# ResizableStandaloneWindow, TabStandaloneWindow → windows/widgets/standalone_windows.py
# CliAnalysisWorker, CliAnalysisManager, MainWindowParameterProvider → windows/workers/cli_workers.py
# GlobalSignalManager, global_signals → windows/managers/signal_manager.py
# ApiHealthWorker, ApiRuntimeWorker → windows/workers/api_workers.py

# ========== SnapZone, SnapPreviewOverlay, CustomMdiArea 已移至 windows/widgets/custom_mdi_area.py ==========
# ========== CliAnalysisWorker, CliAnalysisManager, GlobalSignalManager 已移至 windows/workers/ ==========
# ========== 舊類別定義已移除，現使用 import 版本 ==========


# 以下類別已通過 import 導入，舊定義已移除:
# - CliAnalysisWorker → windows/workers/cli_workers.py
# - CliAnalysisManager → windows/workers/cli_workers.py
# - GlobalSignalManager, global_signals → windows/managers/signal_manager.py


# ========== 舊類別定義已完全移除，使用 windows/ 模組的 import 版本 ==========

# ========== 以下類別已移除，使用 import 版本 ==========
# CliAnalysisWorker  windows/workers/cli_workers.py
# GlobalSignalManager  windows/managers/signal_manager.py
# CliAnalysisManager  windows/workers/cli_workers.py
# MainWindowParameterProvider  windows/workers/cli_workers.py
# cli_analysis_manager 實例  windows/workers/cli_workers.py

# ========== LapAnalysisOptionsDialog 已移至 windows/dialogs/lap_analysis_options_dialog.py ==========

# ========== TelemetryChartWidget 已移至 windows/widgets/telemetry_chart_widget.py ==========
# ========== DraggableTitleBar 已移至 windows/widgets/draggable_title_bar.py ==========

# ========== PopoutSubWindow 已移至 windows/widgets/popout_subwindow.py ==========

# ========== WindowSettingsDialog 已移至 windows/dialogs/window_settings_dialog.py ==========

class StyleHMainWindow(QMainWindow):
    """風格H: 專業賽車分析工作站主視窗"""
    
    def __init__(self, progress_callback=None):
        """
        初始化主視窗
        
        Args:
            progress_callback: 可選的進度回調函數
                              簽名: callback(progress: int, message: str)
                              - progress: 0-100 的整數
                              - message: 當前階段描述
        """
        super().__init__()
        
        # 0% - 開始初始化
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(0, tr('splash_initializing'))
        logger.debug("[INIT] 🚀 開始初始化 F1 TelemetryStation Pro 主視窗...")
        # API health monitor attributes
        self.ready_label = None
        self.api_status_label = None
        self.time_label = None
        self.api_health_timer = None
        self._api_health_worker = None
        self._api_health_worker_active = False
        self._api_last_state = "unknown"
        self._api_status_details = []
        self._api_health_manual_request = False
        self.api_mode_enabled = False
        self.api_base_url = None
        self.check_api_action = None
        self.cli_status_label = None
        self.api_runtime_timer = None
        self._api_runtime_worker = None
        self._api_runtime_worker_active = False
        self._runtime_status_resolver = RuntimeStatusResolver()
        self._last_cli_status_signature = None
        self._parameter_broadcast_timer = QTimer(self)
        self._parameter_broadcast_timer.setSingleShot(True)
        self._parameter_broadcast_timer.setInterval(350)
        self._parameter_broadcast_timer.timeout.connect(self._broadcast_pending_parameters)
        self._pending_parameter_payload: Optional[Dict[str, Any]] = None

        
        # GUI 語言會自動從設定檔載入，不需要強制設定
        # set_gui_language('en')  # 已移除強制設定
        
        self.setWindowTitle(APP_FULL_TITLE)  # ✅ 使用集中管理的版本號
        
        # 設定應用程式圖示（視窗左上角） - 支援 EXE 模式
        icon_path = get_resource_path(Path("image") / "logo.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))
            logger.debug(f"[INIT] ✅ 視窗圖示已設定: {icon_path}")
        else:
            logger.debug(f"[INIT] ⚠️  找不到圖示檔案: {icon_path}")
            logger.debug(f"[INIT]    EXE 模式: {IS_EXE_MODE}, 基礎路徑: {Path(sys._MEIPASS) if IS_EXE_MODE else Path.cwd()}")
        
        # 10% - 視窗標題設定完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(10, tr('splash_loading_window'))
        logger.debug("[INIT] ✅ 視窗標題已設定")
        # self.setMinimumSize(1600, 900) - 主視窗尺寸限制已移除
        
        # 初始化分析追蹤屬性
        self.active_analysis_tabs = []
        logger.debug("[INIT] ✅ 分析追蹤屬性已初始化")
        
        # 初始化子視窗追蹤列表
        self.active_subwindows = []
        logger.debug("[INIT] ✅ 子視窗追蹤列表已初始化")
        
        # 初始化MDI區域引用（用於同步功能）
        self.mdi_areas = []  # 存儲所有MDI區域的引用
        logger.debug("[INIT] ✅ MDI區域引用已初始化")

        # 初始化彈出分頁追蹤字典
        self.popped_out_tabs = {}  # {tab_index: {'standalone_window': window, 'original_widget': widget, 'tab_name': name}}
        logger.debug("[INIT] ✅ 彈出分頁追蹤字典已初始化")

        # 工作區快照紀錄
        self._last_workspace_path: Optional[str] = None
        logger.debug("[INIT] ✅ 工作區儲存紀錄已初始化")
        
        # Workspace Manager 初始化
        from core.workspace_database import WorkspaceDatabase
        from core.workspace_serializer import WorkspaceSerializer
        workspace_db_path = Path("workspaces") / "f1t_workspaces.db"
        self.workspace_db = WorkspaceDatabase(str(workspace_db_path))
        self.workspace_serializer = WorkspaceSerializer(main_window=self)
        logger.debug("[INIT] ✅ Workspace Manager 已初始化")
        
        # 初始化遙測分析狀態追蹤
        self.lap_analysis_active = False  # 是否有遙測分析活動
        self.lap_analysis_windows = set()  # 活動的遙測分析視窗集合
        self.lap_controls_visible = False  # 遙測控件是否可見
        self._lap_controls_added = False  # 追蹤控件是否已添加到工具欄
        
        # ⚠️ 新增：全域共享參數池（所有停用同步的視窗共享）
        # 當用戶取消勾選"與主視窗同步車手與圈數"時，所有停用同步的視窗將使用此參數池
        self.shared_independent_params = {
            'year1': None,           # 車手 1 年份
            'race1': None,           # 車手 1 賽事
            'session1': None,        # 車手 1 賽段
            'driver1': None,         # 車手 1 代號
            'lap1': None,            # 車手 1 圈數
            'year2': None,           # 車手 2 年份
            'race2': None,           # 車手 2 賽事
            'session2': None,        # 車手 2 賽段
            'driver2': None,         # 車手 2 代號
            'lap2': None,            # 車手 2 圈數
            'use_time_axis': False   # 時間軸模式
        }
        logger.debug("[INIT] ✅ 全域共享參數池已初始化（用於跨模組停用同步功能）")
        
        # 🆕 車手列表快取機制（啟動時載入，全域共享）
        self._cached_drivers_by_year = {}  # {year: [driver_codes]}
        logger.debug("[INIT] ✅ 車手列表快取已初始化")
        
        # 20% - 追蹤屬性初始化完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(20, tr('splash_loading_state'))
        logger.debug("[INIT] ✅ 遙測分析狀態追蹤已初始化")

        # F1TV 認證管理器
        from core.f1tv_auth import F1TVAuthManager
        self.f1tv_auth_manager = F1TVAuthManager(self)
        self.f1tv_auth_manager.auth_success.connect(self._on_f1tv_auth_success)
        self.f1tv_auth_manager.auth_failed.connect(self._on_f1tv_auth_failed)
        self.f1tv_auth_manager.auth_state_changed.connect(self._on_f1tv_auth_state_changed)
        self.f1tv_status_label = None  # 將在狀態列中初始化
        logger.debug("[INIT] ✅ F1TV 認證管理器已初始化")
        
        # 賽季日曆支援
        self._season_provider = SeasonCalendarProvider()
        self._season_events_cache: Dict[int, List[SeasonEvent]] = {}
        self._season_error_message: Optional[str] = None
        self._race_event_lookup: Dict[str, SeasonEvent] = {}
        self._display_to_race_key: Dict[str, str] = {}
        self._fastf1_overrides: Dict[str, str] = {
            "Great Britain": "British",
            "United States": "United States",
            "Emilia Romagna": "Emilia Romagna",
            "Saudi Arabia": "Saudi Arabia",
            "Las Vegas": "Las Vegas",
            "Abu Dhabi": "Abu Dhabi",
        }
        
        # 30% - 賽季日曆初始化完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(30, tr('splash_loading_calendar'))
        
        self._color_palette_provider = color_palette_provider
        self._initialize_color_palette()
        
        # 40% - 顏色配置載入完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(40, tr('splash_loading_colors'))

        # 🆕 初始化 Live Timing 管理器 (Phase 1 重構)
        # 必須在 init_ui() 之前初始化，因為 create_professional_menubar() 會使用它
        from windows.managers import LiveTimingManager, TabManager, MDIManager, ParameterSyncManager, LapAnalysisManager
        self.live_timing_manager = LiveTimingManager(self)
        logger.debug("[INIT] ✅ LiveTimingManager 已初始化")
        
        # 🆕 初始化 Tab 管理器 (Phase 2 重構)
        self.tab_manager = TabManager(self)
        logger.debug("[INIT] ✅ TabManager 已初始化")
        
        # 🆕 初始化 MDI 管理器 (Phase 3 重構)
        self.mdi_manager = MDIManager(self)
        logger.debug("[INIT] ✅ MDIManager 已初始化")
        
        # 🆕 初始化參數同步管理器 (Phase 4.1 重構)
        self.param_sync_manager = ParameterSyncManager(self)
        logger.debug("[INIT] ✅ ParameterSyncManager 已初始化")
        
        # 🆕 初始化圈速分析管理器 (Phase 4.3 重構)
        self.lap_analysis_manager = LapAnalysisManager(self)
        logger.debug("[INIT] ✅ LapAnalysisManager 已初始化")

        logger.debug("[INIT] 🔧 開始初始化用戶界面...")
        self.init_ui()
        
        # 55% - UI 初始化完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(55, tr('splash_loading_ui'))
        
        logger.debug("[INIT] 🎨 開始應用樣式...")
        self.apply_style_h()
        
        # 70% - 樣式應用完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(70, tr('splash_applying_style'))
        
        # 整合連動管理器
        logger.debug("[INIT] 🔗 開始整合連動管理器...")
        self.integrate_linkage_manager()
        
        # 85% - 連動管理器整合完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(85, tr('splash_setup_linkage'))
        logger.debug("[INIT] ✅ 連動管理器整合完成")
        
        logger.debug("[INIT] [API] Initialising health monitor...")
        self.setup_api_health_monitor()
        logger.debug("[INIT] [API] Health monitor active")

        # 90% - API 監控設定完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(90, tr('splash_setup_api'))
        
        # 🆕 預載入當前年份車手列表（啟動時快取）
        logger.debug("[INIT] 🏎️ 開始預載入車手列表...")
        if progress_callback:
            progress_callback(95, "Loading driver list...")
        
        current_year = datetime.datetime.now().year
        drivers = self.get_drivers_for_year(current_year)
        logger.debug(f"[INIT] ✅ 車手列表預載入完成 ({len(drivers)} 位車手)")
        
        # 100% - 初始化完成
        if progress_callback:
            from core.gui_i18n import tr
            progress_callback(100, tr('splash_complete'))
        logger.debug("[INIT] ✅ 主視窗初始化完成！")
        
        # 延遲檢查標籤欄隱藏狀態和圈速控件狀態
        logger.debug("[INIT] ⏰ 設置延遲檢查機制 (1秒後執行)...")
        
        # 設置延遲檢查機制，確保標籤隱藏狀態正確
        QTimer.singleShot(1000, self.check_and_hide_tabs)
        
        # 延遲檢查遙測分析控件狀態 (2秒後執行，確保所有視窗都已初始化)
        QTimer.singleShot(2000, self.check_and_show_lap_controls_if_needed)

    def _initialize_color_palette(self, *args, **kwargs):
        """代理方法 - 委派給 ColorPaletteInitializer"""
        from windows.managers.color_palette_initializer import ColorPaletteInitializer
        if not hasattr(self, '_color_palette_initializer'):
            self._color_palette_initializer = ColorPaletteInitializer(self)
        return self._color_palette_initializer._initialize_color_palette(*args, **kwargs)

    def _load_driver_team_mapping_from_standings(self, *args, **kwargs):
        """代理方法 - 委派給 DriverMappingLoader"""
        from windows.managers.driver_mapping_loader import DriverMappingLoader
        if not hasattr(self, '_driver_mapping_loader'):
            self._driver_mapping_loader = DriverMappingLoader(self)
        return self._driver_mapping_loader._load_driver_team_mapping_from_standings(*args, **kwargs)

    def _show_palette_error_message(self, *args, **kwargs):
        """代理方法 - 委派給 PaletteErrorShower"""
        from windows.managers.palette_error_shower import PaletteErrorShower
        if not hasattr(self, '_palette_error_shower'):
            self._palette_error_shower = PaletteErrorShower(self)
        return self._palette_error_shower._show_palette_error_message(*args, **kwargs)

    def init_ui(self, *args, **kwargs):
        """代理方法 - 委派給 UiInitializer"""
        from windows.managers.ui_initializer import UiInitializer
        if not hasattr(self, '_ui_initializer'):
            self._ui_initializer = UiInitializer(self)
        return self._ui_initializer.init_ui(*args, **kwargs)

    def create_professional_menubar(self):
        """創建專業菜單欄"""
        menubar = self.menuBar()
        
        # 檔案菜單
        file_menu = menubar.addMenu(tr('file_menu'))
        file_menu.addAction(tr('save_workspace', 'Save Workspace'), self.save_workspace)
        file_menu.addAction(tr('load_workspace', 'Load Workspace'), self.load_workspace)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        file_menu.addSeparator()
        file_menu.addAction('Exit', self.close)
        
        # 檢視菜單 (已隱藏)
        # view_menu = menubar.addMenu(tr('view_menu'))
        # view_menu.addAction(tr('tile_windows', 'Tile Windows'), self.tile_windows)
        # view_menu.addAction(tr('cascade_windows', 'Cascade Windows'), self.cascade_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('minimize_all_windows', 'Minimize All Windows'), self.minimize_all_windows)
        # view_menu.addAction(tr('maximize_all_windows', 'Maximize All Windows'), self.maximize_all_windows)
        # view_menu.addAction(tr('restore_all_windows', 'Restore All Windows'), self.restore_all_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('close_all_windows', 'Close All Windows'), self.close_all_windows)
        # view_menu.addSeparator()
        # view_menu.addAction(tr('full_screen', 'Full Screen'), self.toggle_fullscreen)
        
        # 分析菜單 (已隱藏)
        # analysis_menu = menubar.addMenu(tr('menu_analysis', 'Analysis'))
        # analysis_menu.addAction(tr('menu_driver_standings', 'Driver Standings'), self.open_driver_standings)
        # analysis_menu.addAction(tr('menu_constructor_standings', 'Constructor Standings'), self.open_constructor_standings)
        # analysis_menu.addSeparator()
        # # Vehicle Parts Changes - 暫時禁用開發中
        # parts_action = analysis_menu.addAction(tr('menu_parts_analysis', 'Vehicle Parts Changes'), self.open_parts_analysis)
        # parts_action.setEnabled(False)  # 禁用
        # parts_action.setStatusTip(tr('parts_analysis_disabled', 'This feature is under development'))
        # analysis_menu.addSeparator()
        # analysis_menu.addAction(tr('menu_season_progress', 'Season Progress'), self.open_season_progress)
        
        # Live Timing 菜單 (使用 LiveTimingManager 重構)
        live_timing_menu = menubar.addMenu(tr('menu_live_timing', 'Live Timing'))
        self.live_timing_manager.setup_menu(live_timing_menu)
        
        # 工具菜單
        tools_menu = menubar.addMenu(tr('tools_menu'))
        tools_menu.addAction(tr('system_settings', 'System Settings'), self.system_settings)
        self.check_api_action = QAction(tr('check_api_status', 'Check API Status'), self)
        self.check_api_action.setStatusTip(tr('check_api_status_tip', 'Run an API health check immediately'))
        self.check_api_action.triggered.connect(self.manual_api_health_check)
        tools_menu.addAction(self.check_api_action)

        tools_menu.addSeparator()
        
        # 語言切換功能
        language_menu = tools_menu.addMenu(tr('language_menu', 'Language'))
        
        # 英文選項
        self.english_action = QAction('🇺🇸 English', self)
        self.english_action.setCheckable(True)
        self.english_action.triggered.connect(lambda: self.set_interface_language('en'))
        language_menu.addAction(self.english_action)
        
        # 中文選項
        self.chinese_action = QAction('🇹🇼 中文', self)
        self.chinese_action.setCheckable(True)
        self.chinese_action.triggered.connect(lambda: self.set_interface_language('zh'))
        language_menu.addAction(self.chinese_action)
        
        # 日文選項
        self.japanese_action = QAction('🇯🇵 日本語', self)
        self.japanese_action.setCheckable(True)
        self.japanese_action.triggered.connect(lambda: self.set_interface_language('ja'))
        language_menu.addAction(self.japanese_action)
        
        # 設定當前語言狀態
        current_lang = get_gui_language()
        if current_lang == 'en':
            self.english_action.setChecked(True)
        elif current_lang == 'ja':
            self.japanese_action.setChecked(True)
        else:
            self.chinese_action.setChecked(True)
        
        tools_menu.addSeparator()
        
        # X軸連動功能控制
        self.linkage_action = QAction('🔗 Telemetry X-Axis Linkage', self)
        self.linkage_action.setCheckable(True)
        self.linkage_action.setChecked(True)  # 預設啟用
        self.linkage_action.triggered.connect(self.toggle_lap_analysis_linkage)
        tools_menu.addAction(self.linkage_action)
        
        # F1TV Account 選單
        f1tv_menu = menubar.addMenu(tr('f1tv_account_menu', 'F1TV Account'))
        self.f1tv_login_action = QAction(tr('f1tv_login_action', 'Login / Manage Account'), self)
        self.f1tv_login_action.triggered.connect(self._open_f1tv_auth_dialog)
        f1tv_menu.addAction(self.f1tv_login_action)
        
        f1tv_menu.addSeparator()
        
        # 查看 Token 狀態
        self.f1tv_status_action = QAction(tr('f1tv_status_action', 'View Token Status'), self)
        self.f1tv_status_action.triggered.connect(self._show_f1tv_token_status)
        f1tv_menu.addAction(self.f1tv_status_action)
        
        # 清除 Token
        self.f1tv_clear_token_action = QAction(tr('f1tv_clear_token_action', 'Clear Saved Token'), self)
        self.f1tv_clear_token_action.triggered.connect(self._clear_f1tv_token)
        f1tv_menu.addAction(self.f1tv_clear_token_action)
        
        f1tv_menu.addSeparator()
        
        # 登出
        self.f1tv_logout_action = QAction(tr('f1tv_logout_action', 'Logout'), self)
        self.f1tv_logout_action.triggered.connect(self._logout_f1tv)
        f1tv_menu.addAction(self.f1tv_logout_action)

        # 說明菜單
        help_menu = menubar.addMenu(tr('help_menu', '說明'))
        help_menu.addAction(tr('about_action', '關於 F1T'), self.show_about_dialog)


    # ========== _setup_live_timing_menu 已移除，使用 LiveTimingManager.setup_menu() ==========


    def get_drivers_for_year(self, *args, **kwargs):
        """代理方法 - 委派給 DriverListProvider"""
        from windows.managers.driver_list_provider import DriverListProvider
        if not hasattr(self, '_driver_list_provider'):
            self._driver_list_provider = DriverListProvider(self)
        return self._driver_list_provider.get_drivers_for_year(*args, **kwargs)

    def show_about_dialog(self, *args, **kwargs):
        """代理方法 - 委派給 AboutDialogShower"""
        from windows.managers.about_dialog_shower import AboutDialogShower
        if not hasattr(self, '_about_dialog_shower'):
            self._about_dialog_shower = AboutDialogShower(self)
        return self._about_dialog_shower.show_about_dialog(*args, **kwargs)

    def _open_f1tv_auth_dialog(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvAuthOpener"""
        from windows.managers.f1tv_auth_opener import F1tvAuthOpener
        if not hasattr(self, '_f1tv_auth_opener'):
            self._f1tv_auth_opener = F1tvAuthOpener(self)
        return self._f1tv_auth_opener._open_f1tv_auth_dialog(*args, **kwargs)

    def _logout_f1tv(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvLogoutHandler"""
        from windows.managers.f1tv_logout_handler import F1tvLogoutHandler
        if not hasattr(self, '_f1tv_logout_handler'):
            self._f1tv_logout_handler = F1tvLogoutHandler(self)
        return self._f1tv_logout_handler._logout_f1tv(*args, **kwargs)

    def _show_f1tv_token_status(self):
        """顯示 F1TV Token 狀態"""
        from PyQt5.QtWidgets import QMessageBox
        
        if self.f1tv_auth_manager.is_authenticated():
            token_info = self.f1tv_auth_manager.get_token_info()
            if token_info:
                product = token_info.get('product', 'Unknown')
                exp_str = token_info.get('exp_str', 'Unknown')
                status = token_info.get('subscription_status', 'Unknown')
                token_file = self.f1tv_auth_manager.get_token_file_path()
                
                msg = (
                    f"Status: Authenticated\n\n"
                    f"Product: {product}\n"
                    f"Subscription: {status}\n"
                    f"Expires: {exp_str}\n\n"
                    f"Token file: {token_file}"
                )
                QMessageBox.information(
                    self, 
                    tr('f1tv_token_status_title', 'F1TV Token Status'),
                    msg
                )
            else:
                QMessageBox.warning(
                    self,
                    tr('f1tv_token_status_title', 'F1TV Token Status'),
                    tr('f1tv_token_info_error', 'Unable to retrieve token info')
                )
        else:
            QMessageBox.information(
                self,
                tr('f1tv_token_status_title', 'F1TV Token Status'),
                tr('f1tv_not_logged_in', 'Not logged in.\n\nClick "Login / Manage Account" to authenticate.')
            )
    
    def _clear_f1tv_token(self):
        """清除已存儲的 F1TV Token"""
        from PyQt5.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            tr('f1tv_clear_token_title', 'Clear F1TV Token'),
            tr('f1tv_clear_token_confirm', 
               'Are you sure you want to clear the saved F1TV token?\n\n'
               'You will need to login again to access Live Timing data.'),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.f1tv_auth_manager.clear_token()
            QMessageBox.information(
                self,
                tr('f1tv_clear_token_title', 'Clear F1TV Token'),
                tr('f1tv_token_cleared', 'F1TV token has been cleared.')
            )

    def _on_f1tv_auth_success(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvAuthSuccessHandler"""
        from windows.managers.f1tv_auth_success_handler import F1tvAuthSuccessHandler
        if not hasattr(self, '_f1tv_auth_success_handler'):
            self._f1tv_auth_success_handler = F1tvAuthSuccessHandler(self)
        return self._f1tv_auth_success_handler._on_f1tv_auth_success(*args, **kwargs)

    def _on_f1tv_auth_failed(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvAuthFailedHandler"""
        from windows.managers.f1tv_auth_failed_handler import F1tvAuthFailedHandler
        if not hasattr(self, '_f1tv_auth_failed_handler'):
            self._f1tv_auth_failed_handler = F1tvAuthFailedHandler(self)
        return self._f1tv_auth_failed_handler._on_f1tv_auth_failed(*args, **kwargs)

    def _on_f1tv_auth_state_changed(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvAuthStateHandler"""
        from windows.managers.f1tv_auth_state_handler import F1tvAuthStateHandler
        if not hasattr(self, '_f1tv_auth_state_handler'):
            self._f1tv_auth_state_handler = F1tvAuthStateHandler(self)
        return self._f1tv_auth_state_handler._on_f1tv_auth_state_changed(*args, **kwargs)

    def _update_f1tv_status_label(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvStatusUpdater"""
        from windows.managers.f1tv_status_updater import F1tvStatusUpdater
        if not hasattr(self, '_f1tv_status_updater'):
            self._f1tv_status_updater = F1tvStatusUpdater(self)
        return self._f1tv_status_updater._update_f1tv_status_label(*args, **kwargs)

    def _broadcast_f1tv_auth_state(self, *args, **kwargs):
        """代理方法 - 委派給 F1tvAuthBroadcaster"""
        from windows.managers.f1tv_auth_broadcaster import F1tvAuthBroadcaster
        if not hasattr(self, '_f1tv_auth_broadcaster'):
            self._f1tv_auth_broadcaster = F1tvAuthBroadcaster(self)
        return self._f1tv_auth_broadcaster._broadcast_f1tv_auth_state(*args, **kwargs)

    def _setup_live_timing_dock(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingDockSetup"""
        from windows.managers.live_timing_dock_setup import LiveTimingDockSetup
        if not hasattr(self, '_live_timing_dock_setup'):
            self._live_timing_dock_setup = LiveTimingDockSetup(self)
        return self._live_timing_dock_setup._setup_live_timing_dock(*args, **kwargs)

    def _show_live_timing_dock(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingDockShower"""
        from windows.managers.live_timing_dock_shower import LiveTimingDockShower
        if not hasattr(self, '_live_timing_dock_shower'):
            self._live_timing_dock_shower = LiveTimingDockShower(self)
        return self._live_timing_dock_shower._show_live_timing_dock(*args, **kwargs)

    def _hide_live_timing_dock(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingDockHider"""
        from windows.managers.live_timing_dock_hider import LiveTimingDockHider
        if not hasattr(self, '_live_timing_dock_hider'):
            self._live_timing_dock_hider = LiveTimingDockHider(self)
        return self._live_timing_dock_hider._hide_live_timing_dock(*args, **kwargs)

    def _on_live_timing_module_opened(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingOpenedHandler"""
        from windows.managers.live_timing_opened_handler import LiveTimingOpenedHandler
        if not hasattr(self, '_live_timing_opened_handler'):
            self._live_timing_opened_handler = LiveTimingOpenedHandler(self)
        return self._live_timing_opened_handler._on_live_timing_module_opened(*args, **kwargs)

    def _on_live_timing_module_closed(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingClosedHandler"""
        from windows.managers.live_timing_closed_handler import LiveTimingClosedHandler
        if not hasattr(self, '_live_timing_closed_handler'):
            self._live_timing_closed_handler = LiveTimingClosedHandler(self)
        return self._live_timing_closed_handler._on_live_timing_module_closed(*args, **kwargs)

    def _open_live_timing_module(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingOpener"""
        from windows.managers.live_timing_opener import LiveTimingOpener
        if not hasattr(self, '_live_timing_opener'):
            self._live_timing_opener = LiveTimingOpener(self)
        return self._live_timing_opener._open_live_timing_module(*args, **kwargs)

    def _toggle_live_timing_control_panel(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingPanelToggler"""
        from windows.managers.live_timing_panel_toggler import LiveTimingPanelToggler
        if not hasattr(self, '_live_timing_panel_toggler'):
            self._live_timing_panel_toggler = LiveTimingPanelToggler(self)
        return self._live_timing_panel_toggler._toggle_live_timing_control_panel(*args, **kwargs)

    def _open_live_timing_control_panel(self, *args, **kwargs):
        """代理方法 - 委派給 LiveTimingPanelOpener"""
        from windows.managers.live_timing_panel_opener import LiveTimingPanelOpener
        if not hasattr(self, '_live_timing_panel_opener'):
            self._live_timing_panel_opener = LiveTimingPanelOpener(self)
        return self._live_timing_panel_opener._open_live_timing_control_panel(*args, **kwargs)

    def create_professional_toolbar(self):
        """創建專業工具欄"""
        toolbar = QToolBar()
        toolbar.setObjectName("ProfessionalToolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        # 修改：增加工具欄高度以容納遙測分析控件
        toolbar.setFixedHeight(35)  # 從35增加到50像素
        self.addToolBar(toolbar)
        
        # 參數輸入區域
        toolbar.addWidget(QLabel(tr("year_label", "Year:")))
        self.year_combo = QComboBox()
        self.year_combo.setObjectName("ParameterCombo")
        # ✅ 修正年份範圍：只包含有數據的年份 (2018-當前年份)
        from datetime import datetime
        current_year = datetime.now().year
        min_year = 2018  # FastF1/Ergast 支援的最早年份
        self.year_combo.addItems([str(year) for year in range(min_year, current_year + 1)])
        self.year_combo.setCurrentText(str(current_year))
        self.year_combo.setFixedWidth(70)
        toolbar.addWidget(self.year_combo)
        
        toolbar.addWidget(QLabel(tr("race_label", "Race:")))
        self.race_combo = QComboBox()
        self.race_combo.setObjectName("ParameterCombo")
        # 賽事項目將由 on_year_changed 方法動態填充
        self.race_combo.setFixedWidth(250)  # 增加寬度以容納較長的賽事名稱
        toolbar.addWidget(self.race_combo)
        
        toolbar.addWidget(QLabel(tr("session_label", "Session:")))
        self.session_combo = QComboBox()
        self.session_combo.setObjectName("ParameterCombo")
        self.session_combo.addItems(["FP1", "FP2", "FP3", "SQ", "S", "Q", "R"])  # Sprint (S) 支援
        self.session_combo.setCurrentText("R")
        self.session_combo.setFixedWidth(50)
        toolbar.addWidget(self.session_combo)
        
        # 保存工具欄引用以便動態添加/移除控件
        self.main_toolbar = toolbar
        
        # 建立遙測分析控件但不添加到工具欄（將在需要時動態添加）
        self._create_lap_analysis_controls()
        
        toolbar.addSeparator()
        
        # 檢視控制
        toolbar.addAction(tr("tile_windows_action", "Tile Windows"), self.tile_windows)
        toolbar.addAction(tr("cascade_windows_action", "Cascade Windows"), self.cascade_windows)
        
        # 連接年份變更事件
        self.year_combo.currentTextChanged.connect(self.on_year_changed)
        
        # 連接賽事和會話變更事件 - 添加同步功能
        self.race_combo.currentTextChanged.connect(self.on_main_race_changed)
        self.session_combo.currentTextChanged.connect(self.on_main_session_changed)
        
        # 初始化賽事列表
        initial_year = int(self.year_combo.currentText())
        self._refresh_calendar_for_year(initial_year)

    # ------------------------------------------------------------------
    # 賽季日曆支援
    # ------------------------------------------------------------------
    def _get_calendar_events(self, *args, **kwargs):
        """代理方法 - 委派給 CalendarEventsGetter"""
        from windows.managers.calendar_events_getter import CalendarEventsGetter
        if not hasattr(self, '_calendar_events_getter'):
            self._calendar_events_getter = CalendarEventsGetter(self)
        return self._calendar_events_getter._get_calendar_events(*args, **kwargs)

    def _refresh_calendar_for_year(self, *args, **kwargs):
        """代理方法 - 委派給 CalendarYearRefresher"""
        from windows.managers.calendar_year_refresher import CalendarYearRefresher
        if not hasattr(self, '_calendar_year_refresher'):
            self._calendar_year_refresher = CalendarYearRefresher(self)
        return self._calendar_year_refresher._refresh_calendar_for_year(*args, **kwargs)

    def _select_race_by_key(self, *args, **kwargs):
        """代理方法 - 委派給 RaceSelector"""
        from windows.managers.race_selector import RaceSelector
        if not hasattr(self, '_race_selector'):
            self._race_selector = RaceSelector(self)
        return self._race_selector._select_race_by_key(*args, **kwargs)

    def _update_session_combo(self, *args, **kwargs):
        """代理方法 - 委派給 SessionComboUpdater"""
        from windows.managers.session_combo_updater import SessionComboUpdater
        if not hasattr(self, '_session_combo_updater'):
            self._session_combo_updater = SessionComboUpdater(self)
        return self._session_combo_updater._update_session_combo(*args, **kwargs)

    def get_selected_year(self) -> int:
        try:
            return int(self.year_combo.currentText())
        except Exception:
            return 2025

    def get_selected_event(self) -> Optional[SeasonEvent]:
        data = self.race_combo.currentData()
        if isinstance(data, SeasonEvent):
            return data
        display_text = self.race_combo.currentText()
        race_key = self._strip_race_display(display_text)
        mapped_key = self._display_to_race_key.get(display_text) or self._display_to_race_key.get(race_key)
        if mapped_key:
            return self._race_event_lookup.get(mapped_key)
        return self._race_event_lookup.get(race_key)

    def get_selected_race_key(self) -> str:
        event = self.get_selected_event()
        if event:
            return event.race_key
        display_text = self.race_combo.currentText()
        race_key = self._strip_race_display(display_text)
        return self._display_to_race_key.get(display_text) or self._display_to_race_key.get(race_key) or race_key or "Unknown"

    def get_selected_session_code(self) -> str:
        data = self.session_combo.currentData()
        if data and hasattr(data, "code"):
            return getattr(data, "code")
        text = self.session_combo.currentText()
        return text.strip() if text else "R"

    @staticmethod
    def _strip_race_display(text: str) -> str:
        if not text:
            return ""
        if "(" in text:
            return text.split("(")[0].strip()
        return text.strip()

    def _format_race_display(self, event: SeasonEvent) -> str:
        if not isinstance(event, SeasonEvent):
            return ""
        if event.is_completed:
            return event.display_label
        suffix = tr("season_calendar_upcoming_suffix", "[未開賽]")
        if suffix and suffix in event.display_label:
            return event.display_label
        return f"{event.display_label} {suffix}" if suffix else event.display_label
    
    def _create_lap_analysis_controls(self, *args, **kwargs):
        """代理方法 - 委派給 LapAnalysisControlsCreator"""
        from windows.managers.lap_analysis_controls_creator import LapAnalysisControlsCreator
        if not hasattr(self, '_lap_analysis_controls_creator'):
            self._lap_analysis_controls_creator = LapAnalysisControlsCreator(self)
        return self._lap_analysis_controls_creator._create_lap_analysis_controls(*args, **kwargs)

    def get_races_for_year(self, *args, **kwargs):
        """代理方法 - 委派給 RacesForYearGetter"""
        from windows.managers.races_for_year_getter import RacesForYearGetter
        if not hasattr(self, '_races_for_year_getter'):
            self._races_for_year_getter = RacesForYearGetter(self)
        return self._races_for_year_getter.get_races_for_year(*args, **kwargs)

    def get_fastf1_race_name(self, *args, **kwargs):
        """代理方法 - 委派給 Fastf1RaceNamer"""
        from windows.managers.fastf1_race_namer import Fastf1RaceNamer
        if not hasattr(self, '_fastf1_race_namer'):
            self._fastf1_race_namer = Fastf1RaceNamer(self)
        return self._fastf1_race_namer.get_fastf1_race_name(*args, **kwargs)

    def _get_race_key_from_display(self, *args, **kwargs):
        """代理方法 - 委派給 RaceKeyConverter"""
        from windows.managers.race_key_converter import RaceKeyConverter
        if not hasattr(self, '_race_key_converter'):
            self._race_key_converter = RaceKeyConverter(self)
        return self._race_key_converter._get_race_key_from_display(*args, **kwargs)

    def on_year_changed(self, *args, **kwargs):
        """代理方法 - 委派給 YearChangeHandler"""
        from windows.managers.year_change_handler import YearChangeHandler
        if not hasattr(self, '_year_change_handler'):
            self._year_change_handler = YearChangeHandler(self)
        return self._year_change_handler.on_year_changed(*args, **kwargs)

    def on_main_race_changed(self, *args, **kwargs):
        """代理方法 - 委派給 MainRaceHandler"""
        from windows.managers.main_race_handler import MainRaceHandler
        if not hasattr(self, '_main_race_handler'):
            self._main_race_handler = MainRaceHandler(self)
        return self._main_race_handler.on_main_race_changed(*args, **kwargs)

    def on_main_session_changed(self, *args, **kwargs):
        """代理方法 - 委派給 MainSessionHandler"""
        from windows.managers.main_session_handler import MainSessionHandler
        if not hasattr(self, '_main_session_handler'):
            self._main_session_handler = MainSessionHandler(self)
        return self._main_session_handler.on_main_session_changed(*args, **kwargs)

    def check_and_show_lap_controls_if_needed(self, *args, **kwargs):
        """代理方法 - 委派給 LapControlsChecker"""
        from windows.managers.lap_controls_checker import LapControlsChecker
        if not hasattr(self, '_lap_controls_checker'):
            self._lap_controls_checker = LapControlsChecker(self)
        return self._lap_controls_checker.check_and_show_lap_controls_if_needed(*args, **kwargs)

    def force_show_lap_controls(self):
        """強制顯示遙測分析控件（測試用）"""
        logger.debug("[LAP_CONTROL] [DEBUG]   🚨 強制顯示遙測分析控件...")
        self.show_lap_controls()
    
    def initialize_driver_lists(self, *args, **kwargs):
        """代理方法 - 委派給 DriverListsInitializer"""
        from windows.managers.driver_lists_initializer import DriverListsInitializer
        if not hasattr(self, '_driver_lists_initializer'):
            self._driver_lists_initializer = DriverListsInitializer(self)
        return self._driver_lists_initializer.initialize_driver_lists(*args, **kwargs)

    def show_lap_controls(self, *args, **kwargs):
        """代理方法 - 委派給 LapControlsShower"""
        from windows.managers.lap_controls_shower import LapControlsShower
        if not hasattr(self, '_lap_controls_shower'):
            self._lap_controls_shower = LapControlsShower(self)
        return self._lap_controls_shower.show_lap_controls(*args, **kwargs)

    def hide_lap_controls(self, *args, **kwargs):
        """代理方法 - 委派給 LapControlsHider"""
        from windows.managers.lap_controls_hider import LapControlsHider
        if not hasattr(self, '_lap_controls_hider'):
            self._lap_controls_hider = LapControlsHider(self)
        return self._lap_controls_hider.hide_lap_controls(*args, **kwargs)

    def on_lap_analysis_window_opened(self, *args, **kwargs):
        """代理方法 - 委派給 LapWindowOpenedHandler"""
        from windows.managers.lap_window_opened_handler import LapWindowOpenedHandler
        if not hasattr(self, '_lap_window_opened_handler'):
            self._lap_window_opened_handler = LapWindowOpenedHandler(self)
        return self._lap_window_opened_handler.on_lap_analysis_window_opened(*args, **kwargs)

    def on_lap_analysis_window_closed(self, *args, **kwargs):
        """代理方法 - 委派給 LapWindowCloseHandler"""
        from windows.managers.lap_window_close_handler import LapWindowCloseHandler
        if not hasattr(self, '_lap_window_close_handler'):
            self._lap_window_close_handler = LapWindowCloseHandler(self)
        return self._lap_window_close_handler.on_lap_analysis_window_closed(*args, **kwargs)

    def _trigger_toolbar_status_for_lap_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 ToolbarStatusTrigger"""
        from windows.managers.toolbar_status_trigger import ToolbarStatusTrigger
        if not hasattr(self, '_toolbar_status_trigger'):
            self._toolbar_status_trigger = ToolbarStatusTrigger(self)
        return self._toolbar_status_trigger._trigger_toolbar_status_for_lap_analysis(*args, **kwargs)

    def _check_and_trigger_batch_update(self, *args, **kwargs):
        """代理方法 - 委派給 BatchUpdateTrigger"""
        from windows.managers.batch_update_trigger import BatchUpdateTrigger
        if not hasattr(self, '_batch_update_trigger'):
            self._batch_update_trigger = BatchUpdateTrigger(self)
        return self._batch_update_trigger._check_and_trigger_batch_update(*args, **kwargs)

    def update_all_lap_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 LapAnalysisUpdater"""
        from windows.managers.lap_analysis_updater import LapAnalysisUpdater
        if not hasattr(self, '_lap_analysis_updater'):
            self._lap_analysis_updater = LapAnalysisUpdater(self)
        return self._lap_analysis_updater.update_all_lap_analysis(*args, **kwargs)

    def _on_main_fastest_lap_changed(self, *args, **kwargs):
        """代理方法 - 委派給 FastestLapHandler"""
        from windows.managers.fastest_lap_handler import FastestLapHandler
        if not hasattr(self, '_fastest_lap_handler'):
            self._fastest_lap_handler = FastestLapHandler(self)
        return self._fastest_lap_handler._on_main_fastest_lap_changed(*args, **kwargs)

    def on_lap_parameters_changed(self, *args, **kwargs):
        """代理方法 - 委派給 LapParamsChangeHandler"""
        from windows.managers.lap_params_change_handler import LapParamsChangeHandler
        if not hasattr(self, '_lap_params_change_handler'):
            self._lap_params_change_handler = LapParamsChangeHandler(self)
        return self._lap_params_change_handler.on_lap_parameters_changed(*args, **kwargs)

    def sync_all_independent_windows(self, *args, **kwargs):
        """代理方法 - 委派給 SyncManager"""
        from windows.managers.sync_manager import SyncManager
        if not hasattr(self, '_sync_manager'):
            self._sync_manager = SyncManager(self)
        return self._sync_manager.sync_all_independent_windows(*args, **kwargs)

    def on_race_parameters_changed(self, *args, **kwargs):
        """代理方法 - 委派給 RaceParamsHandler"""
        from windows.managers.race_params_handler import RaceParamsHandler
        if not hasattr(self, '_race_params_handler'):
            self._race_params_handler = RaceParamsHandler(self)
        return self._race_params_handler.on_race_parameters_changed(*args, **kwargs)

    def _get_telemetry_analysis_windows(self, *args, **kwargs):
        """代理方法 - 委派給 TelemetryWindowsGetter"""
        from windows.managers.telemetry_windows_getter import TelemetryWindowsGetter
        if not hasattr(self, '_telemetry_windows_getter'):
            self._telemetry_windows_getter = TelemetryWindowsGetter(self)
        return self._telemetry_windows_getter._get_telemetry_analysis_windows(*args, **kwargs)

    def create_left_panel(self, *args, **kwargs):
        """代理方法 - 委派給 LeftPanelCreator"""
        from windows.managers.left_panel_creator import LeftPanelCreator
        if not hasattr(self, '_left_panel_creator'):
            self._left_panel_creator = LeftPanelCreator(self)
        return self._left_panel_creator.create_left_panel(*args, **kwargs)

    def create_professional_function_tree(self, *args, **kwargs):
        """代理方法 - 委派給 FunctionTreeBuilder"""
        from windows.managers.function_tree_builder import FunctionTreeBuilder
        if not hasattr(self, '_function_tree_builder'):
            self._function_tree_builder = FunctionTreeBuilder(self)
        return self._function_tree_builder.create_professional_function_tree(*args, **kwargs)

    def create_professional_workspace(self, *args, **kwargs):
        """代理方法 - 委派給 ProfessionalWorkspaceBuilder"""
        from windows.managers.professional_workspace_builder import ProfessionalWorkspaceBuilder
        if not hasattr(self, '_professional_workspace_builder'):
            self._professional_workspace_builder = ProfessionalWorkspaceBuilder(self)
        return self._professional_workspace_builder.create_professional_workspace(*args, **kwargs)

    def init_default_tabs(self, *args, **kwargs):
        """代理方法 - 委派給 DefaultTabsInitializer"""
        from windows.managers.default_tabs_initializer import DefaultTabsInitializer
        if not hasattr(self, '_default_tabs_initializer'):
            self._default_tabs_initializer = DefaultTabsInitializer(self)
        return self._default_tabs_initializer.init_default_tabs(*args, **kwargs)

    def _setup_tab_context_menu(self):
        """為 QTabWidget 設定右鍵選單"""
        # 設置 TabBar 的右鍵選單策略
        self.tab_widget.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tab_widget.tabBar().customContextMenuRequested.connect(self._show_tab_context_menu)
        logger.debug("[TAB_POPOUT] ✅ 分頁右鍵選單已設置")
    
    def _show_tab_context_menu(self, *args, **kwargs):
        """代理方法 - 委派給 TabContextMenuShower"""
        from windows.managers.tab_context_menu_shower import TabContextMenuShower
        if not hasattr(self, '_tab_context_menu_shower'):
            self._tab_context_menu_shower = TabContextMenuShower(self)
        return self._tab_context_menu_shower._show_tab_context_menu(*args, **kwargs)

    def add_new_tab(self, *args, **kwargs):
        """代理方法 - 委派給 NewTabAdder"""
        from windows.managers.new_tab_adder import NewTabAdder
        if not hasattr(self, '_new_tab_adder'):
            self._new_tab_adder = NewTabAdder(self)
        return self._new_tab_adder.add_new_tab(*args, **kwargs)

    def create_tab_for_workspace(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceTabCreator"""
        from windows.managers.workspace_tab_creator import WorkspaceTabCreator
        if not hasattr(self, '_workspace_tab_creator'):
            self._workspace_tab_creator = WorkspaceTabCreator(self)
        return self._workspace_tab_creator.create_tab_for_workspace(*args, **kwargs)

    def _convert_to_chinese_number(self, num: int) -> str:
        """將數字轉換為中文數字（一、二、三...）"""
        chinese_nums = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                        "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十"]
        if 1 <= num <= 20:
            return chinese_nums[num - 1]
        else:
            return str(num)  # 超過 20 就用數字
        
    def close_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TabCloser"""
        from windows.managers.tab_closer import TabCloser
        if not hasattr(self, '_tab_closer'):
            self._tab_closer = TabCloser(self)
        return self._tab_closer.close_tab(*args, **kwargs)

    def close_current_tab(self):
        """關閉當前分頁"""
        current_index = self.tab_widget.currentIndex()
        if current_index >= 0:
            self.close_tab(current_index)
    
    def close_all_mdi_windows_in_current_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TabMdiCloser"""
        from windows.managers.tab_mdi_closer import TabMdiCloser
        if not hasattr(self, '_tab_mdi_closer'):
            self._tab_mdi_closer = TabMdiCloser(self)
        return self._tab_mdi_closer.close_all_mdi_windows_in_current_tab(*args, **kwargs)

    def show_all_data_in_current_tab(self, *args, **kwargs):
        """代理方法 - 委派給 AllDataShower"""
        from windows.managers.all_data_shower import AllDataShower
        if not hasattr(self, '_all_data_shower'):
            self._all_data_shower = AllDataShower(self)
        return self._all_data_shower.show_all_data_in_current_tab(*args, **kwargs)

    def _on_tab_changed(self, *args, **kwargs):
        """代理方法 - 委派給 TabChangeHandler"""
        from windows.managers.tab_change_handler import TabChangeHandler
        if not hasattr(self, '_tab_change_handler'):
            self._tab_change_handler = TabChangeHandler(self)
        return self._tab_change_handler._on_tab_changed(*args, **kwargs)

    def update_tab_count(self):
        """更新分頁數量顯示"""
        count = self.tab_widget.count()
        self.tab_count_label.setText(f"分頁: {count}")
    
    # ==================== 分頁彈出功能 ====================
    
    def pop_out_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TabPopOuter"""
        from windows.managers.tab_pop_outer import TabPopOuter
        if not hasattr(self, '_tab_pop_outer'):
            self._tab_pop_outer = TabPopOuter(self)
        return self._tab_pop_outer.pop_out_tab(*args, **kwargs)

    def pop_back_in_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TabPopBacker"""
        from windows.managers.tab_pop_backer import TabPopBacker
        if not hasattr(self, '_tab_pop_backer'):
            self._tab_pop_backer = TabPopBacker(self)
        return self._tab_pop_backer.pop_back_in_tab(*args, **kwargs)

    def _update_tab_appearance(self, *args, **kwargs):
        """代理方法 - 委派給 TabAppearanceUpdater"""
        from windows.managers.tab_appearance_updater import TabAppearanceUpdater
        if not hasattr(self, '_tab_appearance_updater'):
            self._tab_appearance_updater = TabAppearanceUpdater(self)
        return self._tab_appearance_updater._update_tab_appearance(*args, **kwargs)

    def rename_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TabRenamer"""
        from windows.managers.tab_renamer import TabRenamer
        if not hasattr(self, '_tab_renamer'):
            self._tab_renamer = TabRenamer(self)
        return self._tab_renamer.rename_tab(*args, **kwargs)

    def _get_unique_tab_name(self, *args, **kwargs):
        """代理方法 - 委派給 UniqueTabNamer"""
        from windows.managers.unique_tab_namer import UniqueTabNamer
        if not hasattr(self, '_unique_tab_namer'):
            self._unique_tab_namer = UniqueTabNamer(self)
        return self._unique_tab_namer._get_unique_tab_name(*args, **kwargs)

    def _ensure_mdi_visible(self, *args, **kwargs):
        """代理方法 - 委派給 MdiVisibilityEnsurer"""
        from windows.managers.mdi_visibility_ensurer import MdiVisibilityEnsurer
        if not hasattr(self, '_mdi_visibility_ensurer'):
            self._mdi_visibility_ensurer = MdiVisibilityEnsurer(self)
        return self._mdi_visibility_ensurer._ensure_mdi_visible(*args, **kwargs)

    def check_and_hide_tabs(self):
        """✅ 檢查標籤欄狀態（已改為啟用模式）"""
        logger.debug("[TAB] ⏰ 檢查標籤欄狀態...")
        logger.debug(f"[TAB] QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        logger.debug(f"[TAB] QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
        # ✅ 確保標籤欄顯示（與之前相反）
        self.tab_widget.tabBar().setVisible(True)
        
        logger.debug(f"[TAB] ✅ 標籤欄已啟用")
        
    def second_tab_check(self):
        """第二次標籤檢查（延遲2秒後）- 簡化版本"""
        logger.debug(f"[TAB_HIDE] 延遲檢查 - QTabBar 可見性: {self.tab_widget.tabBar().isVisible()}")
        logger.debug(f"[TAB_HIDE] 延遲檢查 - QTabBar 高度: {self.tab_widget.tabBar().height()}")
        
    def third_tab_check(self, *args, **kwargs):
        """代理方法 - 委派給 ThirdTabChecker"""
        from windows.managers.third_tab_checker import ThirdTabChecker
        if not hasattr(self, '_third_tab_checker'):
            self._third_tab_checker = ThirdTabChecker(self)
        return self._third_tab_checker.third_tab_check(*args, **kwargs)

    def create_and_register_mdi_area(self, object_name):
        """創建MDI區域並自動註冊到主視窗"""
        mdi_area = CustomMdiArea()
        mdi_area.setObjectName(object_name)
        mdi_area.setViewMode(QMdiArea.SubWindowView)
        
        # 註冊到主視窗的MDI區域列表
        self.register_mdi_area(mdi_area)
        
        return mdi_area
    
    def register_mdi_area(self, *args, **kwargs):
        """代理方法 - 委派給 MdiAreaRegistrar"""
        from windows.managers.mdi_area_registrar import MdiAreaRegistrar
        if not hasattr(self, '_mdi_area_registrar'):
            self._mdi_area_registrar = MdiAreaRegistrar(self)
        return self._mdi_area_registrar.register_mdi_area(*args, **kwargs)

    def sync_to_all_mdi_subwindows(self, *args, **kwargs):
        """代理方法 - 委派給 MdiSubwindowSyncer"""
        from windows.managers.mdi_subwindow_syncer import MdiSubwindowSyncer
        if not hasattr(self, '_mdi_subwindow_syncer'):
            self._mdi_subwindow_syncer = MdiSubwindowSyncer(self)
        return self._mdi_subwindow_syncer.sync_to_all_mdi_subwindows(*args, **kwargs)

    def sync_to_mdi_area(self, *args, **kwargs):
        """代理方法 - 委派給 MdiAreaSyncer"""
        from windows.managers.mdi_area_syncer import MdiAreaSyncer
        if not hasattr(self, '_mdi_area_syncer'):
            self._mdi_area_syncer = MdiAreaSyncer(self)
        return self._mdi_area_syncer.sync_to_mdi_area(*args, **kwargs)

    def force_white_background(self, *args, **kwargs):
        """代理方法 - 委派給 WhiteBgForcer"""
        from windows.managers.white_bg_forcer import WhiteBgForcer
        if not hasattr(self, '_white_bg_forcer'):
            self._white_bg_forcer = WhiteBgForcer(self)
        return self._white_bg_forcer.force_white_background(*args, **kwargs)

    def create_welcome_tab(self, *args, **kwargs):
        """代理方法 - 委派給 WelcomeTabBuilder"""
        from windows.managers.welcome_tab_builder import WelcomeTabBuilder
        if not hasattr(self, '_welcome_tab_builder'):
            self._welcome_tab_builder = WelcomeTabBuilder(self)
        return self._welcome_tab_builder.create_welcome_tab(*args, **kwargs)

    def create_data_overview_tab(self, *args, **kwargs):
        """代理方法 - 委派給 DataOverviewBuilder"""
        from windows.managers.data_overview_builder import DataOverviewBuilder
        if not hasattr(self, '_data_overview_builder'):
            self._data_overview_builder = DataOverviewBuilder(self)
        return self._data_overview_builder.create_data_overview_tab(*args, **kwargs)

    def create_telemetry_analysis_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TelemetryTabBuilder"""
        from windows.managers.telemetry_tab_builder import TelemetryTabBuilder
        if not hasattr(self, '_telemetry_tab_builder'):
            self._telemetry_tab_builder = TelemetryTabBuilder(self)
        return self._telemetry_tab_builder.create_telemetry_analysis_tab(*args, **kwargs)

    def create_laptime_comparison_tab(self, *args, **kwargs):
        """代理方法 - 委派給 LaptimeComparisonTabCreator"""
        from windows.managers.laptime_comparison_tab_creator import LaptimeComparisonTabCreator
        if not hasattr(self, '_laptime_comparison_tab_creator'):
            self._laptime_comparison_tab_creator = LaptimeComparisonTabCreator(self)
        return self._laptime_comparison_tab_creator.create_laptime_comparison_tab(*args, **kwargs)

    def create_track_analysis_tab(self, *args, **kwargs):
        """代理方法 - 委派給 TrackAnalysisTabCreator"""
        from windows.managers.track_analysis_tab_creator import TrackAnalysisTabCreator
        if not hasattr(self, '_track_analysis_tab_creator'):
            self._track_analysis_tab_creator = TrackAnalysisTabCreator(self)
        return self._track_analysis_tab_creator.create_track_analysis_tab(*args, **kwargs)

    def create_lap_analysis_table(self, *args, **kwargs):
        """代理方法 - 委派給 LapAnalysisTableCreator"""
        from windows.managers.lap_analysis_table_creator import LapAnalysisTableCreator
        if not hasattr(self, '_lap_analysis_table_creator'):
            self._lap_analysis_table_creator = LapAnalysisTableCreator(self)
        return self._lap_analysis_table_creator.create_lap_analysis_table(*args, **kwargs)

    def _on_splitter_moved(self, pos, index):
        """當用戶拖動 Splitter 時，標記功能樹為用戶已調整"""
        if hasattr(self, 'function_tree'):
            self.function_tree.mark_user_resized()
    
    def _adjust_splitter_for_tree(self, *args, **kwargs):
        """代理方法 - 委派給 SplitterAdjuster"""
        from windows.managers.splitter_adjuster import SplitterAdjuster
        if not hasattr(self, '_splitter_adjuster'):
            self._splitter_adjuster = SplitterAdjuster(self)
        return self._splitter_adjuster._adjust_splitter_for_tree(*args, **kwargs)

    def create_professional_status_bar(self, *args, **kwargs):
        """代理方法 - 委派給 StatusBarBuilder"""
        from windows.managers.status_bar_builder import StatusBarBuilder
        if not hasattr(self, '_status_bar_builder'):
            self._status_bar_builder = StatusBarBuilder(self)
        return self._status_bar_builder.create_professional_status_bar(*args, **kwargs)

    def _determine_api_base_url(self) -> str:
        """Resolve the API base URL using the public endpoint enforcement."""

        def _log(message: str) -> None:
            logger.info("[API-URL] %s", message)

        return resolve_api_base_url(event_logger=_log)

    def setup_api_health_monitor(self, *args, **kwargs):
        """代理方法 - 委派給 ApiHealthMonitorSetup"""
        from windows.managers.api_health_monitor_setup import ApiHealthMonitorSetup
        if not hasattr(self, '_api_health_monitor_setup'):
            self._api_health_monitor_setup = ApiHealthMonitorSetup(self)
        return self._api_health_monitor_setup.setup_api_health_monitor(*args, **kwargs)

    def trigger_api_health_check(self, *args, **kwargs):
        """代理方法 - 委派給 ApiHealthTrigger"""
        from windows.managers.api_health_trigger import ApiHealthTrigger
        if not hasattr(self, '_api_health_trigger'):
            self._api_health_trigger = ApiHealthTrigger(self)
        return self._api_health_trigger.trigger_api_health_check(*args, **kwargs)

    def on_api_health_result(self, *args, **kwargs):
        """代理方法 - 委派給 ApiHealthHandler"""
        from windows.managers.api_health_handler import ApiHealthHandler
        if not hasattr(self, '_api_health_handler'):
            self._api_health_handler = ApiHealthHandler(self)
        return self._api_health_handler.on_api_health_result(*args, **kwargs)

    def on_api_health_finished(self) -> None:
        """處理 Health Worker 完成信號
        
        ✅ 新架構：Worker 不銷毀，只重置狀態標誌，可重複使用
        """
        self._api_health_worker_active = False
        # ✅ Worker 保留不刪除，下次可以重新 start()
        
        if self.check_api_action:
            self.check_api_action.setEnabled(True)

    def manual_api_health_check(self) -> None:
        """Slot wired to the Tools menu to trigger manual health checks."""
        self.trigger_api_health_check(manual=True)

    def setup_api_runtime_monitor(self, *args, **kwargs):
        """代理方法 - 委派給 ApiRuntimeMonitorSetup"""
        from windows.managers.api_runtime_monitor_setup import ApiRuntimeMonitorSetup
        if not hasattr(self, '_api_runtime_monitor_setup'):
            self._api_runtime_monitor_setup = ApiRuntimeMonitorSetup(self)
        return self._api_runtime_monitor_setup.setup_api_runtime_monitor(*args, **kwargs)

    def trigger_api_runtime_poll(self, *args, **kwargs):
        """代理方法 - 委派給 ApiRuntimePoller"""
        from windows.managers.api_runtime_poller import ApiRuntimePoller
        if not hasattr(self, '_api_runtime_poller'):
            self._api_runtime_poller = ApiRuntimePoller(self)
        return self._api_runtime_poller.trigger_api_runtime_poll(*args, **kwargs)

    def on_api_runtime_result(self, *args, **kwargs):
        """代理方法 - 委派給 ApiRuntimeHandler"""
        from windows.managers.api_runtime_handler import ApiRuntimeHandler
        if not hasattr(self, '_api_runtime_handler'):
            self._api_runtime_handler = ApiRuntimeHandler(self)
        return self._api_runtime_handler.on_api_runtime_result(*args, **kwargs)

    def _apply_cli_status_view(self, *args, **kwargs):
        """代理方法 - 委派給 CliStatusViewApplier"""
        from windows.managers.cli_status_view_applier import CliStatusViewApplier
        if not hasattr(self, '_cli_status_view_applier'):
            self._cli_status_view_applier = CliStatusViewApplier(self)
        return self._cli_status_view_applier._apply_cli_status_view(*args, **kwargs)

    def _schedule_parameter_broadcast(self, *args, **kwargs):
        """代理方法 - 委派給 ParamBroadcastScheduler"""
        from windows.managers.param_broadcast_scheduler import ParamBroadcastScheduler
        if not hasattr(self, '_param_broadcast_scheduler'):
            self._param_broadcast_scheduler = ParamBroadcastScheduler(self)
        return self._param_broadcast_scheduler._schedule_parameter_broadcast(*args, **kwargs)

    def _broadcast_pending_parameters(self, *args, **kwargs):
        """代理方法 - 委派給 PendingParamsBroadcaster"""
        from windows.managers.pending_params_broadcaster import PendingParamsBroadcaster
        if not hasattr(self, '_pending_params_broadcaster'):
            self._pending_params_broadcaster = PendingParamsBroadcaster(self)
        return self._pending_params_broadcaster._broadcast_pending_parameters(*args, **kwargs)

    def on_api_runtime_finished(self) -> None:
        """處理 Runtime Worker 完成信號
        
        ✅ 新架構：Worker 不銷毀，只重置狀態標誌，可重複使用
        """
        self._api_runtime_worker_active = False
        # ✅ Worker 保留不刪除，下次可以重新 start()


    def update_status_bar(self):
        """更新狀態列 (只維護時間與同步視窗標題)。"""
        if hasattr(self, 'time_label') and self.time_label is not None:
            self.time_label.setText(f"[TIME] {datetime.datetime.now().strftime('%H:%M:%S')}")

        if hasattr(self, 'year_combo') and hasattr(self, 'race_combo') and hasattr(self, 'session_combo'):
            try:
                self.update_all_window_titles()
            except Exception as exc:
                logger.debug('update_all_window_titles failed: %s', exc)

    def get_current_parameters(self):
        """獲取當前參數設定"""
        display_race = self.race_combo.currentText() if hasattr(self, 'race_combo') else 'Japan'
        fastf1_race = self.get_fastf1_race_name(display_race)  # 轉換為 FastF1 期望的名稱
        
        return {
            'year': self.year_combo.currentText() if hasattr(self, 'year_combo') else '2025',
            'race': fastf1_race,  # 使用轉換後的名稱
            'session': self.session_combo.currentText() if hasattr(self, 'session_combo') else 'R'
        }

    def get_current_lap_toolbar_parameters(self, *args, **kwargs):
        """代理方法 - 委派給 LapToolbarParamsGetter"""
        from windows.managers.lap_toolbar_params_getter import LapToolbarParamsGetter
        if not hasattr(self, '_lap_toolbar_params_getter'):
            self._lap_toolbar_params_getter = LapToolbarParamsGetter(self)
        return self._lap_toolbar_params_getter.get_current_lap_toolbar_parameters(*args, **kwargs)

    def format_window_title(self, module_name):
        """格式化視窗標題為: 模組名稱_年分_賽事_賽段"""
        params = self.get_current_parameters()
        return f"{module_name}_{params['year']}_{params['race']}_{params['session']}"
    
    def update_all_window_titles(self, *args, **kwargs):
        """代理方法 - 委派給 WindowTitlesUpdater"""
        from windows.managers.window_titles_updater import WindowTitlesUpdater
        if not hasattr(self, '_window_titles_updater'):
            self._window_titles_updater = WindowTitlesUpdater(self)
        return self._window_titles_updater.update_all_window_titles(*args, **kwargs)

    def check_and_remove_welcome_page(self, *args, **kwargs):
        """代理方法 - 委派給 WelcomePageRemover"""
        from windows.managers.welcome_page_remover import WelcomePageRemover
        if not hasattr(self, '_welcome_page_remover'):
            self._welcome_page_remover = WelcomePageRemover(self)
        return self._welcome_page_remover.check_and_remove_welcome_page(*args, **kwargs)

    def create_empty_analysis_tab(self, *args, **kwargs):
        """代理方法 - 委派給 EmptyAnalysisTabCreator"""
        from windows.managers.empty_analysis_tab_creator import EmptyAnalysisTabCreator
        if not hasattr(self, '_empty_analysis_tab_creator'):
            self._empty_analysis_tab_creator = EmptyAnalysisTabCreator(self)
        return self._empty_analysis_tab_creator.create_empty_analysis_tab(*args, **kwargs)

    def _create_toolbar_status_widget(self, *args, **kwargs):
        """代理方法 - 委派給 ToolbarStatusCreator"""
        from windows.managers.toolbar_status_creator import ToolbarStatusCreator
        if not hasattr(self, '_toolbar_status_creator'):
            self._toolbar_status_creator = ToolbarStatusCreator(self)
        return self._toolbar_status_creator._create_toolbar_status_widget(*args, **kwargs)

    def update_toolbar_status(self, *args, **kwargs):
        """代理方法 - 委派給 ToolbarStatusUpdater"""
        from windows.managers.toolbar_status_updater import ToolbarStatusUpdater
        if not hasattr(self, '_toolbar_status_updater'):
            self._toolbar_status_updater = ToolbarStatusUpdater(self)
        return self._toolbar_status_updater.update_toolbar_status(*args, **kwargs)

    def clear_toolbar_status(self):
        """清除工具欄狀態信息"""
        self.update_toolbar_status("")
        
    def create_analysis_window(self, *args, **kwargs):
        """代理方法 - 委派給 AnalysisWindowCreator"""
        from windows.managers.analysis_window_creator import AnalysisWindowCreator
        if not hasattr(self, '_analysis_window_creator'):
            self._analysis_window_creator = AnalysisWindowCreator(self)
        return self._analysis_window_creator.create_analysis_window(*args, **kwargs)

    def _get_expected_window_title_pattern(self, *args, **kwargs):
        """代理方法 - 委派給 WindowTitlePatternGetter"""
        from windows.managers.window_title_pattern_getter import WindowTitlePatternGetter
        if not hasattr(self, '_window_title_pattern_getter'):
            self._window_title_pattern_getter = WindowTitlePatternGetter(self)
        return self._window_title_pattern_getter._get_expected_window_title_pattern(*args, **kwargs)

    def _find_existing_window(self, *args, **kwargs):
        """代理方法 - 委派給 ExistingWindowFinder"""
        from windows.managers.existing_window_finder import ExistingWindowFinder
        if not hasattr(self, '_existing_window_finder'):
            self._existing_window_finder = ExistingWindowFinder(self)
        return self._existing_window_finder._find_existing_window(*args, **kwargs)

    def _mark_module_factory_type(self, module, module_type):
        """為模組標記工廠類型以支援工作區還原"""
        if module and module_type:
            try:
                setattr(module, "_factory_module_type", module_type)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Unable to tag module with factory type %s: %s", module_type, exc)
        return module

    def _prompt_throttle_analysis_options(self, *args, **kwargs):
        """代理方法 - 委派給 ThrottleOptionsPrompter"""
        from windows.managers.throttle_options_prompter import ThrottleOptionsPrompter
        if not hasattr(self, '_throttle_options_prompter'):
            self._throttle_options_prompter = ThrottleOptionsPrompter(self)
        return self._throttle_options_prompter._prompt_throttle_analysis_options(*args, **kwargs)

    def _show_throttle_line_chart_placeholder(self):
        """顯示油門折線圖（現已實現）"""
        # 改為直接調用實際的油門折線圖模組
        self._create_throttle_line_chart_window()

    def _create_throttle_line_chart_window(self, *args, **kwargs):
        """代理方法 - 委派給 ThrottleChartCreator"""
        from windows.managers.throttle_chart_creator import ThrottleChartCreator
        if not hasattr(self, '_throttle_chart_creator'):
            self._throttle_chart_creator = ThrottleChartCreator(self)
        return self._throttle_chart_creator._create_throttle_line_chart_window(*args, **kwargs)

    def _prompt_detailed_lap_options(self, *args, **kwargs):
        """代理方法 - 委派給 DetailedLapPrompter"""
        from windows.managers.detailed_lap_prompter import DetailedLapPrompter
        if not hasattr(self, '_detailed_lap_prompter'):
            self._detailed_lap_prompter = DetailedLapPrompter(self)
        return self._detailed_lap_prompter._prompt_detailed_lap_options(*args, **kwargs)

    def _prompt_ideal_lap_options(self, *args, **kwargs):
        """代理方法 - 委派給 IdealLapOptionsPrompter"""
        from windows.managers.ideal_lap_options_prompter import IdealLapOptionsPrompter
        if not hasattr(self, '_ideal_lap_options_prompter'):
            self._ideal_lap_options_prompter = IdealLapOptionsPrompter(self)
        return self._ideal_lap_options_prompter._prompt_ideal_lap_options(*args, **kwargs)

    def _create_detailed_lap_boxplot_window(self, *args, **kwargs):
        """代理方法 - 委派給 DetailedLapBoxplotCreator"""
        from windows.managers.detailed_lap_boxplot_creator import DetailedLapBoxplotCreator
        if not hasattr(self, '_detailed_lap_boxplot_creator'):
            self._detailed_lap_boxplot_creator = DetailedLapBoxplotCreator(self)
        return self._detailed_lap_boxplot_creator._create_detailed_lap_boxplot_window(*args, **kwargs)

    def _create_ideal_lap_ranking_window(self, *args, **kwargs):
        """代理方法 - 委派給 IdealLapRankingCreator"""
        from windows.managers.ideal_lap_ranking_creator import IdealLapRankingCreator
        if not hasattr(self, '_ideal_lap_ranking_creator'):
            self._ideal_lap_ranking_creator = IdealLapRankingCreator(self)
        return self._ideal_lap_ranking_creator._create_ideal_lap_ranking_window(*args, **kwargs)

    def _create_driver_position_window(self, *args, **kwargs):
        """代理方法 - 委派給 DriverPositionCreator"""
        from windows.managers.driver_position_creator import DriverPositionCreator
        if not hasattr(self, '_driver_position_creator'):
            self._driver_position_creator = DriverPositionCreator(self)
        return self._driver_position_creator._create_driver_position_window(*args, **kwargs)

    def _create_ideal_lap_heatmap_window(self, *args, **kwargs):
        """代理方法 - 委派給 IdealLapHeatmapCreator"""
        from windows.managers.ideal_lap_heatmap_creator import IdealLapHeatmapCreator
        if not hasattr(self, '_ideal_lap_heatmap_creator'):
            self._ideal_lap_heatmap_creator = IdealLapHeatmapCreator(self)
        return self._ideal_lap_heatmap_creator._create_ideal_lap_heatmap_window(*args, **kwargs)

    def _create_ideal_lap_sector_comparison_window(self, *args, **kwargs):
        """代理方法 - 委派給 IdealLapSectorCreator"""
        from windows.managers.ideal_lap_sector_creator import IdealLapSectorCreator
        if not hasattr(self, '_ideal_lap_sector_creator'):
            self._ideal_lap_sector_creator = IdealLapSectorCreator(self)
        return self._ideal_lap_sector_creator._create_ideal_lap_sector_comparison_window(*args, **kwargs)

    def _position_subwindow(self, *args, **kwargs):
        """代理方法 - 委派給 SubwindowPositioner"""
        from windows.managers.subwindow_positioner import SubwindowPositioner
        if not hasattr(self, '_subwindow_positioner'):
            self._subwindow_positioner = SubwindowPositioner(self)
        return self._subwindow_positioner._position_subwindow(*args, **kwargs)

    def _create_analysis_module(self, *args, **kwargs):
        """代理方法 - 委派給 AnalysisModuleCreator"""
        from windows.managers.analysis_module_creator import AnalysisModuleCreator
        if not hasattr(self, '_analysis_module_creator'):
            self._analysis_module_creator = AnalysisModuleCreator(self)
        return self._analysis_module_creator._create_analysis_module(*args, **kwargs)

    def _extract_module_name(self, function_name):
        """從功能名稱提取模組名稱"""
        return function_name.replace(" - 分析", "").replace("分析", "")
    
    def _create_legacy_content(self, *args, **kwargs):
        """代理方法 - 委派給 LegacyContentCreator"""
        from windows.managers.legacy_content_creator import LegacyContentCreator
        if not hasattr(self, '_legacy_content_creator'):
            self._legacy_content_creator = LegacyContentCreator(self)
        return self._legacy_content_creator._create_legacy_content(*args, **kwargs)

    def close_all_mdi_windows(self, *args, **kwargs):
        """代理方法 - 委派給 MdiWindowsCloser"""
        from windows.managers.mdi_windows_closer import MdiWindowsCloser
        if not hasattr(self, '_mdi_windows_closer'):
            self._mdi_windows_closer = MdiWindowsCloser(self)
        return self._mdi_windows_closer.close_all_mdi_windows(*args, **kwargs)

    def _find_linkage_modules_in_widget(self, *args, **kwargs):
        """代理方法 - 委派給 LinkageFinder"""
        from windows.managers.linkage_finder import LinkageFinder
        if not hasattr(self, '_linkage_finder'):
            self._linkage_finder = LinkageFinder(self)
        return self._linkage_finder._find_linkage_modules_in_widget(*args, **kwargs)

    def reset_all_charts(self, *args, **kwargs):
        """代理方法 - 委派給 ChartResetter"""
        from windows.managers.chart_resetter import ChartResetter
        if not hasattr(self, '_chart_resetter'):
            self._chart_resetter = ChartResetter(self)
        return self._chart_resetter.reset_all_charts(*args, **kwargs)

    def open_session(self): 
        params = self.get_current_parameters()
        logger.debug(f"[檔案] 開啟會話請求 - {params['year']} {params['race']} {params['session']}")
        QMessageBox.information(
            self,
            tr('open_session_disabled', '開啟會話'),
            tr('open_session_disabled_message', 'API-ONLY 模式下請透過 API 或既有 JSON 載入分析資料。')
        )

    def save_workspace(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceSaver"""
        from windows.managers.workspace_saver import WorkspaceSaver
        if not hasattr(self, '_workspace_saver'):
            self._workspace_saver = WorkspaceSaver(self)
        return self._workspace_saver.save_workspace(*args, **kwargs)

    def load_workspace(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceLoader"""
        from windows.managers.workspace_loader import WorkspaceLoader
        if not hasattr(self, '_workspace_loader'):
            self._workspace_loader = WorkspaceLoader(self)
        return self._workspace_loader.load_workspace(*args, **kwargs)

    def _on_workspace_saved(self, workspace_id: int, workspace_name: str):
        """Workspace 儲存完成的回調"""
        logger.debug(f"[WORKSPACE] ✅ Workspace 已儲存: ID={workspace_id}, Name={workspace_name}")
        # 未來可以在這裡添加 Recent Workspaces 更新邏輯
    
    def _on_workspace_loaded(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceLoadedHandler"""
        from windows.managers.workspace_loaded_handler import WorkspaceLoadedHandler
        if not hasattr(self, '_workspace_loaded_handler'):
            self._workspace_loaded_handler = WorkspaceLoadedHandler(self)
        return self._workspace_loaded_handler._on_workspace_loaded(*args, **kwargs)

    def _update_all_mdi_scroll_areas(self, *args, **kwargs):
        """代理方法 - 委派給 MdiScrollUpdater"""
        from windows.managers.mdi_scroll_updater import MdiScrollUpdater
        if not hasattr(self, '_mdi_scroll_updater'):
            self._mdi_scroll_updater = MdiScrollUpdater(self)
        return self._mdi_scroll_updater._update_all_mdi_scroll_areas(*args, **kwargs)

    def _tile_all_workspace_windows_delayed(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceTilerDelayed"""
        from windows.managers.workspace_tiler_delayed import WorkspaceTilerDelayed
        if not hasattr(self, '_workspace_tiler_delayed'):
            self._workspace_tiler_delayed = WorkspaceTilerDelayed(self)
        return self._workspace_tiler_delayed._tile_all_workspace_windows_delayed(*args, **kwargs)

    def _tile_all_workspace_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceWindowTiler"""
        from windows.managers.workspace_window_tiler import WorkspaceWindowTiler
        if not hasattr(self, '_workspace_window_tiler'):
            self._workspace_window_tiler = WorkspaceWindowTiler(self)
        return self._workspace_window_tiler._tile_all_workspace_windows(*args, **kwargs)

    def _build_workspace_snapshot(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceSnapshotBuilder"""
        from windows.managers.workspace_snapshot_builder import WorkspaceSnapshotBuilder
        if not hasattr(self, '_workspace_snapshot_builder'):
            self._workspace_snapshot_builder = WorkspaceSnapshotBuilder(self)
        return self._workspace_snapshot_builder._build_workspace_snapshot(*args, **kwargs)

    def _collect_open_windows_state(self) -> List[Dict[str, Any]]:
        """蒐集目前開啟的分析視窗狀態以支援工作區還原"""
        open_windows: List[Dict[str, Any]] = []
        for subwindow in getattr(self, "active_subwindows", []) or []:
            if not isinstance(subwindow, PopoutSubWindow):
                continue
            state = self._collect_subwindow_state(subwindow)
            if state:
                open_windows.append(state)
        return open_windows

    def _collect_subwindow_state(self, *args, **kwargs):
        """代理方法 - 委派給 SubwindowStateCollector"""
        from windows.managers.subwindow_state_collector import SubwindowStateCollector
        if not hasattr(self, '_subwindow_state_collector'):
            self._subwindow_state_collector = SubwindowStateCollector(self)
        return self._subwindow_state_collector._collect_subwindow_state(*args, **kwargs)

    def _collect_module_state(self, *args, **kwargs):
        """代理方法 - 委派給 ModuleStateCollector"""
        from windows.managers.module_state_collector import ModuleStateCollector
        if not hasattr(self, '_module_state_collector'):
            self._module_state_collector = ModuleStateCollector(self)
        return self._module_state_collector._collect_module_state(*args, **kwargs)

    def _apply_workspace_snapshot(self, *args, **kwargs):
        """代理方法 - 委派給 WorkspaceSnapshotApplier"""
        from windows.managers.workspace_snapshot_applier import WorkspaceSnapshotApplier
        if not hasattr(self, '_workspace_snapshot_applier'):
            self._workspace_snapshot_applier = WorkspaceSnapshotApplier(self)
        return self._workspace_snapshot_applier._apply_workspace_snapshot(*args, **kwargs)

    def _restore_open_windows(self, *args, **kwargs):
        """代理方法 - 委派給 OpenWindowsRestorer"""
        from windows.managers.open_windows_restorer import OpenWindowsRestorer
        if not hasattr(self, '_open_windows_restorer'):
            self._open_windows_restorer = OpenWindowsRestorer(self)
        return self._open_windows_restorer._restore_open_windows(*args, **kwargs)

    def _restore_single_window(self, *args, **kwargs):
        """代理方法 - 委派給 SingleWindowRestorer"""
        from windows.managers.single_window_restorer import SingleWindowRestorer
        if not hasattr(self, '_single_window_restorer'):
            self._single_window_restorer = SingleWindowRestorer(self)
        return self._single_window_restorer._restore_single_window(*args, **kwargs)

    def _instantiate_module_from_state(self, *args, **kwargs):
        """代理方法 - 委派給 ModuleInstantiator"""
        from windows.managers.module_instantiator import ModuleInstantiator
        if not hasattr(self, '_module_instantiator'):
            self._module_instantiator = ModuleInstantiator(self)
        return self._module_instantiator._instantiate_module_from_state(*args, **kwargs)

    def _apply_module_parameters(self, *args, **kwargs):
        """代理方法 - 委派給 ModuleParamsApplier"""
        from windows.managers.module_params_applier import ModuleParamsApplier
        if not hasattr(self, '_module_params_applier'):
            self._module_params_applier = ModuleParamsApplier(self)
        return self._module_params_applier._apply_module_parameters(*args, **kwargs)

    def _find_mdi_area_by_name(self, object_name: Optional[str]) -> Optional['CustomMdiArea']:
        """根據 objectName 尋找已登錄的 MDI 區域"""
        if not object_name:
            return None
        for mdi_area in getattr(self, "mdi_areas", []) or []:
            if mdi_area.objectName() == object_name:
                return mdi_area
        return None

    def export_report(self): 
        #print("[檔案] 匯出報告")
        pass
        
    def lap_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 LapAnalysisLauncher"""
        from windows.managers.lap_analysis_launcher import LapAnalysisLauncher
        if not hasattr(self, '_lap_analysis_launcher'):
            self._lap_analysis_launcher = LapAnalysisLauncher(self)
        return self._lap_analysis_launcher.lap_analysis(*args, **kwargs)

    def create_telemetry_window(self, *args, **kwargs):
        """代理方法 - 委派給 TelemetryWindowCreator"""
        from windows.managers.telemetry_window_creator import TelemetryWindowCreator
        if not hasattr(self, '_telemetry_window_creator'):
            self._telemetry_window_creator = TelemetryWindowCreator(self)
        return self._telemetry_window_creator.create_telemetry_window(*args, **kwargs)

    def get_current_mdi_area(self, *args, **kwargs):
        """代理方法 - 委派給 CurrentMdiGetter"""
        from windows.managers.current_mdi_getter import CurrentMdiGetter
        if not hasattr(self, '_current_mdi_getter'):
            self._current_mdi_getter = CurrentMdiGetter(self)
        return self._current_mdi_getter.get_current_mdi_area(*args, **kwargs)

    def create_placeholder_telemetry_widget(self, *args, **kwargs):
        """代理方法 - 委派給 PlaceholderWidgetCreator"""
        from windows.managers.placeholder_widget_creator import PlaceholderWidgetCreator
        if not hasattr(self, '_placeholder_widget_creator'):
            self._placeholder_widget_creator = PlaceholderWidgetCreator(self)
        return self._placeholder_widget_creator.create_placeholder_telemetry_widget(*args, **kwargs)

    def get_chart_info(self, *args, **kwargs):
        """代理方法 - 委派給 ChartInfoGetter"""
        from windows.managers.chart_info_getter import ChartInfoGetter
        if not hasattr(self, '_chart_info_getter'):
            self._chart_info_getter = ChartInfoGetter(self)
        return self._chart_info_getter.get_chart_info(*args, **kwargs)

    def open_track_analysis_window(self, *args, **kwargs):
        """代理方法 - 委派給 TrackAnalysisOpener"""
        from windows.managers.track_analysis_opener import TrackAnalysisOpener
        if not hasattr(self, '_track_analysis_opener'):
            self._track_analysis_opener = TrackAnalysisOpener(self)
        return self._track_analysis_opener.open_track_analysis_window(*args, **kwargs)

    def _open_season_start_reaction_module(self):
        """開啟年度起跑反應分析模組 (Season Start Reaction)"""
        from windows.managers.season_start_reaction_opener import SeasonStartReactionOpener
        if not hasattr(self, '_season_start_reaction_opener'):
            self._season_start_reaction_opener = SeasonStartReactionOpener(self)
        return self._season_start_reaction_opener.open_season_start_reaction_module()

    def _open_pole_defense_module(self):
        """開啟桿位防守統計模組 (Pole Defense Statistics)"""
        from windows.managers.pole_defense_opener import PoleDefenseOpener
        if not hasattr(self, '_pole_defense_opener'):
            self._pole_defense_opener = PoleDefenseOpener(self)
        return self._pole_defense_opener.open_pole_defense_module()

    def _open_traffic_timeline_module(self):
        """開啟車流時間線分析模組 (Traffic Timeline)"""
        from windows.managers.traffic_timeline_opener import TrafficTimelineOpener
        if not hasattr(self, '_traffic_timeline_opener'):
            self._traffic_timeline_opener = TrafficTimelineOpener(self)
        return self._traffic_timeline_opener.open_traffic_timeline_module()

    def temp_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 TempAnalysisLauncher"""
        from windows.managers.temp_analysis_launcher import TempAnalysisLauncher
        if not hasattr(self, '_temp_analysis_launcher'):
            self._temp_analysis_launcher = TempAnalysisLauncher(self)
        return self._temp_analysis_launcher.temp_analysis(*args, **kwargs)
    
    # 保留 rain_analysis 作為向後相容的別名
    def rain_analysis(self, *args, **kwargs):
        """向後相容別名 - 重定向到 temp_analysis"""
        return self.temp_analysis(*args, **kwargs)

    def open_telemetry_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 TelemetryAnalysisOpener"""
        from windows.managers.telemetry_analysis_opener import TelemetryAnalysisOpener
        if not hasattr(self, '_telemetry_analysis_opener'):
            self._telemetry_analysis_opener = TelemetryAnalysisOpener(self)
        return self._telemetry_analysis_opener.open_telemetry_analysis(*args, **kwargs)

    def telemetry_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 遙測比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def driver_comparison(self): 
        params = self.get_current_parameters()
        #print(f"[分析] 車手比較 - {params['year']} {params['race']} {params['session']}")
        pass
        
    def sector_analysis(self): 
        #print("[分析] 扇區分析")
        pass
    def tile_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WindowTiler"""
        from windows.managers.window_tiler import WindowTiler
        if not hasattr(self, '_window_tiler'):
            self._window_tiler = WindowTiler(self)
        return self._window_tiler.tile_windows(*args, **kwargs)

    def cascade_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WindowCascader"""
        from windows.managers.window_cascader import WindowCascader
        if not hasattr(self, '_window_cascader'):
            self._window_cascader = WindowCascader(self)
        return self._window_cascader.cascade_windows(*args, **kwargs)

    def minimize_all_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WindowMinimizer"""
        from windows.managers.window_minimizer import WindowMinimizer
        if not hasattr(self, '_window_minimizer'):
            self._window_minimizer = WindowMinimizer(self)
        return self._window_minimizer.minimize_all_windows(*args, **kwargs)

    def maximize_all_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WindowMaximizer"""
        from windows.managers.window_maximizer import WindowMaximizer
        if not hasattr(self, '_window_maximizer'):
            self._window_maximizer = WindowMaximizer(self)
        return self._window_maximizer.maximize_all_windows(*args, **kwargs)

    def restore_all_windows(self, *args, **kwargs):
        """代理方法 - 委派給 WindowRestorerAll"""
        from windows.managers.window_restorer_all import WindowRestorerAll
        if not hasattr(self, '_window_restorer_all'):
            self._window_restorer_all = WindowRestorerAll(self)
        return self._window_restorer_all.restore_all_windows(*args, **kwargs)

    def close_all_windows(self, *args, **kwargs):
        """代理方法 - 委派給 AllWindowsCloser"""
        from windows.managers.all_windows_closer import AllWindowsCloser
        if not hasattr(self, '_all_windows_closer'):
            self._all_windows_closer = AllWindowsCloser(self)
        return self._all_windows_closer.close_all_windows(*args, **kwargs)

    def toggle_fullscreen(self, *args, **kwargs):
        """代理方法 - 委派給 FullscreenToggler"""
        from windows.managers.fullscreen_toggler import FullscreenToggler
        if not hasattr(self, '_fullscreen_toggler'):
            self._fullscreen_toggler = FullscreenToggler(self)
        return self._fullscreen_toggler.toggle_fullscreen(*args, **kwargs)

    def open_driver_standings(self, *args, **kwargs):
        """代理方法 - 委派給 DriverStandingsOpener"""
        from windows.managers.driver_standings_opener import DriverStandingsOpener
        if not hasattr(self, '_driver_standings_opener'):
            self._driver_standings_opener = DriverStandingsOpener(self)
        return self._driver_standings_opener.open_driver_standings(*args, **kwargs)

    def open_constructor_standings(self, *args, **kwargs):
        """代理方法 - 委派給 ConstructorStandingsOpener"""
        from windows.managers.constructor_standings_opener import ConstructorStandingsOpener
        if not hasattr(self, '_constructor_standings_opener'):
            self._constructor_standings_opener = ConstructorStandingsOpener(self)
        return self._constructor_standings_opener.open_constructor_standings(*args, **kwargs)

    def open_parts_analysis(self, *args, **kwargs):
        """代理方法 - 委派給 PartsAnalysisOpener"""
        from windows.managers.parts_analysis_opener import PartsAnalysisOpener
        if not hasattr(self, '_parts_analysis_opener'):
            self._parts_analysis_opener = PartsAnalysisOpener(self)
        return self._parts_analysis_opener.open_parts_analysis(*args, **kwargs)

    def open_season_progress(self, *args, **kwargs):
        """代理方法 - 委派給 SeasonProgressOpener"""
        from windows.managers.season_progress_opener import SeasonProgressOpener
        if not hasattr(self, '_season_progress_opener'):
            self._season_progress_opener = SeasonProgressOpener(self)
        return self._season_progress_opener.open_season_progress(*args, **kwargs)

    def data_validation(self): 
        #print("[工具] 數據驗證")
        pass
        
    def system_settings(self): 
        try:
            gui_settings_manager.open_system_settings_dialog(self)
        except Exception as exc:
            logger.error(f"[ERROR] 開啟系統設定時發生錯誤: {exc}")
    
    def set_interface_language(self, *args, **kwargs):
        """代理方法 - 委派給 LanguageSetter"""
        from windows.managers.language_setter import LanguageSetter
        if not hasattr(self, '_language_setter'):
            self._language_setter = LanguageSetter(self)
        return self._language_setter.set_interface_language(*args, **kwargs)

    def refresh_menu_text(self):
        """刷新功能表文字"""
        try:
            # 這裡可以添加即時更新功能表文字的邏輯
            # 目前需要重啟應用程式才能完全生效
            pass
        except Exception as e:
            logger.error(f"[ERROR] 刷新功能表文字失敗: {e}")
        
    def toggle_lap_analysis_linkage(self, *args, **kwargs):
        """代理方法 - 委派給 LapLinkageToggler"""
        from windows.managers.lap_linkage_toggler import LapLinkageToggler
        if not hasattr(self, '_lap_linkage_toggler'):
            self._lap_linkage_toggler = LapLinkageToggler(self)
        return self._lap_linkage_toggler.toggle_lap_analysis_linkage(*args, **kwargs)

    def get_lap_linkage_enabled(self, *args, **kwargs):
        """代理方法 - 委派給 LapLinkageGetter"""
        from windows.managers.lap_linkage_getter import LapLinkageGetter
        if not hasattr(self, '_lap_linkage_getter'):
            self._lap_linkage_getter = LapLinkageGetter(self)
        return self._lap_linkage_getter.get_lap_linkage_enabled(*args, **kwargs)

    def toggle_lap_analysis_x_linkage(self, *args, **kwargs):
        """代理方法 - 委派給 XLinkageToggler"""
        from windows.managers.x_linkage_toggler import XLinkageToggler
        if not hasattr(self, '_x_linkage_toggler'):
            self._x_linkage_toggler = XLinkageToggler(self)
        return self._x_linkage_toggler.toggle_lap_analysis_x_linkage(*args, **kwargs)

    def integrate_linkage_manager(self, *args, **kwargs):
        """代理方法 - 委派給 LinkageIntegrator"""
        from windows.managers.linkage_integrator import LinkageIntegrator
        if not hasattr(self, '_linkage_integrator'):
            self._linkage_integrator = LinkageIntegrator(self)
        return self._linkage_integrator.integrate_linkage_manager(*args, **kwargs)

    def on_linkage_manager_state_changed(self, *args, **kwargs):
        """代理方法 - 委派給 LinkageStateHandler"""
        from windows.managers.linkage_state_handler import LinkageStateHandler
        if not hasattr(self, '_linkage_state_handler'):
            self._linkage_state_handler = LinkageStateHandler(self)
        return self._linkage_state_handler.on_linkage_manager_state_changed(*args, **kwargs)

    def apply_style_h(self, *args, **kwargs):
        """代理方法 - 委派給 StyleApplier"""
        from windows.managers.style_applier import StyleApplier
        if not hasattr(self, '_style_applier'):
            self._style_applier = StyleApplier(self)
        return self._style_applier.apply_style_h(*args, **kwargs)

    def show_error_message(self, title, message):
        """顯示錯誤訊息對話框"""
        from PyQt5.QtWidgets import QMessageBox
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def resizeEvent(self, event):
        """主視窗調整大小時，同步調整固定視窗"""
        super().resizeEvent(event)
        
        # 尋找 Welcome Tab 中的 MDI 區域
        if hasattr(self, 'tab_widget'):
            for i in range(self.tab_widget.count()):
                tab_widget = self.tab_widget.widget(i)
                if tab_widget:
                    # 遞迴搜尋 CustomMdiArea
                    mdi_area = self._find_mdi_area(tab_widget)
                    if mdi_area and hasattr(mdi_area, '_rearrange_fixed_windows'):
                        logger.debug(f"[MAIN_RESIZE] 主視窗調整大小，觸發 MDI 重新排列")
                        mdi_area._rearrange_fixed_windows()

    def _find_mdi_area(self, *args, **kwargs):
        """代理方法 - 委派給 MdiAreaFinder"""
        from windows.managers.mdi_area_finder import MdiAreaFinder
        if not hasattr(self, '_mdi_area_finder'):
            self._mdi_area_finder = MdiAreaFinder(self)
        return self._mdi_area_finder._find_mdi_area(*args, **kwargs)

    def closeEvent(self, *args, **kwargs):
        """代理方法 - 委派給 CloseEventHandler"""
        from windows.managers.close_event_handler import CloseEventHandler
        if not hasattr(self, '_close_event_handler'):
            self._close_event_handler = CloseEventHandler(self)
        return self._close_event_handler.closeEvent(*args, **kwargs)

    def stop_all_analyses(self, *args, **kwargs):
        """代理方法 - 委派給 AnalysisStopper"""
        from windows.managers.analysis_stopper import AnalysisStopper
        if not hasattr(self, '_analysis_stopper'):
            self._analysis_stopper = AnalysisStopper(self)
        return self._analysis_stopper.stop_all_analyses(*args, **kwargs)

    def close_all_subwindows(self, *args, **kwargs):
        """代理方法 - 委派給 SubwindowCloser"""
        from windows.managers.subwindow_closer import SubwindowCloser
        if not hasattr(self, '_subwindow_closer'):
            self._subwindow_closer = SubwindowCloser(self)
        return self._subwindow_closer.close_all_subwindows(*args, **kwargs)

    def on_subwindow_closed(self, *args, **kwargs):
        """代理方法 - 委派給 SubwindowClosedHandler"""
        from windows.managers.subwindow_closed_handler import SubwindowClosedHandler
        if not hasattr(self, '_subwindow_closed_handler'):
            self._subwindow_closed_handler = SubwindowClosedHandler(self)
        return self._subwindow_closed_handler.on_subwindow_closed(*args, **kwargs)

    def _check_and_update_toolbar_status(self, *args, **kwargs):
        """代理方法 - 委派給 ToolbarStatusChecker"""
        from windows.managers.toolbar_status_checker import ToolbarStatusChecker
        if not hasattr(self, '_toolbar_status_checker'):
            self._toolbar_status_checker = ToolbarStatusChecker(self)
        return self._toolbar_status_checker._check_and_update_toolbar_status(*args, **kwargs)

    def remove_welcome_tab(self, *args, **kwargs):
        """代理方法 - 委派給 WelcomeTabRemover"""
        from windows.managers.welcome_tab_remover import WelcomeTabRemover
        if not hasattr(self, '_welcome_tab_remover'):
            self._welcome_tab_remover = WelcomeTabRemover(self)
        return self._welcome_tab_remover.remove_welcome_tab(*args, **kwargs)

    def closeEvent(self, event):
        """
        主視窗關閉事件處理
        
        ⚠️ 資源洩漏修復: 清理所有執行緒、信號和資源，防止 Dummy 執行緒洩漏
        
        清理項目:
        1. 停止 API 健康檢查執行緒 (ApiHealthWorker)
        2. 停止 API 運行時監控執行緒 (ApiRuntimeWorker)
        3. 停止所有定時器 (QTimer)
        4. 關閉所有 MDI 子視窗和分析模組
        5. 斷開所有信號連接
        6. 清理全局管理器
        7. 等待所有 QThread 完全終止（修復 Python 3.13 執行緒清理錯誤）
        """
        logger.debug("[CLEANUP] 🛑 主視窗正在關閉，開始清理資源...")
        
        try:
            # ========== 步驟 0: 收集所有活動的 QThread ==========
            active_threads = []
            
            # 收集 API 監控執行緒
            if hasattr(self, '_api_health_worker') and self._api_health_worker:
                active_threads.append(('ApiHealthWorker', self._api_health_worker))
            if hasattr(self, '_api_runtime_worker') and self._api_runtime_worker:
                active_threads.append(('ApiRuntimeWorker', self._api_runtime_worker))
            
            # 收集所有子視窗中的 QThread
            if hasattr(self, 'mdi_areas') and self.mdi_areas:
                for mdi_area in self.mdi_areas:
                    try:
                        # 檢查 MDI Area 是否仍然有效（未被 C++ 刪除）
                        if not mdi_area or not hasattr(mdi_area, 'subWindowList'):
                            continue
                        
                        # 嘗試獲取子視窗列表
                        sub_windows = mdi_area.subWindowList()
                        
                        for sub_window in sub_windows:
                            try:
                                widget = sub_window.widget()
                                if not widget:
                                    continue
                                
                                # 檢查 Live Timing 模組中的 RealTimeDataSource
                                if hasattr(widget, '_realtime_source'):
                                    source = widget._realtime_source
                                    if source and hasattr(source, '_worker') and source._worker:
                                        if hasattr(source._worker, 'isRunning') and source._worker.isRunning():
                                            active_threads.append(('LiveTiming.RealtimeWorker', source._worker))
                                            logger.debug("[CLEANUP] 🔍 發現 Live Timing 執行緒")
                                
                                # 檢查標準分析模組
                                if hasattr(widget, 'analysis_module'):
                                    module = widget.analysis_module
                                    # 搜索模組中的所有 QThread 屬性
                                    for attr_name in dir(module):
                                        try:
                                            attr = getattr(module, attr_name)
                                            if isinstance(attr, QThread) and attr.isRunning():
                                                active_threads.append((f'{type(module).__name__}.{attr_name}', attr))
                                        except:
                                            pass
                            except RuntimeError:
                                # 子視窗已被刪除，跳過
                                continue
                    except RuntimeError:
                        # MDI Area 已被 C++ 刪除，跳過
                        continue
            
            logger.debug(f"[CLEANUP] 🔍 找到 {len(active_threads)} 個活動執行緒")
            
            # ========== 步驟 1: 停止 API 監控執行緒 ==========
            logger.debug("[CLEANUP] 📡 停止 API 監控執行緒...")
            
            # 停止 API 健康檢查執行緒
            if hasattr(self, '_api_health_worker') and self._api_health_worker:
                try:
                    logger.debug("[CLEANUP]   🔴 停止 ApiHealthWorker...")
                    self._api_health_worker_active = False
                    self._api_health_worker.quit()
                    if not self._api_health_worker.wait(3000):  # 等待 3 秒
                        logger.debug("[CLEANUP]   ⚠️ ApiHealthWorker 未正常退出，強制終止")
                        self._api_health_worker.terminate()
                        self._api_health_worker.wait(1000)
                    logger.debug("[CLEANUP]   ✅ ApiHealthWorker 已停止")
                except Exception as e:
                    logger.debug(f"[CLEANUP]   ⚠️ 停止 ApiHealthWorker 時出錯: {e}")
                finally:
                    self._api_health_worker = None
            
            # 停止 API 運行時監控執行緒
            if hasattr(self, '_api_runtime_worker') and self._api_runtime_worker:
                try:
                    logger.debug("[CLEANUP]   🔴 停止 ApiRuntimeWorker...")
                    self._api_runtime_worker_active = False
                    self._api_runtime_worker.quit()
                    if not self._api_runtime_worker.wait(3000):  # 等待 3 秒
                        logger.debug("[CLEANUP]   ⚠️ ApiRuntimeWorker 未正常退出，強制終止")
                        self._api_runtime_worker.terminate()
                        self._api_runtime_worker.wait(1000)
                    logger.debug("[CLEANUP]   ✅ ApiRuntimeWorker 已停止")
                except Exception as e:
                    logger.debug(f"[CLEANUP]   ⚠️ 停止 ApiRuntimeWorker 時出錯: {e}")
                finally:
                    self._api_runtime_worker = None
            
            # ========== 步驟 2: 停止所有定時器 ==========
            logger.debug("[CLEANUP] ⏰ 停止所有定時器...")
            
            if hasattr(self, 'api_health_timer') and self.api_health_timer:
                self.api_health_timer.stop()
                logger.debug("[CLEANUP]   ✅ api_health_timer 已停止")
            
            if hasattr(self, 'api_runtime_timer') and self.api_runtime_timer:
                self.api_runtime_timer.stop()
                logger.debug("[CLEANUP]   ✅ api_runtime_timer 已停止")
            
            if hasattr(self, '_parameter_broadcast_timer') and self._parameter_broadcast_timer:
                self._parameter_broadcast_timer.stop()
                logger.debug("[CLEANUP]   ✅ _parameter_broadcast_timer 已停止")
            
            # ========== 步驟 3: 關閉所有 MDI 子視窗 ==========
            logger.debug("[CLEANUP] 🪟 關閉所有 MDI 子視窗...")
            
            if hasattr(self, 'mdi_areas') and self.mdi_areas:
                for mdi_area in self.mdi_areas:
                    try:
                        # 檢查 MDI Area 是否仍然有效
                        if not mdi_area or not hasattr(mdi_area, 'closeAllSubWindows'):
                            continue
                        
                        mdi_area.closeAllSubWindows()
                        logger.debug(f"[CLEANUP]   ✅ 已關閉 MDI 區域的所有子視窗")
                    except RuntimeError as e:
                        # MDI Area 已被 C++ 刪除
                        logger.debug(f"[CLEANUP]   ⚠️ MDI Area 已被刪除: {e}")
                    except Exception as e:
                        logger.debug(f"[CLEANUP]   ⚠️ 關閉 MDI 子視窗時出錯: {e}")
            
            # ========== 步驟 4: 等待所有收集到的執行緒完全終止 ==========
            logger.debug(f"[CLEANUP] ⏳ 等待 {len(active_threads)} 個執行緒完全終止...")
            
            for thread_name, thread in active_threads:
                try:
                    if not thread or not hasattr(thread, 'isRunning'):
                        continue
                        
                    if thread.isRunning():
                        logger.debug(f"[CLEANUP]   🔴 停止執行緒: {thread_name}")
                        
                        # 特殊處理 Live Timing 的 SignalR 執行緒
                        if 'RealtimeWorker' in thread_name or 'SignalR' in thread_name:
                            try:
                                # 先調用 stop() 方法（如果有）
                                if hasattr(thread, 'stop'):
                                    logger.debug(f"[CLEANUP]      調用 {thread_name}.stop()")
                                    thread.stop()
                                    # 給予更多時間讓 WebSocket 正常關閉
                                    if not thread.wait(5000):  # 等待 5 秒
                                        logger.debug(f"[CLEANUP]   ⚠️ {thread_name} 未正常退出，強制終止")
                                        thread.terminate()
                                        thread.wait(1000)
                                else:
                                    # 沒有 stop() 方法，直接 quit
                                    thread.quit()
                                    if not thread.wait(3000):
                                        thread.terminate()
                                        thread.wait(1000)
                            except Exception as e:
                                logger.debug(f"[CLEANUP]   ⚠️ 停止 {thread_name} 時出錯: {e}")
                        else:
                            # 標準執行緒清理
                            thread.quit()
                            if not thread.wait(3000):  # 等待 3 秒
                                logger.debug(f"[CLEANUP]   ⚠️ {thread_name} 未正常退出，強制終止")
                                thread.terminate()
                                thread.wait(1000)
                        
                        logger.debug(f"[CLEANUP]   ✅ {thread_name} 已完全終止")
                except RuntimeError as e:
                    # 執行緒物件已被 C++ 刪除
                    logger.debug(f"[CLEANUP]   ⚠️ {thread_name} 已被刪除: {e}")
                except Exception as e:
                    logger.debug(f"[CLEANUP]   ⚠️ 終止執行緒 {thread_name} 時出錯: {e}")
            
            # ========== 步驟 5: 清理追蹤列表 ==========
            logger.debug("[CLEANUP] 📋 清理追蹤列表...")
            
            if hasattr(self, 'active_subwindows'):
                self.active_subwindows.clear()
                logger.debug("[CLEANUP]   ✅ active_subwindows 已清空")
            
            if hasattr(self, 'lap_analysis_windows'):
                self.lap_analysis_windows.clear()
                logger.debug("[CLEANUP]   ✅ lap_analysis_windows 已清空")
            
            if hasattr(self, 'active_analysis_tabs'):
                self.active_analysis_tabs.clear()
                logger.debug("[CLEANUP]   ✅ active_analysis_tabs 已清空")
            
            # ========== 步驟 6: 清理全局管理器 ==========
            logger.debug("[CLEANUP] 🌐 清理全局管理器...")
            
            try:
                from modules.gui.lap_analysis.linkage_manager import linkage_manager
                if linkage_manager:
                    linkage_manager.clear_all_linkages()
                    logger.debug("[CLEANUP]   ✅ linkage_manager 已清理")
            except Exception as e:
                logger.debug(f"[CLEANUP]   ⚠️ 清理 linkage_manager 時出錯: {e}")
            
            # ========== 步驟 7: 清理功能樹 Widget ==========
            logger.debug("[CLEANUP] 🌳 清理功能樹...")
            
            if hasattr(self, 'function_tree') and self.function_tree:
                try:
                    self.function_tree.cleanup()
                    self.function_tree = None
                    logger.debug("[CLEANUP]   ✅ function_tree 已清理")
                except Exception as e:
                    logger.debug(f"[CLEANUP]   ⚠️ 清理 function_tree 時出錯: {e}")
            
            # ========== 步驟 8: 強制處理所有待處理的事件 ==========
            logger.debug("[CLEANUP] 🔄 處理待處理的 Qt 事件...")
            QApplication.processEvents()
            
            logger.debug("[CLEANUP] ✅ 主視窗資源清理完成")
            
        except Exception as e:
            logger.debug(f"[CLEANUP] ❌ 清理過程中發生錯誤: {e}")
            import traceback
            traceback.print_exc()
        
        # 接受關閉事件
        event.accept()
        logger.debug("[CLEANUP] 🏁 主視窗關閉事件處理完成")


def main():
    """主函數"""
    logger.debug("[MAIN] 啟動 F1T 專業賽車分析工作站...")
    
    # ========== Python 3.13 執行緒警告抑制器 ==========
    # 抑制 Python 3.13 在程式退出時的 Dummy Thread 清理警告
    # 這是 Python 3.13 與 Qt C++ 擴展執行緒互動的已知問題
    import warnings
    
    # 抑制特定的執行緒警告
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="threading")
    
    # 設定 sys.excepthook 來捕獲並忽略執行緒清理錯誤
    original_excepthook = sys.excepthook
    
    def custom_excepthook(exc_type, exc_value, exc_traceback):
        """自定義異常處理器，忽略執行緒清理時的 TypeError"""
        # 忽略 threading.py 中 __del__ 方法的 NoneType 錯誤
        if exc_type == TypeError and "_DeleteDummyThreadOnDel" in str(exc_traceback):
            return  # 靜默忽略
        # 其他異常正常處理
        original_excepthook(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = custom_excepthook
    logger.debug("[MAIN] ✅ Python 3.13 執行緒警告抑制器已啟用")
    
    # ========== Windows 任務欄圖標設定 ==========
    # 在 Windows 上設定 App User Model ID，讓任務欄顯示自定義圖標
    if sys.platform == 'win32':
        try:
            import ctypes
            # 設定 App User Model ID，使應用程式在任務欄中獨立顯示
            myappid = 'F1T.ProfessionalRacingAnalysis.GUI.V060'  # 唯一的應用程式 ID
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            logger.debug("[MAIN] ✅ Windows App User Model ID 已設定")
        except Exception as e:
            logger.debug(f"[MAIN] ⚠️ 設定 App User Model ID 失敗: {e}")
    
    # 必須在 QApplication 創建之前設置，以支援 QWebEngineView
    from PyQt5.QtCore import Qt
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("F1T Professional Racing Analysis Workstation")
    app.setOrganizationName("F1T Professional Racing Analysis Team")
    
    # 設置應用程式圖標（應用程式層級）
    try:
        icon_path = get_resource_path(Path("image") / "logo.ico")
        if icon_path.exists():
            from PyQt5.QtGui import QIcon
            app.setWindowIcon(QIcon(str(icon_path)))
            logger.debug(f"[MAIN] ✅ 應用程式圖標已設定: {icon_path}")
        else:
            logger.debug(f"[MAIN] ⚠️ 找不到圖標檔案: {icon_path}")
    except Exception as e:
        logger.debug(f"[MAIN] ⚠️ 設定應用程式圖標失敗: {e}")
    
    # 設置應用程式字體
    font = QFont("Arial", 8)
    app.setFont(font)
    
    # 設置應用程序在最後一個視窗關閉時退出
    app.setQuitOnLastWindowClosed(True)
    
    # ========== 整合啟動畫面 ==========
    logger.debug("[MAIN] 🎨 創建啟動畫面...")
    from modules.gui.splash_screen import create_splash_screen
    from core.gui_i18n import tr
    
    splash = create_splash_screen(2)  # Version 2: 白底黑字極簡風格
    splash.show()
    app.processEvents()  # 立即顯示啟動畫面
    
    def update_progress(progress: int, message: str):
        """進度更新回調函數"""
        splash.set_progress(progress, message)
        app.processEvents()  # 確保進度立即更新
    
    logger.debug("[MAIN] ✅ 啟動畫面已顯示")
    
    # ========== 創建主視窗（帶錯誤處理）==========
    window = None
    init_error = None
    
    try:
        logger.debug("[MAIN] 🏗️ 創建主視窗...")
        window = StyleHMainWindow(progress_callback=update_progress)
        logger.debug("[MAIN] ✅ 主視窗創建成功")
        
        # 延遲 500ms 後關閉啟動畫面
        QTimer.singleShot(500, splash.close)
        
    except Exception as e:
        logger.debug(f"[MAIN] ❌ 主視窗初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        
        init_error = e
        
        # 更新啟動畫面顯示錯誤
        update_progress(100, tr('splash_error_opening'))
        QTimer.singleShot(1000, splash.close)  # 1秒後關閉
        
        # 嘗試創建最小化的視窗（無進度回調）
        try:
            logger.debug("[MAIN] 🔄 嘗試創建簡化視窗...")
            window = StyleHMainWindow()  # 無回調版本
            logger.debug("[MAIN] ⚠️ 簡化視窗創建成功（功能可能不完整）")
        except Exception as e2:
            logger.debug(f"[MAIN] ❌ 簡化視窗創建也失敗: {e2}")
            # 完全失敗，只關閉啟動畫面
            splash.close()
            raise
    
    # ========== 顯示主視窗 ==========
    if window:
        window.show()
        
        # 如果初始化有錯誤，顯示警告對話框
        if init_error:
            QTimer.singleShot(1500, lambda: QMessageBox.critical(
                window,
                tr('error_initialization_failed'),
                f"{tr('error_init_message')}\n\n{str(init_error)}"
            ))
    
    # 執行事件循環
    result = app.exec_()
    
    logger.debug("[MAIN] 🧹 開始清理應用程式資源...")
    
    # ✅ 步驟 1: 強制處理所有待處理的事件
    app.processEvents()
    
    # ✅ 步驟 2: 智能執行緒清理（避免卡住）
    import threading
    import time
    from PyQt5.QtCore import QThread
    
    start_time = time.time()
    active_threads = [t for t in threading.enumerate() if t != threading.main_thread()]
    
    if active_threads:
        logger.debug(f"[MAIN] ⏳ 檢測到 {len(active_threads)} 個活動執行緒")
        
        # 分類執行緒
        qthreads = []
        dummy_threads = []
        other_threads = []
        
        for thread in active_threads:
            thread_name = thread.name
            thread_class = thread.__class__.__name__
            
            # 跳過 DummyThread（這些無法 join，會自動清理）
            if 'Dummy' in thread_class or 'dummy' in thread_name.lower():
                dummy_threads.append(thread)
                continue
            
            # QThread 需要特殊處理
            if isinstance(thread, QThread):
                qthreads.append(thread)
                # ✅ 嘗試停止 QThread
                if thread.isRunning():
                    thread.requestInterruption()
                    thread.quit()  # 退出事件循環
            else:
                other_threads.append(thread)
        
        # 輸出執行緒分類
        if dummy_threads:
            logger.debug(f"[MAIN]   ⚠️  {len(dummy_threads)} 個 DummyThread (跳過等待)")
        if qthreads:
            logger.debug(f"[MAIN]   🔵 {len(qthreads)} 個 QThread")
        if other_threads:
            logger.debug(f"[MAIN]   🟡 {len(other_threads)} 個其他執行緒")
        
        # 僅等待 QThread 和其他執行緒（短超時）
        threads_to_wait = qthreads + other_threads
        
        if threads_to_wait:
            logger.debug(f"[MAIN] ⏳ 等待 {len(threads_to_wait)} 個執行緒結束（最多 1.5 秒）...")
            
            for thread in threads_to_wait:
                # 計算剩餘時間
                elapsed = time.time() - start_time
                remaining = max(0, 1.5 - elapsed)  # 增加到 1.5 秒
                
                if remaining <= 0:
                    logger.debug(f"[MAIN]   ⏱️  超時，跳過剩餘執行緒")
                    break
                
                if thread.is_alive():
                    thread_id = f"'{thread.name}' ({thread.__class__.__name__})"
                    thread.join(timeout=remaining)
                    if thread.is_alive():
                        logger.debug(f"[MAIN]   ⚠️  執行緒 {thread_id} 未在時限內結束")
                        # ✅ 對於 QThread，嘗試強制終止
                        if isinstance(thread, QThread):
                            logger.debug(f"[MAIN]   🔨 強制終止 QThread {thread_id}")
                            thread.terminate()
                            thread.wait(100)
        
        # 最終狀態
        final_threads = [t for t in threading.enumerate() if t != threading.main_thread()]
        if final_threads:
            logger.debug(f"[MAIN]   ℹ️  剩餘 {len(final_threads)} 個執行緒（將由 Python 自動清理）")
            for t in final_threads:
                logger.debug(f"[MAIN]      - {t.name} ({t.__class__.__name__})")
    
    # ✅ 步驟 3: 強制垃圾回收
    import gc
    collected = gc.collect()
    logger.debug(f"[MAIN] 🗑️  垃圾回收完成，釋放 {collected} 個對象")
    
    logger.debug("[MAIN] 🛑 F1T 程序正常退出")
    sys.exit(result)

if __name__ == "__main__":
    main()
