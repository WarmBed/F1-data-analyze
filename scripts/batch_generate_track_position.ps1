# 批次生成 2024 和 2025 年所有賽道的 track position JSON
# 包含新增的 FastF1 官方彎道資訊

$ErrorActionPreference = "Continue"

# 2024 賽季賽道列表
$races2024 = @(
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
    "Las Vegas", "Qatar", "Abu Dhabi"
)

# 2025 賽季賽道列表（目前已有的）
$races2025 = @(
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
    "Las Vegas", "Qatar", "Abu Dhabi"
)

$successCount = 0
$failCount = 0
$totalRaces = $races2024.Count + $races2025.Count

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  批次生成 Track Position JSON" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "總計: $totalRaces 場比賽`n" -ForegroundColor Yellow

# 生成 2024 年
Write-Host "`n=== 2024 賽季 ===" -ForegroundColor Green
foreach ($race in $races2024) {
    Write-Host "`n[$($successCount + $failCount + 1)/$totalRaces] 處理中: 2024 $race..." -ForegroundColor Yellow
    
    try {
        $output = python f1_analysis_modular_main.py -f 2 -y 2024 -r $race -s R 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [✓] 成功: 2024 $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  [✗] 失敗: 2024 $race (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [✗] 錯誤: 2024 $race - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 2  # 避免 API 請求過快
}

# 生成 2025 年
Write-Host "`n=== 2025 賽季 ===" -ForegroundColor Green
foreach ($race in $races2025) {
    Write-Host "`n[$($successCount + $failCount + 1)/$totalRaces] 處理中: 2025 $race..." -ForegroundColor Yellow
    
    try {
        $output = python f1_analysis_modular_main.py -f 2 -y 2025 -r $race -s R 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [✓] 成功: 2025 $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  [✗] 失敗: 2025 $race (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [✗] 錯誤: 2025 $race - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 2  # 避免 API 請求過快
}

# 總結
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  批次生成完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "成功: $successCount / $totalRaces" -ForegroundColor Green
Write-Host "失敗: $failCount / $totalRaces" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

# 列出生成的檔案
Write-Host "`n生成的 JSON 檔案:" -ForegroundColor Yellow
Get-ChildItem -Path json -Filter "*track_position_analysis_202*.json" | 
    Sort-Object Name | 
    ForEach-Object { 
        Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" 
    }

Write-Host "`n完成!" -ForegroundColor Green
