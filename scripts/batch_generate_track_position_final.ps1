# 批次生成 2024 和 2025 年所有賽道的 track position JSON
# 包含新增的 FastF1 官方彎道資訊
# 刪除緩存確保使用最新代碼

$ErrorActionPreference = "Continue"

# 步驟 0: 清理緩存和 JSON
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  清理舊檔案" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 刪除緩存
$cacheFiles = Get-ChildItem -Path cache -Filter "*track_position*.pkl" -ErrorAction SilentlyContinue
if ($cacheFiles) {
    $cacheFiles | Remove-Item -Force
    Write-Host "已刪除 $($cacheFiles.Count) 個緩存檔案" -ForegroundColor Green
} else {
    Write-Host "無需刪除緩存" -ForegroundColor Gray
}

# 刪除舊 JSON
$jsonFiles = Get-ChildItem -Path json -Filter "*track_position*.json" | Where-Object { $_.Name -match "202[45]" }
if ($jsonFiles) {
    $jsonFiles | Remove-Item -Force
    Write-Host "已刪除 $($jsonFiles.Count) 個 JSON 檔案" -ForegroundColor Green
} else {
    Write-Host "無需刪除 JSON" -ForegroundColor Gray
}

Write-Host ""

# 2024 賽季賽道列表
$races2024 = @(
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
    "Las Vegas", "Qatar", "Abu Dhabi"
)

# 2025 賽季賽道列表
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
        python f1_analysis_modular_main.py -f 2 -y 2024 -r $race -s R 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            # 驗證 JSON 是否包含 official_corners
            $jsonFile = Get-ChildItem -Path json -Filter "*track_position_analysis_2024*$race*.json" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($jsonFile) {
                $content = Get-Content $jsonFile.FullName -Raw | ConvertFrom-Json
                $hasCorners = $null -ne $content.data.official_corners
                $cornerCount = if ($hasCorners) { $content.data.official_corners.count } else { 0 }
                
                Write-Host "  [OK] 成功: 2024 $race (彎道: $cornerCount 個)" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  [WARN] 成功但未找到 JSON: 2024 $race" -ForegroundColor Yellow
                $successCount++
            }
        } else {
            Write-Host "  [FAIL] 失敗: 2024 $race (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [ERROR] 錯誤: 2024 $race - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 1
}

# 生成 2025 年
Write-Host "`n=== 2025 賽季 ===" -ForegroundColor Green
foreach ($race in $races2025) {
    Write-Host "`n[$($successCount + $failCount + 1)/$totalRaces] 處理中: 2025 $race..." -ForegroundColor Yellow
    
    try {
        python f1_analysis_modular_main.py -f 2 -y 2025 -r $race -s R 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            # 驗證 JSON 是否包含 official_corners
            $jsonFile = Get-ChildItem -Path json -Filter "*track_position_analysis_2025*$race*.json" -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($jsonFile) {
                $content = Get-Content $jsonFile.FullName -Raw | ConvertFrom-Json
                $hasCorners = $null -ne $content.data.official_corners
                $cornerCount = if ($hasCorners) { $content.data.official_corners.count } else { 0 }
                
                Write-Host "  [OK] 成功: 2025 $race (彎道: $cornerCount 個)" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  [WARN] 成功但未找到 JSON: 2025 $race" -ForegroundColor Yellow
                $successCount++
            }
        } else {
            Write-Host "  [FAIL] 失敗: 2025 $race (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
            $failCount++
        }
    } catch {
        Write-Host "  [ERROR] 錯誤: 2025 $race - $($_.Exception.Message)" -ForegroundColor Red
        $failCount++
    }
    
    Start-Sleep -Seconds 1
}

# 總結
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  批次生成完成" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "成功: $successCount / $totalRaces" -ForegroundColor Green
Write-Host "失敗: $failCount / $totalRaces" -ForegroundColor $(if ($failCount -eq 0) { "Green" } else { "Red" })

# 驗證 official_corners
Write-Host "`n=== 驗證 official_corners 欄位 ===" -ForegroundColor Yellow
$jsonFiles = Get-ChildItem -Path json -Filter "*track_position_analysis_202*.json"
$withCorners = 0
$withoutCorners = 0

foreach ($file in $jsonFiles) {
    $content = Get-Content $file.FullName -Raw | ConvertFrom-Json
    if ($null -ne $content.data.official_corners) {
        $withCorners++
    } else {
        $withoutCorners++
        Write-Host "  [MISSING] $($file.Name)" -ForegroundColor Red
    }
}

Write-Host "包含 official_corners: $withCorners" -ForegroundColor Green
Write-Host "缺少 official_corners: $withoutCorners" -ForegroundColor $(if ($withoutCorners -eq 0) { "Green" } else { "Red" })

Write-Host "`n完成!" -ForegroundColor Green
