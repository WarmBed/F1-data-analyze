# F1T NSSM Service Installer
# Version: 1.0.0
# Purpose: Install all F1T services as Windows services using NSSM

#Requires -RunAsAdministrator

$ErrorActionPreference = "Stop"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Service Installer - Installing Windows Services" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Color "ERROR This script requires Administrator privileges" "Red"
    Write-Color "Please run PowerShell as Administrator and try again`n" "Yellow"
    exit 1
}

# Locate NSSM
Write-Color "[1/8] Locating NSSM..." "Yellow"
$nssmPath = "$PSScriptRoot\nssm.exe"

if (-not (Test-Path $nssmPath)) {
    Write-Color "  ERROR NSSM not found at: $nssmPath" "Red"
    Write-Color "  Please run: .\nssm\install-nssm.ps1 first" "Yellow"
    exit 1
}
Write-Color "  OK NSSM found: $nssmPath" "Green"

# Get project root directory
$projectRoot = Split-Path $PSScriptRoot -Parent
Write-Color "`n[2/8] Project root: $projectRoot" "Yellow"

# Get Python executable path
Write-Color "`n[3/8] Locating Python..." "Yellow"
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    Write-Color "  ERROR Python not found in PATH" "Red"
    exit 1
}
Write-Color "  OK Python: $pythonPath" "Green"

# Create NSSM logs directory
Write-Color "`n[4/8] Creating NSSM logs directory..." "Yellow"
$logsDir = Join-Path $PSScriptRoot "logs"
if (-not (Test-Path $logsDir)) {
    New-Item -ItemType Directory -Force -Path $logsDir | Out-Null
    Write-Color "  OK Created: $logsDir" "Green"
} else {
    Write-Color "  OK Exists: $logsDir" "Green"
}

# Service definitions
$services = @(
    @{
        Name = "F1T-API"
        DisplayName = "F1T Telemetry API Server"
        Description = "F1 Telemetry REST API service for data analysis"
        Application = $pythonPath
        AppDirectory = $projectRoot
        Arguments = "refactored_api.py"
        StdoutLog = Join-Path $logsDir "f1t-api.log"
        StderrLog = Join-Path $logsDir "f1t-api.error.log"
        StartupType = "Automatic"
        RestartDelay = 5000
    },
    @{
        Name = "F1T-PeriodicUpdate"
        DisplayName = "F1T Periodic Update Service"
        Description = "F1 Telemetry automatic data update scheduler"
        Application = $pythonPath
        AppDirectory = $projectRoot
        Arguments = "scripts\periodic_update_service.py"
        StdoutLog = Join-Path $logsDir "periodic-update.log"
        StderrLog = Join-Path $logsDir "periodic-update.error.log"
        StartupType = "Automatic"
        RestartDelay = 5000
    },
    @{
        Name = "F1T-CloudflareTunnel"
        DisplayName = "F1T Cloudflare Tunnel"
        Description = "Cloudflare Tunnel for F1T API public access"
        Application = Join-Path $projectRoot "cloudflared\cloudflared.exe"
        AppDirectory = $projectRoot
        Arguments = "--config cloudflared\config.yml tunnel run myfastapi"
        StdoutLog = Join-Path $logsDir "cloudflare-tunnel.log"
        StderrLog = Join-Path $logsDir "cloudflare-tunnel.error.log"
        StartupType = "Automatic"
        RestartDelay = 5000
    }
)

# Check for existing services
Write-Color "`n[5/8] Checking for existing services..." "Yellow"
$existingServices = @()
foreach ($svc in $services) {
    $existing = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Color "  WARNING Service exists: $($svc.Name)" "Yellow"
        $existingServices += $svc.Name
    }
}

