# ========================================
# 批次生成 2025 賽季所有賽事的排位賽預測
# 功能: 執行 F74 為所有賽道生成 qualifying_prediction JSON
# ========================================

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "批次生成 F74 排位賽預測 - 2025 賽季" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 2025 賽季所有賽事列表（按賽曆順序）
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
    "Mexico",
    "Brazil",
    "Las Vegas",
    "Qatar",
    "Abu Dhabi"
)

$year = 2025
$successCount = 0
$failCount = 0
$totalRaces = $races.Count

Write-Host "📋 總賽事數: $totalRaces" -ForegroundColor Yellow
Write-Host "🎯 目標年份: $year" -ForegroundColor Yellow
Write-Host ""

foreach ($race in $races) {
    $index = $races.IndexOf($race) + 1
    
    Write-Host "[$index/$totalRaces] 🏁 處理: $race" -ForegroundColor Cyan
    Write-Host "   執行命令: python f1_analysis_modular_main.py -f 74 -y $year -r `"$race`"" -ForegroundColor Gray
    
    try {
        # 執行 F74
        $output = python f1_analysis_modular_main.py -f 74 -y $year -r "$race" 2>&1
        
        # 檢查輸出中是否有成功標記
        if ($output -match "JSON 檔案已保存" -or $output -match "✅") {
            Write-Host "   ✅ 成功: $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "   ⚠️  警告: $race (可能無數據)" -ForegroundColor Yellow
            $failCount++
        }
        
        # 檢查生成的 JSON 檔案
        $jsonFile = "json\qualifying_prediction_${year}_${race}.json"
        if (Test-Path $jsonFile) {
            $fileInfo = Get-Item $jsonFile
            Write-Host "   📄 檔案: $jsonFile ($($fileInfo.Length) bytes)" -ForegroundColor Gray
        }
        
    } catch {
        Write-Host "   ❌ 錯誤: $race - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Write-Host ""
    
    # 每 5 個賽事後暫停 2 秒，避免過度負載
    if ($index % 5 -eq 0) {
        Write-Host "⏸️  暫停 2 秒..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "批次生成完成！" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "✅ 成功: $successCount 個賽事" -ForegroundColor Green
Write-Host "❌ 失敗: $failCount 個賽事" -ForegroundColor Red
Write-Host "📊 總計: $totalRaces 個賽事" -ForegroundColor Yellow
Write-Host ""

# 列出所有生成的 JSON 檔案
Write-Host "📂 生成的 JSON 檔案:" -ForegroundColor Cyan
Get-ChildItem "json\qualifying_prediction_2025_*.json" | 
    Sort-Object LastWriteTime -Descending | 
    Select-Object Name, LastWriteTime, @{Name="Size(KB)";Expression={[math]::Round($_.Length/1KB, 2)}} |
    Format-Table -AutoSize

Write-Host ""
Write-Host "💡 提示: 請在 GUI 中重新載入 Qualifying Prediction 模組以查看更新後的數據" -ForegroundColor Yellow
