# F1T Services Manager for Windows
# Pure PowerShell solution - No dependencies required

$ErrorActionPreference = "Stop"

# Color output
function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Services Manager - Windows PowerShell Edition" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Service definitions
$services = @(
    @{
        Name = "F1T-API"
        Command = "python"
        Args = @("refactored_api.py")
        LogFile = "logs\f1t-api.log"
        Color = "Green"
    },
    @{
        Name = "Periodic-Update"
        Command = "python"
        Args = @("scripts\periodic_update_service.py")
        LogFile = "logs\periodic-update.log"
        Color = "Yellow"
    },
    @{
        Name = "Cloudflare-Tunnel"
        Command = "cloudflared\cloudflared.exe"
        Args = @("--config", "cloudflared\config.yml", "tunnel", "run", "myfastapi")
        LogFile = "logs\cloudflare-tunnel.log"
        Color = "Cyan"
    }
)

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Force -Path "logs" | Out-Null
}

# Start all services
Write-Color "[1/3] Starting all services...`n" "Yellow"

$jobs = @()
$jobInfo = @()

foreach ($svc in $services) {
    Write-Color "  Starting $($svc.Name)..." $svc.Color
    
    # Prepare command
    $scriptBlock = {
        param($cmd, $arguments, $logFile)
        
        # Redirect output to log file
        $process = Start-Process -FilePath $cmd `
                                  -ArgumentList $arguments `
                                  -WorkingDirectory $PWD `
                                  -NoNewWindow `
                                  -PassThru `
                                  -RedirectStandardOutput $logFile `
                                  -RedirectStandardError "$logFile.err"
        
        # Keep process alive
        $process.WaitForExit()
        return $process.ExitCode
    }
    
    try {
        # Start as background job
        $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $svc.Command, $svc.Args, $svc.LogFile
        
        $jobs += $job
        $jobInfo += @{
            JobId = $job.Id
            Name = $svc.Name
            LogFile = $svc.LogFile
            Color = $svc.Color
        }
        
        Write-Color "    OK Started (Job ID: $($job.Id))" "Green"
    } catch {
        Write-Color "    ERROR Failed to start: $_" "Red"
    }
}

# Wait for services to initialize
Write-Color "`n[2/3] Waiting for services to initialize..." "Yellow"
Start-Sleep -Seconds 5

# Check job status
Write-Color "`n[3/3] Service Status:" "Yellow"
Write-Color "============================================================" "Cyan"

foreach ($info in $jobInfo) {
    $job = Get-Job -Id $info.JobId -ErrorAction SilentlyContinue
    if ($job) {
        $status = $job.State
        $statusColor = if ($status -eq "Running") { "Green" } else { "Red" }
        Write-Color "  $($info.Name): $status (Job ID: $($info.JobId))" $statusColor
        Write-Color "    Log: $($info.LogFile)" "Gray"
    }
}

# Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " SUCCESS - All services started in background!" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "Management Commands:" "White"
Write-Color "  View jobs:     Get-Job" "Gray"
Write-Color "  Stop all:      Get-Job | Stop-Job" "Gray"
Write-Color "  Remove jobs:   Get-Job | Remove-Job -Force" "Gray"
Write-Color "  API log:       Get-Content logs\f1t-api.log -Tail 50 -Wait" "Gray"
Write-Color "  Update log:    Get-Content logs\periodic-update.log -Tail 50 -Wait" "Gray"
Write-Color "  Tunnel log:    Get-Content logs\cloudflare-tunnel.log -Tail 50 -Wait" "Gray"
Write-Color "`nTo stop all services, run: .\windows\stop-services.ps1`n" "Cyan"

# Save job info for later management
$jobInfo | Export-Clixml -Path "logs\running-services.xml"
Write-Color "Service info saved to: logs\running-services.xml" "Gray"
