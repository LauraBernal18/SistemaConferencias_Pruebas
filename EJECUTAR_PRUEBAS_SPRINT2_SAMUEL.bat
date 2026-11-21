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
%PY% -m pytest tests/funcionales/test_hu004.py tests/funcionales/test_hu011.py tests/funcionales/test_hu012.py tests/funcionales/test_hu014.py -v --html=reportes\sprint2_hu004_hu011_hu012_hu014.html --self-contained-html
pause
