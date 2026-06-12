# F1T 建構虛擬環境設置腳本
# 用法: .\setup_venv_build.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$VenvPath = "$ProjectRoot\venv_build"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "F1T 建構虛擬環境設置" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Step 1: 刪除舊的虛擬環境
Write-Host "`n[Step 1] 刪除舊的虛擬環境..." -ForegroundColor Yellow
if (Test-Path $VenvPath) {
    Remove-Item -Path $VenvPath -Recurse -Force
    Write-Host "  ✅ 已刪除舊的 venv_build" -ForegroundColor Green
} else {
    Write-Host "  ℹ️ venv_build 不存在，跳過" -ForegroundColor Gray
}

# Step 2: 創建新的虛擬環境
Write-Host "`n[Step 2] 創建新的虛擬環境..." -ForegroundColor Yellow
python -m venv $VenvPath
if (Test-Path "$VenvPath\Scripts\python.exe") {
    Write-Host "  ✅ 虛擬環境創建成功" -ForegroundColor Green
} else {
    Write-Host "  ❌ 虛擬環境創建失敗" -ForegroundColor Red
    exit 1
}

# Step 3: 升級 pip
Write-Host "`n[Step 3] 升級 pip..." -ForegroundColor Yellow
& "$VenvPath\Scripts\python.exe" -m pip install --upgrade pip --quiet
Write-Host "  ✅ pip 已升級" -ForegroundColor Green

# Step 4: 安裝 PyQt5 (指定版本)
Write-Host "`n[Step 4] 安裝 PyQt5==5.15.10..." -ForegroundColor Yellow
& "$VenvPath\Scripts\pip.exe" install PyQt5==5.15.10 --quiet
Write-Host "  ✅ PyQt5 安裝成功" -ForegroundColor Green

# Step 5: 驗證 PyQt5 版本
Write-Host "`n[Step 5] 驗證 PyQt5 版本..." -ForegroundColor Yellow
$pyqt_version = & "$VenvPath\Scripts\python.exe" -c "from PyQt5.QtCore import PYQT_VERSION_STR; print(PYQT_VERSION_STR)"
Write-Host "  ✅ PyQt5 版本: $pyqt_version" -ForegroundColor Green

# Step 6: 安裝 PyInstaller
Write-Host "`n[Step 6] 安裝 PyInstaller..." -ForegroundColor Yellow
& "$VenvPath\Scripts\pip.exe" install pyinstaller pyinstaller-hooks-contrib --quiet
Write-Host "  ✅ PyInstaller 安裝成功" -ForegroundColor Green

# Step 7: 安裝其他依賴
Write-Host "`n[Step 7] 安裝其他依賴套件..." -ForegroundColor Yellow
$packages = @(
    "fastf1",
    "pandas",
    "matplotlib",
    "scipy",
    "Pillow",
    "requests",
    "numpy",
    "prettytable",
    "tabulate",
    "openpyxl",
    "seaborn",
    "scikit-learn",
    "reportlab",
    "certifi",
    "packaging",
    "pefile",
    "pywin32-ctypes"
)

foreach ($pkg in $packages) {
    Write-Host "  安裝 $pkg..." -ForegroundColor Gray
    & "$VenvPath\Scripts\pip.exe" install $pkg --quiet
}
Write-Host "  ✅ 所有依賴安裝成功" -ForegroundColor Green

# Step 8: 顯示已安裝套件
Write-Host "`n[Step 8] 已安裝的關鍵套件:" -ForegroundColor Yellow
& "$VenvPath\Scripts\pip.exe" list | Select-String -Pattern "PyQt5|pyinstaller|fastf1|pandas|matplotlib"

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "✅ 建構虛擬環境設置完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "`n現在可以執行 build_exe_gui.py 來建構 EXE" -ForegroundColor White
