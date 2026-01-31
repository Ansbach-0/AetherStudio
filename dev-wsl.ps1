# =============================================
# WSL + ROCm Development Server
# Para GPUs AMD (RX 7800XT) com aceleração ROCm
# =============================================

param(
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [string]$PythonEnv = "voicecloner",
    [string]$WslDistro = "Ubuntu-22.04"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Configuration
$BackendStartDelay = 7  # WSL needs more time to initialize

# Convert Windows path to WSL path
$WslPath = $ScriptDir -replace '\\','/' -replace '^([A-Za-z]):',{ '/mnt/' + $_.Groups[1].Value.ToLower() }

# Find Bun (for frontend)
$BunPath = "$env:USERPROFILE\.bun\bin\bun.exe"
if (-not (Test-Path $BunPath)) {
    Write-Host "ERROR: Bun not found at $BunPath" -ForegroundColor Red
    exit 1
}

function Stop-PortProcess {
    param([int]$Port)
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | 
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Magenta
Write-Host "   AETHER Voice Cloner - WSL + ROCm Mode" -ForegroundColor Magenta
Write-Host "   GPU Acceleration for AMD Radeon" -ForegroundColor Magenta
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

# Clean ports
Write-Host "[1/4] Cleaning ports 8000, 5173..." -ForegroundColor Yellow
Stop-PortProcess 8000
Stop-PortProcess 5173
Start-Sleep -Seconds 1
Write-Host "      Done!" -ForegroundColor Green

# Start Backend in WSL
if (-not $FrontendOnly) {
    Write-Host "[2/4] Starting Backend (WSL + ROCm)..." -ForegroundColor Yellow
    Write-Host "      WSL Distro: $WslDistro" -ForegroundColor DarkGray
    Write-Host "      Project Path: $WslPath" -ForegroundColor DarkGray
    
    # Build WSL command
    $wslCmd = @"
cd $WslPath && \
source ~/miniconda3/etc/profile.d/conda.sh && \
conda activate $PythonEnv && \
export HSA_OVERRIDE_GFX_VERSION=11.0.0 && \
export PYTORCH_ROCM_ARCH=gfx1100 && \
echo '=== ROCm Backend Starting ===' && \
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'ROCm: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"CPU\"}')" && \
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"@
    
    # Try Windows Terminal first, fallback to powershell
    $wtExists = Get-Command wt -ErrorAction SilentlyContinue
    if ($wtExists) {
        Start-Process wt -ArgumentList "-d", ".", "wsl", "-d", $WslDistro, "--", "bash", "-c", "`"$wslCmd`""
    } else {
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "wsl -d $WslDistro bash -c '$wslCmd'"
    }
    
    Write-Host "      Backend starting at http://localhost:8000" -ForegroundColor Green
}

# Wait for backend to initialize
if (-not $FrontendOnly -and -not $BackendOnly) {
    Write-Host "[3/4] Waiting ${BackendStartDelay}s for WSL backend to initialize..." -ForegroundColor Yellow
    for ($i = $BackendStartDelay; $i -gt 0; $i--) {
        Write-Host -NoNewline "`r      Starting frontend in $i seconds... "
        Start-Sleep -Seconds 1
    }
    Write-Host "`r      Ready!                              " -ForegroundColor Green
}

# Start Frontend
if (-not $BackendOnly) {
    Write-Host "[4/4] Starting Frontend..." -ForegroundColor Yellow
    $ff = Join-Path $env:TEMP "frontend-wsl.ps1"
    "Set-Location '$ScriptDir'; & '$BunPath' run dev" | Out-File $ff -Encoding UTF8
    Start-Process powershell -ArgumentList "-NoExit", "-ExecutionPolicy", "Bypass", "-File", $ff -WindowStyle Normal
    Write-Host "      Frontend starting at http://localhost:5173" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Magenta
Write-Host "   All services started with ROCm!" -ForegroundColor Green
Write-Host "" -ForegroundColor White
Write-Host "   Backend:  http://localhost:8000 (WSL)" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173 (Windows)" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "" -ForegroundColor White
Write-Host "   GPU: AMD Radeon RX 7800XT (ROCm 6.2)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Magenta
Write-Host ""

# Check if backend is responding
Write-Host "Checking backend health..." -ForegroundColor DarkGray
Start-Sleep -Seconds 3
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
    Write-Host "Backend is ONLINE!" -ForegroundColor Green
} catch {
    Write-Host "Backend still initializing... check the WSL terminal" -ForegroundColor Yellow
}
