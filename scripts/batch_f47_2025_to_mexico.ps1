# ============================================================
# F47 全車手彎道分析 - 2025 賽季批量執行腳本
# ============================================================
# 功能：自動執行 CLI Function 47（全車手彎道速度分析）
# 範圍：2025 年所有賽事到墨西哥站（第 20 場）
# 會話：R（正賽）、Q（排位賽）、FP1/FP2/FP3（練習賽）
# ============================================================

# 設置編碼
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  F47 全車手彎道分析 - 2025 賽季批量執行" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""

# 定義 2025 賽季賽事列表（到墨西哥站）
$races = @(
    @{Round=1;  Name="Australia";      Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=2;  Name="China";          Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=3;  Name="Japan";          Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=4;  Name="Bahrain";        Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=5;  Name="Saudi Arabia";   Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=6;  Name="Miami";          Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=7;  Name="Emilia Romagna"; Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=8;  Name="Monaco";         Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=9;  Name="Spain";          Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=10; Name="Canada";         Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=11; Name="Austria";        Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=12; Name="Great Britain";  Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=13; Name="Belgium";        Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=14; Name="Hungary";        Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=15; Name="Netherlands";    Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=16; Name="Italy";          Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=17; Name="Azerbaijan";     Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=18; Name="Singapore";      Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=19; Name="United States";  Sessions=@("R", "Q", "FP1", "FP2", "FP3")},
    @{Round=20; Name="Mexico";         Sessions=@("Q")}  # 墨西哥站只有排位賽
)

# 計數器
$totalRaces = $races.Count
$totalSessions = ($races | ForEach-Object { $_.Sessions.Count } | Measure-Object -Sum).Sum
$currentSession = 0
$successCount = 0
$failCount = 0
$skipCount = 0

Write-Host "執行計畫：" -ForegroundColor Green
Write-Host "  - 賽事數量：$totalRaces 場" -ForegroundColor White
Write-Host "  - 總會話數：$totalSessions 個" -ForegroundColor White
Write-Host "  - CLI 功能：F47 (全車手彎道速度分析)" -ForegroundColor White
Write-Host ""
Write-Host "按 Enter 開始執行，或 Ctrl+C 取消..." -ForegroundColor Yellow
Read-Host

# 開始計時
$startTime = Get-Date

# 遍歷每場賽事
foreach ($race in $races) {
    $raceName = $race.Name
    $round = $race.Round
    
    Write-Host ""
    Write-Host ("-" * 70) -ForegroundColor Gray
    Write-Host "第 $round 場：$raceName" -ForegroundColor Cyan
    Write-Host ("-" * 70) -ForegroundColor Gray
    
    # 遍歷每個會話
    foreach ($session in $race.Sessions) {
        $currentSession++
        $progress = [math]::Round(($currentSession / $totalSessions) * 100, 1)
        
        Write-Host ""
        Write-Host "[$currentSession/$totalSessions] ($progress%) - $raceName - $session" -ForegroundColor Yellow
        
        # 檢查 JSON 是否已存在
        $jsonPattern = "json\all_drivers_cornering_analysis_2025_${raceName}_${session}_*.json"
        $existingJson = Get-ChildItem -Path $jsonPattern -ErrorAction SilentlyContinue
        
        if ($existingJson) {
            Write-Host "  跳過：JSON 已存在 ($($existingJson.Name))" -ForegroundColor DarkGray
            $skipCount++
            continue
        }
        
        # 執行 CLI F47
        Write-Host "  執行：python f1_analysis_modular_main.py -f 47 -y 2025 -r `"$raceName`" -s $session" -ForegroundColor White
        
        try {
            $output = python f1_analysis_modular_main.py -f 47 -y 2025 -r "$raceName" -s $session 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  成功" -ForegroundColor Green
                $successCount++
            } else {
                Write-Host "  失敗 (返回碼: $LASTEXITCODE)" -ForegroundColor Red
                Write-Host "  錯誤輸出：" -ForegroundColor Red
                Write-Host $output -ForegroundColor DarkRed
                $failCount++
            }
        } catch {
            Write-Host "  異常：$($_.Exception.Message)" -ForegroundColor Red
            $failCount++
        }
        
        # 短暫延遲避免過載
        Start-Sleep -Milliseconds 500
    }
}

# 結束計時
$endTime = Get-Date
$duration = $endTime - $startTime

# 顯示總結
Write-Host ""
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "  執行完成" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host ""
Write-Host "統計資訊：" -ForegroundColor Green
Write-Host "  - 成功：$successCount 個會話" -ForegroundColor Green
Write-Host "  - 失敗：$failCount 個會話" -ForegroundColor Red
Write-Host "  - 跳過：$skipCount 個會話（已存在）" -ForegroundColor DarkGray
Write-Host "  - 總計：$totalSessions 個會話" -ForegroundColor White
Write-Host ""
Write-Host "執行時間：$($duration.ToString('hh\:mm\:ss'))" -ForegroundColor White
Write-Host ""

# 顯示生成的 JSON 檔案
Write-Host "生成的 JSON 檔案：" -ForegroundColor Green
$jsonFiles = Get-ChildItem -Path "json\all_drivers_cornering_analysis_2025_*.json" | Sort-Object LastWriteTime -Descending | Select-Object -First 20
if ($jsonFiles) {
    foreach ($file in $jsonFiles) {
        $size = [math]::Round($file.Length / 1KB, 1)
        Write-Host "  - $($file.Name) ($size KB)" -ForegroundColor White
    }
} else {
    Write-Host "  （無新檔案）" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "腳本執行完畢！" -ForegroundColor Yellow
