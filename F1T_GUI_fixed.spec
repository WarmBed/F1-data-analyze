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
