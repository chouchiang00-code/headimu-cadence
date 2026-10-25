@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
echo V16 data preparation: (A) pack Voisard head signals, (B) download DUO-GAIT subset from Zenodo
echo Reads ..\dataset_extracted and ..\results_v11 (unchanged), writes ..\v16_data
"%PY%" -u pack_v16.py --data "..\dataset_extracted" --results "..\results_v11" --out "..\v16_data" || goto :err
echo.
echo DONE. Output in Voisard2025\v16_data
pause
exit /b 0
:err
echo.
echo FAILED. Please send a screenshot.
pause
exit /b 1
