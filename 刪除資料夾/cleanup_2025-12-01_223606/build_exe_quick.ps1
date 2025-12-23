#!/usr/bin/env pwsh
<#
.SYNOPSIS
    F1T GUI - 快速打包腳本（簡化版）
    
.DESCRIPTION
    執行最小化的打包流程，適合快速測試
#>

Write-Host "`n🚀 F1T GUI V0.8.0 - 快速打包" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# 檢查版本
Write-Host "`n📌 當前版本:" -ForegroundColor Yellow
python -c "from config.version import APP_FULL_TITLE; print(f'  {APP_FULL_TITLE}')"

# 清理
Write-Host "`n🧹 清理舊檔案..." -ForegroundColor Yellow
Remove-Item -Recurse -Force build, dist -ErrorAction SilentlyContinue

# 打包
Write-Host "`n📦 開始打包 (這可能需要幾分鐘)..." -ForegroundColor Yellow
python -m PyInstaller F1T_GUI.spec --clean --noconfirm

# 驗證
if (Test-Path "dist\F1T_GUI.exe") {
    $size = [math]::Round((Get-Item "dist\F1T_GUI.exe").Length / 1MB, 2)
    Write-Host "`n✅ 打包成功！" -ForegroundColor Green
    Write-Host "  📂 檔案: dist\F1T_GUI.exe" -ForegroundColor Cyan
    Write-Host "  📊 大小: $size MB" -ForegroundColor Cyan
    Write-Host "`n💡 測試執行: .\dist\F1T_GUI.exe`n" -ForegroundColor Yellow
} else {
    Write-Host "`n❌ 打包失敗！" -ForegroundColor Red
    exit 1
}
