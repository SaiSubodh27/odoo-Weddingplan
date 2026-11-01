# The Royal Knot - Start All Servers
# Run this from the project root: .\start-servers.ps1

Write-Host ""
Write-Host "  * THE ROYAL KNOT - Wedding Management System" -ForegroundColor DarkYellow
Write-Host "  Starting all servers..." -ForegroundColor Gray
Write-Host ""

# Kill anything on 8000 or 5173
@(8000, 5173) | ForEach-Object {
    $port = $_
    $pids = (Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue |
             Where-Object State -in @('Listen','Bound') |
             Select-Object -ExpandProperty OwningProcess -Unique)
    if ($pids) {
        $pids | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        Write-Host "  Freed port $port" -ForegroundColor DarkGray
        Start-Sleep -Milliseconds 500
    }
}

# Resolve project root and python path dynamically
$rootDir = $PSScriptRoot
$backendDir = Join-Path $rootDir "backend"

$pythonExe = "python"
if (Test-Path "C:\RoyalKnot\venv\Scripts\python.exe") {
    $pythonExe = "C:\RoyalKnot\venv\Scripts\python.exe"
}
elseif (Test-Path (Join-Path $backendDir ".venv\Scripts\python.exe")) {
    $pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"
}
elseif (Test-Path (Join-Path $rootDir ".venv\Scripts\python.exe")) {
    $pythonExe = Join-Path $rootDir ".venv\Scripts\python.exe"
}

# Start Backend
Write-Host "  [1/2] Starting FastAPI backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
$backendJob = Start-Job -ScriptBlock {
    param($bDir, $py)
    Set-Location $bDir
    & $py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
} -ArgumentList $backendDir, $pythonExe

Start-Sleep -Seconds 4

# Verify backend
$retries = 0
$backendOk = $false
while ($retries -lt 6 -and -not $backendOk) {
    try {
        $r = Invoke-RestMethod "http://127.0.0.1:8000/api/v1/health" -TimeoutSec 3 -ErrorAction Stop
        if ($r.status -eq "operational") { $backendOk = $true }
    }
    catch {
        # waiting for server startup
    }
    if (-not $backendOk) {
        Start-Sleep -Seconds 2
        $retries++
    }
}

if ($backendOk) {
    Write-Host "  [OK] Backend healthy (database connected)" -ForegroundColor Green
}
else {
    Write-Host "  [ERROR] Backend failed to start - check logs" -ForegroundColor Red
}

# Start Frontend
Write-Host "  [2/2] Starting Vite frontend on http://localhost:5173 ..." -ForegroundColor Cyan
$frontendJob = Start-Job -ScriptBlock {
    param($rDir)
    Set-Location $rDir
    npm --prefix frontend run dev
} -ArgumentList $rootDir

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "  * All servers running!" -ForegroundColor DarkYellow
Write-Host "  +---------------------------------------------+" -ForegroundColor DarkGray
Write-Host "  |  Employee Portal  ->  http://localhost:5173  |" -ForegroundColor White
Write-Host "  |  Client Register  ->  http://localhost:5173/client-register |" -ForegroundColor White
Write-Host "  |  Backend API      ->  http://localhost:8000  |" -ForegroundColor White
Write-Host "  +---------------------------------------------+" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Press Ctrl+C to stop all servers." -ForegroundColor Gray
Write-Host ""

# Keep running and stream logs
try {
    while ($true) {
        Receive-Job $backendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  [backend] $_" -ForegroundColor DarkCyan }
        Receive-Job $frontendJob -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  [frontend] $_" -ForegroundColor DarkMagenta }
        Start-Sleep -Seconds 2
    }
}
finally {
    Stop-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Remove-Job $backendJob, $frontendJob -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "  Servers stopped." -ForegroundColor Gray
}
