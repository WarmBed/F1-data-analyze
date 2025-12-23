# 補齊 2022 年缺失的 15 場賽事
$missing2022 = @(
    "Azerbaijan",
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

Write-Host "`n=== 補齊 2022 年缺失賽事 (15 場) ===" -ForegroundColor Cyan
Write-Host "開始時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor Gray

$completed = 0
$failed = 0

foreach ($race in $missing2022) {
    $index = $missing2022.IndexOf($race) + 1
    Write-Host "[$index/15] 正在收集: 2022 $race" -ForegroundColor Yellow
    
    try {
        $output = python f1_analysis_modular_main.py -f 70 -y 2022 -r $race 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✅ 成功" -ForegroundColor Green
            $completed++
        }
        else {
            Write-Host "  ❌ 失敗 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "  錯誤: $($output | Select-Object -Last 3)" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  ❌ 異常: $_" -ForegroundColor Red
        $failed++
    }
    
    # 顯示進度
    $progress = [math]::Round(($index / 15) * 100, 1)
    Write-Host "  進度: $completed 成功, $failed 失敗 ($progress%)`n" -ForegroundColor Gray
    
    # 避免 API 請求過快
    Start-Sleep -Seconds 2
}

Write-Host "`n=== 2022 年補齊完成 ===" -ForegroundColor Cyan
Write-Host "結束時間: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host "成功: $completed 場" -ForegroundColor Green
Write-Host "失敗: $failed 場" -ForegroundColor Red

if ($completed -eq 15) {
    Write-Host "`n🎉 2022 年數據收集 100% 完成！" -ForegroundColor Green
}
elseif ($completed -gt 0) {
    Write-Host "`n⚠️  部分完成，建議重新執行腳本補齊失敗項目" -ForegroundColor Yellow
}
