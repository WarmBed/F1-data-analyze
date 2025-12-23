# SSL 證書修復腳本
# 為所有 GUI 模組的 requests 調用添加 verify=certifi.where()

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " SSL 證書修復腳本" -ForegroundColor Cyan
Write-Host " 修復 EXE API 調用問題" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 需要修復的檔案清單（從 grep 結果提取）
$files = @(
    "modules\gui\themes\color_palette_provider.py",
    "modules\gui\tire_analysis\tire_analysis_mdi.py",
    "modules\gui\telemetry_analysis_mdi.py",
    "modules\gui\all_drivers\brake\brake_performance_loader.py",
    "modules\gui\season_progress\season_progress_mdi.py",
    "modules\gui\all_drivers\brake\brake_chart_data_loader.py",
    "modules\gui\all_drivers\brake\brake_all_laps_loader.py",
    "modules\gui\race_analysis\track\track_analysis_mdi.py",
    "modules\gui\race_analysis\track\track_analysis_module.py",
    "modules\gui\race_analysis\track_map\historical_track_map_data_loader.py",
    "modules\gui\race_analysis\temp\temp_analysis_mdi.py",
    "modules\gui\race_analysis\position\driver_position_analysis_mdi.py",
    "modules\gui\race_analysis\pitstop\pitstop_analysis_mdi.py",
    "modules\gui\race_prediction\race_prediction_mdi.py",
    "modules\gui\race_analysis\accident\accident_data_manager.py",
    "modules\gui\partupdated_analysis\parts_analysis_mdi.py",
    "modules\gui\qualifying_prediction\qualifying_prediction_mdi.py",
    "modules\gui\fp2_qualifying_prediction\fp2_qualifying_prediction_mdi.py",
    "modules\gui\multi_season\season_start_reaction\season_start_reaction_mdi.py",
    "modules\gui\live_timing\core\local_source.py",
    "modules\gui\multi_season\pole_defense\pole_defense_mdi.py",
    "modules\gui\lap_analysis\rpm_analysis\rpm_analysis_mdi.py",
    "modules\gui\lap_analysis\timediff_analysis\timediff_analysis_mdi.py",
    "modules\gui\lap_analysis\traffic_timeline_analysis\traffic_timeline_analysis_mdi.py",
    "modules\gui\lap_analysis\telemetry_data_loader_base.py",
    "modules\gui\lap_analysis\Throttle_analysis\throttle_analysis_mdi.py",
    "modules\gui\lap_analysis\speed_analysis\speed_analysis_mdi.py",
    "modules\gui\lap_analysis\Throttle_analysis\throttle_box_plot_analysis\throttle_box_plot_analysis_mdi.py",
    "modules\gui\lap_analysis\speed_analysis\straight_line_speed_loader.py",
    "modules\gui\lap_analysis\speeddiff_analysis\speeddiff_analysis_mdi.py",
    "modules\gui\lap_analysis\Throttle_analysis\throttle_line_chart_analysis\throttle_line_chart_data_loader.py",
    "modules\gui\lap_analysis\lap_box_plot\lap_box_plot_analysis_mdi.py",
    "modules\gui\lap_analysis\gear_analysis\gear_analysis_mdi.py",
    "modules\gui\lap_analysis\distancediff_analysis\distancediff_analysis_mdi.py",
    "modules\gui\lap_analysis\ideal_lap\ideal_lap_sector_heatmap\ideal_lap_sector_heatmap_mdi.py",
    "modules\gui\lap_analysis\ideal_lap\ideal_lap_ranking_table\ideal_lap_ranking_table_mdi.py",
    "modules\gui\lap_analysis\ideal_lap\ideal_lap_sector_comparison\ideal_lap_sector_comparison_mdi.py",
    "modules\gui\lap_analysis\acceleration_analysis\acceleration_analysis_mdi.py",
    "modules\gui\driver_standings\driver_standings_mdi.py",
    "modules\gui\driver_race\lap_box_plot_analysis\lap_box_plot_analysis_mdi.py",
    "modules\gui\lap_analysis\brake_analysis\brake_analysis_mdi.py",
    "modules\gui\driver_race\detailed_lap_analysis\driverlap_analysis_mdi.py",
    "modules\gui\all_drivers\max_speed\max_speed_data_loader.py",
    "modules\gui\diagnostics\objgraph_window.py",
    "modules\gui\all_drivers\corner_performance\corner_performance_loader.py"
)

$count = 0
$fixed = 0
$skipped = 0

foreach ($file in $files) {
    $count++
    $filePath = Join-Path $PSScriptRoot $file
    
    if (-not (Test-Path $filePath)) {
        Write-Host "[$count/$($files.Count)] ⚠️  跳過（檔案不存在）: $file" -ForegroundColor Yellow
        $skipped++
        continue
    }
    
    $content = Get-Content $filePath -Raw -Encoding UTF8
    
    # 檢查是否已經有 verify=certifi.where()
    if ($content -match 'verify\s*=\s*certifi\.where\(\)') {
        Write-Host "[$count/$($files.Count)] ⏭️  跳過（已修復）: $file" -ForegroundColor Gray
        $skipped++
        continue
    }
    
    # 檢查是否有 import certifi
    if ($content -notmatch 'import certifi') {
        Write-Host "[$count/$($files.Count)] ⚠️  跳過（需手動檢查）: $file" -ForegroundColor Yellow
        $skipped++
        continue
    }
    
    # 修復 requests.post 和 requests.get
    $modified = $false
    
    # Pattern 1: requests.post( ... timeout=X)
    if ($content -match 'requests\.post\([^)]+timeout\s*=\s*[^,)]+\)') {
        $content = $content -replace '(timeout\s*=\s*[^,)]+)([\s\n\r]*\))', '$1,${2}verify=certifi.where()  # ✅ SSL 證書（EXE 必須）${2}'
        $modified = $true
    }
    
    # Pattern 2: requests.get( ... timeout=X)
    if ($content -match 'requests\.get\([^)]+timeout\s*=\s*[^,)]+\)') {
        $content = $content -replace '(timeout\s*=\s*[^,)]+)([\s\n\r]*\))', '$1,${2}verify=certifi.where()  # ✅ SSL 證書（EXE 必須）${2}'
        $modified = $true
    }
    
    if ($modified) {
        Set-Content $filePath -Value $content -Encoding UTF8 -NoNewline
        Write-Host "[$count/$($files.Count)] ✅ 已修復: $file" -ForegroundColor Green
        $fixed++
    } else {
        Write-Host "[$count/$($files.Count)] ⚠️  未匹配: $file" -ForegroundColor Yellow
        $skipped++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 修復完成" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "總計: $count 個檔案"
Write-Host "已修復: $fixed"
Write-Host "跳過: $skipped"
