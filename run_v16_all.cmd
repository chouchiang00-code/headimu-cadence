@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set "PY=..\.venv\Scripts\python.exe"
if not exist "%PY%" set "PY=python"
echo V16 analyses: reads ..\results_v11, ..\v16_data, ..\external\duogait\processed.zip; writes ..\results_v16
if not exist "..\results_v16" mkdir "..\results_v16"
"%PY%" -u prep4_merge_duogait.py ..\v16_data "..\results_v16\ext" || goto :err
"%PY%" -u run_v16_endtoend.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" --jobs 2 || goto :err
"%PY%" -u run_v16_b2tune.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" || goto :err
"%PY%" -u run_v16_b2t_eval.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" || goto :err
"%PY%" -u analysis\v16_endtoend_stats.py "..\results_v16\e2e" || goto :err
"%PY%" -u analysis\v16_gyro_offset.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" || goto :err
"%PY%" -u run_v16_trust.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" "..\results_v16\trust" || goto :err
"%PY%" -u analysis\v16_trust_extra.py "..\results_v16\trust" || goto :err
"%PY%" -u run_v16_external.py "..\results_v16\ext\duogait_head.npz" "..\external\duogait\processed.zip" "..\results_v16\e2e" "..\results_v16\trust" "..\results_v16\ext" || goto :err
"%PY%" -u analysis\v16_external_stats.py "..\results_v16\ext" || goto :err
"%PY%" -u run_v16_sensitivity.py "..\v16_data\voisard_head_pack.npz" "..\results_v11" "..\results_v16\e2e" "..\results_v16\sens" || goto :err
"%PY%" -u analysis\v15_text_numbers.py "..\results_v11" || goto :err
"%PY%" -u figures_results\make_figs_v16.py "..\results_v16\e2e" "..\results_v16\trust" "..\results_v16\figures" "..\results_v11" "..\results_v16\ext" || goto :err
echo.
echo DONE. Output in ..\results_v16
pause
exit /b 0
:err
echo.
echo FAILED. Please send a screenshot.
pause
exit /b 1