if ($existingServices.Count -gt 0) {
    Write-Color "`n  Found $($existingServices.Count) existing service(s)" "Yellow"
    $response = Read-Host "  Remove and reinstall? (y/n)"
    
    if ($response -eq 'y') {
        Write-Color "  Removing existing services..." "Gray"
        foreach ($svcName in $existingServices) {
            try {
                # Stop service first
                $svc = Get-Service -Name $svcName
                if ($svc.Status -eq 'Running') {
                    Write-Color "    Stopping $svcName..." "Gray"
                    Stop-Service -Name $svcName -Force
                    Start-Sleep -Seconds 2
                }
                
                # Remove service
                & $nssmPath remove $svcName confirm
                Write-Color "    OK Removed: $svcName" "Green"
            } catch {
                Write-Color "    ERROR Failed to remove ${svcName}: $_" "Red"
            }
        }
    } else {
        Write-Color "  INFO Installation cancelled" "Cyan"
        exit 0
    }
}

# Install services
Write-Color "`n[6/8] Installing services..." "Yellow"
$installed = 0

foreach ($svc in $services) {
    Write-Color "`n  Installing: $($svc.Name)" "Cyan"
    Write-Color "    Display: $($svc.DisplayName)" "Gray"
    
    try {
        # Install service
        Write-Color "    Creating service..." "Gray"
        & $nssmPath install $svc.Name $svc.Application $svc.Arguments | Out-Null
        
        # Set service parameters
        Write-Color "    Configuring..." "Gray"
        & $nssmPath set $svc.Name DisplayName $svc.DisplayName | Out-Null
        & $nssmPath set $svc.Name Description $svc.Description | Out-Null
        & $nssmPath set $svc.Name AppDirectory $svc.AppDirectory | Out-Null
        & $nssmPath set $svc.Name Start $svc.StartupType | Out-Null
        
        # Set I/O redirection
        & $nssmPath set $svc.Name AppStdout $svc.StdoutLog | Out-Null
        & $nssmPath set $svc.Name AppStderr $svc.StderrLog | Out-Null
        
        # Set restart settings
        & $nssmPath set $svc.Name AppRestartDelay $svc.RestartDelay | Out-Null
        & $nssmPath set $svc.Name AppExit Default Restart | Out-Null
        
        # Set environment variables
        & $nssmPath set $svc.Name AppEnvironmentExtra "PYTHONPATH=$projectRoot" "PYTHONIOENCODING=utf-8" | Out-Null
        
        Write-Color "    OK Installed successfully" "Green"
        $installed++
        
    } catch {
        Write-Color "    ERROR Failed to install: $_" "Red"
    }
}

# Set service dependencies (API should start before Update service)
Write-Color "`n[7/8] Configuring service dependencies..." "Yellow"
try {
    # Periodic Update depends on API
    & $nssmPath set F1T-PeriodicUpdate DependOnService F1T-API | Out-Null
    Write-Color "  OK F1T-PeriodicUpdate depends on F1T-API" "Green"
} catch {
    Write-Color "  WARNING Could not set dependencies: $_" "Yellow"
}

# Verify installation
Write-Color "`n[8/8] Verifying installation..." "Yellow"
$verified = 0
foreach ($svc in $services) {
    $service = Get-Service -Name $svc.Name -ErrorAction SilentlyContinue
    if ($service) {
        Write-Color "  OK $($svc.Name): Status=$($service.Status), StartType=$($service.StartType)" "Green"
        $verified++
    } else {
        Write-Color "  ERROR $($svc.Name): Not found" "Red"
    }
}

# Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " Service Installation Complete!" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "Results:" "White"
Write-Color "  Installed: $installed / $($services.Count)" "Gray"
Write-Color "  Verified:  $verified / $($services.Count)" "Gray"

Write-Color "`nManagement Commands:" "White"
Write-Color "  Start all:     .\nssm\manage-services.ps1 -Action Start" "Gray"
Write-Color "  Stop all:      .\nssm\manage-services.ps1 -Action Stop" "Gray"
Write-Color "  Status:        .\nssm\manage-services.ps1 -Action Status" "Gray"
Write-Color "  Uninstall:     .\nssm\uninstall-services.ps1" "Gray"

Write-Color "`nWindows Services Manager:" "White"
Write-Color "  services.msc`n" "Gray"

if ($verified -eq $services.Count) {
    Write-Color "Ready to start services!" "Green"
    $startNow = Read-Host "`nStart all services now? (y/n)"
    
    if ($startNow -eq 'y') {
        Write-Color "`nStarting services..." "Yellow"
        & "$PSScriptRoot\manage-services.ps1" -Action Start
    }
}
