# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['f1t_gui_main.py'],
    pathex=[],
    binaries=[],
    datas=[],  # GUI 使用 API-ONLY 模式,不打包 JSON
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
        'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_data_loader',
        'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_chart_widget',
        
        # Detailed Lap Analysis 模組（動態導入）
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog',
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_analysis_module',
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_analysis_mdi',
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_data_loader',
        'modules.gui.driver_race.detailed_lap_analysis.detailed_lap_chart_widget',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_mdi',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_module',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_data_loader',
        'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_chart_widget',
        
        # Lap Analysis Chart Widgets（動態導入）
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget',
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_module',
        'modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi',
        'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget',
        'modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi',
        'modules.gui.lap_analysis.rpm_analysis.rpm_analysis_module',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi',
        'modules.gui.lap_analysis.gear_analysis.gear_analysis_module',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi',
        'modules.gui.lap_analysis.brake_analysis.brake_analysis_module',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi',
        'modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_module',
        
        # 其他分析模組（動態導入）
        'modules.gui.lap_analysis.lap_time_analysis_module',
        'modules.gui.lap_analysis.lap_time_analysis_mdi',
        'modules.gui.speed_analysis.speed_analysis_module',
        'modules.gui.pitstop_analysis.pitstop_analysis_mdi',
        'modules.gui.pitstop_analysis.pitstop_analysis_module',
        'modules.gui.accident_analysis.accident_analysis_mdi',
        'modules.gui.accident_analysis.accident_analysis_module',
        'modules.gui.telemetry_analysis_mdi',
        'modules.gui.rain_analysis.rain_analysis_module',
        'modules.gui.rain_analysis.rain_analysis_mdi',
        'modules.gui.rain_analysis.rain_analysis_data_loader',
        'modules.gui.rain_analysis.rain_analysis_chart_widget',
        'modules.gui.tire_analysis.tire_analysis_module',
        'modules.gui.tire_analysis.tire_analysis_mdi',
        'modules.gui.tire_analysis.tire_analysis_data_loader',
        'modules.gui.tire_analysis.tire_analysis_chart_widget',
        'modules.gui.track_analysis',
        
        # Module Factory 和 Interfaces
        'modules.gui.interfaces.analysis_module',
        
        # Universal Chart Widget 和 Base 模組
        'modules.gui.universal_chart_widget',
        'modules.gui.throttle_duration_chart_widget',
        'modules.gui.lap_time_chart_widget',
        'modules.gui.base.universal_data_loader_base',
        'modules.gui.base.universal_analysis_mdi',
        
        # Core 模組
        'core.gui_i18n',
        'core.gui_settings_manager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyinstaller_runtime_hook.py'],  # 啟動時自動設置 F1_LOG_LEVEL=DEBUG
    excludes=[],
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
