# Run the MVP Streamlit demo (Windows)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..

if (-not (Test-Path .venv\Scripts\python.exe)) {
    Write-Host "Tip: create venv first: python -m venv .venv"
}

if (-not (Test-Path .env)) {
    @"
# Required: https://aistudio.google.com/apikey
GOOGLE_API_KEY=your-google-api-key-here
"@ | Set-Content -Path .env -Encoding utf8
    Write-Host "Created .env — add your GOOGLE_API_KEY before analyzing."
}

python -m streamlit run apps\streamlit_app\app.py