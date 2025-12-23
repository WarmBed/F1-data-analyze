# 驗證所有 qualifying_prediction JSON 檔案的訓練指標

$files = Get-ChildItem "json" -Filter "qualifying_prediction_2025_*.json"
Write-Host "檢查 $($files.Count) 個 JSON 檔案的訓練指標...`n" -ForegroundColor Green

$hasIssue = $false
$results = @()

foreach ($file in $files) {
    $data = Get-Content $file.FullName -Raw | ConvertFrom-Json
    $meta = $data.metadata
    $raceName = $file.Name -replace 'qualifying_prediction_2025_|\.json', ''
    
    $result = [PSCustomObject]@{
        Race = $raceName
        R2 = [math]::Round($meta.model_r2, 4)
        MAE = [math]::Round($meta.model_mae, 3)
        SampleCount = $meta.sample_count
        HasActualResults = $meta.has_actual_results
    }
    
    $results += $result
    
    if ($meta.model_r2 -eq 0 -and $meta.model_mae -eq 0) {
        $hasIssue = $true
    }
}

# 顯示結果表格
$results | Sort-Object Race | Format-Table -AutoSize

if (-not $hasIssue) {
    Write-Host "✅ 所有 JSON 檔案都包含完整的訓練指標！" -ForegroundColor Green
    Write-Host "`n統計摘要:" -ForegroundColor Cyan
    $avgR2 = ($results | Measure-Object -Property R2 -Average).Average
    $avgMAE = ($results | Measure-Object -Property MAE -Average).Average
    Write-Host "  平均 R²: $([math]::Round($avgR2, 4))" -ForegroundColor White
    Write-Host "  平均 MAE: $([math]::Round($avgMAE, 3))s" -ForegroundColor White
    Write-Host "  有實際結果的賽事: $(($results | Where-Object HasActualResults -eq $true).Count)/$($results.Count)" -ForegroundColor White
} else {
    Write-Host "⚠️  部分檔案缺少訓練指標" -ForegroundColor Red
}
