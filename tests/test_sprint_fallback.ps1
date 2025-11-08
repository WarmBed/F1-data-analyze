#==============================================================================
# F1T Sprint Weekend Data Generation - Session Fallback Testing
# Sprint 週末數據生成 - Session 自動降級測試
#==============================================================================
# 日期: 2025-11-04
# 功能: 測試 FP3→Sprint 自動切換機制
#==============================================================================

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Sprint Weekend Fallback 測試腳本" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================================================
# 測試 1: Austria - Sprint 週末（應自動從 FP3 降級至 Sprint）
# ============================================================================

Write-Host "`n[測試 1/3] Austria 2024 - FP3→Sprint 自動降級" -ForegroundColor Yellow
Write-Host "預期行為: 檢測到無 FP3，自動使用 Sprint session`n" -ForegroundColor Gray

# 功能 47: Corner Analysis (FP3→Sprint)
Write-Host "執行: 功能 47 (Corner Analysis)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 47 -y 2024 -r Austria -s FP3

Write-Host "`n輸出檔案應為: all_drivers_cornering_analysis_2024_Austria_Sprint.json" -ForegroundColor Cyan

# 功能 70: FP-Q Data (應使用 Sprint 替代 FP3)
Write-Host "`n執行: 功能 70 (FP-Q Data)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 70 -y 2024 -r Austria -s R

Write-Host "`n" -ForegroundColor Gray
Write-Host "=" * 80 -ForegroundColor Gray

# ============================================================================
# 測試 2: Brazil - Sprint 週末
# ============================================================================

Write-Host "`n[測試 2/3] Brazil 2024 - FP3→Sprint 自動降級" -ForegroundColor Yellow

# 功能 47: Corner Analysis
Write-Host "執行: 功能 47 (Corner Analysis)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 47 -y 2024 -r Brazil -s FP3

# 功能 70: FP-Q Data
Write-Host "`n執行: 功能 70 (FP-Q Data)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 70 -y 2024 -r Brazil -s R

Write-Host "`n" -ForegroundColor Gray
Write-Host "=" * 80 -ForegroundColor Gray

# ============================================================================
# 測試 3: Qatar - Sprint 週末
# ============================================================================

Write-Host "`n[測試 3/3] Qatar 2024 - FP3→Sprint 自動降級" -ForegroundColor Yellow

# 功能 47: Corner Analysis
Write-Host "執行: 功能 47 (Corner Analysis)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 47 -y 2024 -r Qatar -s FP3

# 功能 70: FP-Q Data
Write-Host "`n執行: 功能 70 (FP-Q Data)" -ForegroundColor Green
python f1_analysis_modular_main.py -f 70 -y 2024 -r Qatar -s R

Write-Host "`n" -ForegroundColor Gray
Write-Host "=" * 80 -ForegroundColor Gray

# ============================================================================
# 驗證生成的檔案
# ============================================================================

Write-Host "`n`n========================================" -ForegroundColor Cyan
Write-Host "  驗證生成的 JSON 檔案" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Corner Analysis 檔案（應為 Sprint）:" -ForegroundColor Yellow
Get-ChildItem -Path "json" -Filter "*cornering_analysis_2024*Austria*.json" | Select-Object Name, Length, LastWriteTime
Get-ChildItem -Path "json" -Filter "*cornering_analysis_2024*Brazil*.json" | Select-Object Name, Length, LastWriteTime
Get-ChildItem -Path "json" -Filter "*cornering_analysis_2024*Qatar*.json" | Select-Object Name, Length, LastWriteTime

Write-Host "`nFP-Q 數據檔案:" -ForegroundColor Yellow
Get-ChildItem -Path "json\predictionJSON" -Filter "*2024_Austria*.json" | Select-Object Name, Length, LastWriteTime
Get-ChildItem -Path "json\predictionJSON" -Filter "*2024_Brazil*.json" | Select-Object Name, Length, LastWriteTime
Get-ChildItem -Path "json\predictionJSON" -Filter "*2024_Qatar*.json" | Select-Object Name, Length, LastWriteTime

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  測試完成！" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "下一步: 使用生成的數據訓練 Austria、Brazil、Qatar 模型" -ForegroundColor Green
Write-Host "執行: python batch_train_all_tracks_v3.8.py --trials 500 --workers 4`n" -ForegroundColor Cyan
