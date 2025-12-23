# ============================================================
# F47 測試腳本 - 單一賽事測試
# ============================================================
# 測試 CLI Function 47 是否正常運作
# 測試賽事：2025 Japan Q (排位賽)
# ============================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  F47 全車手彎道分析 - 單一賽事測試" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 測試參數
$year = 2025
$race = "Japan"
$session = "Q"

Write-Host "測試配置：" -ForegroundColor Green
Write-Host "  - 年份：$year" -ForegroundColor White
Write-Host "  - 賽事：$race" -ForegroundColor White
Write-Host "  - 會話：$session" -ForegroundColor White
Write-Host "  - 功能：F47 (全車手彎道速度分析)" -ForegroundColor White
Write-Host ""

# 檢查 JSON 是否已存在
$jsonPattern = "json\all_drivers_cornering_analysis_${year}_${race}_${session}_*.json"
$existingJson = Get-ChildItem -Path $jsonPattern -ErrorAction SilentlyContinue

if ($existingJson) {
    Write-Host "發現已存在的 JSON 檔案：" -ForegroundColor Yellow
    foreach ($file in $existingJson) {
        $size = [math]::Round($file.Length / 1KB, 1)
        Write-Host "  - $($file.Name) ($size KB, 修改時間: $($file.LastWriteTime))" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "是否要重新生成？(Y/N)" -ForegroundColor Yellow
    $response = Read-Host
    
    if ($response -ne "Y" -and $response -ne "y") {
        Write-Host "測試取消" -ForegroundColor DarkGray
        exit 0
    }
}

Write-Host "開始執行 CLI F47..." -ForegroundColor Green
Write-Host ""

# 執行命令
$command = "python f1_analysis_modular_main.py -f 47 -y $year -r `"$race`" -s $session"
Write-Host "執行命令：$command" -ForegroundColor Cyan
Write-Host ("-" * 70) -ForegroundColor Gray

$startTime = Get-Date

try {
    # 執行並捕獲輸出
    python f1_analysis_modular_main.py -f 47 -y $year -r "$race" -s $session
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    
    Write-Host ""
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "執行成功！" -ForegroundColor Green
        Write-Host "執行時間：$($duration.ToString('mm\:ss\.fff'))" -ForegroundColor White
        
        # 檢查生成的 JSON
        $newJson = Get-ChildItem -Path $jsonPattern -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        
        if ($newJson) {
            Write-Host ""
            Write-Host "生成的 JSON 檔案：" -ForegroundColor Green
            $size = [math]::Round($newJson.Length / 1KB, 1)
            Write-Host "  - 檔名：$($newJson.Name)" -ForegroundColor White
            Write-Host "  - 大小：$size KB" -ForegroundColor White
            Write-Host "  - 時間：$($newJson.LastWriteTime)" -ForegroundColor White
            
            # 讀取並顯示 JSON 結構
            Write-Host ""
            Write-Host "JSON 內容預覽：" -ForegroundColor Green
            $jsonContent = Get-Content $newJson.FullName -Raw | ConvertFrom-Json
            
            if ($jsonContent.success) {
                Write-Host "  - 成功：$($jsonContent.success)" -ForegroundColor Green
                Write-Host "  - 訊息：$($jsonContent.message)" -ForegroundColor White
                
                if ($jsonContent.data) {
                    Write-Host "  - 數據區塊：" -ForegroundColor Cyan
                    
                    if ($jsonContent.data.selected_corners) {
                        $corners = $jsonContent.data.selected_corners
                        Write-Host "    └─ 選擇的彎道：" -ForegroundColor White
                        $lowSpeed = "$($corners.low_speed.corner_number) ($($corners.low_speed.avg_speed) km/h)"
                        $mediumSpeed = "$($corners.medium_speed.corner_number) ($($corners.medium_speed.avg_speed) km/h)"
                        $highSpeed = "$($corners.high_speed.corner_number) ($($corners.high_speed.avg_speed) km/h)"
                        Write-Host "       低速彎：$lowSpeed" -ForegroundColor DarkGray
                        Write-Host "       中速彎：$mediumSpeed" -ForegroundColor DarkGray
                        Write-Host "       高速彎：$highSpeed" -ForegroundColor DarkGray
                    }
                    
                    if ($jsonContent.data.fastest_lap_analysis) {
                        $fastest = $jsonContent.data.fastest_lap_analysis
                        Write-Host "    └─ 最速圈分析：" -ForegroundColor White
                        
                        if ($fastest.low_speed) {
                            $driverCount = $fastest.low_speed.Count
                            Write-Host "       • 低速彎數據：$driverCount 位車手" -ForegroundColor DarkGray
                        }
                    }
                }
            } else {
                Write-Host "  - 成功：$($jsonContent.success)" -ForegroundColor Red
                Write-Host "  - 錯誤訊息：$($jsonContent.message)" -ForegroundColor Red
            }
        } else {
            Write-Host ""
            Write-Host "警告：未找到生成的 JSON 檔案" -ForegroundColor Yellow
        }
    } else {
        Write-Host "執行失敗！" -ForegroundColor Red
        Write-Host "返回碼：$LASTEXITCODE" -ForegroundColor Red
    }
} catch {
    Write-Host ""
    Write-Host "異常錯誤：" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor DarkRed
}

Write-Host ""
Write-Host "測試完成！" -ForegroundColor Yellow
