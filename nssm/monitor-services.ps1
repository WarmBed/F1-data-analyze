# F1T Services Real-time Monitor
# Watch service status in real-time

param(
    [int]$RefreshSeconds = 3
)

function Get-ServiceStatus {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "F1T Services Monitor - $timestamp" -ForegroundColor Cyan
    Write-Host "Refresh every ${RefreshSeconds}s (Press Ctrl+C to stop)" -ForegroundColor Gray
    Write-Host "============================================================`n" -ForegroundColor Cyan
    
    # Check services
    $services = Get-Service F1T-* -ErrorAction SilentlyContinue
    
    if ($services) {
        foreach ($svc in $services) {
            $statusIcon = if ($svc.Status -eq 'Running') { '✅' } else { '❌' }
            $statusColor = if ($svc.Status -eq 'Running') { 'Green' } else { 'Red' }
            
            Write-Host "  $statusIcon $($svc.Name)" -NoNewline
            Write-Host " - " -NoNewline
            Write-Host "$($svc.Status)" -ForegroundColor $statusColor
        }
    } else {
        Write-Host "  No F1T services found" -ForegroundColor Yellow
    }
    
    # Check processes
    Write-Host "`n[Processes]" -ForegroundColor Yellow
    
    $pythonCount = (Get-Process python -ErrorAction SilentlyContinue).Count
    $cloudflaredCount = (Get-Process cloudflared -ErrorAction SilentlyContinue).Count
    
    Write-Host "  Python processes: $pythonCount" -ForegroundColor Gray
    Write-Host "  Cloudflared processes: $cloudflaredCount" -ForegroundColor Gray
    
    # Check API health
    Write-Host "`n[API Health]" -ForegroundColor Yellow
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            Write-Host "  ✅ API is responding (HTTP $($response.StatusCode))" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ❌ API is not responding" -ForegroundColor Red
    }
    
    # Check log activity
    Write-Host "`n[Recent Log Activity]" -ForegroundColor Yellow
    
    $logFiles = @(
        @{Name="API"; Path="logs\f1t-api.log"},
        @{Name="Update"; Path="logs\periodic-update.log"},
        @{Name="Tunnel"; Path="logs\cloudflare-tunnel.log"}
    )
    
    foreach ($log in $logFiles) {
        if (Test-Path $log.Path) {
            $file = Get-Item $log.Path
            $age = (Get-Date) - $file.LastWriteTime
            
            if ($age.TotalMinutes -lt 1) {
                $ageStr = "$([math]::Round($age.TotalSeconds))s ago"
                $color = "Green"
            } elseif ($age.TotalMinutes -lt 5) {
                $ageStr = "$([math]::Round($age.TotalMinutes))m ago"
                $color = "Yellow"
            } else {
                $ageStr = "$([math]::Round($age.TotalMinutes))m ago"
                $color = "Red"
            }
            
            Write-Host "  $($log.Name): Updated $ageStr" -ForegroundColor $color
        } else {
            Write-Host "  $($log.Name): No log file" -ForegroundColor Gray
        }
    }
    
    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "Commands:" -ForegroundColor White
    Write-Host "  Start:  .\nssm\nssm.exe start F1T-API" -ForegroundColor Gray
    Write-Host "  Stop:   .\nssm\nssm.exe stop F1T-API" -ForegroundColor Gray
    Write-Host "  Status: .\nssm\nssm.exe status F1T-API" -ForegroundColor Gray
}

# Main loop
Write-Host "Starting F1T Services Monitor..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

try {
    while ($true) {
        Get-ServiceStatus
        Start-Sleep -Seconds $RefreshSeconds
    }
} catch {
    Write-Host "`n`nMonitor stopped" -ForegroundColor Yellow
}
