# 清理賽道特徵收集相關的 JSON 檔案
# 用途：刪除 Function 48, 54, 34, 17, 1 生成的 JSON，準備重新收集

Write-Host "🧹 開始清理賽道特徵相關的 JSON 檔案..." -ForegroundColor Cyan
Write-Host "=" * 60

# 定義要刪除的 JSON 檔案模式
$patterns = @(
    "*all_drivers_straight_line_speed*.json",  # Function 48
    "*driver_throttle_ratio*.json",            # Function 54
    "*brake_performance*.json",                # Function 34
    "*dynamic_corner*.json",                   # Function 17
    "*corner_detection*.json",                 # Function 17
    "*rain_intensity*.json",                   # Function 1
    "*enhanced_rain*.json"                     # Function 1
)

$totalDeleted = 0

foreach ($pattern in $patterns) {
    Write-Host "`n🔍 搜索模式: $pattern" -ForegroundColor Yellow
    
    $files = Get-ChildItem json -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    
    if ($files) {
        $count = $files.Count
        Write-Host "   找到 $count 個檔案" -ForegroundColor Green
        
        foreach ($file in $files) {
            Write-Host "   刪除: $($file.Name)" -ForegroundColor Gray
            Remove-Item $file.FullName -Force
            $totalDeleted++
        }
    } else {
        Write-Host "   未找到檔案" -ForegroundColor DarkGray
    }
}

Write-Host "`n" + ("=" * 60)
Write-Host "✅ 清理完成！共刪除 $totalDeleted 個 JSON 檔案" -ForegroundColor Green
Write-Host ""

# 確認操作
Read-Host "按 Enter 鍵繼續..."
