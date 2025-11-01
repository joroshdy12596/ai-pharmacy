@echo off
REM Batch wrapper to run the Django management command cleanup_empty_stock and append output to a log
SET VENV=%~dp0venv\Scripts\activate
SET PY=%~dp0venv\Scripts\python.exe
SET LOG=%~dp0cleanup_empty_stock.log

echo ===== %DATE% %TIME% ===== >> "%LOG%"
"%PY%" "%~dp0manage.py" cleanup_empty_stock >> "%LOG%" 2>&1
echo Completed at %TIME% >> "%LOG%"
