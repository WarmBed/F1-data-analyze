# 🔧 一鍵重新打包 EXE（包含 API-ONLY 修復）

Write-Host "=================================" -ForegroundColor Cyan
Write-Host "   F1T GUI 重新打包腳本" -ForegroundColor Cyan
Write-Host "   包含 API-ONLY 修復驗證" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# 步驟 1：驗證 API-ONLY 修復
Write-Host "🔍 [1/5] 驗證 API-ONLY 修復狀態..." -ForegroundColor Yellow

$brakeFile = "modules\gui\lap_analysis\brake_analysis\brake_analysis_mdi.py"
$apiOnlyMarkers = (Get-Content $brakeFile -Encoding UTF8 | Select-String -Pattern "\[API-ONLY\]").Count

if ($apiOnlyMarkers -ge 3) {
    Write-Host "  ✅ 檢測到 $apiOnlyMarkers 處 [API-ONLY] 標記" -ForegroundColor Green
} else {
    Write-Host "  ❌ 警告：只檢測到 $apiOnlyMarkers 處 [API-ONLY] 標記（預期至少 3 處）" -ForegroundColor Red
    $continue = Read-Host "  是否繼續打包？(y/N)"
    if ($continue -ne "y") {
        Write-Host "  打包已取消" -ForegroundColor Red
        exit 1
    }
}

# 檢查違規代碼
$violations = (Get-Content $brakeFile -Encoding UTF8 | Select-String -Pattern "create_telemetry_analysis\(\)").Count
if ($violations -gt 0) {
    Write-Host "  ⚠️  警告：檢測到 $violations 處可能的違規代碼（create_telemetry_analysis）" -ForegroundColor Yellow
}

Write-Host ""

# 步驟 2：清理舊的建置檔案
Write-Host "🧹 [2/5] 清理舊的建置檔案..." -ForegroundColor Yellow

if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 已刪除 dist 目錄" -ForegroundColor Green
}

if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "  ✅ 已刪除 build 目錄" -ForegroundColor Green
}

Write-Host ""

# 步驟 3：清理 Python 緩存
Write-Host "🧹 [3/5] 清理 Python 緩存..." -ForegroundColor Yellow

$pycacheCount = 0
Get-ChildItem -Path "." -Include "__pycache__","*.pyc" -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $pycacheCount++
}

Write-Host "  ✅ 已清理 $pycacheCount 個緩存檔案/目錄" -ForegroundColor Green
Write-Host ""

# 步驟 4：執行 PyInstaller 打包
Write-Host "📦 [4/5] 執行 PyInstaller 打包..." -ForegroundColor Yellow
Write-Host "  （這可能需要幾分鐘，請耐心等待...）" -ForegroundColor Gray
Write-Host ""

$buildStartTime = Get-Date
python -m PyInstaller F1T_GUI.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "  ❌ 打包失敗！錯誤代碼: $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

$buildEndTime = Get-Date
$buildDuration = $buildEndTime - $buildStartTime

Write-Host ""
Write-Host "  ✅ 打包成功！耗時: $($buildDuration.TotalSeconds.ToString('F1')) 秒" -ForegroundColor Green
Write-Host ""

# 步驟 5：驗證 EXE
Write-Host "🔍 [5/5] 驗證生成的 EXE..." -ForegroundColor Yellow

if (Test-Path "dist\F1T_GUI.exe") {
    $exeInfo = Get-Item "dist\F1T_GUI.exe"
    $exeSizeMB = [math]::Round($exeInfo.Length / 1MB, 2)
    
    Write-Host "  ✅ EXE 檔案已生成" -ForegroundColor Green
    Write-Host "  📂 路徑: dist\F1T_GUI.exe" -ForegroundColor Gray
    Write-Host "  📊 大小: $exeSizeMB MB" -ForegroundColor Gray
    Write-Host "  🕐 修改時間: $($exeInfo.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
    
    # 檢查檔案時間是否新於修復時間
    $brakeFileInfo = Get-Item $brakeFile
    if ($exeInfo.LastWriteTime -gt $brakeFileInfo.LastWriteTime) {
        Write-Host "  ✅ EXE 打包時間新於源代碼修改時間" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  警告：EXE 打包時間可能舊於源代碼修改時間" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ❌ 錯誤：找不到 dist\F1T_GUI.exe" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "   打包完成！" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "📋 下一步測試建議：" -ForegroundColor Yellow
Write-Host "  1. 執行 EXE：.\dist\F1T_GUI.exe" -ForegroundColor Gray
Write-Host "  2. 開啟 Brake Analysis 模組" -ForegroundColor Gray
Write-Host "  3. 更新圈數參數（例如：Lap 5 → Lap 6）" -ForegroundColor Gray
Write-Host "  4. 驗證不會彈出 Pitstop 視窗" -ForegroundColor Gray
Write-Host ""

# 詢問是否立即運行 EXE
$runNow = Read-Host "是否立即運行 EXE 進行測試？(y/N)"
if ($runNow -eq "y") {
    Write-Host ""
    Write-Host "🚀 啟動 F1T GUI (EXE)..." -ForegroundColor Cyan
    Start-Process "dist\F1T_GUI.exe"
}
