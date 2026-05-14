@echo off
title PalworldSaveTools Launcher
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
python "%~dp0start.py"
pause
exit /b %errorlevel%