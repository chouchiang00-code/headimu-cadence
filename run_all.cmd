@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
set /a JOBS=%NUMBER_OF_PROCESSORS%-1
if %JOBS% LSS 1 set JOBS=1
if %JOBS% GTR 16 set JOBS=16
echo [1/3] Extracting needed files from the archive (once, about 4-5 GB)...
"%PY%" extract_needed.py "..\downloads\dataset.zip" "..\dataset_extracted" || goto :err
echo [2/3] Format check...
"%PY%" run_pipeline.py inspect --data "..\dataset_extracted" --out "..\results_v11_inspect" --jobs %JOBS% --n 3 > "..\results_v11_inspect_log.txt" 2>&1 || (echo Format check failed, see Voisard2025\results_v11_inspect_log.txt & goto :err)
echo [3/3] Full analysis with %JOBS% processes (typically 10-60 min)...
"%PY%" run_pipeline.py run --data "..\dataset_extracted" --out "..\results_v11" --jobs %JOBS% || goto :err
echo.
echo DONE. Results are in Voisard2025\results_v11
pause
exit /b 0
:err
echo.
echo FAILED. Please send a screenshot of the messages above.
pause
exit /b 1
