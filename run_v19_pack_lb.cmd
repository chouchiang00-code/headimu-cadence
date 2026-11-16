@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Packing lower-back signals for V19 (about 5-10 minutes)...
"..\.venv\Scripts\python.exe" -u pack_v19_lb.py --data "..\dataset_extracted" --results "..\results_v11" --out "..\v16_data"
if errorlevel 1 (echo FAILED - please send the messages above to Claude) else (echo DONE - file: ..\v16_data\voisard_lb_pack.npz)
pause
