@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
"%PY%" -u prep3_v16.py ".." || goto :err
echo.
echo DONE.
pause
exit /b 0
:err
echo FAILED. Please send a screenshot.
pause
exit /b 1
