param([int]$RefreshInterval = 5)

$expectedTotal = 665

function Get-JsonCount {
    param($pattern)
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    return @($files).Count
}

Write-Host "Monitor Started" -ForegroundColor Cyan
$startTime = Get-Date

while ($true) {
    Clear-Host
    $elapsed = (Get-Date) - $startTime
    
    Write-Host "=== Track Features Monitor ===" -ForegroundColor Cyan
    Write-Host "Runtime: $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Yellow
    Write-Host ""
    
    $count1 = Get-JsonCount "*enhanced_rain_analysis*_FP3.json"
    Write-Host "F1  Weather : $count1 / 133" -ForegroundColor $(if($count1 -eq 133){"Green"}else{"Yellow"})
    
    $count34 = Get-JsonCount "*brake_performance*_FP3.json"
    Write-Host "F34 Brake   : $count34 / 133" -ForegroundColor $(if($count34 -eq 133){"Green"}else{"Yellow"})
    
    $count47 = Get-JsonCount "*all_drivers_cornering_analysis*_FP3.json"
    Write-Host "F47 Corner  : $count47 / 133" -ForegroundColor $(if($count47 -eq 133){"Green"}else{"Yellow"})
    
    $count48 = Get-JsonCount "*all_drivers_straight_line_speed*_FP3.json"
    Write-Host "F48 Speed   : $count48 / 133" -ForegroundColor $(if($count48 -eq 133){"Green"}else{"Yellow"})
    
    $count54 = Get-JsonCount "*driver_throttle_ratio*_FP3.json"
    Write-Host "F54 Throttle: $count54 / 133" -ForegroundColor $(if($count54 -eq 133){"Green"}else{"Yellow"})
    
    Write-Host ""
    $totalCount = $count1 + $count34 + $count47 + $count48 + $count54
    $percentage = [math]::Round(($totalCount / $expectedTotal) * 100, 1)
    Write-Host "Total: $totalCount / $expectedTotal - $percentage%" -ForegroundColor $(if($totalCount -eq $expectedTotal){"Green"}else{"Cyan"})
    
    Start-Sleep -Seconds $RefreshInterval
}
