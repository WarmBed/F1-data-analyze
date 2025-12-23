# ========================================
# 清除 Windows 圖標緩存
# Clear Windows Icon Cache
# ========================================
# 用途: 如果 EXE 在任務欄仍顯示錯誤圖標，執行此腳本清除緩存
# ========================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "🧹 清除 Windows 圖標緩存" -ForegroundColor Yellow
Write-Host "========================================`n" -ForegroundColor Cyan

# 檢查管理員權限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "⚠️ 警告: 建議以管理員身份執行此腳本以獲得最佳效果" -ForegroundColor Yellow
    Write-Host "   右鍵點擊 PowerShell → 以管理員身份執行`n" -ForegroundColor Gray
}

try {
    Write-Host "步驟 1: 關閉檔案總管..." -ForegroundColor Cyan
    Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 檔案總管已關閉`n" -ForegroundColor Green
    
    Write-Host "步驟 2: 刪除圖標緩存檔案..." -ForegroundColor Cyan
    $iconCachePaths = @(
        "$env:LOCALAPPDATA\IconCache.db",
        "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache*.db",
        "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\thumbcache*.db"
    )
    
    $deletedCount = 0
    foreach ($path in $iconCachePaths) {
        $files = Get-Item $path -ErrorAction SilentlyContinue
        if ($files) {
            foreach ($file in $files) {
                try {
                    Remove-Item $file.FullName -Force -ErrorAction Stop
                    Write-Host "   ✅ 已刪除: $($file.Name)" -ForegroundColor Green
                    $deletedCount++
                } catch {
                    Write-Host "   ⚠️ 無法刪除: $($file.Name) - $($_.Exception.Message)" -ForegroundColor Yellow
                }
            }
        }
    }
    
    if ($deletedCount -eq 0) {
        Write-Host "   ℹ️ 未找到需要刪除的緩存檔案" -ForegroundColor Gray
    } else {
        Write-Host "`n   共刪除 $deletedCount 個緩存檔案`n" -ForegroundColor Green
    }
    
    Write-Host "步驟 3: 重新啟動檔案總管..." -ForegroundColor Cyan
    Start-Process explorer
    Start-Sleep -Seconds 2
    Write-Host "   ✅ 檔案總管已重新啟動`n" -ForegroundColor Green
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "✅ 圖標緩存清除完成！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Cyan
    
    Write-Host "下一步:" -ForegroundColor Yellow
    Write-Host "   1. 重新啟動 F1T_GUI.exe" -ForegroundColor White
    Write-Host "   2. 檢查任務欄是否顯示 F1T 圖標" -ForegroundColor White
    Write-Host "   3. 如果仍未生效，請重新啟動電腦`n" -ForegroundColor White
    
} catch {
    Write-Host "`n❌ 錯誤: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   請以管理員身份執行此腳本`n" -ForegroundColor Yellow
}

Write-Host "按任意鍵退出..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
