# Monitor FP1/FP2/FP3 Track Features JSON Collection Progress
# Usage: .\monitor_all_sessions.ps1 -RefreshInterval 5

param([int]$RefreshInterval = 5)

$expectedPerSession = 665  # 133 races * 5 functions

function Get-JsonCount {
    param($pattern)
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    return @($files).Count
}

function Get-SessionStats {
    param($session)
    
    $counts = @{
        'F1'  = Get-JsonCount "*enhanced_rain_analysis*_$session.json"
        'F34' = Get-JsonCount "*brake_performance*_$session.json"
        'F47' = Get-JsonCount "*all_drivers_cornering_analysis*_$session.json"
        'F48' = Get-JsonCount "*all_drivers_straight_line_speed*_$session.json"
        'F54' = Get-JsonCount "*throttle_ratio*_$session.json"
    }
    
    $total = ($counts.Values | Measure-Object -Sum).Sum
    return @{
        'Counts' = $counts
        'Total' = $total
        'Percentage' = [math]::Round(($total / 665) * 100, 1)
    }
}

Write-Host "Monitor Started - Press Ctrl+C to stop" -ForegroundColor Cyan
$startTime = Get-Date

while ($true) {
    Clear-Host
    
    $elapsed = (Get-Date) - $startTime
    $elapsedStr = "{0:hh\:mm\:ss}" -f $elapsed
    
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "   Track Features JSON Collection Monitor (FP1/FP2/FP3)" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Runtime: $elapsedStr" -ForegroundColor Yellow
    Write-Host "Refresh: $RefreshInterval sec" -ForegroundColor DarkGray
    Write-Host ""
    
    # Get stats for each session
    $fp1Stats = Get-SessionStats "FP1"
    $fp2Stats = Get-SessionStats "FP2"
    $fp3Stats = Get-SessionStats "FP3"
    
    # Display FP1
    Write-Host "=== FP1 Practice 1 ===" -ForegroundColor Yellow
    foreach ($func in @('F1', 'F34', 'F47', 'F48', 'F54')) {
        $count = $fp1Stats.Counts[$func]
        $color = if ($count -eq 133) { "Green" } else { "White" }
        $funcName = switch ($func) {
            'F1'  { "Weather" }
            'F34' { "Brake" }
            'F47' { "Corner" }
            'F48' { "Speed" }
            'F54' { "Throttle" }
        }
        Write-Host "  $func ($funcName): $count / 133" -ForegroundColor $color
    }
    $totalColor = if($fp1Stats.Total -eq 665){"Green"}else{"Cyan"}
    Write-Host ("  Total: {0} / 665 ({1}%)" -f $fp1Stats.Total, $fp1Stats.Percentage) -ForegroundColor $totalColor
    Write-Host ""
    
    # Display FP2
    Write-Host "=== FP2 Practice 2 ===" -ForegroundColor Yellow
    foreach ($func in @('F1', 'F34', 'F47', 'F48', 'F54')) {
        $count = $fp2Stats.Counts[$func]
        $color = if ($count -eq 133) { "Green" } else { "White" }
        $funcName = switch ($func) {
            'F1'  { "Weather" }
            'F34' { "Brake" }
            'F47' { "Corner" }
            'F48' { "Speed" }
            'F54' { "Throttle" }
        }
        Write-Host "  $func ($funcName): $count / 133" -ForegroundColor $color
    }
    $totalColor = if($fp2Stats.Total -eq 665){"Green"}else{"Cyan"}
    Write-Host ("  Total: {0} / 665 ({1}%)" -f $fp2Stats.Total, $fp2Stats.Percentage) -ForegroundColor $totalColor
    Write-Host ""
    
    # Display FP3
    Write-Host "=== FP3 Practice 3 ===" -ForegroundColor Yellow
    foreach ($func in @('F1', 'F34', 'F47', 'F48', 'F54')) {
        $count = $fp3Stats.Counts[$func]
        $color = if ($count -eq 133) { "Green" } else { "White" }
        $funcName = switch ($func) {
            'F1'  { "Weather" }
            'F34' { "Brake" }
            'F47' { "Corner" }
            'F48' { "Speed" }
            'F54' { "Throttle" }
        }
        Write-Host "  $func ($funcName): $count / 133" -ForegroundColor $color
    }
    $totalColor = if($fp3Stats.Total -eq 665){"Green"}else{"Cyan"}
    Write-Host ("  Total: {0} / 665 ({1}%)" -f $fp3Stats.Total, $fp3Stats.Percentage) -ForegroundColor $totalColor
    Write-Host ""
    
    # Grand total
    Write-Host "=================================================================" -ForegroundColor Cyan
    $grandTotal = $fp1Stats.Total + $fp2Stats.Total + $fp3Stats.Total
    $grandExpected = 665 * 3  # 1995
    $grandPercentage = [math]::Round(($grandTotal / $grandExpected) * 100, 1)
    
    $grandColor = if($grandTotal -eq $grandExpected){"Green"}else{"Cyan"}
    Write-Host ("All Sessions Total: {0} / {1} ({2}%)" -f $grandTotal, $grandExpected, $grandPercentage) -ForegroundColor $grandColor
    Write-Host ""
    
    # Estimate remaining time (if there is progress)
    if ($grandTotal -gt 0 -and $elapsed.TotalSeconds -gt 60) {
        $avgSecondsPerFile = $elapsed.TotalSeconds / $grandTotal
        $remainingFiles = $grandExpected - $grandTotal
        $remainingSeconds = $avgSecondsPerFile * $remainingFiles
        $remainingTime = [TimeSpan]::FromSeconds($remainingSeconds)
        Write-Host ("Estimated Time Remaining: {0:hh\:mm\:ss}" -f $remainingTime) -ForegroundColor Yellow
        Write-Host ("Average Speed: {0:F1} sec/file" -f $avgSecondsPerFile) -ForegroundColor DarkGray
    }
    
    Write-Host ""
    Write-Host "Press Ctrl+C to stop monitoring..." -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $RefreshInterval
}
