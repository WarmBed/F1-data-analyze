#!/usr/bin/env pwsh
<#
.SYNOPSIS
    F1T GUI V0.7.0 - 完整打包腳本

.DESCRIPTION
    執行完整的 PyInstaller 打包流程，包含環境檢查、清理、打包和驗證
    
.NOTES
    Version: 0.7.0
    Author: F1T Development Team
    Date: 2025-11-08
#>

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ==================== 顏色配置 ====================
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

function Write-Header {
    param([string]$Title)
    Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host ("=" * 70) -ForegroundColor Cyan
}

function Write-Step {
    param([string]$Message)
    Write-ColorOutput "`n▶ $Message" "Yellow"
}

function Write-Success {
    param([string]$Message)
    Write-ColorOutput "✅ $Message" "Green"
}

function Write-Error {
    param([string]$Message)
    Write-ColorOutput "❌ $Message" "Red"
}

function Write-Warning {
    param([string]$Message)
    Write-ColorOutput "⚠️  $Message" "Yellow"
}

# ==================== 主流程 ====================

Write-Header "F1T GUI V0.7.0 - PyInstaller 打包流程"

# 階段 1: 環境檢查
Write-Step "階段 1: 環境檢查"

# 檢查 Python
try {
    $pythonVersion = python --version 2>&1
    Write-Success "Python: $pythonVersion"
} catch {
    Write-Error "找不到 Python！請確認 Python 已安裝並加入 PATH"
    exit 1
}

# 檢查 PyInstaller
try {
    $pyinstallerVersion = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
    Write-Success "PyInstaller: $pyinstallerVersion"
} catch {
    Write-Error "找不到 PyInstaller！執行: pip install pyinstaller"
    exit 1
}

# 檢查必要檔案
$requiredFiles = @(
    "f1t_gui_main.py",
    "F1T_GUI.spec",
    "pyinstaller_runtime_hook.py",
    "image/logo.png",
    "image/logo.ico",
    "config/version.py"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Success "檔案存在: $file"
    } else {
        Write-Error "缺少檔案: $file"
        exit 1
    }
}

# 驗證版本號
Write-Step "驗證版本資訊"
$versionInfo = python -c "from config.version import APP_VERSION, APP_FULL_TITLE; print(f'{APP_FULL_TITLE}')" 2>&1
Write-ColorOutput "  當前版本: $versionInfo" "Cyan"

# 階段 2: 執行 SPEC 檢查
Write-Step "階段 2: 執行 SPEC 完整性檢查"
python tests/check_spec.py
if ($LASTEXITCODE -ne 0) {
    Write-Error "SPEC 檢查失敗！請先修復問題"
    exit 1
}

# 階段 3: 清理舊的建置檔案
Write-Step "階段 3: 清理舊的建置檔案"

$dirsToClean = @("build", "dist")
foreach ($dir in $dirsToClean) {
    if (Test-Path $dir) {
        Write-ColorOutput "  正在刪除: $dir" "Gray"
        Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
        Write-Success "已清理: $dir"
    }
}

# 清理舊的 .spec 緩存
if (Test-Path "*.spec.bak") {
    Remove-Item "*.spec.bak" -ErrorAction SilentlyContinue
}

Write-Success "清理完成"

# 階段 4: 執行 PyInstaller 打包
Write-Step "階段 4: 執行 PyInstaller 打包"
Write-ColorOutput "  這可能需要幾分鐘時間，請耐心等待..." "Gray"

$buildStartTime = Get-Date

try {
    python -m PyInstaller F1T_GUI.spec --clean --noconfirm
    
    if ($LASTEXITCODE -eq 0) {
        $buildEndTime = Get-Date
        $buildDuration = ($buildEndTime - $buildStartTime).TotalSeconds
        Write-Success "打包完成！耗時: $([math]::Round($buildDuration, 2)) 秒"
    } else {
        Write-Error "PyInstaller 打包失敗！"
        exit 1
    }
} catch {
    Write-Error "打包過程發生錯誤: $_"
    exit 1
}

# 階段 5: 驗證生成的 EXE
Write-Step "階段 5: 驗證生成的 EXE"

