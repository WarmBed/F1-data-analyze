# 簡單的批量生成進度監控
# 每 10 秒顯示一次進度

while ($true) {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "       批量生成賽道特徵 JSON - 即時進度監控" -ForegroundColor Cyan  
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[更新時間] $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""
    
    # 檢查資料夾
    if (Test-Path "json\trackFeaturesJSON") {
        $files = Get-ChildItem "json\trackFeaturesJSON" -Filter "*.json"
        $totalCount = $files.Count
        $targetCount = 745
        $percentage = [math]::Round($totalCount / $targetCount * 100, 1)
        
        # 顯示總進度
        Write-Host "【總進度】" -ForegroundColor Yellow
        Write-Host "  已生成: $totalCount / $targetCount 檔案" -ForegroundColor White
        Write-Host "  完成度: $percentage%" -ForegroundColor $(if ($percentage -ge 80) { "Green" } elseif ($percentage -ge 50) { "Yellow" } else { "Red" })
        Write-Host ""
        
        # 統計各功能
        Write-Host "【各功能統計】" -ForegroundColor Yellow
        
        $f48 = ($files | Where-Object { $_.Name -like "*straight_line_speed*" }).Count
        $f54 = ($files | Where-Object { $_.Name -like "*throttle_ratio*" }).Count
        $f34 = ($files | Where-Object { $_.Name -like "*brake_performance*" }).Count
        $f47 = ($files | Where-Object { $_.Name -like "*cornering_analysis*" }).Count
        $f1 = ($files | Where-Object { $_.Name -like "*rain_analysis*" }).Count
        
        Write-Host "  F48 (直線速度):  $f48 / 149" -ForegroundColor Cyan
        Write-Host "  F54 (油門比例):  $f54 / 149" -ForegroundColor Cyan
        Write-Host "  F34 (煞車性能):  $f34 / 149" -ForegroundColor Cyan
        Write-Host "  F47 (彎道分析):  $f47 / 149" -ForegroundColor Cyan
        Write-Host "  F1  (天氣數據):  $f1 / 149" -ForegroundColor Cyan
        Write-Host ""
        
        # 預估剩餘時間
        $remaining = $targetCount - $totalCount
        $avgTimePerTask = 30  # 秒
        $estimatedSeconds = $remaining * $avgTimePerTask
        $estimatedHours = [math]::Floor($estimatedSeconds / 3600)
        $estimatedMinutes = [math]::Floor(($estimatedSeconds % 3600) / 60)
        
        Write-Host "【預估剩餘時間】" -ForegroundColor Yellow
        Write-Host "  約 $estimatedHours 小時 $estimatedMinutes 分鐘" -ForegroundColor White
        Write-Host ""
        
        # 最新生成的檔案
        $latestFiles = $files | Sort-Object LastWriteTime -Descending | Select-Object -First 5
        if ($latestFiles) {
            Write-Host "【最新生成】" -ForegroundColor Green
            foreach ($file in $latestFiles) {
                $ageSeconds = ((Get-Date) - $file.LastWriteTime).TotalSeconds
                $sizeKB = [math]::Round($file.Length / 1KB, 1)
                Write-Host "  $($file.Name)" -ForegroundColor Gray
                Write-Host "    ($sizeKB KB, $([math]::Round($ageSeconds, 0)) 秒前)" -ForegroundColor DarkGray
            }
        }
        
    } else {
        Write-Host "資料夾 json\trackFeaturesJSON 尚未創建" -ForegroundColor Red
        Write-Host "批量腳本可能尚未開始執行..." -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host "按 Ctrl+C 停止監控 | 每 10 秒自動刷新" -ForegroundColor DarkGray
    Write-Host "============================================================" -ForegroundColor Cyan
    
    Start-Sleep -Seconds 10
}
