@echo off
setlocal
cd /d "%~dp0"
echo Starting TridentWear at http://127.0.0.1:8000
echo.
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
echo.
echo Server stopped or failed to start. Review the message above.
pause
