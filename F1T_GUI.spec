# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['f1t_gui_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('image/logo.png', 'image'),  # Splash screen logo
        ('image/logo.ico', 'image'),  # Application icon
        # GUI 使用 API-ONLY 模式,不打包 JSON
    ],
    hiddenimports=[
        # Throttle Analysis 模組（動態導入）
        'modules.gui.Throttle_analysis.throttle_analysis_options_dialog',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.signal_bus',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_duration_chart_widget',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.lap_time_chart_widget',
        'modules.gui.Throttle_analysis.throttle_line_chart_analysis.linked_chart_widget',
        'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module',
        'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi',
        'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_chart_widget',
        
        # Detailed Lap Analysis 模組（動態導入）
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog',
        'modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module',
        'modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi',
        'modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_chart_widget',
        'modules.gui.driver_race.detailed_lap_analysis.laptime_boxplot_widget',
        'modules.gui.driver_race.detailed_lap_analysis.lap_filter_utils',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_module',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget',
        
        # ⭐ Lap Box Plot Analysis（根目錄版本）
        'modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi',
        'modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_module',
        'modules.gui.lap_box_plot_analysis.lap_box_plot_chart_widget',
        
        # Lap Analysis Chart Widgets（動態導入）
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget',
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi',
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_data_loader',
        'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget',
        'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi',
        'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_data_loader',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_data_loader',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_data_loader',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_data_loader',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_data_loader',
        
        # 其他分析模組（動態導入）
        'modules.gui.pitstop_analysis.pitstop_analysis_mdi',
        'modules.gui.pitstop_analysis.pitstop_analysis_complete',
        'modules.gui.accident_analysis.accident_analysis_mdi',
        'modules.gui.accident_analysis.accident_analysis',
        'modules.gui.accident_analysis.accident_analysis_complete',
        'modules.gui.accident_analysis.accident_data_manager',
        'modules.gui.accident_analysis.accident_statistics_summary',
        'modules.gui.accident_analysis.all_incidents_analysis',
        'modules.gui.accident_analysis.severity_distribution_analysis',
        'modules.gui.accident_analysis.special_incidents_analysis',
        'modules.gui.accident_analysis.team_risk_analysis',
        'modules.gui.telemetry_analysis_mdi',
        'modules.gui.rain_analysis.rain_analysis_module',
        'modules.gui.rain_analysis.rain_analysis_mdi',
        'modules.gui.rain_analysis.rain_analysis_chart_widget',
        'modules.gui.tire_analysis.tire_analysis_module',
        'modules.gui.tire_analysis.tire_analysis_mdi',
        'modules.gui.tire_analysis.tire_analysis_chart_widget',
        
        # ⭐ Track Analysis 模組（完整子模組）
        'modules.gui.track_analysis',
        'modules.gui.track_analysis.track_analysis_mdi',
        'modules.gui.track_analysis.track_analysis_module',
        'modules.gui.track_analysis.track_data_loader',
        'modules.gui.track_analysis.track_data_processor',
        'modules.gui.track_analysis.track_map_widget',
        
        # ⭐ 缺失的 Lap Analysis 子模組（speeddiff, distancediff, timediff）
        'modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi',
        'modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget',
        'modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_data_loader',
        'modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi',
        'modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget',
        'modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_data_loader',
        'modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi',
        'modules.gui.lap_analysis.timediff_analysis.timediff_analysis_chart_widget',
        'modules.gui.lap_analysis.timediff_analysis.timediff_analysis_data_loader',
        
        # ⭐ Championship/Standings 模組
        'modules.gui.constructor_standings',
        'modules.gui.constructor_standings.constructor_standings_mdi',
        'modules.gui.constructor_standings.constructor_standings_widget',
        'modules.gui.constructor_standings.constructor_standings_data_loader',
        'modules.gui.driver_standings',
        'modules.gui.driver_standings.driver_standings_mdi',
        'modules.gui.driver_standings.driver_standings_widget',
        'modules.gui.driver_standings.driver_standings_data_loader',
        'modules.gui.season_progress',
        'modules.gui.season_progress.season_progress_mdi',
        'modules.gui.season_progress.season_progress_widget',
        'modules.gui.season_progress.season_progress_data_loader',
        
        # ⭐ 缺失的 Weather Timeline 模組
        'modules.gui.weather_timeline',
        'modules.gui.weather_timeline.weather_timeline_mdi',
        'modules.gui.weather_timeline.weather_timeline_widget',
        'modules.gui.weather_timeline.weather_timeline_data_loader',
        
        # ⭐ Ideal Lap Analysis 子模組
        'modules.gui.ideal_lap_analysis',
        'modules.gui.ideal_lap_analysis.ideal_lap_options_dialog',
        'modules.gui.ideal_lap_analysis.shared_colors',
        'modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module',
        'modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi',
        'modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_widget',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_module',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_data_loader',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_widget',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_module',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_data_loader',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_widget',
        'modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_table_widget',
        
        # ⭐ 缺失的 Shared 模組
        'modules.gui.shared.season_calendar_provider',
        
        # ⭐ 缺失的 Themes 模組
        'modules.gui.themes.color_palette_provider',
        'modules.gui.themes',
        
        # ⭐ All Drivers 分析模組（新增）
        'modules.gui.all_drivers_brake_performance_analysis',
        'modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_module',
        'modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi',
        'modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_widget',
        'modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_table_widget',
        'modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_dual_view',
        'modules.gui.all_drivers_brake_performance_analysis.brake_performance_loader',
        'modules.gui.all_drivers_brake_performance_analysis.register_module',
        'modules.gui.all_drivers_straight_line_speed_analysis',
        'modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_module',
        'modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi',
        'modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_widget',
        'modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget',
        'modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_dual_view',
        'modules.gui.all_drivers_straight_line_speed_analysis.register_module',
        
        # ⭐ Corner Performance Analysis 模組（V0.6.0 新增）
        'modules.gui.all_drivers_corner_performance_analysis',
        'modules.gui.all_drivers_corner_performance_analysis.all_drivers_corner_performance_mdi',
        'modules.gui.all_drivers_corner_performance_analysis.corner_performance_loader',
        'modules.gui.all_drivers_corner_performance_analysis.corner_performance_scatter_widget',
        
        # ⭐ Corner Box Plot Analysis 模組（V0.6.0 新增）
        
        # ⭐ Qualifying Prediction 模組（V0.7.0 新增）
        'modules.gui.qualifying_prediction',
        'modules.gui.qualifying_prediction.qualifying_prediction_mdi',
        'modules.gui.qualifying_prediction.qualifying_prediction_widget',
        'modules.gui.qualifying_prediction.qualifying_prediction_data_loader',
        
        # ⭐ Driver Position Analysis 模組（V0.7.0 新增）
        'modules.gui.driver_position_analysis',
        'modules.gui.driver_position_analysis.driver_position_analysis_mdi',
        'modules.gui.driver_position_analysis.driver_position_analysis_module',
        'modules.gui.driver_position_analysis.driver_position_analysis_widget',
        
        # ⭐ Settings 模組
        'modules.gui.settings',
        'modules.gui.settings.system_settings_dialog',
        
        # ⭐ Diagnostics 模組 (已移除 objgraph_window)
        'modules.gui.diagnostics',
        
        # ⭐ Driver Analysis 模組
        'modules.gui.driver_analysis',
        'modules.gui.driver_analysis.driver_comprehensive_full',
        'modules.gui.driver_analysis.driver_statistics_overview',
        'modules.gui.driver_analysis.driver_telemetry_statistics',
        
        # ⭐ Championship 模組
        'modules.gui.championship',
        'modules.gui.championship.standings_widgets',
        
        # Module Factory 和 Interfaces
        'modules.gui.interfaces.analysis_module',
        
        # Universal Chart Widget 和 Base 模組
        'modules.gui.splash_screen',
        'modules.gui.universal_chart_widget',
        'modules.gui.base.universal_data_loader_base',
        'modules.gui.base.universal_chart_widget_base',
        'modules.gui.base.universal_analysis_mdi_base',
        
        # ⭐ Telemetry Base 模組（實際檔案）
        'modules.gui.lap_analysis.telemetry_data_loader_base',
        
        # ⭐ Lap Analysis Linkage 模組（實際檔案）
        'modules.gui.lap_analysis.linkage',
        'modules.gui.lap_analysis.linkage.linkage_manager',
        'modules.gui.lap_analysis.linkage.linkage_mixin',
        'modules.gui.lap_analysis.linkage.linkage_ui',
        'modules.gui.lap_analysis.linkage.telemetry_generation_helper',
        
        # ⭐ FIA Parts Analysis 模組 (V0.7.0 新增)
        'modules.gui.partupdated_analysis',
        'modules.gui.partupdated_analysis.parts_analysis_mdi',
        'modules.gui.partupdated_analysis.parts_analysis_widget',
        
        # ⭐ Championship Demo（如果存在）
        'modules.gui.championship_standings_demo',
        'modules.gui.championship_standings_demo.standings_data_loader',
        'modules.gui.championship_standings_demo.standings_demo_widget',
        
        # ⭐ Live Timing 模組（V0.9.0 完整新增）
        'modules.gui.live_timing',
        'modules.gui.live_timing.core',
        'modules.gui.live_timing.core.api_client',
        'modules.gui.live_timing.core.base_live_mdi',
        'modules.gui.live_timing.core.data_manager',
        'modules.gui.live_timing.core.f1_api_downloader',
        'modules.gui.live_timing.core.local_source',
        'modules.gui.live_timing.core.module_factory',
        'modules.gui.live_timing.core.position_processor',
        'modules.gui.live_timing.core.realtime_source',
        'modules.gui.live_timing.core.signalr_client',
        'modules.gui.live_timing.core.snapshot_cache',
        'modules.gui.live_timing.live_timing_modules',
        'modules.gui.live_timing.live_timing_modules.battle_insight',
        'modules.gui.live_timing.live_timing_modules.circle_map',
        'modules.gui.live_timing.live_timing_modules.control_dock',
        'modules.gui.live_timing.live_timing_modules.control_panel',
        'modules.gui.live_timing.live_timing_modules.driver_strategy',
        'modules.gui.live_timing.live_timing_modules.lap_history',
        'modules.gui.live_timing.live_timing_modules.lap_time_distribution',
        'modules.gui.live_timing.live_timing_modules.pit_window',
        'modules.gui.live_timing.live_timing_modules.race_control_messages',
        'modules.gui.live_timing.live_timing_modules.ranking_tower',
        'modules.gui.live_timing.live_timing_modules.sector_comparison',
        'modules.gui.live_timing.live_timing_modules.speed_trace',
        'modules.gui.live_timing.live_timing_modules.track_map',
        'modules.gui.live_timing.live_timing_modules.tyre_strategy',
        
        # ⭐ Live Timing Widgets（F1TV WebView2 認證）
        'modules.gui.live_timing.widgets',
        'modules.gui.live_timing.widgets.f1tv_webview_auth',
        
        # ⭐ Race Prediction 模組（V0.9.0 新增）
        'modules.gui.race_prediction',
        'modules.gui.race_prediction.race_prediction_mdi',
        'modules.gui.race_prediction.race_prediction_widget',
        'modules.gui.race_prediction.race_prediction_data_loader',
        
        # ⭐ Track Elevation 模組（V0.9.0 新增）
        'modules.gui.track_elevation',
        'modules.gui.track_elevation.elevation_chart_widget',
        'modules.gui.track_elevation.elevation_chart_widget_pyqt5',
        
        # ⭐ Historical Track Map 模組（V0.9.0 新增）
        'modules.gui.Historical_track_map',
        'modules.gui.Historical_track_map.historical_track_map_mdi',
        'modules.gui.Historical_track_map.historical_track_map_data_loader',
        'modules.gui.Historical_track_map.speed_distribution_widget',
        
        # ⭐ Classification Analysis 模組（V0.9.0 新增）
        'modules.gui.classification_analysis',
        'modules.gui.classification_analysis.demo_launcher',
        
        # Core 模組
        'core.dependency_guard',
        'core.logger',
        'core.api_base_url',
        'core.gui_i18n',
        'core.gui_help_catalog',
        'core.gui_settings_manager',
        'core.runtime_status_resolver',
        'core.api_runtime_state',
        
        # ⭐ 第三方庫的隱藏依賴
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'numpy.core._multiarray_umath',
        'pandas._libs',
        'pandas._libs.tslibs.timedeltas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'requests.adapters',
        'requests.auth',
        'requests.cookies',
        'requests.models',
        'requests.sessions',
        'requests.structures',
        
        # ⭐ pywebview（F1TV 登入認證）
        'webview',
        'webview.window',
        'webview.guilib',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyinstaller_runtime_hook.py'],  # 啟動時自動設置 F1_LOG_LEVEL=DEBUG
    excludes=[
        # 排除 PyTorch 相關模組（GUI 不需要，且會造成 PyInstaller 衝突）
        'torch',
        'torchvision',
        'torchaudio',
        'torch._C',
        'torch.cuda',
        'torch.backends',
        # 排除 TensorFlow 相關
        'tensorflow',
        'tensorflow_core',
        'keras',
        # 排除 scikit-learn（GUI 不需要）
        'sklearn',
        'sklearn.ensemble',
        'sklearn.tree',
        # 排除 scipy（GUI 不需要，只有 CLI 分析用）
        'scipy',
        'scipy.stats',
        'scipy.spatial',
        'scipy.interpolate',
        'scipy.linalg',
        'scipy.optimize',
        'scipy.signal',
        'scipy.sparse',
        'scipy.special',
        'scipy.integrate',
        # 排除 objgraph（Memory Diagnostics 已移除）
        'objgraph',
        # 排除測試模組
        'pytest',
        'unittest',
        '_pytest',
        # 排除其他不需要的大型套件
        'IPython',
        'jupyter',
        'notebook',
        'jupyterlab',
        'sympy',
        'numba',
        'llvmlite',
        'dask',
        'bokeh',
        'holoviews',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='F1T_GUI',
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
    icon='image\\logo.ico',
)
