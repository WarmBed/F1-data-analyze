# 簡化版監控腳本
param([int]$RefreshInterval = 5)

$expectedTotal = 665  # 133 races * 5 functions

function Get-JsonCount {
    param($pattern)
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    return @($files).Count
}

Write-Host "開始監控賽道特徵 JSON 生成..." -ForegroundColor Cyan
Write-Host "預期總數: $expectedTotal 個檔案" -ForegroundColor Yellow
Write-Host ""

$startTime = Get-Date

while ($true) {
    Clear-Host
    
    $elapsed = (Get-Date) - $startTime
    $elapsedStr = "{0:hh\:mm\:ss}" -f $elapsed
    
    Write-Host "=== 賽道特徵生成監控 ===" -ForegroundColor Cyan
    Write-Host "運行時間: $elapsedStr" -ForegroundColor Yellow
    Write-Host ""
    
    # Function 1 - 天氣
    $count1 = Get-JsonCount "*enhanced_rain_analysis*_FP3.json"
    Write-Host "F1  Weather : $count1 / 133" -ForegroundColor $(if($count1 -eq 133){"Green"}else{"Yellow"})
    
    # Function 34 - 煞車
    $count34 = Get-JsonCount "*brake_performance*_FP3.json"
    Write-Host "F34 Brake   : $count34 / 133" -ForegroundColor $(if($count34 -eq 133){"Green"}else{"Yellow"})
    
    # Function 47 - 彎道
    $count47 = Get-JsonCount "*all_drivers_cornering_analysis*_FP3.json"
    Write-Host "F47 Corner  : $count47 / 133" -ForegroundColor $(if($count47 -eq 133){"Green"}else{"Yellow"})
    
    # Function 48 - 速度
    $count48 = Get-JsonCount "*all_drivers_straight_line_speed*_FP3.json"
    Write-Host "F48 Speed   : $count48 / 133" -ForegroundColor $(if($count48 -eq 133){"Green"}else{"Yellow"})
    
    # Function 54 - 油門
    $count54 = Get-JsonCount "*driver_throttle_ratio*_FP3.json"
    Write-Host "F54 Throttle: $count54 / 133" -ForegroundColor $(if($count54 -eq 133){"Green"}else{"Yellow"})
    
    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    
    $totalCount = $count1 + $count34 + $count47 + $count48 + $count54
    $percentage = [math]::Round(($totalCount / $expectedTotal) * 100, 1)
    
    Write-Host "Total: $totalCount / $expectedTotal - $percentage%" -ForegroundColor $(if($totalCount -eq $expectedTotal){"Green"}else{"Cyan"})
    
    Write-Host ""
    Write-Host "按 Ctrl+C 停止監控..." -ForegroundColor DarkGray
    
    Start-Sleep -Seconds $RefreshInterval
}
