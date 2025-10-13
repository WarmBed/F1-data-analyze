# F1T NSSM Service Installer - Run as Administrator Helper
# This script will automatically elevate to Administrator

$ErrorActionPreference = "Stop"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`nNot running as Administrator" -ForegroundColor Yellow
    Write-Host "Elevating to Administrator privileges..." -ForegroundColor Cyan
    
    # Get the path to install-services.ps1
    $scriptPath = Join-Path $PSScriptRoot "install-services.ps1"
    
    # Restart as administrator
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoExit -File `"$scriptPath`"" -Verb RunAs
    
    Write-Host "`nNew Administrator window opened" -ForegroundColor Green
    Write-Host "Please complete the installation in that window`n" -ForegroundColor Gray
    exit
}

# If we're here, we have admin rights
Write-Host "`nRunning with Administrator privileges" -ForegroundColor Green
Write-Host "Executing install-services.ps1...`n" -ForegroundColor Cyan

# Execute the actual installation script
& "$PSScriptRoot\install-services.ps1"
