Set-Location -Path $PSScriptRoot
Write-Host "Starting The Royal Knot Backend on http://localhost:8000..." -ForegroundColor Cyan
& ".\.venv\Scripts\uvicorn.exe" main:app --reload --port 8000
