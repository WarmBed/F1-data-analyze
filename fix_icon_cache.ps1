# Clean Windows Icon Cache and Rebuild
Write-Host "Clearing Windows Icon Cache..." -ForegroundColor Cyan

# Delete icon cache database
$iconCachePaths = @(
    "$env:LOCALAPPDATA\IconCache.db",
    "$env:LOCALAPPDATA\Microsoft\Windows\Explorer\iconcache_*.db"
)

foreach ($path in $iconCachePaths) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Force -ErrorAction SilentlyContinue
        Write-Host "Deleted: $path" -ForegroundColor Green
    }
}

# Restart Windows Explorer
Write-Host ""
Write-Host "Restarting Windows Explorer..." -ForegroundColor Cyan
Stop-Process -Name explorer -Force
Start-Sleep -Seconds 2
Start-Process explorer

Write-Host ""
Write-Host "Icon cache cleared! Please check dist\F1T_GUI.exe icon" -ForegroundColor Green
Write-Host "Tip: If icon still not shown, please restart computer" -ForegroundColor Yellow
