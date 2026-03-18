@echo off
echo [*] Installing backend dependencies...
pip install -r requirements.txt
echo [*] Creating data folder...
if not exist "data" mkdir data
echo [*] Starting backend on http://localhost:8000
uvicorn app.main:app --reload --port 8000
