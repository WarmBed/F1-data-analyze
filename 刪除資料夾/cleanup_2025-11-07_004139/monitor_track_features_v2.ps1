# Track Feature JSON Generation Monitor
# Simple and stable version

param(
    [int]$RefreshInterval = 5,
    [switch]$ShowDetails
)

Write-Host "Track Feature JSON Generation Monitor" -ForegroundColor Cyan
Write-Host ("=" * 80)
Write-Host ""

# Define monitoring patterns
$patterns = @(
    @{Name="Function 48 (Speed)"; Pattern="*all_drivers_straight_line_speed*.json"},
    @{Name="Function 54 (Throttle)"; Pattern="*driver_throttle_ratio*.json"},
    @{Name="Function 34 (Brake)"; Pattern="*brake_performance*.json"},
    @{Name="Function 17 (Corner)"; Pattern="*dynamic_corner*.json"},
    @{Name="Function 1 (Weather)"; Pattern="*enhanced_rain*.json"}
)

$expectedTotal = 665  # 133 races x 5 functions
$startTime = Get-Date
$lastCounts = @{}

function Get-JsonCount {
    param([string]$pattern)
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    return $files.Count
}

function Show-Progress {
    Clear-Host
    
    $elapsed = (Get-Date) - $startTime
    $elapsedStr = $elapsed.ToString('hh\:mm\:ss')
    
    Write-Host "Track Feature JSON Generation Monitor" -ForegroundColor Cyan
    Write-Host ("=" * 80)
    Write-Host "Runtime: $elapsedStr" -ForegroundColor Yellow
    Write-Host "Refresh: $RefreshInterval seconds" -ForegroundColor Yellow
    Write-Host "Target: $expectedTotal JSON files" -ForegroundColor Yellow
    Write-Host ""
    
    $totalCount = 0
    $newFilesTotal = 0
    
    foreach ($item in $patterns) {
        $name = $item.Name
        $pattern = $item.Pattern
        
        $count = Get-JsonCount $pattern
        $totalCount += $count
        
        # Calculate new files
        $newFiles = 0
        if ($lastCounts.ContainsKey($name)) {
            $diff = $count - $lastCounts[$name]
            if ($diff -gt 0) {
                $newFiles = $diff
                $newFilesTotal += $newFiles
            }
        }
        $lastCounts[$name] = $count
        
        # Display progress
        $expected = [Math]::Floor($expectedTotal / 5)
        $percentage = if ($expected -gt 0) { ($count / $expected) * 100 } else { 0 }
        $barLength = [Math]::Min([Math]::Floor($percentage / 2), 50)
        $bar = "=" * $barLength
        $percentStr = $percentage.ToString("F1")
        
        Write-Host "$name " -NoNewline -ForegroundColor White
        Write-Host "($count / $expected)" -ForegroundColor Gray
        Write-Host "  $bar $percentStr percent" -ForegroundColor Green
        
        if ($newFiles -gt 0) {
            Write-Host "  New: +$newFiles files" -ForegroundColor Yellow
        }
        
        Write-Host ""
    }
    
    # Total summary
    Write-Host ("=" * 80)
    $overallPct = ($totalCount / $expectedTotal) * 100
    $overallStr = $overallPct.ToString("F1")
    Write-Host "Total: $totalCount / $expectedTotal ($overallStr percent)" -ForegroundColor Cyan
    
    if ($newFilesTotal -gt 0) {
        Write-Host "New this round: $newFilesTotal files" -ForegroundColor Yellow
        
        # Estimate completion time
        $remaining = $expectedTotal - $totalCount
        $rate = $newFilesTotal / $RefreshInterval
        
        if ($rate -gt 0) {
            $estSeconds = $remaining / $rate
            $estTime = [TimeSpan]::FromSeconds($estSeconds)
            $estStr = $estTime.ToString('hh\:mm\:ss')
            Write-Host "Estimated completion: $estStr" -ForegroundColor Magenta
        }
    }
    
    Write-Host ""
    Write-Host "Press Ctrl+C to stop..." -ForegroundColor DarkGray
}

# Main monitoring loop
try {
    while ($true) {
        Show-Progress
        Start-Sleep -Seconds $RefreshInterval
    }
}
catch {
    Write-Host "`n`nMonitoring stopped" -ForegroundColor Yellow
    
    # Final statistics
    Write-Host "`nFinal Statistics:" -ForegroundColor Cyan
    $finalTotal = 0
    
    foreach ($item in $patterns) {
        $count = Get-JsonCount $item.Pattern
        $finalTotal += $count
        Write-Host "  $($item.Name): $count files" -ForegroundColor White
    }
    
    $finalPct = ($finalTotal / $expectedTotal) * 100
    $finalStr = $finalPct.ToString("F1")
    Write-Host "`nCompletion: $finalTotal / $expectedTotal ($finalStr percent)" -ForegroundColor Green
}
