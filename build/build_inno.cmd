@echo off
title PST Inno Setup Installer Build
cd /d "%~dp0\.."
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
if not exist .venv\Scripts\python.exe (
    echo Creating virtual environment with uv...
    uv venv .venv
)
echo Syncing dependencies...
uv sync
uv run python build\build_inno.py %*
pause
exit /b %errorlevel%
