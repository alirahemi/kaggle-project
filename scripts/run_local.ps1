# Start local development stack on Windows
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example"
    Copy-Item ".env.example" ".env"
}

Write-Host "Starting infrastructure with docker compose…"
docker compose up -d postgres redis

Write-Host "Waiting for Postgres…"
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    docker compose exec -T postgres pg_isready -U bureaucracy -d bureaucracy 2>$null
    if ($LASTEXITCODE -eq 0) { $ready = $true; break }
    Start-Sleep -Seconds 1
}
if (-not $ready) { throw "Postgres did not become ready in time" }

if ($args -contains "--docker") {
    Write-Host "Starting API and Streamlit containers…"
    docker compose up -d api streamlit
    Write-Host "API:       http://localhost:8000"
    Write-Host "Streamlit: http://localhost:8501"
    exit 0
}

$env:PYTHONPATH = $Root
Write-Host "Starting API gateway…"
Start-Process -NoNewWindow python -ArgumentList "-m", "uvicorn", "apps.api_gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"

Write-Host "Starting Streamlit…"
Start-Process -NoNewWindow streamlit -ArgumentList "run", "apps/streamlit_app/app.py", "--server.port", "8501"

Write-Host "API:       http://localhost:8000"
Write-Host "Streamlit: http://localhost:8501"
