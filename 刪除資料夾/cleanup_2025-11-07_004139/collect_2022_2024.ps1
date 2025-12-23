# 收集 2022-2024 年完整數據
$years = @(2022, 2023, 2024)

Write-Host "`n=== 收集 2022-2024 年數據 ===" -ForegroundColor Cyan

foreach ($year in $years) {
    Write-Host "`n### 處理 $year 年 ###" -ForegroundColor Yellow
    
    try {
        python f1_analysis_modular_main.py -f 70 --start-year $year --end-year $year
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ $year 年完成" -ForegroundColor Green
        } else {
            Write-Host "❌ $year 年失敗" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "❌ $year 年異常: $_" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 5
}

Write-Host "`n=== 2022-2024 年收集完成 ===" -ForegroundColor Cyan
