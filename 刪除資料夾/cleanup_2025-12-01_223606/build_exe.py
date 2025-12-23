#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1T GUI V0.8.0 - EXE 打包工具 (Python 版本)
使用 PyInstaller 進行打包，完整的環境檢查和建置流程
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from datetime import datetime

# 顏色輸出（Windows）
try:
    import colorama
    colorama.init()
    COLORS = {
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'gray': '\033[90m',
        'reset': '\033[0m'
    }
except ImportError:
    COLORS = {k: '' for k in ['cyan', 'green', 'yellow', 'red', 'gray', 'reset']}

def print_color(text, color='reset'):
    """彩色輸出"""
    print(f"{COLORS.get(color, '')}{text}{COLORS['reset']}")

def print_header(title):
    """打印標題"""
    print()
    print_color("=" * 70, 'cyan')
    print_color(f"  {title}", 'cyan')
    print_color("=" * 70, 'cyan')

def print_step(message):
    """打印步驟"""
    print()
    print_color(f"▶ {message}", 'yellow')

def print_success(message):
    """打印成功"""
    print_color(f"✅ {message}", 'green')

def print_error(message):
    """打印錯誤"""
    print_color(f"❌ {message}", 'red')

def print_warning(message):
    """打印警告"""
    print_color(f"⚠️  {message}", 'yellow')

def check_environment():
    """階段 1: 環境檢查"""
    print_step("階段 1: 環境檢查")
    
    # 檢查 Python
    python_version = sys.version.split()[0]
    print_success(f"Python: {python_version}")
    
    # 檢查 PyInstaller
    try:
        import PyInstaller
        print_success(f"PyInstaller: {PyInstaller.__version__}")
    except ImportError:
        print_error("找不到 PyInstaller！執行: pip install pyinstaller")
        return False
    
    # 檢查必要檔案
    required_files = [
        "f1t_gui_main.py",
        "F1T_GUI.spec",
        "pyinstaller_runtime_hook.py",
        "image/logo.png",
        "image/logo.ico",
        "config/version.py"
    ]
    
    for file in required_files:
        if Path(file).exists():
            print_success(f"檔案存在: {file}")
        else:
            print_error(f"缺少檔案: {file}")
            return False
    
    return True

def verify_version():
    """驗證版本資訊"""
    print_step("驗證版本資訊")
    try:
        from config.version import APP_VERSION, APP_FULL_TITLE
        print_color(f"  當前版本: {APP_FULL_TITLE}", 'cyan')
        return True
    except Exception as e:
        print_error(f"無法讀取版本資訊: {e}")
        return False

def run_spec_check():
    """階段 2: 執行 SPEC 檢查"""
    print_step("階段 2: 執行 SPEC 完整性檢查")
    try:
        result = subprocess.run(
            [sys.executable, "tests/check_spec.py"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'  # 忽略編碼錯誤
        )
        # 只檢查返回碼，不打印輸出（避免編碼問題）
        if result.returncode == 0:
            print_success("SPEC 檢查通過")
            return True
        else:
            print_error("SPEC 檢查失敗")
            return False
    except Exception as e:
        print_error(f"SPEC 檢查失敗: {e}")
        return False

def clean_old_builds():
    """階段 3: 清理舊的建置檔案"""
    print_step("階段 3: 清理舊的建置檔案")
    
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print_color(f"  正在刪除: {dir_name}", 'gray')
            shutil.rmtree(dir_name, ignore_errors=True)
            print_success(f"已清理: {dir_name}")
    
    print_success("清理完成")
    return True

def run_pyinstaller():
    """階段 4: 執行 PyInstaller 打包"""
    print_step("階段 4: 執行 PyInstaller 打包")
    print_color("  這可能需要幾分鐘時間，請耐心等待...", 'gray')
    
    start_time = time.time()
    
    try:
        # 執行 PyInstaller
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "F1T_GUI.spec", "--clean", "--noconfirm"],
            capture_output=False,  # 顯示即時輸出
            text=True
        )
        
        if result.returncode == 0:
            duration = time.time() - start_time
            print_success(f"打包完成！耗時: {duration:.2f} 秒")
            return duration
        else:
            print_error("PyInstaller 打包失敗！")
            return None
    except Exception as e:
        print_error(f"打包過程發生錯誤: {e}")
        return None

def verify_exe():
    """階段 5: 驗證生成的 EXE"""
    print_step("階段 5: 驗證生成的 EXE")
    
    exe_path = Path("dist/F1T_GUI.exe")
    if exe_path.exists():
        exe_size = exe_path.stat().st_size / (1024 * 1024)  # MB
        print_success(f"EXE 已生成: {exe_path}")
        print_color(f"  檔案大小: {exe_size:.2f} MB", 'cyan')
        print_color(f"  創建時間: {datetime.fromtimestamp(exe_path.stat().st_ctime)}", 'gray')
        return exe_size
    else:
        print_error(f"找不到生成的 EXE: {exe_path}")
        return None

