# 批次生成 2024 和 2025 年所有賽道的 track position JSON
$ErrorActionPreference = "Continue"

# 清理緩存
Write-Host "清理緩存..." -ForegroundColor Cyan
Get-ChildItem -Path cache -Filter "*track_position*.pkl" -ErrorAction SilentlyContinue | Remove-Item -Force
Get-ChildItem -Path json -Filter "*track_position*.json" | Where-Object { $_.Name -match "202[45]" } | Remove-Item -Force

# 賽道列表
$races2024 = @(
    "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
    "Miami", "Monaco", "Spain", "Canada", "Austria",
    "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
    "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
    "Las Vegas", "Qatar", "Abu Dhabi"
)

$races2025 = $races2024

$success = 0
$fail = 0

# 生成 2024
Write-Host "`n=== 2024 ===" -ForegroundColor Green
foreach ($race in $races2024) {
    Write-Host "處理: 2024 $race" -ForegroundColor Yellow
    python f1_analysis_modular_main.py -f 2 -y 2024 -r $race -s R 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $success++
        Write-Host "  成功" -ForegroundColor Green
    } else {
        $fail++
        Write-Host "  失敗" -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}

# 生成 2025
Write-Host "`n=== 2025 ===" -ForegroundColor Green
foreach ($race in $races2025) {
    Write-Host "處理: 2025 $race" -ForegroundColor Yellow
    python f1_analysis_modular_main.py -f 2 -y 2025 -r $race -s R 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $success++
        Write-Host "  成功" -ForegroundColor Green
    } else {
        $fail++
        Write-Host "  失敗" -ForegroundColor Red
    }
    Start-Sleep -Seconds 1
}

Write-Host "`n=== 完成 ===" -ForegroundColor Cyan
Write-Host "成功: $success" -ForegroundColor Green
Write-Host "失敗: $fail" -ForegroundColor Red
