#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1T GUI V0.7.0 - 打包前最終檢查
執行所有必要的驗證，確保可以順利打包
"""

import os
import sys
from pathlib import Path

# 設置 UTF-8 輸出
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_icon(color):
    """檢查狀態圖標"""
    icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️'
    }
    return icons.get(color, '•')

def print_header(title):
    """打印標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_section(title):
    """打印區段標題"""
    print(f"\n{'─' * 70}")
    print(f"📋 {title}")
    print('─' * 70)

# ==================== 開始檢查 ====================
print_header("F1T GUI V0.7.0 - 打包前最終檢查")

all_passed = True
warnings = []

# ==================== 1. 版本資訊檢查 ====================
print_section("1. 版本資訊")

try:
    from config.version import APP_VERSION, APP_FULL_TITLE, VERSION_HISTORY
    print(f"{check_icon('success')} 版本號: {APP_VERSION}")
    print(f"{check_icon('success')} 完整標題: {APP_FULL_TITLE}")
    
    if APP_VERSION in VERSION_HISTORY:
        version_info = VERSION_HISTORY[APP_VERSION]
        print(f"{check_icon('success')} 發布日期: {version_info.get('date', 'Unknown')}")
        print(f"{check_icon('success')} 功能數量: {len(version_info.get('features', []))} 項")
    else:
        print(f"{check_icon('error')} 版本歷史中找不到 {APP_VERSION}")
        all_passed = False
except Exception as e:
    print(f"{check_icon('error')} 無法讀取版本資訊: {e}")
    all_passed = False

# ==================== 2. 必要檔案檢查 ====================
print_section("2. 必要檔案")

required_files = {
    "主程式": "f1t_gui_main.py",
    "SPEC 配置": "F1T_GUI.spec",
    "Runtime Hook": "pyinstaller_runtime_hook.py",
    "版本配置": "config/version.py",
    "Splash Logo": "image/logo.png",
    "應用程式圖標": "image/logo.ico",
}

for desc, filepath in required_files.items():
    if Path(filepath).exists():
        size = Path(filepath).stat().st_size
        if size > 0:
            print(f"{check_icon('success')} {desc}: {filepath} ({size} bytes)")
        else:
            print(f"{check_icon('warning')} {desc}: {filepath} (檔案為空)")
            warnings.append(f"{desc} 檔案為空")
    else:
        print(f"{check_icon('error')} {desc}: {filepath} (不存在)")
        all_passed = False

# ==================== 3. 模組導入檢查 ====================
print_section("3. 關鍵模組導入")

critical_modules = [
    ("GUI 主模組", "f1t_gui_main"),
    ("版本管理", "config.version"),
    ("國際化", "core.gui_i18n"),
    ("顏色配置", "modules.gui.themes.color_palette_provider"),
    ("Parts Analysis", "modules.gui.partupdated_analysis.parts_analysis_mdi"),
    ("Workspace", "modules.gui.workspace.workspace_manager"),
    ("Data Loader", "modules.gui.lap_analysis.base.telemetry_data_loader"),
]

for desc, module_name in critical_modules:
    try:
        __import__(module_name)
        print(f"{check_icon('success')} {desc}: {module_name}")
    except ImportError as e:
        print(f"{check_icon('error')} {desc}: {module_name} - {e}")
        all_passed = False
    except Exception as e:
        print(f"{check_icon('warning')} {desc}: {module_name} - {e}")
        warnings.append(f"{desc} 導入時有警告")

# ==================== 4. PyInstaller 環境檢查 ====================
print_section("4. PyInstaller 環境")

try:
    import PyInstaller
    print(f"{check_icon('success')} PyInstaller 版本: {PyInstaller.__version__}")
except ImportError:
    print(f"{check_icon('error')} PyInstaller 未安裝")
    all_passed = False

