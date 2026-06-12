@echo off
chcp 65001 >nul
cd /d "%~dp0.."
echo ════════════════════════════════════════════════════════
echo   F1T GUI EXE 一鍵建構工具
echo ════════════════════════════════════════════════════════
echo.

echo [步驟 1/3] 啟動虛擬環境...
call venv_build\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ 虛擬環境不存在，正在建立...
    python -m venv venv_build
    call venv_build\Scripts\activate.bat
)
echo ✅ 虛擬環境已啟動
echo.

echo [步驟 2/3] 安裝必要套件...
echo 這可能需要 2-3 分鐘，請稍候...
pip install pyinstaller fastf1 pandas matplotlib requests python-dateutil -q
if errorlevel 1 (
    echo ⚠️ 部分套件安裝可能失敗，繼續嘗試建構...
) else (
    echo ✅ 套件安裝完成
)
echo.

echo [步驟 3/3] 建構 EXE...
echo 這可能需要 3-5 分鐘，請稍候...
pyinstaller build_tools\F1T_GUI_clean.spec --clean --noconfirm
if errorlevel 1 (
    echo ❌ 建構失敗！
    pause
    exit /b 1
)
echo.

echo ════════════════════════════════════════════════════════
echo   ✅ 建構完成！
echo ════════════════════════════════════════════════════════
echo.
echo EXE 檔案位置: dist\F1T_GUI.exe
echo.

echo 是否要開啟 dist 資料夾？
choice /C YN /M "按 Y 開啟，N 退出"
if errorlevel 2 goto end
if errorlevel 1 start explorer dist

:end
call deactivate 2>nul
echo.
echo 按任意鍵退出...
pause >nul
