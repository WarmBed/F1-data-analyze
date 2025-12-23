# 批次生成 2024 和 2025 年所有賽道的 track position JSON
# 直接使用 CLI，不通過 API

$ErrorActionPreference = "Continue"

# 2024 賽季賽道
$races2024 = @(
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
    "Las Vegas", "Qatar", "Abu Dhabi"
)

# 2025 賽季賽道
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

Write-Host "========================================"
Write-Host "  Batch Generate Track Position JSON"
Write-Host "========================================"
Write-Host "Total: $totalRaces races`n"

# 生成 2024 年
Write-Host "`n=== 2024 Season ==="
foreach ($race in $races2024) {
    $current = $successCount + $failCount + 1
    Write-Host "`n[$current/$totalRaces] Processing: 2024 $race..."
    
    try {
        # 直接執行 CLI
        python f1_analysis_modular_main.py -f 2 -y 2024 -r $race -s R 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Success: 2024 $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  [FAIL] Failed: 2024 $race" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [ERROR] 2024 $race" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 1
}

# 生成 2025 年
Write-Host "`n=== 2025 Season ==="
foreach ($race in $races2025) {
    $current = $successCount + $failCount + 1
    Write-Host "`n[$current/$totalRaces] Processing: 2025 $race..."
    
    try {
        # 直接執行 CLI
        python f1_analysis_modular_main.py -f 2 -y 2025 -r $race -s R 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  [OK] Success: 2025 $race" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "  [FAIL] Failed: 2025 $race" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [ERROR] 2025 $race" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 1
}

# 總結
Write-Host "`n========================================"
Write-Host "  Batch Generation Complete"
Write-Host "========================================"
Write-Host "Success: $successCount / $totalRaces" -ForegroundColor Green
Write-Host "Failed: $failCount / $totalRaces" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

# 列出生成的檔案
Write-Host "`nGenerated JSON files:"
Get-ChildItem -Path json -Filter "*track_position_analysis_202*.json" | 
    Sort-Object Name | 
    ForEach-Object { 
        Write-Host "  - $($_.Name) ($([math]::Round($_.Length/1KB, 2)) KB)" 
    }

Write-Host "`nDone!"
