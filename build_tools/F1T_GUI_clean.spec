# -*- mode: python ; coding: utf-8 -*-
# F1T GUI - 精簡版 PyInstaller 配置
# 使用乾淨虛擬環境建構，確保最小依賴
# 更新日期：2025-12-20
#
# 🔒 日誌系統政策：
# - EXE 模式下預設禁用所有日誌輸出（透過 runtime_hook_disable_logger.py）
# - 設定環境變數 F1T_EXE_DISABLE_LOG=1 來禁用日誌
# - 如需啟用 EXE 日誌（除錯用），移除或註釋 runtime_hooks 中的 hook
# - 開發模式（非 EXE）不受影響，日誌正常運作

from pathlib import Path
import certifi
import sys
from PyInstaller.utils.hooks import collect_submodules

# 導入版本號
sys.path.insert(0, str(Path(SPECPATH).parent))
try:
    from config.version import APP_VERSION
except ImportError:
    APP_VERSION = "V0.15.1"

# 直接使用版本號（保留 "V" 前綴）
version_str = APP_VERSION

block_cipher = None

# 項目根目錄
project_root = Path(SPECPATH).parent

# Python 標準庫路徑 (用於手動添加 unittest)
import sysconfig
stdlib_path = Path(sysconfig.get_paths()['stdlib'])

# 需要包含的數據檔案和資料夾
added_files = [
    # ========== Python 標準庫模組 (Python 3.13 相容性) ==========
    # unittest 模組 - PyInstaller 在 Python 3.13 中無法自動收集
    (str(stdlib_path / 'unittest'), 'unittest'),
    
    # 圖標和圖片資源
    (str(project_root / 'image'), 'image'),
    
    # 字體資源 (PDF 報告用)
    (str(project_root / 'fonts'), 'fonts'),
    
    # 配置檔案
    (str(project_root / 'config'), 'config'),
    
    # 核心模組
    (str(project_root / 'core'), 'core'),
    
    # GUI 模組（整個資料夾）
    (str(project_root / 'modules' / 'gui'), 'modules/gui'),
    
    # Strategy Simulator 模組（整個資料夾）- 新增
    (str(project_root / 'strategy_simulator'), 'strategy_simulator'),
    
    # Windows 模組（整個資料夾）- 新增
    (str(project_root / 'windows'), 'windows'),
    
    
    # ⚠️ CLI_modules 已移除 - GUI EXE 不需要 CLI 功能
    # 如需 CLI 功能，請使用獨立的 CLI 執行檔
    # (str(project_root / 'CLI_modules'), 'CLI_modules'),
    
    # API 模組 - 新增
    (str(project_root / 'api'), 'api'),
    
    # ✅ SSL 證書（API HTTPS 連線必須）
    (certifi.where(), 'certifi'),
]

# 📊 JSON 數據檔案（API 降級用）
# 動態收集最新的 season_calendar 和 weather JSON
import glob

# 添加最新的 season_calendar multi_year JSON
season_jsons = glob.glob(str(project_root / 'json' / 'season_calendar_multi_year_*.json'))
if season_jsons:
    latest_season = sorted(season_jsons, key=lambda x: Path(x).stat().st_mtime, reverse=True)[0]
    added_files.append((latest_season, 'json'))

# 添加 weather 資料夾（如果存在）
weather_dir = project_root / 'json' / 'weather'
if weather_dir.exists():
    added_files.append((str(weather_dir), 'json/weather'))

# 添加 track_circuit_data JSON 檔案（DRS 區域、彎道資料等）
track_circuit_files = glob.glob(str(project_root / 'json' / 'track_circuit_data_*.json'))
for track_file in track_circuit_files:
    added_files.append((track_file, 'json'))


