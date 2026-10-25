@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set /a JOBS=%NUMBER_OF_PROCESSORS%-1
if %JOBS% LSS 1 set JOBS=1
if %JOBS% GTR 16 set JOBS=16
echo [1/3] V15 feature extraction with %JOBS% processes (typically 10-40 min)...
"%PY%" run_features.py --data "..\dataset_extracted" --results "..\results_v11" --out "..\results_v15" --jobs %JOBS% || goto :err
echo [2/3] V15 statistics...
"%PY%" analysis\v15_stats.py "..\results_v11" "..\results_v15" || goto :err
echo [3/3] Step-regularity screen...
"%PY%" analysis\sr_screen.py "..\results_v11" "..\results_v15\sr_screen.json" > "..\results_v15\sr_screen_log.txt" || goto :err
echo.
echo DONE. Results are in Voisard2025\results_v15 (results_v11 is not modified)
pause
exit /b 0
:err
echo.
echo FAILED. Please send a screenshot of the messages above.
pause
exit /b 1
