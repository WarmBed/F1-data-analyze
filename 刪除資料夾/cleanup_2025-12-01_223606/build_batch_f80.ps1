# F1T Batch Download Function 80 - Build Script
# Usage: .\build_batch_f80.ps1

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  F1T Batch F80 - EXE Build Tool" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Stage 1: Environment Check
Write-Host "`n[1/4] Checking environment..." -ForegroundColor Yellow

# Check Python
$pythonVersion = python --version 2>&1
Write-Host "  Python: $pythonVersion" -ForegroundColor Green

# Check PyInstaller
try {
    $pyinstallerVersion = python -c "import PyInstaller; print(PyInstaller.__version__)" 2>&1
    Write-Host "  PyInstaller: $pyinstallerVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] PyInstaller not installed! Run: pip install pyinstaller" -ForegroundColor Red
    exit 1
}

# Check required files
$requiredFiles = @(
    "batch_download_function80.py",
    "F1T_Batch_F80.spec",
    "f1_analysis_modular_main.py",
    "image/logo.ico"
)

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] Missing: $file" -ForegroundColor Red
        exit 1
    }
}

# Stage 2: Clean old files
Write-Host "`n[2/4] Cleaning old files..." -ForegroundColor Yellow

if (Test-Path "dist/F1T_Batch_F80.exe") {
    Remove-Item "dist/F1T_Batch_F80.exe" -Force
    Write-Host "  Removed old EXE file" -ForegroundColor Gray
}

if (Test-Path "build/F1T_Batch_F80") {
    Remove-Item "build/F1T_Batch_F80" -Recurse -Force
    Write-Host "  Removed old build folder" -ForegroundColor Gray
}

# Stage 3: Run PyInstaller
Write-Host "`n[3/4] Running PyInstaller..." -ForegroundColor Yellow
Write-Host "  This may take a few minutes..." -ForegroundColor Gray

$startTime = Get-Date

python -m PyInstaller F1T_Batch_F80.spec --noconfirm

$endTime = Get-Date
$duration = ($endTime - $startTime).TotalSeconds

if ($LASTEXITCODE -eq 0) {
    Write-Host "  [OK] Build complete! (Duration: $([math]::Round($duration, 1)) seconds)" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] Build failed!" -ForegroundColor Red
    exit 1
}

# Stage 4: Verify output
Write-Host "`n[4/4] Verifying output..." -ForegroundColor Yellow

$exePath = "dist/F1T_Batch_F80.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    $sizeMB = [math]::Round($fileInfo.Length / 1MB, 2)
    
    Write-Host "  [OK] EXE file generated" -ForegroundColor Green
    Write-Host "       Path: $($fileInfo.FullName)" -ForegroundColor Cyan
    Write-Host "       Size: $sizeMB MB" -ForegroundColor Cyan
    Write-Host "       Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
    
    Write-Host "`n[DONE]" -ForegroundColor Green
    Write-Host "  EXE Location: $exePath" -ForegroundColor Cyan
    Write-Host "  Usage:" -ForegroundColor Yellow
    Write-Host "    .\dist\F1T_Batch_F80.exe                    # Download all completed races" -ForegroundColor Gray
    Write-Host "    .\dist\F1T_Batch_F80.exe --force            # Force regenerate" -ForegroundColor Gray
    Write-Host "    .\dist\F1T_Batch_F80.exe --races Qatar      # Download specific race" -ForegroundColor Gray
} else {
    Write-Host "  [ERROR] EXE file not found!" -ForegroundColor Red
    exit 1
}
