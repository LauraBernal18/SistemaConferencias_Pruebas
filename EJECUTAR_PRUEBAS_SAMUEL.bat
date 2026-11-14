@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
  set "PY=venv\Scripts\python.exe"
) else (
  set "PY=python"
)
if not exist reportes mkdir reportes
%PY% -m pytest tests/funcionales/test_hu001.py tests/funcionales/test_hu008.py tests/funcionales/test_hu009.py tests/funcionales/test_hu010.py tests/funcionales/test_hu032.py -v --html=reportes\sprint1_hu001_hu008_hu009_hu010_hu032.html --self-contained-html
pause
