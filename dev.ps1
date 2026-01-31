param([switch]$BackendOnly,[switch]$FrontendOnly,[switch]$UseWSL,[string]$PythonEnv="voicecloner")
Set-StrictMode -Version Latest
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Configuration
$BackendStartDelay = 5  # Wait seconds before starting frontend

# Find Python (Conda)
$CondaEnvPath = "$env:USERPROFILE\miniconda3\envs\$PythonEnv\python.exe"
if (-not (Test-Path $CondaEnvPath)) {$CondaEnvPath = "$env:USERPROFILE\anaconda3\envs\$PythonEnv\python.exe"}
if (-not (Test-Path $CondaEnvPath) -and -not $UseWSL) {Write-Host "ERROR: Conda env not found (try -UseWSL for WSL backend)" -ForegroundColor Red; exit 1}

# Find Bun
$BunPath = "$env:USERPROFILE\.bun\bin\bun.exe"
if (-not (Test-Path $BunPath)) {Write-Host "ERROR: Bun not found" -ForegroundColor Red; exit 1}

function StopPort {param([int]$p); Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | % {Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue}}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   AETHER Voice Cloner Dev Server" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Clean ports
Write-Host "[1/4] Cleaning ports 8000, 5173..." -ForegroundColor Yellow
StopPort 8000; StopPort 5173; Start-Sleep -Seconds 1
Write-Host "      Done!" -ForegroundColor Green

# Start Backend
if (-not $FrontendOnly) {
    if ($UseWSL) {
        Write-Host "[2/4] Starting Backend (WSL + ROCm)..." -ForegroundColor Yellow
        $WslPath = $ScriptDir -replace '\\','/' -replace '^([A-Za-z]):','/mnt/$1'.ToLower()
        $wslCmd = "cd $WslPath && source ~/miniconda3/etc/profile.d/conda.sh && conda activate $PythonEnv && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"
        Start-Process wt -ArgumentList "wsl", "-e", "bash", "-c", "`"$wslCmd`"" -ErrorAction SilentlyContinue
        if ($LASTEXITCODE -ne 0) {
            # Fallback for systems without Windows Terminal
            Start-Process powershell -ArgumentList "-NoExit", "-Command", "wsl bash -c '$wslCmd'"
        }
    } else {
        Write-Host "[2/4] Starting Backend (Windows Conda)..." -ForegroundColor Yellow
        $bf = Join-Path $env:TEMP "backend.ps1"
        "Set-Location '$ScriptDir'; & '$CondaEnvPath' -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload" | Out-File $bf -Encoding UTF8
        Start-Process powershell -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-File",$bf -WindowStyle Normal
    }
    Write-Host "      Backend starting at http://localhost:8000" -ForegroundColor Green
}

# Wait for backend to initialize
if (-not $FrontendOnly -and -not $BackendOnly) {
    Write-Host "[3/4] Waiting ${BackendStartDelay}s for backend to initialize..." -ForegroundColor Yellow
    for ($i = $BackendStartDelay; $i -gt 0; $i--) {
        Write-Host -NoNewline "`r      Starting frontend in $i... "
        Start-Sleep -Seconds 1
    }
    Write-Host "`r      Ready!                        " -ForegroundColor Green
}

# Start Frontend
if (-not $BackendOnly) {
    Write-Host "[4/4] Starting Frontend..." -ForegroundColor Yellow
    $ff = Join-Path $env:TEMP "frontend.ps1"
    "Set-Location '$ScriptDir'; & '$BunPath' run dev" | Out-File $ff -Encoding UTF8
    Start-Process powershell -ArgumentList "-NoExit","-ExecutionPolicy","Bypass","-File",$ff -WindowStyle Normal
    Write-Host "      Frontend starting at http://localhost:5173" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   All services started!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "   API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "TIP: Use -UseWSL flag for GPU acceleration (ROCm)" -ForegroundColor DarkGray
Write-Host "Example: .\dev.ps1 -UseWSL" -ForegroundColor DarkGray
