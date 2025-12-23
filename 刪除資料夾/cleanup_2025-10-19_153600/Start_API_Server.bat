@echo off
setlocal

REM ================================================
REM  F1T API Server Launcher (PowerShell Wrapper)
REM ================================================

set SCRIPT_DIR=%~dp0
set PYTHON_EXEC=C:\Users\mike2\AppData\Local\Programs\Python\Python313\python.exe
set API_SCRIPT=%SCRIPT_DIR%refactored_api.py

if not exist "%PYTHON_EXEC%" (
    echo [ERROR] Python executable not found at %PYTHON_EXEC%
    echo Please install Python 3.13 or update the path in Start_API_Server.bat
    pause
    exit /b 1
)

if not exist "%API_SCRIPT%" (
    echo [ERROR] API script not found at %API_SCRIPT%
    pause
    exit /b 1
)

REM Launch via PowerShell to respect project policy
powershell -NoProfile -ExecutionPolicy Bypass ^
    -Command "$ErrorActionPreference='Stop'; Set-Location '%SCRIPT_DIR%'; $env:PYTHONPATH='%SCRIPT_DIR%'; $env:PYTHONIOENCODING='utf-8'; Write-Host '=========================================' -ForegroundColor Cyan; Write-Host '  F1T API Server - Launching' -ForegroundColor Cyan; Write-Host '  Python: %PYTHON_EXEC%' -ForegroundColor Yellow; Write-Host '  Script: %API_SCRIPT%' -ForegroundColor Yellow; Write-Host '=========================================' -ForegroundColor Cyan; & '%PYTHON_EXEC%' '%API_SCRIPT%'; $exitCode=$LASTEXITCODE; if ($exitCode -ne 0) { Write-Host ('API server exited with code {0}' -f $exitCode) -ForegroundColor Red } else { Write-Host 'API server stopped normally.' -ForegroundColor Green }; Read-Host 'Press Enter to close window'"

endlocal
