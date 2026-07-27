@echo off
title PalworldSaveTools (faulthandler)
cd /d "%~dp0"

where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)

set PYTHONFAULTHANDLER=1
uv run python src/palworld_aio/main.py
set "EXIT_CODE=%errorlevel%"
if %EXIT_CODE% neq 0 pause
exit /b %EXIT_CODE%