$exePath = "dist\F1T_GUI.exe"
if (Test-Path $exePath) {
    $exeSize = (Get-Item $exePath).Length / 1MB
    Write-Success "EXE 已生成: $exePath"
    Write-ColorOutput "  檔案大小: $([math]::Round($exeSize, 2)) MB" "Cyan"
    
    # 檢查檔案屬性
    $exeInfo = Get-Item $exePath
    Write-ColorOutput "  創建時間: $($exeInfo.CreationTime)" "Gray"
    Write-ColorOutput "  修改時間: $($exeInfo.LastWriteTime)" "Gray"
} else {
    Write-Error "找不到生成的 EXE: $exePath"
    exit 1
}

# 階段 6: 檢查資源檔案
Write-Step "階段 6: 檢查打包的資源檔案"

$distImageDir = "dist\_internal\image"
if (Test-Path $distImageDir) {
    $imageFiles = Get-ChildItem $distImageDir
    Write-Success "資源檔案已打包: $($imageFiles.Count) 個檔案"
    foreach ($file in $imageFiles) {
        Write-ColorOutput "  - $($file.Name)" "Gray"
    }
} else {
    Write-Warning "找不到資源目錄: $distImageDir"
}

# 階段 7: 生成建置報告
Write-Step "階段 7: 生成建置報告"

$reportPath = "dist\BUILD_REPORT.txt"
$reportContent = @"
F1T GUI - 建置報告
==================

版本資訊:
  應用程式: F1 TelemetryStation Pro
  版本號: V0.7.0
  建置日期: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  
建置環境:
  Python: $pythonVersion
  PyInstaller: $pyinstallerVersion
  作業系統: $([System.Environment]::OSVersion.VersionString)
  
建置配置:
  SPEC 檔案: F1T_GUI.spec
  Runtime Hook: pyinstaller_runtime_hook.py
  Console 模式: False (GUI 應用程式)
  Debug 模式: False (生產環境)
  UPX 壓縮: True
  
EXE 資訊:
  檔案名稱: F1T_GUI.exe
  檔案大小: $([math]::Round($exeSize, 2)) MB
  檔案路徑: $exePath
  
V0.7.0 新增功能:
  • FIA Parts Analysis 模組完整多國語言化
  • 整合 color_palette_provider 車手與車隊顏色系統
  • 實作內容翻譯映射系統（變更類型、分類、描述）
  • 支援 Type 欄位英文提取
  • 支援 Description 欄位完整翻譯（6 種類型說明）
  • 顯示格式完全對齊 Ideal Ranking Table 標準
  • 新增 35 位車手名稱到代碼映射系統
  • 實作 Tooltip 顯示原始中英文內容

建置統計:
  建置時長: $([math]::Round($buildDuration, 2)) 秒
  成功狀態: ✅ 成功
  
注意事項:
  1. EXE 運行時會在用戶目錄創建緩存: ~/.f1telemetrystation/cache
  2. 日誌級別設定為 CRITICAL（極度靜默）
  3. API 模式: production (https://api.f1telemetrystationpro.org)
  4. 首次運行可能需要較長時間初始化
  
"@

$reportContent | Out-File -FilePath $reportPath -Encoding UTF8
Write-Success "建置報告已生成: $reportPath"

# 階段 8: 完成
Write-Header "打包完成！"

Write-ColorOutput "`n📦 EXE 檔案位置:" "Green"
Write-ColorOutput "  $exePath" "Cyan"
Write-ColorOutput "`n📊 檔案大小:" "Green"
Write-ColorOutput "  $([math]::Round($exeSize, 2)) MB" "Cyan"
Write-ColorOutput "`n⏱️  建置時長:" "Green"
Write-ColorOutput "  $([math]::Round($buildDuration, 2)) 秒" "Cyan"

Write-ColorOutput "`n✅ 所有階段完成！可以開始測試 EXE" "Green"
Write-ColorOutput "`n💡 測試建議:" "Yellow"
Write-ColorOutput "  1. 在當前目錄執行: .\dist\F1T_GUI.exe" "Gray"
Write-ColorOutput "  2. 複製 dist\F1T_GUI.exe 到其他電腦測試" "Gray"
Write-ColorOutput "  3. 檢查所有模組功能是否正常" "Gray"
Write-ColorOutput "  4. 驗證 FIA Parts Analysis 模組的多國語言功能" "Gray"

Write-Host "`n" + ("=" * 70) + "`n" -ForegroundColor Cyan
