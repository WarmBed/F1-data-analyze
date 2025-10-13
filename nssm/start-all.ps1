# Quick Start F1T Services (Run as Administrator)
# This script will start all F1T services

#Requires -RunAsAdministrator

Write-Host "`nStarting F1T Services..." -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

$services = @("F1T-API", "F1T-PeriodicUpdate", "F1T-CloudflareTunnel")

foreach ($svcName in $services) {
    $svc = Get-Service -Name $svcName -ErrorAction SilentlyContinue
    if ($svc) {
        if ($svc.Status -eq 'Stopped') {
            Write-Host "  Starting $svcName..." -ForegroundColor Yellow
            try {
                Start-Service -Name $svcName -ErrorAction Stop
                Start-Sleep -Seconds 2
                $newStatus = (Get-Service -Name $svcName).Status
                if ($newStatus -eq 'Running') {
                    Write-Host "    OK Started successfully" -ForegroundColor Green
                } else {
                    Write-Host "    WARNING Status: $newStatus" -ForegroundColor Yellow
                }
            } catch {
                Write-Host "    ERROR Failed: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "  INFO $svcName already running" -ForegroundColor Cyan
        }
    } else {
        Write-Host "  ERROR Service not found: $svcName" -ForegroundColor Red
    }
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Checking final status...`n" -ForegroundColor Cyan

Get-Service F1T-* | Format-Table Name, Status, StartType, DisplayName -AutoSize

Write-Host "`nTest API:" -ForegroundColor White
Write-Host "  Invoke-WebRequest http://localhost:8000/health" -ForegroundColor Gray

Write-Host "`nView logs:" -ForegroundColor White
Write-Host "  Get-Content logs\f1t-api.log -Tail 50 -Wait`n" -ForegroundColor Gray
