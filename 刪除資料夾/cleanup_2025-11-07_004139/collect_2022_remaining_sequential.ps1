# 2022 年剩餘賽事逐場收集（順序執行版）
$remaining2022 = @(
    "Canada",
    "Great Britain",
    "Austria",
    "France",
    "Hungary",
    "Belgium",
    "Netherlands",
    "Italy",
    "Singapore",
    "Japan",
    "United States",
    "Mexico",
    "Brazil",
    "Abu Dhabi"
)

Write-Host "`n=== 2022 年剩餘賽事收集 (14 場) ===" -ForegroundColor Cyan
Write-Host "開始時間: $(Get-Date -Format 'HH:mm:ss')`n" -ForegroundColor Gray

$startTime = Get-Date
$completed = 0
$failed = 0
$skipped = 0

foreach ($race in $remaining2022) {
    $index = $remaining2022.IndexOf($race) + 1
    
    # 檢查檔案是否已存在
    $existingFiles = Get-ChildItem "json\predictionJSON" -Filter "fp_q_data_2022_${race}_*.json" -ErrorAction SilentlyContinue
    
    if ($existingFiles) {
        Write-Host "[$index/14] ⏭️  跳過: 2022 $race (已存在)" -ForegroundColor Gray
        $skipped++
        continue
    }
    
    Write-Host "[$index/14] 🔄 正在收集: 2022 $race" -ForegroundColor Yellow
    
    try {
        # 執行收集
        $process = Start-Process -FilePath "python" `
            -ArgumentList "f1_analysis_modular_main.py", "-f", "70", "-y", "2022", "-r", $race `
            -NoNewWindow -PassThru -Wait
        
        if ($process.ExitCode -eq 0) {
            Write-Host "  ✅ 成功" -ForegroundColor Green
            $completed++
        }
        else {
            Write-Host "  ❌ 失敗 (Exit Code: $($process.ExitCode))" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ 異常: $_" -ForegroundColor Red
        $failed++
    }
    
    # 進度統計
    $elapsed = (Get-Date) - $startTime
    $avgTime = if ($completed -gt 0) { $elapsed.TotalMinutes / $completed } else { 0 }
    $remaining = 14 - $index
    $eta = if ($avgTime -gt 0) { [math]::Round($avgTime * $remaining, 1) } else { 0 }
    
    Write-Host "  📊 進度: $completed 成功 | $failed 失敗 | $skipped 跳過 | ETA: ${eta} 分鐘`n" -ForegroundColor Gray
}

$totalTime = ((Get-Date) - $startTime).TotalMinutes
Write-Host "`n=== 收集完成 ===" -ForegroundColor Cyan
Write-Host "結束時間: $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Gray
Write-Host "總耗時: $([math]::Round($totalTime, 1)) 分鐘" -ForegroundColor Gray
Write-Host "成功: $completed 場" -ForegroundColor Green
Write-Host "失敗: $failed 場" -ForegroundColor Red
Write-Host "跳過: $skipped 場" -ForegroundColor Gray

# 最終驗證
$total2022 = (Get-ChildItem "json\predictionJSON" -Filter "fp_q_data_2022_*.json").Count
$percentage = [math]::Round($total2022/22*100,1)
Write-Host "`n🏁 2022 年最終進度: $total2022/22 ($percentage%)" -ForegroundColor Cyan
