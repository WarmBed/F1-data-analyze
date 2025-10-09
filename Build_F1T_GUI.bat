@echo off
chcp 65001 >nul
REM ========================================
REM F1T GUI - PyInstaller 打包腳本
REM 版本: V0.3.0
REM 日期: 2025-10-09
REM ========================================

echo.
echo ======================================================================
echo    F1 TelemetryStation Pro - EXE 打包工具 V0.3.0
echo ======================================================================
echo.

REM 1. 清理舊檔案
echo [1/5] 正在清理舊的 build 和 dist 目錄...
if exist "build" (
    rmdir /s /q "build"
    echo       ✅ 已刪除 build 目錄
) else (
    echo       ⏭️  build 目錄不存在，跳過
)

if exist "dist" (
    rmdir /s /q "dist"
    echo       ✅ 已刪除 dist 目錄
) else (
    echo       ⏭️  dist 目錄不存在，跳過
)

echo.

REM 2. 檢查 .spec 檔案
echo [2/5] 檢查 F1T_GUI.spec 檔案...
if not exist "F1T_GUI.spec" (
    echo       ❌ 錯誤: 找不到 F1T_GUI.spec 檔案！
    pause
    exit /b 1
)
echo       ✅ F1T_GUI.spec 檔案存在

echo.

REM 3. 檢查 PyInstaller
echo [3/5] 檢查 PyInstaller 安裝...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo       ❌ 錯誤: PyInstaller 未安裝！
    echo.
    echo       請執行: pip install pyinstaller
    pause
    exit /b 1
)
echo       ✅ PyInstaller 已安裝

echo.

REM 4. 執行打包
echo [4/5] 開始打包 EXE（這可能需要幾分鐘）...
echo       使用設定檔: F1T_GUI.spec
echo       包含 48 個 hiddenimports 模組
echo.
pyinstaller F1T_GUI.spec

if errorlevel 1 (
    echo.
    echo       ❌ 打包失敗！請檢查上方的錯誤訊息
    pause
    exit /b 1
)

echo.
echo       ✅ 打包完成！

echo.

REM 5. 驗證輸出
echo [5/5] 驗證打包結果...
if exist "dist\F1T_GUI.exe" (
    echo       ✅ F1T_GUI.exe 已生成
    
    REM 獲取檔案大小
    for %%F in ("dist\F1T_GUI.exe") do set size=%%~zF
    set /a size_mb=%size% / 1048576
    echo       📦 檔案大小: %size_mb% MB
    
    echo.
    echo ======================================================================
    echo    🎉 打包成功！
    echo ======================================================================
    echo.
    echo    EXE 檔案位置: dist\F1T_GUI.exe
    echo.
    echo    測試步驟:
    echo    1. 執行 dist\F1T_GUI.exe
    echo    2. 測試 Throttle Analysis ^> Throttle Line Chart
    echo    3. 測試 Detailed Lap Analysis
    echo    4. 確認所有功能正常
    echo.
    echo ======================================================================
) else (
    echo       ❌ 錯誤: 找不到 dist\F1T_GUI.exe
    echo.
    echo       可能的原因:
    echo       - 打包過程中出現錯誤
    echo       - 缺少必要的依賴套件
    echo.
    pause
    exit /b 1
)

echo.
pause
