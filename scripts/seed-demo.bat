@echo off
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."
if exist "%ROOT_DIR%\backend\.venv\Scripts\python.exe" (
    "%ROOT_DIR%\backend\.venv\Scripts\python.exe" "%SCRIPT_DIR%seed_demo.py" %*
) else (
    python "%SCRIPT_DIR%seed_demo.py" %*
)
