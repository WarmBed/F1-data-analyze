# Move Existing NSSM Logs to nssm\logs Directory
# Purpose: Migrate log files from logs\ to nssm\logs\

$ErrorActionPreference = "Continue"

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  NSSM Log Migration Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$projectRoot = Split-Path $PSScriptRoot -Parent
$oldLogsDir = Join-Path $projectRoot "logs"
$newLogsDir = Join-Path $PSScriptRoot "logs"

Write-Host "[INFO] Source directory: $oldLogsDir" -ForegroundColor Yellow
Write-Host "[INFO] Target directory: $newLogsDir`n" -ForegroundColor Yellow

# Define NSSM log files to migrate
$nssmLogFiles = @(
    "f1t-api.log",
    "f1t-api.error.log",
    "periodic-update.log",
    "periodic-update.error.log",
    "cloudflare-tunnel.log",
    "cloudflare-tunnel.error.log"
)

# Check if old logs directory exists
if (-not (Test-Path $oldLogsDir)) {
    Write-Host "[ERROR] Source directory not found: $oldLogsDir" -ForegroundColor Red
    pause
    exit 1
}

# Ensure new logs directory exists
if (-not (Test-Path $newLogsDir)) {
    Write-Host "[INFO] Creating target directory..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $newLogsDir | Out-Null
    Write-Host "[SUCCESS] Directory created: $newLogsDir`n" -ForegroundColor Green
} else {
    Write-Host "[INFO] Target directory exists`n" -ForegroundColor Green
}

# Migrate each log file
$movedCount = 0
$notFoundCount = 0

foreach ($logFile in $nssmLogFiles) {
    $sourcePath = Join-Path $oldLogsDir $logFile
    $targetPath = Join-Path $newLogsDir $logFile
    
    if (Test-Path $sourcePath) {
        Write-Host "[MOVING] $logFile..." -ForegroundColor Yellow
        
        try {
            # If target exists, append content
            if (Test-Path $targetPath) {
                Write-Host "  -> Target exists, appending content..." -ForegroundColor Cyan
                $sourceContent = Get-Content $sourcePath -Raw
                Add-Content -Path $targetPath -Value "`n--- Migrated from logs\ ---`n$sourceContent"
                Remove-Item $sourcePath -Force
            } else {
                # Move file
                Move-Item -Path $sourcePath -Destination $targetPath -Force
            }
            
            Write-Host "  -> [SUCCESS] Moved to nssm\logs\" -ForegroundColor Green
            $movedCount++
        }
        catch {
            Write-Host "  -> [ERROR] Failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "[SKIP] $logFile (not found)" -ForegroundColor Gray
        $notFoundCount++
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Migration Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Files moved:     $movedCount" -ForegroundColor Green
Write-Host "Files not found: $notFoundCount" -ForegroundColor Yellow
Write-Host "Total processed: $($nssmLogFiles.Count)`n" -ForegroundColor White

if ($movedCount -gt 0) {
    Write-Host "[INFO] NSSM services need to be reconfigured to use new log paths." -ForegroundColor Yellow
    Write-Host "[INFO] Please run: .\nssm\install-services.ps1 to update configuration.`n" -ForegroundColor Yellow
}

Write-Host "[COMPLETE] Log migration finished.`n" -ForegroundColor Green
pause
