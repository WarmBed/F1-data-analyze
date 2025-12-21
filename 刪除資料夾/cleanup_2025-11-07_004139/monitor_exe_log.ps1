# ============================================
# F1T EXE Log Monitor - 即時監控 EXE 運行日誌
# ============================================

Write-Host "🔍 F1T EXE Log Monitor - 啟動" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor DarkGray
Write-Host ""

# 設定日誌檔案路徑
$logFile = "logs\gui-log"

# 檢查 logs 目錄
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
    Write-Host "✅ 已創建 logs 目錄" -ForegroundColor Green
}

# 清理舊的日誌（可選）
if (Test-Path $logFile) {
    Write-Host "🗑️  清理舊日誌檔案..." -ForegroundColor Yellow
    Remove-Item $logFile -Force
}

# 啟動 EXE
Write-Host "🚀 啟動 F1T_GUI.exe..." -ForegroundColor Cyan
$process = Start-Process -FilePath "dist\F1T_GUI.exe" -PassThru -WorkingDirectory $PWD

Write-Host "✅ EXE 已啟動 (PID: $($process.Id))" -ForegroundColor Green
Write-Host ""
Write-Host "=" * 60 -ForegroundColor DarkGray
Write-Host "📋 即時日誌輸出 (每 2 秒更新一次)" -ForegroundColor Yellow
Write-Host "   按 Ctrl+C 停止監控" -ForegroundColor DarkGray
Write-Host "=" * 60 -ForegroundColor DarkGray
Write-Host ""

# 等待日誌檔案創建
$timeout = 10
$elapsed = 0
while (-not (Test-Path $logFile) -and $elapsed -lt $timeout) {
    Start-Sleep -Milliseconds 500
    $elapsed++
}

if (-not (Test-Path $logFile)) {
    Write-Host "⚠️  等待 $timeout 秒後仍未檢測到日誌檔案" -ForegroundColor Yellow
    Write-Host "   日誌檔案路徑: $logFile" -ForegroundColor DarkGray
    Write-Host ""
    Write-Host "💡 可能的原因:" -ForegroundColor Cyan
    Write-Host "   1. EXE 啟動失敗" -ForegroundColor Gray
    Write-Host "   2. 日誌系統未正確初始化" -ForegroundColor Gray
    Write-Host "   3. 日誌寫入到其他位置" -ForegroundColor Gray
    Write-Host ""
    Write-Host "🔍 檢查 logs 目錄中的其他檔案:" -ForegroundColor Yellow
    Get-ChildItem -Path "logs" -Filter "*log*" | Select-Object Name, LastWriteTime, Length | Format-Table -AutoSize
    
    Write-Host ""
    Write-Host "⏳ 繼續等待 EXE 運行 (按 Ctrl+C 終止)..." -ForegroundColor DarkGray
    Wait-Process -Id $process.Id
    exit
}

Write-Host "✅ 檢測到日誌檔案: $logFile" -ForegroundColor Green
Write-Host ""

# 即時顯示日誌內容（tail -f 模式）
$lastSize = 0
$lineCount = 0

try {
    while (-not $process.HasExited) {
        if (Test-Path $logFile) {
            $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
            
            if ($content -and $content.Length -gt $lastSize) {
                # 只顯示新增的內容
                $newContent = $content.Substring($lastSize)
                $lastSize = $content.Length
                
                # 分行並著色輸出
                $newContent -split "`n" | ForEach-Object {
                    if ($_ -match '^\s*$') { return }  # 跳過空行
                    
                    $lineCount++
                    $line = $_
                    
                    # 根據關鍵字著色
                    if ($line -match '\[ERROR\]|❌|失敗') {
                        Write-Host $line -ForegroundColor Red
                    }
                    elseif ($line -match '\[WARNING\]|⚠️|警告') {
                        Write-Host $line -ForegroundColor Yellow
                    }
                    elseif ($line -match '\[SUCCESS\]|✅|成功') {
                        Write-Host $line -ForegroundColor Green
                    }
                    elseif ($line -match '\[DEBUG\]|🔍') {
                        Write-Host $line -ForegroundColor Cyan
                    }
                    elseif ($line -match '\[WORKSPACE\]|🔨|🔄') {
                        Write-Host $line -ForegroundColor Magenta
                    }
                    elseif ($line -match 'tab|Tab|TAB') {
                        Write-Host $line -ForegroundColor Yellow -BackgroundColor DarkBlue
                    }
                    else {
                        Write-Host $line -ForegroundColor Gray
                    }
                }
            }
        }
        
        Start-Sleep -Milliseconds 500
    }
    
    Write-Host ""
    Write-Host "=" * 60 -ForegroundColor DarkGray
    Write-Host "⏹️  EXE 已終止" -ForegroundColor Yellow
    Write-Host "📊 總共記錄 $lineCount 行日誌" -ForegroundColor Cyan
    
} catch {
    Write-Host ""
    Write-Host "❌ 監控中斷: $_" -ForegroundColor Red
} finally {
    Write-Host ""
    Write-Host "📋 完整日誌檔案位置: $logFile" -ForegroundColor Cyan
    Write-Host ""
}
