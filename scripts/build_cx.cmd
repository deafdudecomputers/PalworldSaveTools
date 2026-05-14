@echo off
title PalworldSaveTools Builder (cx_Freeze)
where uv >nul 2>&1 || (
    echo uv not found. Install from https://docs.astral.sh/uv/
    pause
    exit /b 1
)
python "%~dp0build_cx.py" %*
pause
exit /b %errorlevel%
