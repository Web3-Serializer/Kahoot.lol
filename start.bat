@echo off
echo ============================================
echo    KAHOOT BOT DASHBOARD - Local Setup
echo ============================================
echo.

echo [1/4] Installing backend...
cd backend
pip install -r requirements.txt --break-system-packages 2>nul || pip install -r requirements.txt
if not exist "data" mkdir data
echo.

echo [2/4] Installing frontend...
cd ..\frontend
call npm install
echo.

echo [3/4] Starting backend...
cd ..\backend
start "Kahoot Backend" cmd /k "uvicorn app.main:app --reload --port 8000"
timeout /t 3 /nobreak >nul

echo [4/4] Creating admin account...
curl -s -X POST http://localhost:8000/api/admin/init 2>nul
echo.
echo.

echo [*] Starting frontend...
cd ..\frontend
start "Kahoot Frontend" cmd /k "npm run dev"

echo.
echo ============================================
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:5173
echo ============================================
echo.
echo    Admin account created automatically.
echo    Check the backend terminal for the token.
echo.
pause
