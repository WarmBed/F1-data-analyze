@echo off
setlocal EnableDelayedExpansion

REM ================================================
REM  F1T NSSM Services - Start All Services
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
echo   F1T NSSM Services - Starting All
echo ========================================
echo.

REM Define services
set SERVICES=F1T-API F1T-PeriodicUpdate F1T-CloudflareTunnel

REM Start each service
for %%s in (%SERVICES%) do (
    echo [STARTING] %%s...
    
    REM Check if service exists
    sc query "%%s" >nul 2>&1
    if !errorLevel! neq 0 (
        echo [WARNING] Service %%s not found. Skipping...
        echo.
    ) else (
        REM Check current status
        sc query "%%s" | find "RUNNING" >nul
        if !errorLevel! equ 0 (
            echo [INFO] Service %%s is already running.
            echo.
        ) else (
            REM Start the service
            net start "%%s" >nul 2>&1
            if !errorLevel! equ 0 (
                echo [SUCCESS] Service %%s started successfully.
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

for %%s in (%SERVICES%) do (
    sc query "%%s" 2>nul | find "STATE" | find /v "STOPPED"
    if !errorLevel! equ 0 (
        echo [RUNNING] %%s
    ) else (
        echo [STOPPED] %%s
    )
)

echo.
echo ========================================
echo   All services processed.
echo ========================================
echo.

pause
endlocal
