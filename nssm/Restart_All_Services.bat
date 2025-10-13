@echo off
setlocal EnableDelayedExpansion

REM ================================================
REM  F1T NSSM Services - Restart All Services
REM ================================================

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set NSSM_EXE=%SCRIPT_DIR%nssm.exe

REM Check if running as Administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [ADMIN REQUIRED] This script requires Administrator privileges.
    echo Attempting to elevate permissions...
    echo.
    
    REM Re-launch as Administrator
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

REM Check if NSSM exists
if not exist "%NSSM_EXE%" (
    echo [ERROR] NSSM not found at: %NSSM_EXE%
    echo Please run install-nssm.ps1 first.
    pause
    exit /b 1
)

REM Display header
echo ========================================
echo   F1T NSSM Services - Restarting All
echo ========================================
echo.

REM Define services
set SERVICES_STOP=F1T-CloudflareTunnel F1T-PeriodicUpdate F1T-API
set SERVICES_START=F1T-API F1T-PeriodicUpdate F1T-CloudflareTunnel

REM Step 1: Stop all services (reverse order)
echo [PHASE 1] Stopping services...
echo.

for %%s in (%SERVICES_STOP%) do (
    echo [STOPPING] %%s...
    
    sc query "%%s" >nul 2>&1
    if !errorLevel! neq 0 (
        echo [WARNING] Service %%s not found. Skipping...
        echo.
    ) else (
        sc query "%%s" | find "STOPPED" >nul
        if !errorLevel! equ 0 (
            echo [INFO] Service %%s is already stopped.
            echo.
        ) else (
            net stop "%%s" >nul 2>&1
            if !errorLevel! equ 0 (
                echo [SUCCESS] Service %%s stopped.
            ) else (
                echo [ERROR] Failed to stop service %%s.
            )
            echo.
        )
    )
)

REM Wait 2 seconds for services to fully stop
echo [WAITING] Waiting 2 seconds for clean shutdown...
timeout /t 2 /nobreak >nul
echo.

REM Step 2: Start all services (correct order)
echo [PHASE 2] Starting services...
echo.

for %%s in (%SERVICES_START%) do (
    echo [STARTING] %%s...
    
    sc query "%%s" >nul 2>&1
    if !errorLevel! neq 0 (
        echo [WARNING] Service %%s not found. Skipping...
        echo.
    ) else (
        sc query "%%s" | find "RUNNING" >nul
        if !errorLevel! equ 0 (
            echo [INFO] Service %%s is already running.
            echo.
        ) else (
            net start "%%s" >nul 2>&1
            if !errorLevel! equ 0 (
                echo [SUCCESS] Service %%s started.
            ) else (
                echo [ERROR] Failed to start service %%s.
            )
            echo.
        )
    )
)

REM Display final status
echo ========================================
echo   Final Service Status
echo ========================================
echo.

for %%s in (%SERVICES_START%) do (
    sc query "%%s" 2>nul | find "STATE" | find /v "STOPPED"
    if !errorLevel! equ 0 (
        echo [RUNNING] %%s
    ) else (
        echo [STOPPED] %%s
    )
)

echo.
echo ========================================
echo   All services restarted.
echo ========================================
echo.

pause
endlocal
