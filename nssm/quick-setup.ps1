# F1T NSSM Quick Setup - One-Click Installation
# Version: 1.0.0
# This script will guide you through the complete NSSM setup

$ErrorActionPreference = "Stop"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T NSSM Quick Setup - Complete Installation Wizard" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Color "WARNING This script requires Administrator privileges" "Yellow"
    Write-Color "Please right-click PowerShell and select 'Run as Administrator'`n" "Yellow"
    
    $elevate = Read-Host "Try to elevate now? (y/n)"
    if ($elevate -eq 'y') {
        Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs
        exit
    } else {
        Write-Color "`nSetup cancelled`n" "Red"
        exit 1
    }
}

Write-Color "Running with Administrator privileges`n" "Green"

# Step 1: Install NSSM
Write-Color "============================================================" "Cyan"
Write-Color "Step 1: Install NSSM" "White"
Write-Color "============================================================`n" "Cyan"

$nssmInstalled = Test-Path "$PSScriptRoot\nssm.exe"

if ($nssmInstalled) {
    Write-Color "NSSM already installed" "Green"
    $reinstall = Read-Host "Reinstall NSSM? (y/n)"
    if ($reinstall -eq 'y') {
        & "$PSScriptRoot\install-nssm.ps1"
    }
} else {
    Write-Color "NSSM not found, installing now..." "Yellow"
    & "$PSScriptRoot\install-nssm.ps1"
}

# Verify NSSM
if (-not (Test-Path "$PSScriptRoot\nssm.exe")) {
    Write-Color "`nERROR NSSM installation failed" "Red"
    exit 1
}

Write-Color "`nNSSM ready!`n" "Green"
Start-Sleep -Seconds 2

# Step 2: Install Services
Write-Color "============================================================" "Cyan"
Write-Color "Step 2: Install F1T Services" "White"
Write-Color "============================================================`n" "Cyan"

$existingServices = Get-Service F1T-* -ErrorAction SilentlyContinue

if ($existingServices) {
    Write-Color "Found existing F1T services:" "Yellow"
    $existingServices | ForEach-Object { Write-Color "  - $($_.Name)" "Gray" }
    
    $reinstall = Read-Host "`nReinstall services? (y/n)"
    if ($reinstall -ne 'y') {
        Write-Color "`nSkipping service installation" "Cyan"
        $skipInstall = $true
    }
}

if (-not $skipInstall) {
    Write-Color "Installing services...`n" "Yellow"
    & "$PSScriptRoot\install-services.ps1"
}

# Verify services
Write-Color "`nVerifying services..." "Yellow"
$services = Get-Service F1T-* -ErrorAction SilentlyContinue

if (-not $services) {
    Write-Color "ERROR No services installed" "Red"
    exit 1
}

Write-Color "OK Services installed:`n" "Green"
$services | ForEach-Object { 
    Write-Color "  - $($_.Name): $($_.Status)" "Gray"
}

Start-Sleep -Seconds 2

# Step 3: Start Services
Write-Color "`n============================================================" "Cyan"
Write-Color "Step 3: Start Services" "White"
Write-Color "============================================================`n" "Cyan"

$startServices = Read-Host "Start all services now? (y/n)"

if ($startServices -eq 'y') {
    Write-Color "`nStarting services...`n" "Yellow"
    & "$PSScriptRoot\manage-services.ps1" -Action Start
    
    Start-Sleep -Seconds 5
    
    Write-Color "`nChecking service status..." "Yellow"
    & "$PSScriptRoot\manage-services.ps1" -Action Status
} else {
    Write-Color "`nServices installed but not started" "Cyan"
    Write-Color "You can start them later with:" "Gray"
    Write-Color "  .\nssm\manage-services.ps1 -Action Start`n" "Gray"
}

# Final Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " Setup Complete!" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "What's Next?" "White"
Write-Color "`n1. Manage Services:" "Cyan"
Write-Color "   .\nssm\manage-services.ps1 -Action Status" "Gray"
Write-Color "   .\nssm\manage-services.ps1 -Action Start" "Gray"
Write-Color "   .\nssm\manage-services.ps1 -Action Stop" "Gray"
Write-Color "   .\nssm\manage-services.ps1 -Action Restart" "Gray"

Write-Color "`n2. Windows Services Manager:" "Cyan"
Write-Color "   services.msc" "Gray"

Write-Color "`n3. View Logs:" "Cyan"
Write-Color "   Get-Content logs\f1t-api.log -Tail 50 -Wait" "Gray"
Write-Color "   .\nssm\manage-services.ps1 -Action Logs" "Gray"

Write-Color "`n4. Test API:" "Cyan"
Write-Color "   Invoke-WebRequest http://localhost:8000/health" "Gray"

Write-Color "`n5. Read Documentation:" "Cyan"
Write-Color "   .\nssm\NSSM_GUIDE.md" "Gray"

Write-Color "`nPress any key to open services.msc..." "Yellow"
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
services.msc
