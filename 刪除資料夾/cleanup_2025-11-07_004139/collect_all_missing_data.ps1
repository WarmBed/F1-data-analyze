# F1T 功能 70 - 完整數據補齊腳本
# 2025-10-30
# 目標: 補齊 2018-2024 所有缺失的 FP→Q 訓練數據

Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "F1T 功能 70 - FP→Q 訓練數據完整補齊" -ForegroundColor Cyan
Write-Host ("="*80) + "`n" -ForegroundColor Cyan

Write-Host "📊 當前狀態:" -ForegroundColor Yellow
Write-Host "  2018: 已有 14/21 場，缺 7 場" -ForegroundColor White
Write-Host "  2019: 已有 12/21 場，缺 9 場" -ForegroundColor White
Write-Host "  2021: 已有 12/22 場，缺 10 場" -ForegroundColor White
Write-Host "  2022: 已有 0/22 場，缺 22 場" -ForegroundColor White
Write-Host "  2023: 已有 0/23 場，缺 23 場" -ForegroundColor White
Write-Host "  2024: 已有 1/24 場，缺 23 場`n" -ForegroundColor White

Write-Host "🎯 補齊計畫: 共 74 場賽事`n" -ForegroundColor Yellow

$startTime = Get-Date

# ===== 階段 1: 補齊 2018 年 (7 場) =====
Write-Host "`n[階段 1/5] 補齊 2018 年缺失數據..." -ForegroundColor Green
& ".\collect_missing_2018.ps1"
Start-Sleep -Seconds 5

# ===== 階段 2: 補齊 2019 年 (9 場) =====
Write-Host "`n[階段 2/5] 補齊 2019 年缺失數據..." -ForegroundColor Green
& ".\collect_missing_2019.ps1"
Start-Sleep -Seconds 5

# ===== 階段 3: 補齊 2021 年 (10 場) =====
Write-Host "`n[階段 3/5] 補齊 2021 年缺失數據..." -ForegroundColor Green
& ".\collect_missing_2021.ps1"
Start-Sleep -Seconds 5

# ===== 階段 4: 收集 2022-2024 年 (67 場) =====
Write-Host "`n[階段 4/5] 收集 2022-2024 年完整數據..." -ForegroundColor Green
& ".\collect_2022_2024.ps1"

# ===== 階段 5: 驗證結果 =====
Write-Host "`n[階段 5/5] 驗證收集結果..." -ForegroundColor Green

$jsonFiles = Get-ChildItem "json\predictionJSON" -Filter "*.json"
$totalFiles = $jsonFiles.Count

Write-Host "`n" + ("="*80) -ForegroundColor Cyan
Write-Host "✅ 數據收集完成！" -ForegroundColor Green
Write-Host ("="*80) -ForegroundColor Cyan

Write-Host "`n📊 最終統計:" -ForegroundColor Yellow
Write-Host "  JSON 檔案總數: $totalFiles" -ForegroundColor White
Write-Host "  預期總數: ~150 場 (2018-2024)" -ForegroundColor White
Write-Host "  完成度: $(([math]::Round($totalFiles / 150 * 100, 1)))%" -ForegroundColor White

$endTime = Get-Date
$duration = $endTime - $startTime
Write-Host "`n⏱️  總耗時: $($duration.Hours)h $($duration.Minutes)m $($duration.Seconds)s" -ForegroundColor Yellow

Write-Host "`n📁 數據位置: json\predictionJSON\" -ForegroundColor White
Write-Host "`n🎯 下一步: 執行功能 72 (XGBoost 訓練)" -ForegroundColor Cyan
