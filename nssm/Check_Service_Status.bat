@echo off
setlocal EnableDelayedExpansion

REM ================================================
REM  F1T NSSM Services - Check Status
REM ================================================
REM  This script does NOT require Administrator privileges

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set NSSM_EXE=%SCRIPT_DIR%nssm.exe
set LOG_DIR=%SCRIPT_DIR%logs

REM Display header
echo.
echo ========================================
echo   F1T NSSM Services - Status Check
echo ========================================
echo.

REM Define services
set SERVICES=F1T-API F1T-PeriodicUpdate F1T-CloudflareTunnel

REM Check if NSSM exists
if not exist "%NSSM_EXE%" (
    echo [WARNING] NSSM not found at: %NSSM_EXE%
    echo Status check will proceed using Windows service commands.
    echo.
)

REM ===================================
REM  1. Service Status
REM ===================================
echo [1] SERVICE STATUS
echo ========================================

for %%s in (%SERVICES%) do (
    echo.
    echo Service: %%s
    echo -------------------
    
    REM Check if service exists
    sc query "%%s" >nul 2>&1
    if !errorLevel! neq 0 (
        echo Status: [NOT INSTALLED]
    ) else (
        REM Get service status
        for /f "tokens=3" %%a in ('sc query "%%s" ^| find "STATE"') do (
            set STATUS=%%a
        )
        
        if "!STATUS!"=="RUNNING" (
            echo Status: [RUNNING]
        ) else if "!STATUS!"=="STOPPED" (
            echo Status: [STOPPED]
        ) else if "!STATUS!"=="PAUSED" (
            echo Status: [PAUSED]
        ) else (
            echo Status: !STATUS!
        )
        
        REM Get startup type
        for /f "tokens=3" %%b in ('sc qc "%%s" ^| find "START_TYPE"') do (
            set STARTUP=%%b
        )
        echo Startup Type: !STARTUP!
    )
)

echo.
echo.

REM ===================================
REM  2. Process Information
REM ===================================
echo [2] PROCESS INFORMATION
echo ========================================
echo.

REM Check Python processes
echo Python Processes:
tasklist /fi "imagename eq python.exe" /fo table 2>nul | find "python.exe" >nul
if !errorLevel! equ 0 (
    tasklist /fi "imagename eq python.exe" /fo table /nh 2>nul
) else (
    echo   [INFO] No Python processes found.
)

echo.

REM Check Cloudflared processes
echo Cloudflared Processes:
tasklist /fi "imagename eq cloudflared.exe" /fo table 2>nul | find "cloudflared.exe" >nul
if !errorLevel! equ 0 (
    tasklist /fi "imagename eq cloudflared.exe" /fo table /nh 2>nul
) else (
    echo   [INFO] No Cloudflared processes found.
)

echo.
echo.

REM ===================================
REM  3. Log Files Status
REM ===================================
echo [3] LOG FILES STATUS
echo ========================================
echo.

if not exist "%LOG_DIR%" (
    echo [WARNING] Log directory not found: %LOG_DIR%
) else (
    REM Define log files
    set LOG_FILES=f1t-api.log f1t-api.error.log periodic-update.log periodic-update.error.log cloudflare-tunnel.log cloudflare-tunnel.error.log
    
    for %%f in (!LOG_FILES!) do (
        set LOG_PATH=%LOG_DIR%\%%f
        
        if exist "!LOG_PATH!" (
            REM Get file size
            for %%a in ("!LOG_PATH!") do set SIZE=%%~za
            
            REM Get last modified time
            for %%a in ("!LOG_PATH!") do set MODIFIED=%%~ta
            
            REM Convert bytes to KB
            set /a SIZE_KB=!SIZE! / 1024
            
            echo %%f
            echo   Size: !SIZE_KB! KB
            echo   Modified: !MODIFIED!
            echo.
        ) else (
            echo %%f
            echo   Status: [NOT FOUND]
            echo.
        )
    )
)

echo.
echo ========================================
echo   Status check complete.
echo ========================================
echo.

REM Offer to view logs
echo.
choice /c YN /m "Would you like to view recent log entries? (Y/N)"
if !errorLevel! equ 1 (
    echo.
    echo ========================================
    echo   Recent Log Entries (Last 10 lines)
    echo ========================================
    
    for %%f in (f1t-api.log periodic-update.log cloudflare-tunnel.log) do (
        set LOG_PATH=%LOG_DIR%\%%f
        
        if exist "!LOG_PATH!" (
            echo.
            echo --- %%f ---
            powershell -Command "Get-Content '!LOG_PATH!' -Tail 10"
        )
    )
    
    echo.
    echo ========================================
)

pause
endlocal
