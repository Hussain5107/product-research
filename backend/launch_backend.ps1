# launch_backend.ps1
# Run this from the backend folder after installing dependencies.

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ($scriptDir) {
    Set-Location $scriptDir
}

if (-not (Test-Path ".venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not found. Create it first:"
    Write-Host "python -m venv .venv"
    exit 1
}

& ".venv\Scripts\Activate.ps1"
pip install -r requirements.txt --quiet

if (-not $env:POSTGRES_DSN) {
    $env:POSTGRES_DSN = "postgresql+psycopg://producthunter:producthunter_local_dev_password@localhost:5432/producthunter"
}
if (-not $env:REDIS_URL) {
    $env:REDIS_URL = "redis://localhost:6379/0"
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created backend/.env from template."
}

alembic upgrade head

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
