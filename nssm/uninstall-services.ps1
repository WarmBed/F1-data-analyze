# F1T NSSM Service Uninstaller
# Version: 1.0.0
# Purpose: Uninstall all F1T Windows services

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Service Uninstaller - Removing Windows Services" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Check admin privileges
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Color "ERROR This script requires Administrator privileges" "Red"
    Write-Color "Please run PowerShell as Administrator and try again`n" "Yellow"
    exit 1
}

# Locate NSSM
Write-Color "[1/4] Locating NSSM..." "Yellow"
$nssmPath = "$PSScriptRoot\nssm.exe"

if (-not (Test-Path $nssmPath)) {
    Write-Color "  ERROR NSSM not found at: $nssmPath" "Red"
    Write-Color "  Attempting to remove services using sc.exe..." "Yellow"
    $useScExe = $true
} else {
    Write-Color "  OK NSSM found: $nssmPath" "Green"
    $useScExe = $false
}

# Service list
$serviceNames = @(
    "F1T-API",
    "F1T-PeriodicUpdate",
    "F1T-CloudflareTunnel"
)

# Find existing services
Write-Color "`n[2/4] Checking for installed services..." "Yellow"
$existingServices = @()

foreach ($svcName in $serviceNames) {
    $service = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Color "  FOUND $svcName (Status: $($service.Status))" "Yellow"
        $existingServices += @{
            Name = $svcName
            Service = $service
        }
    }
}

if ($existingServices.Count -eq 0) {
    Write-Color "`n  INFO No F1T services found" "Cyan"
    Write-Color "  Nothing to uninstall`n" "Gray"
    exit 0
}

Write-Color "`n  Found $($existingServices.Count) service(s) to remove" "White"

# Confirm removal
Write-Color "`nWARNING This will permanently remove all F1T services!" "Yellow"
$confirm = Read-Host "Continue? (yes/no)"

if ($confirm -ne "yes") {
    Write-Color "`n  INFO Uninstall cancelled by user`n" "Cyan"
    exit 0
}

# Stop and remove services
Write-Color "`n[3/4] Stopping and removing services..." "Yellow"
$removed = 0

foreach ($svcInfo in $existingServices) {
    $svcName = $svcInfo.Name
    $service = $svcInfo.Service
    
    Write-Color "`n  Processing: $svcName" "Cyan"
    
    try {
        # Stop service if running
        if ($service.Status -eq 'Running') {
            Write-Color "    Stopping service..." "Gray"
            Stop-Service -Name $svcName -Force -ErrorAction Stop
            Start-Sleep -Seconds 2
            Write-Color "    OK Stopped" "Green"
        } else {
            Write-Color "    INFO Already stopped" "Gray"
        }
        
        # Remove service
        Write-Color "    Removing service..." "Gray"
        
        if ($useScExe) {
            # Use sc.exe as fallback
            $result = & sc.exe delete $svcName 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Color "    OK Removed using sc.exe" "Green"
                $removed++
            } else {
                Write-Color "    ERROR Failed to remove: $result" "Red"
            }
        } else {
            # Use NSSM
            & $nssmPath remove $svcName confirm
            if ($LASTEXITCODE -eq 0) {
                Write-Color "    OK Removed using NSSM" "Green"
                $removed++
            } else {
                Write-Color "    ERROR Failed to remove" "Red"
            }
        }
        
    } catch {
        Write-Color "    ERROR Exception: $_" "Red"
    }
}

# Verify removal
Write-Color "`n[4/4] Verifying removal..." "Yellow"
Start-Sleep -Seconds 2

$remainingServices = @()
foreach ($svcName in $serviceNames) {
    $service = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Color "  WARNING $svcName still exists" "Yellow"
        $remainingServices += $svcName
    } else {
        Write-Color "  OK $svcName removed" "Green"
    }
}

# Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " Service Uninstallation Complete!" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "Results:" "White"
Write-Color "  Found:     $($existingServices.Count)" "Gray"
Write-Color "  Removed:   $removed" "Gray"
Write-Color "  Remaining: $($remainingServices.Count)" "Gray"

if ($remainingServices.Count -gt 0) {
    Write-Color "`nWARNING Some services could not be removed:" "Yellow"
    foreach ($svcName in $remainingServices) {
        Write-Color "  - $svcName" "Red"
    }
    Write-Color "`nManual removal using services.msc may be required`n" "Yellow"
} else {
    Write-Color "`nAll services successfully removed!" "Green"
    Write-Color "You can now run install-services.ps1 to reinstall if needed`n" "Gray"
}
