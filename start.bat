@echo off
echo Starting Developer Assistant...
echo.

echo [1/2] Starting FastAPI Backend...
start "FastAPI Backend" cmd /k "uvicorn main:app --reload"

timeout /t 3 /nobreak > nul

echo [2/2] Starting React UI...
cd ui
start "React UI" cmd /k "npm run dev"

echo.
echo ========================================
echo Developer Assistant is starting!
echo ========================================
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to stop all services...
pause > nul

taskkill /FI "WindowTitle eq FastAPI Backend*" /T /F
taskkill /FI "WindowTitle eq React UI*" /T /F
