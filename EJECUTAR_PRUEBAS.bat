@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
  set "PY=venv\Scripts\python.exe"
) else (
  set "PY=python"
)
if not exist reportes mkdir reportes
%PY% -m pytest tests/funcionales/test_hu006.py tests/funcionales/test_hu030.py tests/funcionales/test_hu031.py -v --html=reportes\sprint1_hu006_hu030_hu031.html --self-contained-html
pause