# 檢查 UPX（可選）
import subprocess
try:
    result = subprocess.run(['upx', '--version'], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        version_line = result.stdout.split('\n')[0]
        print(f"{check_icon('success')} UPX: {version_line}")
    else:
        print(f"{check_icon('info')} UPX: 未安裝（可選，用於壓縮）")
        warnings.append("UPX 未安裝，EXE 檔案會較大")
except (FileNotFoundError, subprocess.TimeoutExpired):
    print(f"{check_icon('info')} UPX: 未安裝（可選）")
    warnings.append("UPX 未安裝")

# ==================== 5. SPEC 檔案檢查 ====================
print_section("5. SPEC 檔案配置")

try:
    with open("F1T_GUI.spec", 'r', encoding='utf-8') as f:
        spec_content = f.read()
    
    checks = {
        "Runtime Hook": "runtime_hooks=['pyinstaller_runtime_hook.py']",
        "Console=False": "console=False",
        "Debug=False": "debug=False",
        "Icon 配置": "icon='image",
        "Parts Analysis": "modules.gui.partupdated_analysis",
        "Linkage Mixin": "lap_analysis_linkage_mixin",
        "Workspace": "modules.gui.workspace.workspace_manager",
    }
    
    for check_name, check_str in checks.items():
        if check_str in spec_content:
            print(f"{check_icon('success')} {check_name}")
        else:
            print(f"{check_icon('error')} {check_name} 未配置")
            all_passed = False
            
except Exception as e:
    print(f"{check_icon('error')} 無法讀取 SPEC 檔案: {e}")
    all_passed = False

# ==================== 6. 磁碟空間檢查 ====================
print_section("6. 磁碟空間")

try:
    import shutil
    total, used, free = shutil.disk_usage(".")
    free_gb = free / (1024**3)
    
    if free_gb > 5:
        print(f"{check_icon('success')} 可用空間: {free_gb:.2f} GB")
    elif free_gb > 2:
        print(f"{check_icon('warning')} 可用空間: {free_gb:.2f} GB (建議至少 5 GB)")
        warnings.append(f"磁碟空間僅剩 {free_gb:.2f} GB")
    else:
        print(f"{check_icon('error')} 可用空間不足: {free_gb:.2f} GB")
        all_passed = False
except Exception as e:
    print(f"{check_icon('warning')} 無法檢查磁碟空間: {e}")

# ==================== 7. Git 狀態檢查 ====================
print_section("7. Git 狀態")

try:
    import subprocess
    
    # 檢查分支
    branch = subprocess.check_output(['git', 'branch', '--show-current'], text=True).strip()
    print(f"{check_icon('info')} 當前分支: {branch}")
    
    # 檢查未提交的修改
    status = subprocess.check_output(['git', 'status', '--porcelain'], text=True)
    if status:
        modified_count = len(status.strip().split('\n'))
        print(f"{check_icon('warning')} 有 {modified_count} 個未提交的修改")
        warnings.append(f"有 {modified_count} 個未提交的修改")
    else:
        print(f"{check_icon('success')} 工作目錄乾淨")
        
except (FileNotFoundError, subprocess.CalledProcessError):
    print(f"{check_icon('info')} Git 未安裝或不在 Git 倉庫中")

# ==================== 總結 ====================
print("\n" + "=" * 70)
print("檢查結果總結")
print("=" * 70)

if all_passed:
    print(f"\n{check_icon('success')} 所有檢查通過！可以開始打包")
    if warnings:
        print(f"\n{check_icon('warning')} 警告事項 ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    
    print("\n📦 打包命令:")
    print("  完整版: .\\build_exe.ps1")
    print("  快速版: .\\build_exe_quick.ps1")
    print("  手動版: python -m PyInstaller F1T_GUI.spec --clean --noconfirm")
    
    sys.exit(0)
else:
    print(f"\n{check_icon('error')} 發現錯誤，請先修復後再打包")
    if warnings:
        print(f"\n{check_icon('warning')} 警告事項 ({len(warnings)}):")
        for i, warning in enumerate(warnings, 1):
            print(f"  {i}. {warning}")
    sys.exit(1)
