@echo off
setlocal

REM ================================================
REM  F1T NSSM Service Monitor - GUI Launcher
REM ================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..

echo.
echo ========================================
echo   F1T NSSM Service Monitor
echo   啟動監控工具...
echo ========================================
echo.

REM Check if Python is available
where python >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo Please install Python 3.8+ or add it to PATH
    pause
    exit /b 1
)

REM Launch GUI
echo [INFO] Starting NSSM Monitor GUI...
echo.

cd /d "%SCRIPT_DIR%"
python nssm_monitor_gui.py

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Failed to start GUI
    echo Error Code: %errorLevel%
    pause
    exit /b %errorLevel%
)

endlocal
