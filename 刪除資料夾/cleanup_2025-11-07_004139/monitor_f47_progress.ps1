# F47 執行進度監控腳本
# 用途：實時監控 Function 47 的執行進度

$logFile = "logs\f1_cli_2025-10-26.log"

Write-Host "====================================" -ForegroundColor Cyan
Write-Host "  F47 彎道分析進度監控器" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "監控日誌檔案: $logFile" -ForegroundColor Yellow
Write-Host "按 Ctrl+C 停止監控" -ForegroundColor Gray
Write-Host ""

# 檢查日誌檔案是否存在
if (-not (Test-Path $logFile)) {
    Write-Host "[錯誤] 找不到日誌檔案: $logFile" -ForegroundColor Red
    Write-Host "請先執行 F47 分析任務" -ForegroundColor Yellow
    exit 1
}

# 顯示最近的關鍵信息
Write-Host "[初始狀態] 最近 20 筆關鍵記錄:" -ForegroundColor Green
Get-Content $logFile -Tail 100 | Select-String -Pattern "STEP|PROGRESS|INFO" | Select-Object -Last 20 | ForEach-Object {
    Write-Host $_.Line -ForegroundColor White
}

Write-Host ""
Write-Host "-----------------------------------" -ForegroundColor Gray
Write-Host "[實時監控] 等待新的進度更新..." -ForegroundColor Yellow
Write-Host ""

# 實時監控循環
$lastSize = (Get-Item $logFile).Length

while ($true) {
    Start-Sleep -Seconds 2
    
    $currentSize = (Get-Item $logFile).Length
    
    if ($currentSize -gt $lastSize) {
        # 讀取新增的內容
        $newContent = Get-Content $logFile -Tail 30 | Select-String -Pattern "STEP|PROGRESS|INFO|ERROR|SUCCESS"
        
        if ($newContent) {
            foreach ($line in $newContent) {
                $lineText = $line.Line
                
                # 簡單輸出，不做複雜的條件判斷
                if ($lineText -match "ERROR") {
                    Write-Host $lineText -ForegroundColor Red
                } elseif ($lineText -match "SUCCESS") {
                    Write-Host $lineText -ForegroundColor Green
                } elseif ($lineText -match "PROGRESS") {
                    Write-Host $lineText -ForegroundColor Cyan
                } else {
                    Write-Host $lineText -ForegroundColor Yellow
                }
            }
        }
        
        $lastSize = $currentSize
    }
    
    # 檢查是否完成
    $recentLines = Get-Content $logFile -Tail 50 -Raw
    if ($recentLines -match "分析完成|JSON.*saved") {
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Green
        Write-Host "  分析任務完成" -ForegroundColor Green
        Write-Host "====================================" -ForegroundColor Green
        break
    }
}

Write-Host ""
Write-Host "監控結束 - 按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

    
    $currentSize = (Get-Item $logFile).Length
    
    if ($currentSize -gt $lastSize) {
        # 讀取新增的內容
        $newContent = Get-Content $logFile -Tail 20 | Select-String -Pattern "STEP|PROGRESS|INFO.*彎道|ERROR|SUCCESS|完成"
        
        if ($newContent) {
            foreach ($line in $newContent) {
                $lineStr = $line.Line
                
                # 根據內容類型使用不同顏色
                if ($lineStr -match "ERROR") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor Red
                } elseif ($lineStr -match "SUCCESS|完成|✅") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor Green
                } elseif ($lineStr -match "STEP") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor Magenta
                } elseif ($lineStr -match "PROGRESS") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor Cyan
                } elseif ($lineStr -match "INFO") {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor Yellow
                } else {
                    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $lineStr" -ForegroundColor White
                }
            }
        }
        
        $lastSize = $currentSize
    }
    
    # 檢查是否完成（搜尋最近 50 行）
    $recentLines = Get-Content $logFile -Tail 50
    if ($recentLines -match "全車手彎道速度分析完成|JSON.*saved|Function 47.*完成") {
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Green
        Write-Host "  ✅ F47 分析任務完成！" -ForegroundColor Green
        Write-Host "====================================" -ForegroundColor Green
        
        # 顯示 JSON 輸出路徑
        $jsonLine = $recentLines | Select-String -Pattern "JSON.*saved" | Select-Object -Last 1
        if ($jsonLine) {
            Write-Host $jsonLine.Line -ForegroundColor Cyan
        }
        
        break
    }
    
    # 檢查是否出錯
    if ($recentLines -match "ERROR.*Function 47|分析失敗") {
        Write-Host ""
        Write-Host "====================================" -ForegroundColor Red
        Write-Host "  ❌ F47 分析任務失敗" -ForegroundColor Red
        Write-Host "====================================" -ForegroundColor Red
        
        # 顯示錯誤信息
        $errorLines = $recentLines | Select-String -Pattern "ERROR" | Select-Object -Last 5
        foreach ($err in $errorLines) {
            Write-Host $err.Line -ForegroundColor Red
        }
        
        break
    }
}

Write-Host ""
Write-Host "監控結束 - 按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