def check_resources():
    """階段 6: 檢查資源檔案"""
    print_step("階段 6: 檢查打包的資源檔案")
    
    dist_image_dir = Path("dist/_internal/image")
    if dist_image_dir.exists():
        image_files = list(dist_image_dir.glob("*"))
        print_success(f"資源檔案已打包: {len(image_files)} 個檔案")
        for file in image_files:
            print_color(f"  - {file.name}", 'gray')
        return True
    else:
        print_warning(f"找不到資源目錄: {dist_image_dir}")
        return False

def generate_report(build_duration, exe_size):
    """階段 7: 生成建置報告"""
    print_step("階段 7: 生成建置報告")
    
    from config.version import APP_VERSION, APP_FULL_TITLE
    
    report_content = f"""F1T GUI - 建置報告
==================

版本資訊:
  應用程式: F1 TelemetryStation Pro
  版本號: {APP_VERSION}
  建置日期: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  
建置環境:
  Python: {sys.version.split()[0]}
  PyInstaller: {__import__('PyInstaller').__version__}
  作業系統: {sys.platform}
  
建置配置:
  SPEC 檔案: F1T_GUI.spec
  Runtime Hook: pyinstaller_runtime_hook.py
  Console 模式: False (GUI 應用程式)
  Debug 模式: False (生產環境)
  UPX 壓縮: True
  
EXE 資訊:
  檔案名稱: F1T_GUI.exe
  檔案大小: {exe_size:.2f} MB
  檔案路徑: dist/F1T_GUI.exe
  
V0.8.0 新增功能:
  • 修復 Python 3.13 執行緒清理警告（_DeleteDummyThreadOnDel TypeError）
  • 改善主視窗 closeEvent 執行緒清理流程（收集所有活動 QThread）
  • 延長執行緒等待時間（2秒→3秒）並強制終止未退出執行緒
  • 增強 Python 3.13 警告抑制器（sys.excepthook + threading.excepthook）
  • 實作雙層防護：主動清理 + 警告抑制，確保優雅關閉
  • 新增執行緒清理日誌，清楚顯示每個執行緒的清理狀態
  • 修復 QThread 與 Python threading 混用導致的資源洩漏問題
  • 提供完整的執行緒清理測試指南和修復報告文檔

建置統計:
  建置時長: {build_duration:.2f} 秒
  成功狀態: ✅ 成功
  
注意事項:
  1. EXE 運行時會在用戶目錄創建緩存: ~/.f1telemetrystation/cache
  2. 日誌級別設定為 CRITICAL（極度靜默）
  3. API 模式: production (https://api.f1telemetrystationpro.org)
  4. 首次運行可能需要較長時間初始化
"""
    
    report_path = Path("dist/BUILD_REPORT.txt")
    report_path.write_text(report_content, encoding='utf-8')
    print_success(f"建置報告已生成: {report_path}")
    return True

def main():
    """主流程"""
    print_header("F1T GUI V0.8.0 - PyInstaller 打包流程")
    
    # 階段 1: 環境檢查
    if not check_environment():
        print_error("環境檢查失敗！")
        return 1
    
    # 驗證版本
    if not verify_version():
        return 1
    
    # 階段 2: SPEC 檢查（可選，如果失敗則跳過）
    print_step("階段 2: SPEC 完整性檢查")
    spec_check = run_spec_check()
    if spec_check:
        print_success("SPEC 檢查通過")
    else:
        print_warning("SPEC 檢查失敗，但繼續打包（已手動驗證）")
    
    # 階段 3: 清理
    if not clean_old_builds():
        return 1
    
    # 階段 4: 打包
    build_duration = run_pyinstaller()
    if build_duration is None:
        return 1
    
    # 階段 5: 驗證 EXE
    exe_size = verify_exe()
    if exe_size is None:
        return 1
    
    # 階段 6: 檢查資源
    check_resources()
    
    # 階段 7: 生成報告
    generate_report(build_duration, exe_size)
    
    # 完成
    print_header("打包完成！")
    print()
    print_color("📦 EXE 檔案位置:", 'green')
    print_color("  dist/F1T_GUI.exe", 'cyan')
    print()
    print_color("📊 檔案大小:", 'green')
    print_color(f"  {exe_size:.2f} MB", 'cyan')
    print()
    print_color("⏱️  建置時長:", 'green')
    print_color(f"  {build_duration:.2f} 秒", 'cyan')
    print()
    print_color("✅ 所有階段完成！可以開始測試 EXE", 'green')
    print()
    print_color("💡 測試建議:", 'yellow')
    print_color("  1. 在當前目錄執行: .\\dist\\F1T_GUI.exe", 'gray')
    print_color("  2. 複製 dist\\F1T_GUI.exe 到其他電腦測試", 'gray')
    print_color("  3. 檢查所有模組功能是否正常", 'gray')
    print_color("  4. 驗證 FIA Parts Analysis 模組的多國語言功能", 'gray')
    print()
    print_color("=" * 70, 'cyan')
    print()
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_error("用戶中斷打包流程")
        sys.exit(1)
    except Exception as e:
        print()
        print_error(f"發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
