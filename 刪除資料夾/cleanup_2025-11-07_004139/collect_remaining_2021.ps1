# 補齊 2021 年剩餘 6 場賽事
$remaining2021 = @("United States", "Mexico", "Brazil", "Qatar", "Saudi Arabia", "Abu Dhabi")

Write-Host "`n=== 補齊 2021 年剩餘賽事 ===" -ForegroundColor Cyan
Write-Host "共 $($remaining2021.Count) 場賽事`n" -ForegroundColor Yellow

$success = 0
$failed = 0

foreach ($race in $remaining2021) {
    Write-Host "`n[$(($success + $failed + 1))/$($remaining2021.Count)] 收集 2021 $race..." -ForegroundColor Green
    
    try {
        python f1_analysis_modular_main.py -f 70 -y 2021 -r $race
        
        if ($LASTEXITCODE -eq 0) {
            $success++
            Write-Host "✅ $race 完成" -ForegroundColor Green
        } else {
            $failed++
            Write-Host "❌ $race 失敗" -ForegroundColor Red
        }
    }
    catch {
        $failed++
        Write-Host "❌ $race 異常: $_" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 2
}

Write-Host "`n=== 2021 年補齊完成 ===" -ForegroundColor Cyan
Write-Host "成功: $success / 失敗: $failed" -ForegroundColor Yellow

# 自動繼續 2022-2024
if ($success -gt 0) {
    Write-Host "`n🚀 自動開始收集 2022-2024 年數據..." -ForegroundColor Green
    Start-Sleep -Seconds 3
    & ".\collect_2022_2024.ps1"
}
