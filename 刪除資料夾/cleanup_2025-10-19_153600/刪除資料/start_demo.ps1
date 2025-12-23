# 啟動 F1T 分頁架構 DEMO
Write-Host "🏎️  F1T GUI - 分頁架構 + 彈出功能 完整 DEMO" -ForegroundColor Red
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""
Write-Host "📋 準備啟動 DEMO 程式..." -ForegroundColor Cyan
Write-Host ""

# 檢查 Python 環境
Write-Host "🔍 檢查 Python 環境..." -ForegroundColor Green
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Python: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "   ❌ 錯誤: 未找到 Python！" -ForegroundColor Red
    Write-Host "   請先安裝 Python 3.8 或更高版本" -ForegroundColor Yellow
    pause
    exit 1
}

# 檢查 PyQt5
Write-Host "🔍 檢查 PyQt5..." -ForegroundColor Green
python -c "import PyQt5; print(f'   ✅ PyQt5 版本: {PyQt5.QtCore.PYQT_VERSION_STR}')" 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ❌ 錯誤: 未安裝 PyQt5！" -ForegroundColor Red
    Write-Host "   正在嘗試安裝 PyQt5..." -ForegroundColor Yellow
    pip install PyQt5
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ PyQt5 安裝失敗！" -ForegroundColor Red
        pause
        exit 1
    }
}

Write-Host ""
Write-Host "✨ 環境檢查完成！啟動 DEMO..." -ForegroundColor Green
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host ""

# 啟動 DEMO
python demo_tab_architecture.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "DEMO 已關閉" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 測試報告位置:" -ForegroundColor Green
Write-Host "   docs\develop task\GUI Develop task\DEMO測試報告.md" -ForegroundColor White
Write-Host ""
Write-Host "按任意鍵退出..." -ForegroundColor Yellow
pause
