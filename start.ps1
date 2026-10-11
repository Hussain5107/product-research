# start.ps1
# One-click ProductHunter AI launcher for Windows.
# Default mode uses SQLite, so Docker is not required.

$ErrorActionPreference = "Continue"

$here = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $here) { $here = Get-Location }

$backend = Join-Path $here "backend"
$frontend = Join-Path $here "frontend"
$appUrl = "http://127.0.0.1:3000/discovery"
$backendHealthUrl = "http://127.0.0.1:8000/health"
$backendDsn = "sqlite+aiosqlite:///./producthunter.db"

function Test-HttpOk {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 2
        return ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400)
    }
    catch {
        return $false
    }
}

function Wait-ForHttp {
    param(
        [string]$Url,
        [int]$TimeoutSeconds = 60
    )
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpOk -Url $Url) { return $true }
        Start-Sleep -Seconds 2
    }
    return $false
}

function Stop-ProductHunterProcesses {
    param([string]$ProjectPath)

    $processes = Get-CimInstance Win32_Process |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match [regex]::Escape($ProjectPath) -and
            ($_.CommandLine -match "uvicorn" -or $_.CommandLine -match "next" -or $_.CommandLine -match "npm run dev")
        }

    foreach ($process in $processes) {
        try {
            Write-Host "Stopping existing ProductHunter process $($process.ProcessId)..." -ForegroundColor DarkYellow
            Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        }
        catch {
            Write-Host "Could not stop process $($process.ProcessId). Continuing..." -ForegroundColor DarkYellow
        }
    }
}

function Open-Terminal {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )
    $escapedCommand = "cd /d `"$WorkingDirectory`" && $Command"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/k", "title $Title && $escapedCommand" -WindowStyle Normal | Out-Null
}

Write-Host ""
Write-Host "Starting ProductHunter AI..." -ForegroundColor Cyan
Write-Host "Project: $here" -ForegroundColor DarkCyan

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    Write-Host "Node.js/npm was not found. Please install Node.js first." -ForegroundColor Red
    pause
    exit 1
}

if (-not (Test-Path (Join-Path $backend ".venv\Scripts\uvicorn.exe"))) {
    Write-Host "Backend virtual environment is incomplete. Run backend setup first." -ForegroundColor Red
    Write-Host "Expected: backend\.venv\Scripts\uvicorn.exe"
    pause
    exit 1
}

if (-not (Test-Path (Join-Path $frontend "node_modules"))) {
    Write-Host "Installing frontend packages..." -ForegroundColor Yellow
    Push-Location $frontend
    npm install
    Pop-Location
}

Write-Host "Running SQLite database migrations..." -ForegroundColor Yellow
Push-Location $backend
$env:POSTGRES_DSN = $backendDsn
.\.venv\Scripts\alembic.exe upgrade head
Pop-Location

Stop-ProductHunterProcesses -ProjectPath $here
Start-Sleep -Seconds 2

Write-Host "Opening backend server window..." -ForegroundColor Yellow
Open-Terminal `
    -Title "ProductHunter Backend" `
    -WorkingDirectory $backend `
    -Command "set POSTGRES_DSN=$backendDsn && .venv\Scripts\uvicorn.exe app.main:app --host 127.0.0.1 --port 8000"

Write-Host "Opening frontend server window..." -ForegroundColor Yellow
Open-Terminal `
    -Title "ProductHunter Frontend" `
    -WorkingDirectory $frontend `
    -Command "npm run dev -- --hostname 127.0.0.1 --port 3000"

Write-Host "Waiting for backend..." -ForegroundColor Yellow
$backendReady = Wait-ForHttp -Url $backendHealthUrl -TimeoutSeconds 45

Write-Host "Waiting for Product Finder page..." -ForegroundColor Yellow
$frontendReady = Wait-ForHttp -Url $appUrl -TimeoutSeconds 90

if ($backendReady -and $frontendReady) {
    Write-Host "ProductHunter AI is ready." -ForegroundColor Green
    Write-Host "Opening $appUrl" -ForegroundColor Green
    Start-Process $appUrl
}
else {
    Write-Host "Startup is still in progress or one service failed." -ForegroundColor Yellow
    Write-Host "Backend:  $backendHealthUrl"
    Write-Host "Frontend: $appUrl"
    Write-Host "Check the ProductHunter Backend and ProductHunter Frontend windows for details."
}

Write-Host ""
Write-Host "You can close this launcher window. Keep the Backend and Frontend windows open while using the app." -ForegroundColor Cyan
pause
