# F74 排位賽預測數據批次重新生成腳本
# 日期: 2025-11-05

$races = @(
    "Bahrain",
    "Saudi Arabia",
    "Australia",
    "Japan",
    "China",
    "Miami",
    "Emilia Romagna",
    "Monaco",
    "Canada",
    "Spain",
    "Austria",
    "Great Britain",
    "Belgium",
    "Netherlands",
    "Italy",
    "Azerbaijan",
    "Singapore",
    "United States",
    "Mexico"
)

$year = 2025
$totalRaces = $races.Count
$successCount = 0
$failedRaces = @()

Write-Host "========================================"
Write-Host "F74 排位賽預測數據批次生成"
Write-Host "========================================"
Write-Host "年份: $year"
Write-Host "賽事數量: $totalRaces"
Write-Host ""

$index = 1
foreach ($race in $races) {
    Write-Host "[$index/$totalRaces] 處理: $race"
    
    try {
        python f1_analysis_modular_main.py -f 74 -y $year -r "$race"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  成功: $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  可能失敗: $race" -ForegroundColor Yellow
            $failedRaces += $race
        }
    } catch {
        Write-Host "  錯誤: $race" -ForegroundColor Red
        $failedRaces += $race
    }
    
    Start-Sleep -Milliseconds 500
    $index++
}

Write-Host ""
Write-Host "========================================"
Write-Host "執行摘要"
Write-Host "========================================"
Write-Host "總賽事數: $totalRaces"
Write-Host "成功生成: $successCount"
Write-Host "失敗數量: $($failedRaces.Count)"

if ($failedRaces.Count -gt 0) {
    Write-Host ""
    Write-Host "失敗的賽事:"
    foreach ($race in $failedRaces) {
        Write-Host "  - $race"
    }
}

Write-Host ""
Write-Host "批次生成完成！"
