# Git 追蹤清理腳本
# 用途：從 Git 追蹤中移除大型檔案（保留本地檔案）
# 執行時機：在 git push 完成後執行

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Git 追蹤清理腳本" -ForegroundColor Cyan
Write-Host " 將移除已追蹤的大型檔案" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 確認執行
$confirm = Read-Host "確定要從 Git 追蹤中移除 pkl, json, training_data, reports, 刪除資料夾? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "已取消" -ForegroundColor Yellow
    exit
}

Write-Host ""
Write-Host "[1/5] 移除 models/*.pkl..." -ForegroundColor Yellow
git rm -r --cached models/*.pkl 2>$null
git rm -r --cached "models/**/*.pkl" 2>$null

Write-Host "[2/5] 移除 json/ 資料夾..." -ForegroundColor Yellow
git rm -r --cached json/ 2>$null

Write-Host "[3/5] 移除 training_data/ 資料夾..." -ForegroundColor Yellow
git rm -r --cached training_data/ 2>$null

Write-Host "[4/5] 移除 reports/*.json, *.html, *.csv..." -ForegroundColor Yellow
git rm -r --cached "reports/*.json" 2>$null
git rm -r --cached "reports/*.html" 2>$null
git rm -r --cached "reports/*.csv" 2>$null

Write-Host "[5/5] 移除 刪除資料夾/..." -ForegroundColor Yellow
git rm -r --cached "刪除資料夾/" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 清理完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "下一步執行：" -ForegroundColor Cyan
Write-Host '  git commit -m "chore: remove large files from tracking (pkl, json, training_data)"'
Write-Host '  git push origin main --force'
Write-Host ""

# 顯示狀態
Write-Host "目前 Git 狀態：" -ForegroundColor Yellow
git status --short | Select-Object -First 20
