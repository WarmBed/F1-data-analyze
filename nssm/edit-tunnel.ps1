# NSSM GUI - Edit F1T-CloudflareTunnel Service
# Opens NSSM GUI to edit F1T-CloudflareTunnel service configuration

Write-Host "`nOpening NSSM GUI for F1T-CloudflareTunnel..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Elevating to Administrator..." -ForegroundColor Yellow
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
    exit
}

Write-Host "Opening GUI editor for: F1T-CloudflareTunnel" -ForegroundColor Green
Write-Host ""

# Open NSSM GUI
& "$PSScriptRoot\nssm.exe" edit F1T-CloudflareTunnel

Write-Host "`nGUI closed. Check if you made any changes." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Start service:  Start-Service F1T-CloudflareTunnel" -ForegroundColor Gray
Write-Host "  2. Check status:   Get-Service F1T-CloudflareTunnel" -ForegroundColor Gray
Write-Host "  3. View logs:      Get-Content logs\cloudflare-tunnel.log -Tail 20`n" -ForegroundColor Gray

pause
