# 補齊 2018 年缺失的賽事數據
$missing2018 = @("Singapore", "Russia", "Japan", "United States", "Mexico", "Brazil", "Abu Dhabi")

Write-Host "`n=== 補齊 2018 年缺失數據 ===" -ForegroundColor Cyan
Write-Host "共 $($missing2018.Count) 場賽事`n" -ForegroundColor Yellow

$success = 0
$failed = 0

foreach ($race in $missing2018) {
    Write-Host "`n[$(($success + $failed + 1))/$($missing2018.Count)] 收集 2018 $race..." -ForegroundColor Green
    
    try {
        python f1_analysis_modular_main.py -f 70 -y 2018 -r $race
        
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

Write-Host "`n=== 2018 年補齊完成 ===" -ForegroundColor Cyan
Write-Host "成功: $success / 失敗: $failed" -ForegroundColor Yellow
