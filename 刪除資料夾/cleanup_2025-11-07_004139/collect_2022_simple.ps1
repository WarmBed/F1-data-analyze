# 2022 年剩餘賽事逐場收集
$remaining2022 = @(
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

Write-Host "`n=== 2022 年剩餘賽事收集 (13 場) ===" -ForegroundColor Cyan
$startTime = Get-Date
$completed = 0
$failed = 0

foreach ($race in $remaining2022) {
    $index = $remaining2022.IndexOf($race) + 1
    Write-Host "`n[$index/13] 正在收集: 2022 $race" -ForegroundColor Yellow
    
    try {
        python f1_analysis_modular_main.py -f 70 -y 2022 -r $race
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  成功" -ForegroundColor Green
            $completed++
        }
        else {
            Write-Host "  失敗 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            $failed++
        }
    }
    catch {
        Write-Host "  異常: $_" -ForegroundColor Red
        $failed++
    }
    
    $elapsed = (Get-Date) - $startTime
    $avgMin = if ($completed -gt 0) { $elapsed.TotalMinutes / $completed } else { 2 }
    $etaMin = [math]::Round($avgMin * (13 - $index), 1)
    Write-Host "  進度: $completed/$index | 失敗: $failed | ETA: $etaMin 分鐘" -ForegroundColor Gray
}

$totalMin = [math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)
Write-Host "`n=== 收集完成 ===" -ForegroundColor Cyan
Write-Host "總耗時: $totalMin 分鐘" -ForegroundColor Gray
Write-Host "成功: $completed 場 | 失敗: $failed 場" -ForegroundColor Gray

$total2022 = (Get-ChildItem "json\predictionJSON" -Filter "fp_q_data_2022_*.json").Count
Write-Host "`n2022 年最終進度: $total2022/22" -ForegroundColor Cyan
