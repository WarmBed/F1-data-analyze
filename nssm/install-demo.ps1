# NSSM Install Demo - Open GUI to Install Service
# This script will open NSSM GUI for you to install a service

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "NSSM Install GUI Demo" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Choose an option:`n" -ForegroundColor Yellow

Write-Host "1. Install new service (blank form)" -ForegroundColor White
Write-Host "   Command: .\nssm\nssm.exe install`n" -ForegroundColor Gray

Write-Host "2. Install F1T-API (pre-filled name)" -ForegroundColor White
Write-Host "   Command: .\nssm\nssm.exe install F1T-API`n" -ForegroundColor Gray

Write-Host "3. Install F1T-PeriodicUpdate (pre-filled name)" -ForegroundColor White
Write-Host "   Command: .\nssm\nssm.exe install F1T-PeriodicUpdate`n" -ForegroundColor Gray

Write-Host "4. Install F1T-CloudflareTunnel (pre-filled name)" -ForegroundColor White
Write-Host "   Command: .\nssm\nssm.exe install F1T-CloudflareTunnel`n" -ForegroundColor Gray

Write-Host "5. Exit`n" -ForegroundColor White

$choice = Read-Host "Enter your choice (1-5)"

switch ($choice) {
    "1" {
        Write-Host "`nOpening NSSM install GUI (blank)..." -ForegroundColor Yellow
        Start-Process ".\nssm\nssm.exe" -ArgumentList "install" -Verb RunAs
    }
    "2" {
        Write-Host "`nOpening NSSM install GUI for F1T-API..." -ForegroundColor Yellow
        Write-Host "You'll need to fill in:" -ForegroundColor Cyan
        Write-Host "  Path: C:\Users\mike2\AppData\Local\Programs\Python\Python313\python.exe" -ForegroundColor Gray
        Write-Host "  Startup directory: C:\Users\mike2\OneDrive\Code\F1-data-analyze" -ForegroundColor Gray
        Write-Host "  Arguments: refactored_api.py`n" -ForegroundColor Gray
        Start-Process ".\nssm\nssm.exe" -ArgumentList "install F1T-API" -Verb RunAs
    }
    "3" {
        Write-Host "`nOpening NSSM install GUI for F1T-PeriodicUpdate..." -ForegroundColor Yellow
        Write-Host "You'll need to fill in:" -ForegroundColor Cyan
        Write-Host "  Path: C:\Users\mike2\AppData\Local\Programs\Python\Python313\python.exe" -ForegroundColor Gray
        Write-Host "  Startup directory: C:\Users\mike2\OneDrive\Code\F1-data-analyze" -ForegroundColor Gray
        Write-Host "  Arguments: scripts\periodic_update_service.py`n" -ForegroundColor Gray
        Start-Process ".\nssm\nssm.exe" -ArgumentList "install F1T-PeriodicUpdate" -Verb RunAs
    }
    "4" {
        Write-Host "`nOpening NSSM install GUI for F1T-CloudflareTunnel..." -ForegroundColor Yellow
        Write-Host "You'll need to fill in:" -ForegroundColor Cyan
        Write-Host "  Path: C:\Users\mike2\OneDrive\Code\F1-data-analyze\cloudflared\cloudflared.exe" -ForegroundColor Gray
        Write-Host "  Startup directory: C:\Users\mike2\OneDrive\Code\F1-data-analyze" -ForegroundColor Gray
        Write-Host "  Arguments: --config cloudflared\config.yml tunnel run myfastapi`n" -ForegroundColor Gray
        Start-Process ".\nssm\nssm.exe" -ArgumentList "install F1T-CloudflareTunnel" -Verb RunAs
    }
    "5" {
        Write-Host "`nExiting...`n" -ForegroundColor Gray
        exit
    }
    default {
        Write-Host "`nInvalid choice`n" -ForegroundColor Red
    }
}

Write-Host "`nGUI window opened (may be behind other windows)" -ForegroundColor Green
Write-Host "Fill in the form and click 'Install service' button`n" -ForegroundColor White
