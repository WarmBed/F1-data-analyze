# Check F1T Services Status (No admin required)

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "F1T Services Status Check" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check services
Write-Host "[1/3] Windows Services:" -ForegroundColor Yellow
Write-Host ""

Get-Service F1T-* | ForEach-Object {
    $statusColor = if ($_.Status -eq 'Running') { 'Green' } else { 'Red' }
    Write-Host "  $($_.Name)" -ForegroundColor White
    Write-Host "    Status:     $($_.Status)" -ForegroundColor $statusColor
    Write-Host "    Start Type: $($_.StartType)" -ForegroundColor Gray
    Write-Host "    Display:    $($_.DisplayName)" -ForegroundColor Gray
    Write-Host ""
}

# Check processes
Write-Host "[2/3] Running Processes:" -ForegroundColor Yellow
Write-Host ""

$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
$cloudflaredProcs = Get-Process cloudflared -ErrorAction SilentlyContinue

if ($pythonProcs) {
    foreach ($proc in $pythonProcs) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        $cpuSec = [math]::Round($proc.CPU, 2)
        Write-Host "  Python" -ForegroundColor Green
        Write-Host "    PID:    $($proc.Id)" -ForegroundColor Gray
        Write-Host "    CPU:    ${cpuSec}s" -ForegroundColor Gray
        Write-Host "    Memory: ${memMB}MB" -ForegroundColor Gray
        Write-Host ""
    }
}

if ($cloudflaredProcs) {
    foreach ($proc in $cloudflaredProcs) {
        $memMB = [math]::Round($proc.WorkingSet64 / 1MB, 2)
        $cpuSec = [math]::Round($proc.CPU, 2)
        Write-Host "  Cloudflared" -ForegroundColor Green
        Write-Host "    PID:    $($proc.Id)" -ForegroundColor Gray
        Write-Host "    CPU:    ${cpuSec}s" -ForegroundColor Gray
        Write-Host "    Memory: ${memMB}MB" -ForegroundColor Gray
        Write-Host ""
    }
}

if (-not $pythonProcs -and -not $cloudflaredProcs) {
    Write-Host "  No processes found" -ForegroundColor Gray
    Write-Host ""
}

# Check logs
Write-Host "[3/3] Log Files:" -ForegroundColor Yellow
Write-Host ""

$logFiles = @("f1t-api.log", "periodic-update.log", "cloudflare-tunnel.log")

foreach ($logFile in $logFiles) {
    $logPath = "logs\$logFile"
    if (Test-Path $logPath) {
        $fileInfo = Get-Item $logPath
        $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
        $age = (Get-Date) - $fileInfo.LastWriteTime
        $ageStr = if ($age.TotalMinutes -lt 1) { 
            "$([math]::Round($age.TotalSeconds))s ago" 
        } elseif ($age.TotalHours -lt 1) { 
            "$([math]::Round($age.TotalMinutes))m ago" 
        } else { 
            "$([math]::Round($age.TotalHours, 1))h ago" 
        }
        
        $color = if ($age.TotalMinutes -lt 5) { 'Green' } else { 'Yellow' }
        Write-Host "  $logFile" -ForegroundColor $color
        Write-Host "    Size:    ${sizeMB}MB" -ForegroundColor Gray
        Write-Host "    Updated: $ageStr" -ForegroundColor Gray
        Write-Host ""
    } else {
        Write-Host "  $logFile" -ForegroundColor Gray
        Write-Host "    Not found" -ForegroundColor Gray
        Write-Host ""
    }
}

# Summary
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Management Commands:" -ForegroundColor White
Write-Host ""
Write-Host "  Start services:  (Admin) .\nssm\start-all.ps1" -ForegroundColor Gray
Write-Host "  Stop services:   (Admin) Stop-Service F1T-*" -ForegroundColor Gray
Write-Host "  View logs:       Get-Content logs\f1t-api.log -Tail 50 -Wait" -ForegroundColor Gray
Write-Host "  Test API:        Invoke-WebRequest http://localhost:8000/health" -ForegroundColor Gray
Write-Host "  Services UI:     services.msc" -ForegroundColor Gray
Write-Host ""
