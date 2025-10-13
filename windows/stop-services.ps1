# F1T Services Manager - Stop All Services
# Windows PowerShell Edition

$ErrorActionPreference = "Continue"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Services Manager - Stopping All Services" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Load saved job info
$savedJobsFile = "logs\running-services.xml"
if (Test-Path $savedJobsFile) {
    Write-Color "[1/3] Loading service information..." "Yellow"
    try {
        $jobInfo = Import-Clixml -Path $savedJobsFile
        Write-Color "  OK Found $($jobInfo.Count) registered services" "Green"
    } catch {
        Write-Color "  WARNING Cannot load service info: $_" "Yellow"
        $jobInfo = @()
    }
} else {
    Write-Color "[1/3] No saved service info found" "Yellow"
    $jobInfo = @()
}

# Stop all PowerShell jobs
Write-Color "`n[2/3] Stopping PowerShell background jobs..." "Yellow"
$jobs = Get-Job -ErrorAction SilentlyContinue

if ($jobs) {
    foreach ($job in $jobs) {
        Write-Color "  Stopping Job ID $($job.Id) ($($job.State))..." "Gray"
        Stop-Job -Id $job.Id -ErrorAction SilentlyContinue
        Remove-Job -Id $job.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Color "  OK All jobs stopped" "Green"
} else {
    Write-Color "  INFO No jobs running" "Cyan"
}

# Kill related processes
Write-Color "`n[3/3] Stopping related processes..." "Yellow"

$processNames = @("python", "cloudflared")
$stopped = 0

foreach ($procName in $processNames) {
    $processes = Get-Process -Name $procName -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*F1-data-analyze*" -or 
        $_.CommandLine -like "*refactored_api*" -or
        $_.CommandLine -like "*periodic_update*"
    }
    
    foreach ($proc in $processes) {
        try {
            Write-Color "  Stopping $procName (PID: $($proc.Id))..." "Gray"
            Stop-Process -Id $proc.Id -Force -ErrorAction Stop
            $stopped++
        } catch {
            Write-Color "    WARNING Cannot stop process: $_" "Yellow"
        }
    }
}

if ($stopped -gt 0) {
    Write-Color "  OK Stopped $stopped process(es)" "Green"
} else {
    Write-Color "  INFO No related processes found" "Cyan"
}

# Clean up saved job info
if (Test-Path $savedJobsFile) {
    Remove-Item $savedJobsFile -Force -ErrorAction SilentlyContinue
}

# Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " All services stopped" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "To start services again, run: .\windows\start-services.ps1`n" "Gray"