# 隱藏導入 - 必須明確列出的模組
hidden_imports = [
    # ========== PyQt5 核心組件 ==========
    'PyQt5.QtCore',
    'PyQt5.QtGui',
    'PyQt5.QtWidgets',
    'PyQt5.QtNetwork',
    'PyQt5.QtPrintSupport',
    
    # ========== 數據處理 ==========
    'pandas',
    'pandas.core',
    'pandas.io',
    'pandas.io.formats',
    'pandas.io.formats.style',
    'numpy',
    'numpy.core',
    'scipy',
    'scipy.interpolate',
    'scipy.signal',
    
    # ========== 視覺化 ==========
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.figure',
    'matplotlib.colors',
    'matplotlib.cm',
    'PIL',
    'PIL.Image',
    
    # ========== HTTP 和網路 ==========
    'requests',
    'urllib3',
    'urllib3.exceptions',
    'urllib3.util',
    'certifi',
    'email',
    'email.mime',
    'email.mime.multipart',
    'email.mime.text',
    
    # ========== 測試模組（部分功能依賴）==========
    # 使用 collect_submodules 確保完整收集
    *collect_submodules('unittest'),
    
    # ========== 日期時間處理 ==========
    'datetime',
    'dateutil',
    'dateutil.parser',
    'pytz',
    
    # ========== JSON 和序列化 ==========
    'json',
    'pickle',
    
    # ========== 表格輸出 ==========
    'prettytable',
    'openpyxl',
    
    # ========== PDF 生成 ==========
    'reportlab',
    'reportlab.lib',
    'reportlab.lib.pagesizes',
    'reportlab.lib.units',
    'reportlab.lib.utils',
    'reportlab.lib.colors',
    'reportlab.pdfgen',
    'reportlab.pdfgen.canvas',
    
    # ========== 專案核心模組 ==========
    'core.logger',
    'core.gui_i18n',
    'core.api_base_url',
    'core.api_runtime_state',
    'core.dependency_guard',
    'core.gui_settings_manager',
    'core.memory_monitor',
    'core.workspace_serializer',
    'core.workspace_database',
    'core.runtime_status_resolver',
    'core.f1tv_auth',
    'core.gui_help_catalog',
    'core.cli_help_catalog',
    'core.cli_language',
    'config.version',
    
    # ========== API 模組 ==========
    'api',
    'api.services',
    'api.services.cache_service',
    'api.services.cache_service_v2',
    'api.services.simple_analysis_service',
    'api.routers',
    'api.routers.analysis',
    'api.routers.cache',
    'api.routers.config',
    'api.middleware',
    'api.models',
    
    # ========== GUI 基礎模組 ==========
    'modules.gui.base',
    'modules.gui.base.universal_analysis_mdi_base',
    'modules.gui.base.universal_data_loader_base',
    'modules.gui.base.universal_chart_widget_base',
    'modules.gui.base.universal_stint_selector',
    'modules.gui.base.async_loading_progress',
    'modules.gui.base.global_chart_sync_signal',
    'modules.gui.base.loading_indicator',
    'modules.gui.interfaces',
    'modules.gui.interfaces.analysis_module',
    'modules.gui.themes',
    'modules.gui.themes.color_palette_provider',
    'modules.gui.shared',
    'modules.gui.shared.season_calendar_provider',
    'modules.gui.settings',
    'modules.gui.settings.system_settings_dialog',
    'modules.gui.diagnostics',
    'modules.gui.diagnostics.objgraph_window',
    'modules.gui.universal_chart_widget',
    'modules.gui.telemetry_analysis_mdi',
    'modules.gui.telemetry_modules',
    
    # ========== All Drivers 分析模組（新結構）==========
    'modules.gui.all_drivers',
    
    # Acceleration Chart 模組 (F121)
    'modules.gui.all_drivers.acceleration',
    'modules.gui.all_drivers.acceleration.acceleration_chart_mdi',
    'modules.gui.all_drivers.acceleration.acceleration_chart_module',
    'modules.gui.all_drivers.acceleration.acceleration_chart_data_loader',
    'modules.gui.all_drivers.acceleration.acceleration_chart_widget',
    'modules.gui.all_drivers.acceleration.register_module',
    
    # Brake Chart 模組 (F122)
    'modules.gui.all_drivers.brake',
    'modules.gui.all_drivers.brake.brake_chart_mdi',
    'modules.gui.all_drivers.brake.brake_chart_module',
    'modules.gui.all_drivers.brake.brake_chart_data_loader',
    'modules.gui.all_drivers.brake.brake_chart_widget',
    'modules.gui.all_drivers.brake.all_drivers_brake_all_laps_mdi',
    'modules.gui.all_drivers.brake.all_drivers_brake_all_laps_module',
    'modules.gui.all_drivers.brake.all_drivers_brake_all_laps_table_widget',
    'modules.gui.all_drivers.brake.all_drivers_brake_performance_mdi',
    'modules.gui.all_drivers.brake.all_drivers_brake_performance_module',
    'modules.gui.all_drivers.brake.all_drivers_brake_performance_table_widget',
    'modules.gui.all_drivers.brake.all_drivers_brake_performance_widget',
    'modules.gui.all_drivers.brake.all_drivers_brake_performance_dual_view',
    'modules.gui.all_drivers.brake.brake_all_laps_loader',
    'modules.gui.all_drivers.brake.brake_performance_loader',
    'modules.gui.all_drivers.brake.register_module',
    
    # Max Speed 模組
    'modules.gui.all_drivers.max_speed',
    'modules.gui.all_drivers.max_speed.all_drivers_max_speed_mdi',
    'modules.gui.all_drivers.max_speed.all_drivers_max_speed_module',
    'modules.gui.all_drivers.max_speed.max_speed_data_loader',
    'modules.gui.all_drivers.max_speed.all_drivers_max_speed_table_widget',
    
    # Corner Performance 模組
    'modules.gui.all_drivers.corner_performance',
    'modules.gui.all_drivers.corner_performance.all_drivers_corner_performance_mdi',
    'modules.gui.all_drivers.corner_performance.corner_performance_loader',
    'modules.gui.all_drivers.corner_performance.corner_performance_scatter_widget',
    
    # Straight Line Speed 模組
    'modules.gui.all_drivers.straight_line_speed',
    'modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_mdi',
    'modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_module',
    'modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_dual_view',
    'modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_table_widget',
    'modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_widget',
    'modules.gui.all_drivers.straight_line_speed.register_module',
    
    # ========== Race Analysis 模組（新結構）==========
    'modules.gui.race_analysis',
    'modules.gui.race_analysis.weather_timeline',
    'modules.gui.race_analysis.weather_timeline.weather_timeline_mdi',
    'modules.gui.race_analysis.weather_timeline.weather_timeline_widget',
    'modules.gui.race_analysis.weather_timeline.weather_timeline_data_loader',
    
    'modules.gui.race_analysis.pitstop',
    'modules.gui.race_analysis.pitstop.pitstop_analysis_mdi',
    
    'modules.gui.race_analysis.position',
    'modules.gui.race_analysis.position.driver_position_analysis_mdi',
    'modules.gui.race_analysis.position.driver_position_analysis_module',
    'modules.gui.race_analysis.position.driver_position_analysis_widget',
    
    'modules.gui.race_analysis.track',
    'modules.gui.race_analysis.track.track_analysis_module',
    
    'modules.gui.race_analysis.accident',
    'modules.gui.race_analysis.weather_timeline',
    'modules.gui.race_analysis.track_elevation',
    'modules.gui.race_analysis.track_map',
    'modules.gui.race_analysis.track_map.historical_track_map_mdi',
    'modules.gui.race_analysis.track_map.historical_track_map_data_loader',
    'modules.gui.race_analysis.track_map.speed_distribution_widget',
    
    'modules.gui.race_analysis.start_reaction',
    'modules.gui.race_analysis.traffic_analysis',
    
    # ========== Driver Race 模組 ==========
    'modules.gui.driver_race',
    'modules.gui.driver_race.detailed_lap_analysis',
    'modules.gui.driver_race.lap_box_plot_analysis',
    'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi',
    'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget',
    
    # ========== Championship 相關模組 ==========
    'modules.gui.championship',
    'modules.gui.championship_standings_demo',
    'modules.gui.constructor_standings',
    'modules.gui.constructor_standings.constructor_standings_mdi',
    'modules.gui.constructor_standings.constructor_standings_widget',
    'modules.gui.driver_standings',
    'modules.gui.driver_standings.driver_standings_mdi',
    'modules.gui.driver_standings.driver_standings_widget',
    'modules.gui.season_progress',
    'modules.gui.season_progress.season_progress_mdi',
    'modules.gui.season_progress.season_progress_widget',
    
    # ========== Multi-Season 分析模組 ==========
    'modules.gui.multi_season',
    'modules.gui.multi_season.season_start_reaction',
    'modules.gui.multi_season.season_start_reaction.season_start_reaction_mdi',
    'modules.gui.multi_season.season_start_reaction.season_start_reaction_chart_widget',
    'modules.gui.multi_season.pole_defense',
    'modules.gui.multi_season.pole_defense.pole_defense_mdi',
    'modules.gui.multi_season.pole_defense.pole_defense_chart_widget',
    
    # ========== 其他 GUI 分析模組 ==========
    'modules.gui.tire_analysis',
    'modules.gui.tire_analysis.tire_analysis_mdi',
    'modules.gui.tire_analysis.tire_analysis_module',
    'modules.gui.tire_analysis.tire_analysis_chart_widget',
    
    'modules.gui.lap_analysis',
    'modules.gui.telemetry',
    'modules.gui.driver_analysis',
    'modules.gui.classification_analysis',
    
    # ========== Long Run Analysis 模組（新增）==========
    'modules.gui.long_run_analysis',
    'modules.gui.long_run_analysis.long_run_mdi',
    'modules.gui.long_run_analysis.long_run_data_loader',
    'modules.gui.long_run_analysis.long_run_calculator',
    
    'modules.gui.laptime_prediction_compare',
    'modules.gui.qualifying_prediction',
    'modules.gui.qualifying_prediction.qualifying_prediction_mdi',
    'modules.gui.fp2_qualifying_prediction',
    'modules.gui.fp2_qualifying_prediction.fp2_qualifying_prediction_mdi',
    'modules.gui.race_prediction',
    'modules.gui.race_prediction.race_prediction_mdi',
    
    'modules.gui.partupdated_analysis',
    'modules.gui.partupdated_analysis.parts_analysis_mdi',
    
    # ========== Live Timing 模組 ==========
    'modules.gui.live_timing',
    'modules.gui.live_timing.core',
    'modules.gui.live_timing.core.api_client',
    'modules.gui.live_timing.core.base_live_mdi',
    'modules.gui.live_timing.core.data_manager',
    'modules.gui.live_timing.core.database_reader',
    'modules.gui.live_timing.core.realtime_database',
    'modules.gui.live_timing.core.realtime_source',
    'modules.gui.live_timing.core.local_source',
    'modules.gui.live_timing.core.signalr_client',
    'modules.gui.live_timing.core.snapshot_cache',
    'modules.gui.live_timing.core.module_factory',
    'modules.gui.live_timing.core.position_processor',
    'modules.gui.live_timing.core.prediction_worker',
    'modules.gui.live_timing.core.global_sync_signal',
    'modules.gui.live_timing.widgets',
    'modules.gui.live_timing.widgets.f1tv_auth_dialog',
    'modules.gui.live_timing.widgets.f1tv_web_auth_dialog',
    'modules.gui.live_timing.utils',
    'modules.gui.live_timing.live_timing_modules',
    'modules.gui.live_timing.live_timing_modules.battle_insight',
    'modules.gui.live_timing.live_timing_modules.brake_trace',
    'modules.gui.live_timing.live_timing_modules.chase_strategy',
    'modules.gui.live_timing.live_timing_modules.circle_map',
    'modules.gui.live_timing.live_timing_modules.control_dock',
    'modules.gui.live_timing.live_timing_modules.control_panel',
    'modules.gui.live_timing.live_timing_modules.driver_strategy',
    'modules.gui.live_timing.live_timing_modules.drs_trace',
    'modules.gui.live_timing.live_timing_modules.gear_trace',
    'modules.gui.live_timing.live_timing_modules.lap_history',
    'modules.gui.live_timing.live_timing_modules.lap_time_distribution',
    'modules.gui.live_timing.live_timing_modules.live_traffic_timeline',
    'modules.gui.live_timing.live_timing_modules.pit_window',
    'modules.gui.live_timing.live_timing_modules.race_control_messages',
    'modules.gui.live_timing.live_timing_modules.ranking_tower',
    'modules.gui.live_timing.live_timing_modules.ranking_tower_optimized',
    'modules.gui.live_timing.live_timing_modules.rpm_trace',
    'modules.gui.live_timing.live_timing_modules.sector_comparison',
    'modules.gui.live_timing.live_timing_modules.sf_percentage_chart',
    'modules.gui.live_timing.live_timing_modules.speed_trace',
    'modules.gui.live_timing.live_timing_modules.throttle_history',
    'modules.gui.live_timing.live_timing_modules.throttle_trace',
    'modules.gui.live_timing.live_timing_modules.track_map',
    'modules.gui.live_timing.live_timing_modules.track_weather',
    'modules.gui.live_timing.live_timing_modules.traffic_distance',
    'modules.gui.live_timing.live_timing_modules.tyre_strategy',
    
    # ========== Lap Analysis 子模組 ==========
    'modules.gui.lap_analysis',
    'modules.gui.lap_analysis.analysis_module_manager',
    'modules.gui.lap_analysis.telemetry_data_loader_base',
    'modules.gui.lap_analysis.brake_analysis_module',
    'modules.gui.lap_analysis.speed_analysis_module',
    'modules.gui.lap_analysis.throttle_analysis_module',
    'modules.gui.lap_analysis.ideal_lap',
    'modules.gui.lap_analysis.ideal_lap.ideal_lap_options_dialog',
    'modules.gui.lap_analysis.ideal_lap.shared_colors',
    'modules.gui.lap_analysis.linkage',
    'modules.gui.lap_analysis.linkage.linkage_manager',
    'modules.gui.lap_analysis.linkage.linkage_mixin',
    'modules.gui.lap_analysis.linkage.linkage_ui',
    'modules.gui.lap_analysis.linkage.telemetry_generation_helper',
    
    # ========== Traffic Timeline 模組 ==========
    'modules.gui.lap_analysis.traffic_timeline_analysis',
    'modules.gui.lap_analysis.traffic_timeline_analysis.traffic_timeline_analysis_mdi',
    'modules.gui.lap_analysis.traffic_timeline_analysis.traffic_timeline_chart_widget',
    
    # ========== Pedal Behavior Analysis 模組（新增）==========
    'modules.gui.lap_analysis.pedal_behavior_analysis',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_analysis_mdi',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_chart_widget',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_data_manager',
    
    # ========== Lap Analysis 其他子模組 ==========
    'modules.gui.lap_analysis.acceleration_analysis',
    'modules.gui.lap_analysis.brake_analysis',
    'modules.gui.lap_analysis.distancediff_analysis',
    'modules.gui.lap_analysis.gear_analysis',
    'modules.gui.lap_analysis.rpm_analysis',
    'modules.gui.lap_analysis.speeddiff_analysis',
    'modules.gui.lap_analysis.speed_analysis',
    'modules.gui.lap_analysis.Throttle_analysis',
    'modules.gui.lap_analysis.timediff_analysis',
    'modules.gui.lap_analysis.lap_box_plot',
    
    # ========== Splash Screen ==========
    'modules.gui.splash_screen',
    
    # ========== Strategy Simulator 模組 ========== 
    'strategy_simulator',
    'strategy_simulator.gui',
    'strategy_simulator.gui.main_window',
    'strategy_simulator.gui.input_panel',
    'strategy_simulator.gui.results_tabs',
    'strategy_simulator.gui.results_tabs.full_race_tab',
    'strategy_simulator.gui.results_tabs.safety_car_tab',
    'strategy_simulator.gui.results_tabs.strategy_comparison',
    'strategy_simulator.gui.results_tabs.simulation_tab',
    'strategy_simulator.gui.results_tabs.position_analysis_tab',
    'strategy_simulator.gui.results_tabs.opponent_tab',
    'strategy_simulator.gui.results_tabs.fp2_prediction_tab',
    'strategy_simulator.gui.results_tabs.lap_curves',
    'strategy_simulator.gui.results_tabs.detailed_data',
    'strategy_simulator.gui.results_tabs.race_result_analysis_tab',
    'strategy_simulator.gui.i18n_helper',
    'strategy_simulator.core',
    'strategy_simulator.core.lap_simulator',
    'strategy_simulator.core.race_simulator',
    'strategy_simulator.core.monte_carlo',
    'strategy_simulator.core.competitive_monte_carlo',
    'strategy_simulator.core.competitive_optimizer',
    'strategy_simulator.core.opponent_strategy_predictor',
    'strategy_simulator.core.position_tracker',
    'strategy_simulator.core.overtake_calculator',
    'strategy_simulator.core.strategy_optimizer',
    'strategy_simulator.core.blocking_analyzer',
    'strategy_simulator.core.config_loader',
    'strategy_simulator.data',
    'strategy_simulator.data.track_config',
    'strategy_simulator.data.longrun_loader',
    'strategy_simulator.data.team_performance_loader',
    'strategy_simulator.data.track_circuit_analyzer',
    
    # ========== Windows 管理模組 ==========
    'windows',
    'windows.managers',
    'windows.managers.toolbar_builder',
    'windows.managers.menubar_builder',
    'windows.managers.welcome_tab_builder',
    'windows.managers.year_change_handler',
    'windows.managers.mdi_manager',
    'windows.managers.tab_manager',
    'windows.managers.live_timing_manager',
    'windows.managers.workspace_loader',
    'windows.managers.workspace_saver',
    'windows.managers.season_start_reaction_opener',
    'windows.managers.pole_defense_opener',
    'windows.managers.pdf_report_exporter',
    'windows.managers.analysis_module_creator',
    
    'windows.dialogs',
    'windows.dialogs.window_settings_dialog',
    'windows.dialogs.lap_analysis_options_dialog',
    
    'windows.widgets',
    'windows.widgets.popout_subwindow',
    'windows.widgets.custom_mdi_area',
    'windows.widgets.context_menu_tree_widget',
    'windows.widgets.draggable_title_bar',
    'windows.widgets.standalone_windows',
    'windows.widgets.telemetry_chart_widget',
    
    'windows.workers',
    'windows.workers.api_workers',
    'windows.workers.cli_workers',
    
    # ========== SignalR (Live Timing) ==========
    'signalrcore',
    'signalrcore.hub_connection_builder',
    'websocket',
    
    # ========== 機器學習 (Race Prediction) ==========
    # sklearn 模組已移至可選依賴，GUI 不需要
]

