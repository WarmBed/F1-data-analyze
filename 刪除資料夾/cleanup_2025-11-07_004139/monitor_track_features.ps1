# 賽道特徵 JSON 生成監控腳本
# Monitor Track Feature JSON Generation

param(
    [int]$RefreshInterval = 5,  # 刷新間隔（秒）
    [switch]$ShowDetails        # 顯示詳細檔案列表
)

Write-Host "📊 賽道特徵 JSON 生成監控器" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

# 定義要監控的 JSON 模式
$patterns = @{
    "Function 48 (速度)" = "*all_drivers_straight_line_speed*.json"
    "Function 54 (油門)" = "*driver_throttle_ratio*.json"
    "Function 34 (煞車)" = "*brake_performance*.json"
    "Function 17 (彎道)" = "*dynamic_corner*.json"
    "Function 1 (天氣)" = "*enhanced_rain*.json"
}

# 預期總數（133 場賽事 × 5 個功能）
$expectedTotal = 133 * 5

# 初始化統計
$lastCounts = @{}
$startTime = Get-Date

function Get-FileCount {
    param($pattern)
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    return $files.Count
}

function Get-LatestFiles {
    param($pattern, $count = 5)
    Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $count
}

function Show-Statistics {
    Clear-Host
    
    $currentTime = Get-Date
    $elapsed = $currentTime - $startTime
    
    Write-Host "📊 賽道特徵 JSON 生成監控" -ForegroundColor Cyan
    Write-Host "=" * 80
    Write-Host "⏱️  運行時間: $($elapsed.ToString('hh\:mm\:ss'))" -ForegroundColor Yellow
    Write-Host "🔄 刷新間隔: $RefreshInterval 秒" -ForegroundColor Yellow
    Write-Host "🎯 預期總數: $expectedTotal 個 JSON 檔案" -ForegroundColor Yellow
    Write-Host ""
    
    $totalCount = 0
    $newFilesTotal = 0
    
    foreach ($name in $patterns.Keys) {
        $pattern = $patterns[$name]
        
        $count = Get-FileCount $pattern
        $totalCount += $count
        
        # 計算新增數量
        $newFiles = 0
        if ($lastCounts.ContainsKey($name)) {
            $newFiles = $count - $lastCounts[$name]
            if ($newFiles -gt 0) {
                $newFilesTotal += $newFiles
            }
        }
        $lastCounts[$name] = $count
        
        # 顯示統計
        $percentage = if ($expectedTotal -gt 0) { ($count / ($expectedTotal / 5)) * 100 } else { 0 }
        $bar = "=" * [Math]::Min([Math]::Floor($percentage / 2), 50)
        
        Write-Host $name -ForegroundColor White -NoNewline
        $expected = [Math]::Floor($expectedTotal / 5)
        Write-Host " ($count / $expected)" -ForegroundColor Gray
        $percentStr = $percentage.ToString('F1')
        Write-Host "  $bar $percentStr percent" -ForegroundColor Green
        
        if ($newFiles -gt 0) {
            Write-Host "  📈 +$newFiles 個新檔案" -ForegroundColor Yellow
        }
        
        # 顯示最新檔案
        if ($ShowDetails) {
            $latestFiles = Get-LatestFiles $pattern 3
            if ($latestFiles) {
                foreach ($file in $latestFiles) {
                    $age = (Get-Date) - $file.LastWriteTime
                    $ageMin = $age.TotalMinutes.ToString('F1')
                    $displayText = "     - " + $file.Name + " (" + $ageMin + " min ago)"
                    Write-Host $displayText -ForegroundColor DarkGray
                }
            }
        }
        
        Write-Host ""
    }
    
    # 總計
    Write-Host ("=" * 80)
    $overallPercentage = ($totalCount / $expectedTotal) * 100
    $overallStr = $overallPercentage.ToString('F1')
    $totalText = "Total: " + $totalCount + " / " + $expectedTotal + " (" + $overallStr + " percent)"
    Write-Host $totalText -ForegroundColor Cyan
    
    if ($newFilesTotal -gt 0) {
        Write-Host "📈 本輪新增: $newFilesTotal 個檔案" -ForegroundColor Yellow
    }
    
    # 預估完成時間
    if ($totalCount -gt 0 -and $newFilesTotal -gt 0) {
        $remaining = $expectedTotal - $totalCount
        $rate = $newFilesTotal / $RefreshInterval  # 每秒生成速度
        
        if ($rate -gt 0) {
            $estimatedSeconds = $remaining / $rate
            $estimatedTime = [TimeSpan]::FromSeconds($estimatedSeconds)
            Write-Host "⏳ 預估完成時間: $($estimatedTime.ToString('hh\:mm\:ss'))" -ForegroundColor Magenta
        }
    }
    
    Write-Host ""
    Write-Host "按 Ctrl+C 停止監控..." -ForegroundColor DarkGray
    Write-Host "使用 -ShowDetails 參數顯示最新檔案列表" -ForegroundColor DarkGray
}

# 主監控循環
try {
    while ($true) {
        Show-Statistics
        Start-Sleep -Seconds $RefreshInterval
    }
}
catch {
    Write-Host "`n`n⚠️  監控已停止" -ForegroundColor Yellow
    
    # 最終統計
    Write-Host "`n📊 最終統計:" -ForegroundColor Cyan
    $finalTotal = 0
    foreach ($name in $patterns.Keys) {
        $pattern = $patterns[$name]
        $count = Get-FileCount $pattern
        $finalTotal += $count
        Write-Host "  $name : $count 個檔案" -ForegroundColor White
    }
    
    $finalPercentage = ($finalTotal / $expectedTotal) * 100
    $finalStr = $finalPercentage.ToString('F1')
    $completeText = "Completion: " + $finalTotal + " / " + $expectedTotal + " (" + $finalStr + " percent)"
    Write-Host ""
    Write-Host $completeText -ForegroundColor Green
}
