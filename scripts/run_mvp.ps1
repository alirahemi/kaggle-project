# Run the MVP Streamlit demo (Windows)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .venv\Scripts\python.exe)) {
    Write-Host "Tip: create venv first: python -m venv .venv"
}

if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "Created .env — add your GOOGLE_API_KEY before analyzing."
}

python -m streamlit run apps\streamlit_app\app.py