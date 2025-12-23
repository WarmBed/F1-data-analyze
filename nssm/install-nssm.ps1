# F1T NSSM Installer - Automatic Download and Setup
# Version: 1.0.0
# Purpose: Download and install NSSM (Non-Sucking Service Manager)

$ErrorActionPreference = "Stop"

function Write-Color($msg, $color = "White") {
    Write-Host $msg -ForegroundColor $color
}

Write-Color "`n============================================================" "Cyan"
Write-Color "F1T NSSM Installer - Windows Service Manager" "Cyan"
Write-Color "============================================================`n" "Cyan"

# Configuration
$nssmVersion = "2.24"
$nssmUrl = "https://nssm.cc/release/nssm-$nssmVersion.zip"
$downloadPath = "$PSScriptRoot\downloads"
$nssmZip = "$downloadPath\nssm-$nssmVersion.zip"
$nssmExtractPath = "$PSScriptRoot\nssm-$nssmVersion"
$nssmExePath = "$nssmExtractPath\win64\nssm.exe"

# Detect system architecture
$is64bit = [Environment]::Is64BitOperatingSystem
$arch = if ($is64bit) { "win64" } else { "win32" }

Write-Color "[1/6] Checking system architecture..." "Yellow"
Write-Color "  System: Windows $arch" "White"
if ($is64bit) {
    Write-Color "  OK 64-bit system detected" "Green"
} else {
    Write-Color "  WARNING 32-bit system detected" "Yellow"
}

# Check if NSSM is already installed
Write-Color "`n[2/6] Checking existing NSSM installation..." "Yellow"
$existingNssm = Get-Command nssm -ErrorAction SilentlyContinue
if ($existingNssm) {
    $nssmPath = $existingNssm.Source
    Write-Color "  OK NSSM already installed: $nssmPath" "Green"
    
    $response = Read-Host "`n  Continue with download? (y/n)"
    if ($response -ne 'y') {
        Write-Color "`n  INFO Using existing NSSM installation" "Cyan"
        Write-Color "  Location: $nssmPath`n" "Gray"
        exit 0
    }
}

# Create download directory
Write-Color "`n[3/6] Creating download directory..." "Yellow"
if (-not (Test-Path $downloadPath)) {
    New-Item -ItemType Directory -Force -Path $downloadPath | Out-Null
    Write-Color "  OK Directory created: $downloadPath" "Green"
} else {
    Write-Color "  OK Directory exists: $downloadPath" "Green"
}

# Download NSSM
Write-Color "`n[4/6] Downloading NSSM $nssmVersion..." "Yellow"
if (Test-Path $nssmZip) {
    Write-Color "  INFO Archive already exists, skipping download" "Cyan"
} else {
    try {
        Write-Color "  URL: $nssmUrl" "Gray"
        Write-Color "  Downloading..." "Gray"
        
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip -UseBasicParsing
        $ProgressPreference = 'Continue'
        
        $fileSize = [math]::Round((Get-Item $nssmZip).Length / 1MB, 2)
        Write-Color "  OK Downloaded successfully (${fileSize}MB)" "Green"
    } catch {
        Write-Color "  ERROR Failed to download: $_" "Red"
        Write-Color "`n  Manual download:" "Yellow"
        Write-Color "  1. Visit: https://nssm.cc/download" "Gray"
        Write-Color "  2. Download nssm-$nssmVersion.zip" "Gray"
        Write-Color "  3. Place in: $downloadPath" "Gray"
        exit 1
    }
}

# Extract NSSM
Write-Color "`n[5/6] Extracting NSSM..." "Yellow"
if (Test-Path $nssmExtractPath) {
    Write-Color "  INFO Already extracted, removing old version..." "Cyan"
    Remove-Item $nssmExtractPath -Recurse -Force
}

try {
    Expand-Archive -Path $nssmZip -DestinationPath $PSScriptRoot -Force
    Write-Color "  OK Extracted to: $nssmExtractPath" "Green"
} catch {
    Write-Color "  ERROR Failed to extract: $_" "Red"
    exit 1
}

# Verify installation
Write-Color "`n[6/6] Verifying NSSM installation..." "Yellow"
$nssmExe = Join-Path $nssmExtractPath "$arch\nssm.exe"

if (Test-Path $nssmExe) {
    Write-Color "  OK NSSM executable found: $nssmExe" "Green"
    
    # Get version
    $version = & $nssmExe version 2>&1
    Write-Color "  Version: $version" "Gray"
    
    # Create symbolic link for easy access
    $linkPath = "$PSScriptRoot\nssm.exe"
    if (Test-Path $linkPath) {
        Remove-Item $linkPath -Force
    }
    Copy-Item $nssmExe $linkPath -Force
    Write-Color "  OK Shortcut created: $linkPath" "Green"
    
} else {
    Write-Color "  ERROR NSSM executable not found" "Red"
    exit 1
}

# Add to PATH (optional)
Write-Color "`n[Optional] Add NSSM to system PATH?" "Yellow"
Write-Color "  Current NSSM location: $nssmExe" "Gray"
$addToPath = Read-Host "  Add to PATH for system-wide access? (y/n)"

if ($addToPath -eq 'y') {
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $nssmDir = Split-Path $nssmExe
    
    if ($currentPath -notlike "*$nssmDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$currentPath;$nssmDir", "User")
        Write-Color "  OK Added to user PATH: $nssmDir" "Green"
        Write-Color "  NOTE Restart PowerShell to apply changes" "Yellow"
    } else {
        Write-Color "  INFO Already in PATH" "Cyan"
    }
}

# Summary
Write-Color "`n============================================================" "Cyan"
Write-Color " NSSM Installation Complete!" "Green"
Write-Color "============================================================`n" "Cyan"

Write-Color "NSSM Location:" "White"
Write-Color "  Executable: $nssmExe" "Gray"
Write-Color "  Shortcut:   $linkPath" "Gray"

Write-Color "`nNext Steps:" "White"
Write-Color "  1. Install services:  .\nssm\install-services.ps1" "Gray"
Write-Color "  2. Manage services:   .\nssm\manage-services.ps1" "Gray"
Write-Color "  3. Read guide:        .\nssm\NSSM_GUIDE.md" "Gray"

Write-Color "`nQuick Test:" "White"
Write-Color "  .\nssm\nssm.exe version`n" "Gray"
