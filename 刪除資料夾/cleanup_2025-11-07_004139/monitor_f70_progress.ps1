# F1T Function 70 Data Collection Progress Monitor (Enhanced)
# Purpose: Monitor 2018-2025 multi-season FP->Q data collection progress
# Version: 2.1 - Added 2025 season support

$jsonFolder = "json\predictionJSON"
$startTime = Get-Date
$lastCount = 0
$noChangeCount = 0
$maxNoChangeSeconds = 300  # 5 minutes without new files = warning

# Expected races per season (approximate)
$expectedRaces = @{
    2018 = 21
    2019 = 21
    2020 = 17  # COVID season
    2021 = 22
    2022 = 22
    2023 = 23
    2024 = 24
    2025 = 24  # 2025 season (collecting for test set)
}
$totalExpected = ($expectedRaces.Values | Measure-Object -Sum).Sum

while ($true) {
    Clear-Host
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "  F1T Function 70 Monitor - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Check JSON file count
    if (Test-Path $jsonFolder) {
        $jsonFiles = Get-ChildItem $jsonFolder -Filter "*.json" | Sort-Object LastWriteTime -Descending
        $totalFiles = $jsonFiles.Count
        
        # Detect if files are being generated
        if ($totalFiles -eq $lastCount) {
            $noChangeCount += 5  # Increment by refresh interval
        } else {
            $noChangeCount = 0
        }
        $lastCount = $totalFiles
        
        # Status indicator
        if ($noChangeCount -gt $maxNoChangeSeconds) {
            $statusText = "[STALLED]"
            $statusColor = "Red"
        } elseif ($totalFiles -gt 0) {
            $statusText = "[ACTIVE]"
            $statusColor = "Green"
        } else {
            $statusText = "[WAITING]"
            $statusColor = "Yellow"
        }
        
        Write-Host "$statusText Current Status:" -ForegroundColor $statusColor
        Write-Host "  Generated JSON files: $totalFiles / $totalExpected expected" -ForegroundColor White
        
        # Check if newest file is recent
        if ($jsonFiles.Count -gt 0) {
            $newestFile = $jsonFiles[0]
            $timeSinceLastFile = (Get-Date) - $newestFile.LastWriteTime
            
            if ($timeSinceLastFile.TotalSeconds -lt 60) {
                Write-Host "  Last file: $([Math]::Floor($timeSinceLastFile.TotalSeconds)) sec ago " -ForegroundColor Green -NoNewline
                Write-Host "[GENERATING]" -ForegroundColor Green
            } elseif ($timeSinceLastFile.TotalMinutes -lt 5) {
                Write-Host "  Last file: $([Math]::Floor($timeSinceLastFile.TotalMinutes)) min ago " -ForegroundColor Yellow -NoNewline
                Write-Host "[PROCESSING]" -ForegroundColor Yellow
            } else {
                Write-Host "  Last file: $([Math]::Floor($timeSinceLastFile.TotalMinutes)) min ago " -ForegroundColor Red -NoNewline
                Write-Host "[STALLED?]" -ForegroundColor Red
            }
        }
        Write-Host ""
        
        # 🆕 FP Session Statistics
        $sessionStats = @{
            FP1 = @{ Total = 0; WithData = 0; Missing = 0 }
            FP2 = @{ Total = 0; WithData = 0; Missing = 0 }
            FP3 = @{ Total = 0; WithData = 0; Missing = 0 }
        }
        
        # Analyze JSON content for FP sessions
        foreach ($file in $jsonFiles | Select-Object -First 50) {  # Check recent 50 files
            try {
                $content = Get-Content $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                
                # Check each FP session
                # 修正：檢查正確的 JSON 結構
                # 結構: practice_sessions.FP1.driver_data
                foreach ($fpSession in @('FP1', 'FP2', 'FP3')) {
                    $sessionStats[$fpSession].Total++
                    
                    # Check if session has valid data
                    $hasData = $false
                    if ($content.practice_sessions -and $content.practice_sessions.$fpSession) {
                        $driverData = $content.practice_sessions.$fpSession.driver_data
                        if ($driverData -and ($driverData | Get-Member -MemberType NoteProperty).Count -gt 0) {
                            $hasData = $true
                        }
                    }
                    
                    if ($hasData) {
                        $sessionStats[$fpSession].WithData++
                    } else {
                        $sessionStats[$fpSession].Missing++
                    }
                }
            } catch {
                # Ignore JSON parsing errors
            }
        }
        
        # Season statistics with expected counts
        $seasonStats = @{}
        foreach ($file in $jsonFiles) {
            # 修正正則表達式：支援賽事名稱含空格（例如 "Great Britain"）
            # 格式: fp_q_data_{year}_{race}_{timestamp}.json
            if ($file.Name -match "fp_q_data_(\d{4})_") {
                $year = $matches[1]
                if (-not $seasonStats.ContainsKey($year)) {
                    $seasonStats[$year] = 0
                }
                $seasonStats[$year]++
            }
        }
        
        # 🆕 Display FP Session Data Quality
        Write-Host "[SESSIONS] FP Data Quality (Recent 50 files):" -ForegroundColor Cyan
        foreach ($fpSession in @('FP1', 'FP2', 'FP3')) {
            $stats = $sessionStats[$fpSession]
            $total = $stats.Total
            $withData = $stats.WithData
            $missing = $stats.Missing
            
            if ($total -gt 0) {
                $percentage = [Math]::Round(($withData / $total) * 100, 1)
                $color = if ($percentage -gt 80) { "Green" } elseif ($percentage -gt 50) { "Yellow" } else { "Red" }
                
                $barLength = [Math]::Min([Math]::Floor($percentage / 5), 20)
                $emptyLength = 20 - $barLength
                $bar = "#" * $barLength
                $emptyBar = "-" * $emptyLength
                
                Write-Host "  $fpSession : [$bar$emptyBar] $withData/$total valid ($percentage%)" -ForegroundColor $color
            } else {
                Write-Host "  $fpSession : [No data analyzed yet]" -ForegroundColor Gray
            }
        }
        Write-Host ""
        
        Write-Host "[STATS] Season Progress:" -ForegroundColor Cyan
        foreach ($year in ($expectedRaces.Keys | Sort-Object)) {
            $count = if ($seasonStats.ContainsKey($year.ToString())) { $seasonStats[$year.ToString()] } else { 0 }
            $expected = $expectedRaces[$year]
            $percentage = if ($expected -gt 0) { [Math]::Round(($count / $expected) * 100, 1) } else { 0 }
            
            # Color based on completion
            $color = if ($percentage -eq 100) { "Green" } elseif ($percentage -gt 0) { "Yellow" } else { "Gray" }
            
            $bar = "#" * [Math]::Min([Math]::Floor($percentage / 2), 50)
            $emptyBar = "-" * (50 - [Math]::Min([Math]::Floor($percentage / 2), 50))
            
            Write-Host "  $year : [$bar$emptyBar] $count/$expected ($percentage%)" -ForegroundColor $color
        }
        Write-Host ""
        
        # Show recent files with FP session indicators (last 8 to see more activity)
        Write-Host "[FILES] Recent 8 files (with FP session status):" -ForegroundColor Magenta
        $recentFiles = $jsonFiles | Select-Object -First 8
        foreach ($file in $recentFiles) {
            $timeAgo = (Get-Date) - $file.LastWriteTime
            $size = [Math]::Round($file.Length / 1KB, 2)
            
            if ($timeAgo.TotalSeconds -lt 60) {
                $timeStr = "$([Math]::Floor($timeAgo.TotalSeconds))s ago"
                $color = "Green"
            } elseif ($timeAgo.TotalMinutes -lt 60) {
                $timeStr = "$([Math]::Floor($timeAgo.TotalMinutes))m ago"
                $color = "Yellow"
            } else {
                $timeStr = "$([Math]::Floor($timeAgo.TotalHours))h ago"
                $color = "Gray"
            }
            
            # Check FP sessions in file
            $fpStatus = ""
            try {
                $content = Get-Content $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
                $fp1 = "X"; $fp2 = "X"; $fp3 = "X"
                
                # 修正：檢查正確的 JSON 結構
                # 結構: practice_sessions.FP1.driver_data
                if ($content.practice_sessions) {
                    if ($content.practice_sessions.FP1.driver_data -and ($content.practice_sessions.FP1.driver_data | Get-Member -MemberType NoteProperty).Count -gt 0) {
                        $fp1 = "OK"
                    }
                    if ($content.practice_sessions.FP2.driver_data -and ($content.practice_sessions.FP2.driver_data | Get-Member -MemberType NoteProperty).Count -gt 0) {
                        $fp2 = "OK"
                    }
                    if ($content.practice_sessions.FP3.driver_data -and ($content.practice_sessions.FP3.driver_data | Get-Member -MemberType NoteProperty).Count -gt 0) {
                        $fp3 = "OK"
                    }
                }
                $fpStatus = " [FP1:$fp1 FP2:$fp2 FP3:$fp3]"
            } catch {
                $fpStatus = " [Parse Error]"
            }
            
            # Extract race name from filename
            # 格式: fp_q_data_{year}_{race}_{timestamp}.json
            # 賽事名稱可能包含空格（例如 "Great Britain"）
            if ($file.Name -match "fp_q_data_(\d{4})_(.+)_\d{8}_\d{6}\.json$") {
                $year = $matches[1]
                $race = $matches[2]
                Write-Host "  [OK] $year $race$fpStatus ($size KB, $timeStr)" -ForegroundColor $color
            } else {
                Write-Host "  [OK] $($file.Name)$fpStatus ($size KB, $timeStr)" -ForegroundColor $color
            }
        }
        Write-Host ""
        
        # Overall progress
        $progress = [Math]::Min(100, ($totalFiles / $totalExpected) * 100)
        $progressBar = "#" * [Math]::Floor($progress / 2)
        $emptyBar = "-" * (50 - [Math]::Floor($progress / 2))
        
        Write-Host "[PROGRESS] Overall Completion:" -ForegroundColor Yellow
        Write-Host "  [$progressBar$emptyBar] $([Math]::Round($progress, 1))%" -ForegroundColor Cyan
        
        # Time estimation
        $elapsed = (Get-Date) - $startTime
        if ($totalFiles -gt 0 -and $elapsed.TotalMinutes -gt 1) {
            $ratePerMinute = $totalFiles / $elapsed.TotalMinutes
            $remaining = $totalExpected - $totalFiles
            $estimatedMinutes = if ($ratePerMinute -gt 0) { $remaining / $ratePerMinute } else { 0 }
            
            if ($estimatedMinutes -gt 60) {
                $etaText = "$([Math]::Round($estimatedMinutes / 60, 1)) hours"
            } else {
                $etaText = "$([Math]::Round($estimatedMinutes, 0)) minutes"
            }
            
            Write-Host "  Rate: $([Math]::Round($ratePerMinute, 2)) files/min | ETA: $etaText" -ForegroundColor Gray
        }
        Write-Host ""
        
    } else {
        Write-Host "[WARNING] Folder not found: $jsonFolder" -ForegroundColor Red
        Write-Host ""
    }
    
    # Elapsed time
    $elapsed = (Get-Date) - $startTime
    Write-Host "[TIME] Running for: $($elapsed.Hours):$($elapsed.Minutes.ToString('00')):$($elapsed.Seconds.ToString('00'))" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[TIP] Press Ctrl+C to stop monitoring" -ForegroundColor Gray
    Write-Host "================================================================================" -ForegroundColor Cyan
    
    Start-Sleep -Seconds 5
}