# 排除的模組 - 減少 EXE 體積
excludes = [
    # GUI 框架
    'tkinter',
    '_tkinter',
    
    # 測試相關
    'unittest',
    'pytest',
    'test',
    'tests',
    
    # 文檔和開發工具
    'doctest',
    # 'pydoc',      # ❗ 不可排除！pyarrow.vendored.docscrape 需要它
    # 'pydoc_data', # ❗ 不可排除！pyarrow.vendored.docscrape 需要它
    
    # 不需要的標準庫
    # 'email',  # ⚠️ 不可排除！urllib3 需要它
    'http.server',
    'xmlrpc',
    # 'argparse',  # ⚠️ 不可排除！某些模組需要它
    
    # ⭐ 機器學習相關（僅 CLI 功能 76 使用，GUI 不需要）
    'catboost',  # 345 MB - Function 76 集成學習訓練
    'torch',     # 305 MB - 未使用
    'torchvision',
    'torchaudio',
    'tensorflow',
    'tensorboard',
    'llvmlite',  # 84 MB - Numba JIT 編譯器
    'numba',
    
    # PyQt5 非必要模組
    'PyQt5.QtWebEngine',
    'PyQt5.QtWebEngineWidgets',
    'PyQt5.QtWebEngineCore',
    'PyQt5.Qt3DCore',
    'PyQt5.Qt3DRender',
    'PyQt5.Qt3DInput',
    'PyQt5.Qt3DAnimation',
    'PyQt5.QtBluetooth',
    'PyQt5.QtDBus',
    'PyQt5.QtDesigner',
    'PyQt5.QtHelp',
    'PyQt5.QtLocation',
    'PyQt5.QtMultimedia',
    'PyQt5.QtMultimediaWidgets',
    'PyQt5.QtNfc',
    'PyQt5.QtOpenGL',
    'PyQt5.QtPositioning',
    'PyQt5.QtQml',
    'PyQt5.QtQuick',
    'PyQt5.QtQuickWidgets',
    'PyQt5.QtRemoteObjects',
    'PyQt5.QtSensors',
    'PyQt5.QtSerialPort',
    'PyQt5.QtSql',
    'PyQt5.QtSvg',
    'PyQt5.QtTest',
    'PyQt5.QtWebChannel',
    'PyQt5.QtWebSockets',
    'PyQt5.QtXml',
    'PyQt5.QtXmlPatterns',
]

# 分析階段
a = Analysis(
    [str(project_root / 'f1t_gui_main.py')],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(project_root / 'hooks' / 'runtime_hook_disable_logger.py')],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ✅ 過濾掉備份檔案和問題檔案（避免 CArchive 錯誤）
import re
backup_pattern = re.compile(r'-XM0152|龜山|\.bak$|\.backup$|~$')

# 過濾 datas
a.datas = [(dest, src, typ) for dest, src, typ in a.datas 
           if not backup_pattern.search(src) and not backup_pattern.search(dest)]

# 過濾 binaries
a.binaries = [(dest, src, typ) for dest, src, typ in a.binaries 
              if not backup_pattern.search(src) and not backup_pattern.search(dest)]

# 純 Python 模組打包
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# 執行檔建構 - 單檔案模式 (--onefile)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name=f'PitWall_{version_str}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'image' / 'logo.ico'),
)
