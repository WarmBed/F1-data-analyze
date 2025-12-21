# ============================================================================
# Sprint Weekend 數據收集腳本 (2022-2023)
# ============================================================================
# 目的: 為 Austria、Brazil、Qatar 生成 2022-2023 年的 Sprint 數據
# 功能: Function 47 (Corner Analysis) + Function 70 (FP-Q Data)
# ============================================================================

$ErrorActionPreference = "Continue"

# 定義 Sprint 賽事配置
$sprintRaces = @(
    # Austria (Red Bull Ring) - 2022, 2023, 2024 都有 Sprint
    @{Year=2022; Race="Austria"; Sessions=@("Sprint")},
    @{Year=2023; Race="Austria"; Sessions=@("Sprint")},
    
    # Brazil (Interlagos) - 2022, 2023, 2024 都有 Sprint
    @{Year=2022; Race="Brazil"; Sessions=@("Sprint")},
    @{Year=2023; Race="Brazil"; Sessions=@("Sprint")},
    
    # Qatar (Losail) - 2023, 2024 有 Sprint (2023 是首次舉辦)
    @{Year=2023; Race="Qatar"; Sessions=@("Sprint")}
)

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Sprint Weekend 數據收集 (2022-2023)" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

$totalTasks = $sprintRaces.Count * 2  # 每場比賽 2 個功能 (47 + 70)
$currentTask = 0
$successCount = 0
$failCount = 0

foreach ($race in $sprintRaces) {
    $year = $race.Year
    $raceName = $race.Race
    $session = "Sprint"
    
    Write-Host "┌────────────────────────────────────────────────────────┐" -ForegroundColor Yellow
    Write-Host "│ 🏁 $year $raceName Sprint" -ForegroundColor Yellow
    Write-Host "└────────────────────────────────────────────────────────┘" -ForegroundColor Yellow
    
    # ========================================================================
    # Function 47: Corner Analysis (彎道分析)
    # ========================================================================
    $currentTask++
    Write-Host "[$currentTask/$totalTasks] 執行 Function 47: Corner Analysis..." -ForegroundColor Cyan
    
    $command = "python f1_analysis_modular_main.py -f 47 -y $year -r $raceName -s $session"
    Write-Host "  命令: $command" -ForegroundColor Gray
    
    $output = & python f1_analysis_modular_main.py -f 47 -y $year -r $raceName -s $session 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Function 47 完成" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ❌ Function 47 失敗 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        $failCount++
        # 顯示最後 5 行錯誤
        $output | Select-Object -Last 5 | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkRed }
    }
    
    Start-Sleep -Seconds 2
    
    # ========================================================================
    # Function 70: FP-Q Data (練習賽 vs 排位賽數據)
    # ========================================================================
    $currentTask++
    Write-Host "[$currentTask/$totalTasks] 執行 Function 70: FP-Q Data..." -ForegroundColor Cyan
    
    $command = "python f1_analysis_modular_main.py -f 70 -y $year -r $raceName -s R"
    Write-Host "  命令: $command" -ForegroundColor Gray
    
    $output = & python f1_analysis_modular_main.py -f 70 -y $year -r $raceName -s R 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✅ Function 70 完成" -ForegroundColor Green
        $successCount++
    } else {
        Write-Host "  ❌ Function 70 失敗 (Exit Code: $LASTEXITCODE)" -ForegroundColor Red
        $failCount++
        # 顯示最後 5 行錯誤
        $output | Select-Object -Last 5 | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkRed }
    }
    
    Write-Host ""
    Start-Sleep -Seconds 2
}

# ============================================================================
# 統計報告
# ============================================================================
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  數據收集完成" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "總任務數: $totalTasks" -ForegroundColor White
Write-Host "成功: $successCount" -ForegroundColor Green
Write-Host "失敗: $failCount" -ForegroundColor Red
Write-Host ""

# 驗證生成的檔案
Write-Host "📊 驗證生成的檔案:" -ForegroundColor Cyan
Write-Host ""

Write-Host "Corner Analysis (Function 47):" -ForegroundColor Yellow
Get-ChildItem json\*Sprint*.json | 
    Where-Object { $_.Name -match "2022|2023" } |
    Select-Object Name, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime |
    Format-Table -AutoSize

Write-Host "FP-Q Data (Function 70):" -ForegroundColor Yellow
Get-ChildItem json\predictionJSON\fp_q_data*.json | 
    Where-Object { $_.Name -match "2022|2023" } |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 10 |
    Select-Object Name, @{N='Size(KB)';E={[math]::Round($_.Length/1KB,1)}}, LastWriteTime |
    Format-Table -AutoSize

Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "下一步: 執行 batch_train_all_tracks_v3.8.py 訓練模型" -ForegroundColor Green
Write-Host "命令: python batch_train_all_tracks_v3.8.py --trials 500 --workers 4" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
