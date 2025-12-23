# F1T Services Manager - Status Check
# Windows PowerShell Edition

$ErrorActionPreference = "Continue"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T Services Manager - Status Check" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Check PowerShell jobs
Write-Color "[1/3] PowerShell Background Jobs:" "Yellow"
$jobs = Get-Job -ErrorAction SilentlyContinue

if ($jobs) {
    $jobs | Format-Table -Property Id, Name, State, HasMoreData -AutoSize
} else {
    Write-Color "  No jobs running" "Gray"
}

# Check processes
Write-Color "`n[2/3] Related Processes:" "Yellow"

$processChecks = @(
    @{ Name = "Python (API/Update)"; Pattern = "python"; Filter = "*refactored_api*", "*periodic_update*" },
    @{ Name = "Cloudflare Tunnel"; Pattern = "cloudflared"; Filter = "*" }
)

$foundAny = $false
foreach ($check in $processChecks) {
    $processes = Get-Process -Name $check.Pattern -ErrorAction SilentlyContinue
    
    if ($processes) {
        foreach ($proc in $processes) {
            $cmdLine = (Get-WmiObject Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            $isMatch = $false
            
            foreach ($filter in $check.Filter) {
                if ($cmdLine -like $filter) {
                    $isMatch = $true
                    break
                }
            }
            
            if ($isMatch -or $check.Filter -eq "*") {
                Write-Color "  $($check.Name): PID $($proc.Id), CPU: $([math]::Round($proc.CPU, 2))s, Memory: $([math]::Round($proc.WorkingSet64/1MB, 2))MB" "Green"
                $foundAny = $true
            }
        }
    }
}

if (-not $foundAny) {
    Write-Color "  No related processes found" "Gray"
}

# Check log files
Write-Color "`n[3/3] Recent Log Activity:" "Yellow"

$logFiles = @(
    "logs\f1t-api.log",
    "logs\periodic-update.log",
    "logs\cloudflare-tunnel.log"
)

foreach ($logFile in $logFiles) {
    if (Test-Path $logFile) {
        $lastWrite = (Get-Item $logFile).LastWriteTime
        $age = (Get-Date) - $lastWrite
        $ageStr = if ($age.TotalMinutes -lt 1) { "$([math]::Round($age.TotalSeconds))s ago" } 
                  elseif ($age.TotalHours -lt 1) { "$([math]::Round($age.TotalMinutes))m ago" }
                  else { "$([math]::Round($age.TotalHours, 1))h ago" }
        
        $size = [math]::Round((Get-Item $logFile).Length / 1KB, 2)
        $color = if ($age.TotalMinutes -lt 5) { "Green" } else { "Yellow" }
        
        Write-Color "  ${logFile}: ${size}KB, updated $ageStr" $color
    } else {
        Write-Color "  ${logFile}: Not found" "Gray"
    }
}

# Summary
Write-Color "`n============================================================" "Cyan"

$savedJobsFile = "logs\running-services.xml"
if (Test-Path $savedJobsFile) {
    $jobInfo = Import-Clixml -Path $savedJobsFile
    Write-Color " Services registered: $($jobInfo.Count)" "White"
}

Write-Color "`nCommands:" "White"
Write-Color "  View logs:    Get-Content logs\f1t-api.log -Tail 50 -Wait" "Gray"
Write-Color "  Stop all:     .\windows\stop-services.ps1" "Gray"
Write-Color "  Restart:      .\windows\stop-services.ps1; .\windows\start-services.ps1`n" "Gray"
