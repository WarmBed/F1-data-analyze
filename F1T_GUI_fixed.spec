# -*- mode: python ; coding: utf-8 -*-
# F1T GUI - 修正版 PyInstaller 配置
# 確保 logger 和資源文件正常運作

from pathlib import Path

block_cipher = None
project_root = Path(SPECPATH)

# ✅ 包含必要的配置和資源文件
added_files = [
    # Logger 配置（必要）
    (str(project_root / 'config' / 'logging_config.json'), 'config'),

    # 應用程式圖標（必要）
    (str(project_root / 'image' / 'logo.ico'), 'image'),

    # 其他配置文件（建議包含）
    (str(project_root / 'config'), 'config'),

    # 核心模組（必要）
    (str(project_root / 'core'), 'core'),
]

# 隱藏導入（確保必要模組被打包）
hidden_imports = [
    'core.logger',
    'logging.handlers',  # TimedRotatingFileHandler
    # F1TV 認證模組依賴
    'win32crypt',        # Windows DPAPI (Chrome cookie 解密)
    'Crypto',            # pycryptodome
    'Crypto.Cipher',
    'Crypto.Cipher.AES',
    'jwt',               # PyJWT (token 解析)
    
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
    
    # Corner Performance 模組
    'modules.gui.all_drivers.corner_performance',
    'modules.gui.all_drivers.corner_performance.all_drivers_corner_performance_mdi',
    'modules.gui.all_drivers.corner_performance.corner_performance_loader',
    'modules.gui.all_drivers.corner_performance.corner_performance_scatter_widget',
    
    # Windows 管理模組
    'windows.managers.analysis_module_creator',
]

a = Analysis(
    ['f1t_gui_main.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=added_files,  # ✅ 添加資源文件
    hiddenimports=hidden_imports,  # ✅ 添加隱藏導入
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
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
    name='PitWall',
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
    icon=[str(project_root / 'image' / 'logo.ico')],
)
