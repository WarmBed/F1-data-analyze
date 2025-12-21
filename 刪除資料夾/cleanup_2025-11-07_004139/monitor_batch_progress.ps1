# 批量生成進度監控腳本
# 實時顯示賽道特徵 JSON 生成狀態

$jsonDir = "json\trackFeaturesJSON"

# 定義功能 ID 和對應的檔名前綴（不區分大小寫）
$functionPrefixes = @{
    "F48" = "all_drivers_straight_line_speed"
    "F54" = "throttle_ratio"
    "F34" = "brake_performance"
    "F47" = "all_drivers_cornering"
    "F1"  = "enhanced_rain_analysis"
}

# 總目標數量（149 場賽事 × 5 功能）
$totalTarget = 149 * 5

Write-Host "=" * 80
Write-Host "🔍 賽道特徵 JSON 生成進度監控" -ForegroundColor Cyan
Write-Host "=" * 80
Write-Host ""

while ($true) {
    Clear-Host
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "=" * 80
    Write-Host "📊 進度報告 - $timestamp" -ForegroundColor Green
    Write-Host "=" * 80
    Write-Host ""
    
    # 檢查資料夾是否存在
    if (-not (Test-Path $jsonDir)) {
        Write-Host "⚠️  資料夾不存在: $jsonDir" -ForegroundColor Yellow
        Write-Host "   正在等待批量腳本創建資料夾..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        continue
    }
    
    # 統計各功能的 JSON 檔案數量
    $allFiles = Get-ChildItem -Path $jsonDir -Filter "*.json" -File
    $totalCount = $allFiles.Count
    
    Write-Host "📁 總檔案數: $totalCount / $totalTarget" -ForegroundColor Cyan
    Write-Host "📈 完成度: $([math]::Round($totalCount / $totalTarget * 100, 1))%" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "-" * 80
    Write-Host ""
    
    # 統計各功能的數量
    foreach ($funcId in $functionPrefixes.Keys | Sort-Object) {
        $prefix = $functionPrefixes[$funcId]
        $count = ($allFiles | Where-Object { $_.Name -like "$prefix*" }).Count
        $target = 149
        $percentage = [math]::Round($count / $target * 100, 1)
        
        # 顯示進度條
        $barLength = 40
        $filledLength = [math]::Floor($barLength * $count / $target)
        $bar = ("█" * $filledLength) + ("░" * ($barLength - $filledLength))
        
        # 根據完成度設定顏色
        $color = if ($percentage -eq 100) { "Green" } 
                 elseif ($percentage -ge 50) { "Yellow" } 
                 else { "Red" }
        
        Write-Host "$funcId " -NoNewline -ForegroundColor White
        Write-Host "[$bar]" -NoNewline -ForegroundColor $color
        Write-Host " $count/$target ($percentage%)" -ForegroundColor $color
    }
    
    Write-Host ""
    Write-Host "-" * 80
    Write-Host ""
    
    # 預估剩餘時間（假設每個任務平均 30 秒）
    $remaining = $totalTarget - $totalCount
    $estimatedSeconds = $remaining * 30
    $estimatedTime = [TimeSpan]::FromSeconds($estimatedSeconds)
    
    Write-Host "⏱️  預估剩餘時間: " -NoNewline -ForegroundColor White
    Write-Host "$($estimatedTime.Hours)h $($estimatedTime.Minutes)m" -ForegroundColor Yellow
    Write-Host ""
    
    # 最新生成的檔案
    $latestFiles = $allFiles | Sort-Object LastWriteTime -Descending | Select-Object -First 5
    if ($latestFiles) {
        Write-Host "📄 最新生成的 5 個檔案:" -ForegroundColor Cyan
        foreach ($file in $latestFiles) {
            $timeAgo = (Get-Date) - $file.LastWriteTime
            $size = [math]::Round($file.Length / 1KB, 1)
            Write-Host "   • $($file.Name) " -NoNewline -ForegroundColor Gray
            Write-Host "($size KB, $([math]::Round($timeAgo.TotalSeconds, 0))秒前)" -ForegroundColor DarkGray
        }
    }
    
    Write-Host ""
    Write-Host "=" * 80
    Write-Host "🔄 每 5 秒自動刷新 | 按 Ctrl+C 停止監控" -ForegroundColor DarkGray
    Write-Host "=" * 80
    
    Start-Sleep -Seconds 5
}
