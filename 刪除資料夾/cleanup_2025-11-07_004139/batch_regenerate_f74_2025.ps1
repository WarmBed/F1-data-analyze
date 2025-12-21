# ========================================
# F74 排位賽預測數據批次重新生成腳本
# ========================================
# 日期: 2025-11-05
# 功能: 重新生成所有 2025 賽季的 F74 排位賽預測數據
# ========================================

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

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🏎️  F74 排位賽預測數據批次生成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "年份: $year" -ForegroundColor Yellow
Write-Host "賽事數量: $totalRaces" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

foreach ($race in $races) {
    $currentIndex = $races.IndexOf($race) + 1
    
    Write-Host "[$currentIndex/$totalRaces] 🏁 處理: $race" -ForegroundColor White
    Write-Host "執行命令: python f1_analysis_modular_main.py -f 74 -y $year -r `"$race`"`n" -ForegroundColor Gray
    
    try {
        # 執行 CLI 命令
        $output = python f1_analysis_modular_main.py -f 74 -y $year -r "$race" 2>&1
        
        # 檢查輸出中是否有成功訊息
        $outputString = $output -join "`n"
        
        if ($LASTEXITCODE -eq 0 -or $outputString -match "成功|Success|已儲存|saved") {
            Write-Host "  ✅ 成功生成: $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  ⚠️  可能失敗: $race (請檢查日誌)" -ForegroundColor Yellow
            $failedRaces += $race
        }
        
        # 短暫延遲避免 API 限制
        Start-Sleep -Milliseconds 500
        
    } catch {
        Write-Host "  ❌ 執行錯誤: $race" -ForegroundColor Red
        Write-Host "     錯誤訊息: $_" -ForegroundColor Red
        $failedRaces += $race
    }
    
    Write-Host "" # 空行分隔
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 執行摘要" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "總賽事數: $totalRaces" -ForegroundColor White
Write-Host "成功生成: $successCount" -ForegroundColor Green
Write-Host "失敗/警告: $($failedRaces.Count)" -ForegroundColor $(if ($failedRaces.Count -eq 0) { "Green" } else { "Yellow" })

if ($failedRaces.Count -gt 0) {
    Write-Host "`n失敗的賽事列表:" -ForegroundColor Yellow
    foreach ($race in $failedRaces) {
        Write-Host "  - $race" -ForegroundColor Yellow
    }
}

Write-Host "`n✅ 批次生成完成！" -ForegroundColor Green
Write-Host "備份位置: json\backup_f74_20251105_215459" -ForegroundColor Cyan
Write-Host "新檔案位置: json\qualifying_prediction_*.json" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan
