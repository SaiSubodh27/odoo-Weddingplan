@echo off
cd /d "%~dp0"
echo Starting The Royal Knot Backend...
.venv\Scripts\uvicorn.exe main:app --reload --port 8000
