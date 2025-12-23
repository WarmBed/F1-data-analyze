# F1T NSSM Service Manager
# Version: 1.0.0
# Purpose: Unified interface for managing F1T Windows services

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("Start", "Stop", "Restart", "Status", "Logs")]
    [string]$Action = "Status",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("F1T-API", "F1T-PeriodicUpdate", "F1T-CloudflareTunnel", "All")]
    [string]$Service = "All"
)

$ErrorActionPreference = "Continue"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Service Manager - $Action Services" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Service list
$serviceNames = if ($Service -eq "All") {
    @("F1T-API", "F1T-PeriodicUpdate", "F1T-CloudflareTunnel")
} else {
    @($Service)
}

# Execute action
switch ($Action) {
    "Start" {
        Write-Color "Starting services..." "Yellow"
        foreach ($svcName in $serviceNames) {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if ($svc) {
                if ($svc.Status -eq 'Stopped') {
                    Write-Color "  Starting $svcName..." "Gray"
                    try {
                        Start-Service -Name $svcName -ErrorAction Stop
                        Start-Sleep -Seconds 2
                        $newStatus = (Get-Service -Name $svcName).Status
                        if ($newStatus -eq 'Running') {
                            Write-Color "    OK Started successfully" "Green"
                        } else {
                            Write-Color "    WARNING Status: $newStatus" "Yellow"
                        }
                    } catch {
                        Write-Color "    ERROR Failed: $_" "Red"
                    }
                } else {
                    Write-Color "  INFO $svcName already running" "Cyan"
                }
            } else {
                Write-Color "  ERROR Service not found: $svcName" "Red"
            }
        }
    }
    
    "Stop" {
        Write-Color "Stopping services..." "Yellow"
        # Stop in reverse order (respecting dependencies)
        $reverseServices = $serviceNames | Sort-Object -Descending
        
        foreach ($svcName in $reverseServices) {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if ($svc) {
                if ($svc.Status -eq 'Running') {
                    Write-Color "  Stopping $svcName..." "Gray"
                    try {
                        Stop-Service -Name $svcName -Force -ErrorAction Stop
                        Start-Sleep -Seconds 2
                        $newStatus = (Get-Service -Name $svcName).Status
                        if ($newStatus -eq 'Stopped') {
                            Write-Color "    OK Stopped successfully" "Green"
                        } else {
                            Write-Color "    WARNING Status: $newStatus" "Yellow"
                        }
                    } catch {
                        Write-Color "    ERROR Failed: $_" "Red"
                    }
                } else {
                    Write-Color "  INFO $svcName already stopped" "Cyan"
                }
            } else {
                Write-Color "  ERROR Service not found: $svcName" "Red"
            }
        }
    }
    
    "Restart" {
        Write-Color "Restarting services..." "Yellow"
        
        # Stop first (reverse order)
        $reverseServices = $serviceNames | Sort-Object -Descending
        foreach ($svcName in $reverseServices) {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if ($svc -and $svc.Status -eq 'Running') {
                Write-Color "  Stopping $svcName..." "Gray"
                Stop-Service -Name $svcName -Force -ErrorAction SilentlyContinue
            }
        }
        
        Start-Sleep -Seconds 3
        
        # Start (normal order)
        foreach ($svcName in $serviceNames) {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if ($svc) {
                Write-Color "  Starting $svcName..." "Gray"
                try {
                    Start-Service -Name $svcName -ErrorAction Stop
                    Start-Sleep -Seconds 2
                    Write-Color "    OK Restarted" "Green"
                } catch {
                    Write-Color "    ERROR Failed: $_" "Red"
                }
            }
        }
    }
    
    "Status" {
        Write-Color "Service Status:" "Yellow"
        Write-Color "============================================================`n" "Cyan"
        
        $statusTable = @()
        foreach ($svcName in $serviceNames) {
            $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
            if ($svc) {
                $statusColor = switch ($svc.Status) {
                    'Running' { "Green" }
                    'Stopped' { "Red" }
                    default { "Yellow" }
                }
                
                $statusTable += [PSCustomObject]@{
                    Name = $svcName
                    Status = $svc.Status
                    StartType = $svc.StartType
                    DisplayName = $svc.DisplayName
                }
                
                Write-Color "  $($svc.Name)" "White"
                Write-Color "    Status:      $($svc.Status)" $statusColor
                Write-Color "    Start Type:  $($svc.StartType)" "Gray"
                Write-Color "    Display:     $($svc.DisplayName)" "Gray"
                Write-Color ""
            } else {
                Write-Color "  $svcName" "Red"
                Write-Color "    Status: Not Installed" "Red"
                Write-Color ""
            }
        }
        
        # Process information
        Write-Color "Process Information:" "Yellow"
        Write-Color "============================================================`n" "Cyan"
        
        $processes = @(
            @{ Name = "Python"; Pattern = "python"; Services = @("F1T-API", "F1T-PeriodicUpdate") },
            @{ Name = "Cloudflared"; Pattern = "cloudflared"; Services = @("F1T-CloudflareTunnel") }
        )
        
        foreach ($proc in $processes) {
            $runningProcs = Get-Process -Name $proc.Pattern -ErrorAction SilentlyContinue
            if ($runningProcs) {
                foreach ($p in $runningProcs) {
                    $memoryMB = [math]::Round($p.WorkingSet64 / 1MB, 2)
                    $cpuSec = [math]::Round($p.CPU, 2)
                    Write-Color "  $($proc.Name)" "Green"
                    Write-Color "    PID:     $($p.Id)" "Gray"
                    Write-Color "    CPU:     ${cpuSec}s" "Gray"
                    Write-Color "    Memory:  ${memoryMB}MB" "Gray"
                    Write-Color ""
                }
            }
        }
        
        # Log files
        $projectRoot = Split-Path $PSScriptRoot -Parent
        $logsDir = Join-Path $projectRoot "logs"
        
        if (Test-Path $logsDir) {
            Write-Color "Recent Log Activity:" "Yellow"
            Write-Color "============================================================`n" "Cyan"
            
            $logFiles = @(
                "f1t-api.log",
                "periodic-update.log",
                "cloudflare-tunnel.log"
            )
            
            foreach ($logFileName in $logFiles) {
                $logPath = Join-Path $logsDir $logFileName
                if (Test-Path $logPath) {
                    $logFile = Get-Item $logPath
                    $sizeMB = [math]::Round($logFile.Length / 1MB, 2)
                    $age = (Get-Date) - $logFile.LastWriteTime
                    $ageStr = if ($age.TotalMinutes -lt 1) { 
                        "$([math]::Round($age.TotalSeconds))s ago" 
                    } elseif ($age.TotalHours -lt 1) { 
                        "$([math]::Round($age.TotalMinutes))m ago" 
                    } else { 
                        "$([math]::Round($age.TotalHours, 1))h ago" 
                    }
                    
                    $color = if ($age.TotalMinutes -lt 5) { "Green" } else { "Yellow" }
                    Write-Color "  $logFileName" $color
                    Write-Color "    Size:    ${sizeMB}MB" "Gray"
                    Write-Color "    Updated: $ageStr" "Gray"
                    Write-Color ""
                } else {
                    Write-Color "  ${logFileName}: Not found" "Gray"
                }
            }
        }
    }
    
    "Logs" {
        $projectRoot = Split-Path $PSScriptRoot -Parent
        $logsDir = Join-Path $projectRoot "logs"
        
        Write-Color "Opening logs directory..." "Yellow"
        if (Test-Path $logsDir) {
            explorer.exe $logsDir
            Write-Color "  OK Opened: $logsDir" "Green"
        } else {
            Write-Color "  ERROR Logs directory not found: $logsDir" "Red"
        }
    }
}

# Summary commands
Write-Color "`n============================================================" "Cyan"
Write-Color " Command Reference" "White"
Write-Color "============================================================`n" "Cyan"

Write-Color "Service Management:" "White"
Write-Color "  Start:    .\nssm\manage-services.ps1 -Action Start" "Gray"
Write-Color "  Stop:     .\nssm\manage-services.ps1 -Action Stop" "Gray"
Write-Color "  Restart:  .\nssm\manage-services.ps1 -Action Restart" "Gray"
Write-Color "  Status:   .\nssm\manage-services.ps1 -Action Status" "Gray"

Write-Color "`nSingle Service:" "White"
Write-Color "  .\nssm\manage-services.ps1 -Action Start -Service F1T-API" "Gray"

Write-Color "`nDirect Log Access:" "White"
Write-Color "  Get-Content logs\f1t-api.log -Tail 50 -Wait" "Gray"

Write-Color "`nWindows Services Manager:" "White"
Write-Color "  services.msc`n" "Gray"
