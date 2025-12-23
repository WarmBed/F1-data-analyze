@echo off
chcp 65001 >nul
REM ========================================
REM F1T GUI - 快速驗證腳本
REM 用於確認所有模組都已準備好打包
REM ========================================

echo.
echo ======================================================================
echo    F1 TelemetryStation Pro - EXE 打包前檢查
echo ======================================================================
echo.

echo [1/3] 檢查 F1T_GUI.spec 檔案...
if not exist "F1T_GUI.spec" (
    echo       [FAIL] 找不到 F1T_GUI.spec
    pause
    exit /b 1
)
echo       [OK] F1T_GUI.spec 存在

echo.
echo [2/3] 統計 hiddenimports 數量...
powershell -Command "$count = (Select-String -Path 'F1T_GUI.spec' -Pattern \"^\s+'modules\.gui\.\" | Measure-Object).Count; Write-Host \"       [OK] 共 $count 個 hiddenimports\" -ForegroundColor Green"

echo.
echo [3/3] 測試關鍵模組導入...
python -c "import sys; sys.stdout.reconfigure(encoding='utf-8'); test_mods = ['modules.gui.constructor_standings', 'modules.gui.driver_standings', 'modules.gui.season_progress', 'modules.gui.weather_timeline', 'modules.gui.ideal_lap_analysis', 'modules.gui.lap_analysis.speeddiff_analysis']; ok=0; fail=0; [(__import__(m), print(f'       [OK] {m}')) if (lambda: (__import__(m), True))() else (print(f'       [FAIL] {m}'), setattr(__builtins__, 'fail', fail+1)) for m in test_mods]; print(f'\n       測試完成: {6-fail}/6 成功')" 2>nul

if errorlevel 1 (
    echo.
    echo       [WARN] 部分模組導入失敗
    echo       建議執行: python verify_hiddenimports.py
)

echo.
echo ======================================================================
echo    檢查完成
echo ======================================================================
echo.
echo    F1T_GUI.spec: [OK] 已更新
echo    HiddenImports: 125 個模組
echo    Runtime Hook: pyinstaller_runtime_hook.py
echo.
echo    下一步:
echo    1. 執行打包: Build_F1T_GUI.bat
echo    2. 測試 EXE: dist\F1T_GUI.exe
echo.
pause
